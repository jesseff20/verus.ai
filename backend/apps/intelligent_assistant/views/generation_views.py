"""
Views de geração de documentos jurídicos (dinâmico, streaming, regeneração).
"""
import json
import logging
import re
import threading
import queue as queue_module

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from django.db import transaction
from django.http import StreamingHttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from ..services.pgvector_service import PgVectorService
from ..services.rate_limit import check_rate_limit
from ..models import (
    IntelligentSession,
    DocumentBlueprint,
    BlueprintSection,
    BlueprintSubSection,
    GenerationSession,
    SectionGeneration,
    SectionAgentConfig,
    GeneratedDocument,
)
from ._helpers import _format_sse_event, _format_section_fields_content, _authenticate_request
from ..utils import normalize_subsection_breaks

logger = logging.getLogger(__name__)


@extend_schema(
    summary="Gerar Peça Jurídica com Blueprint Dinâmico",
    description="""
    Gera uma peça jurídica usando um blueprint específico.

    **Parâmetros:**
    - `objective`: Descrição do caso e objetivo da peça (obrigatório)
    - `blueprint_id` ou `blueprint_name`: Blueprint a usar (opcional, default: blueprint padrão)
    - `collection_name`: ID da sessão para buscar embeddings (opcional)
    - `section_ids`: Lista de IDs de seções a gerar (opcional, default: todas)

    **Blueprints disponíveis:**
    - Petição Inicial Cível - CPC/2015: 5 seções
    - Contestação Cível - CPC/2015: 5 seções
    - Recurso de Apelação - CPC/2015: 4 seções

    O sistema usa DynamicGraphBuilder para criar o grafo de geração
    baseado no blueprint selecionado.
    """,
    tags=["Blueprints"],
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'objective': {
                    'type': 'string',
                    'description': 'Objetivo da contratação'
                },
                'blueprint_id': {
                    'type': 'string',
                    'format': 'uuid',
                    'description': 'ID do blueprint (opcional)'
                },
                'blueprint_name': {
                    'type': 'string',
                    'description': 'Nome do blueprint (opcional)'
                },
                'collection_name': {
                    'type': 'string',
                    'description': 'ID da sessão para RAG (opcional)'
                },
                'section_ids': {
                    'type': 'array',
                    'items': {'type': 'string', 'format': 'uuid'},
                    'description': 'IDs das seções a gerar (opcional)'
                }
            },
            'required': ['objective']
        }
    },
    responses={
        200: OpenApiResponse(description="Peça jurídica gerada com sucesso"),
        400: OpenApiResponse(description="Dados inválidos"),
        404: OpenApiResponse(description="Blueprint não encontrado"),
        500: OpenApiResponse(description="Erro durante geração")
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_etp_dynamic(request):
    """
    Gera peça jurídica usando blueprint dinâmico.

    POST /api/v1/intelligent-assistant/generate/
    """
    # Extrair dados
    objective = request.data.get('objective', '').strip()
    blueprint_id = request.data.get('blueprint_id')
    blueprint_name = request.data.get('blueprint_name')
    collection_name = request.data.get('collection_name', 'default')
    section_ids = request.data.get('section_ids', [])
    sub_section_decisions = request.data.get('sub_section_decisions', {})

    # Validar objective
    if not objective:
        return Response({
            'error': 'O campo "objective" é obrigatório'
        }, status=status.HTTP_400_BAD_REQUEST)

    # Buscar blueprint
    _bp_qs = DocumentBlueprint.objects.select_related('document_type', 'document_type__category')
    try:
        if blueprint_id:
            blueprint = _bp_qs.get(id=blueprint_id, is_active=True)
        elif blueprint_name:
            blueprint = _bp_qs.get(
                name__iexact=blueprint_name,
                is_active=True
            )
        else:
            # Usar blueprint padrão
            blueprint = _bp_qs.filter(
                is_active=True,
                is_default=True
            ).first()

            if not blueprint:
                # Fallback para qualquer blueprint ativo
                blueprint = _bp_qs.filter(is_active=True).first()

            if not blueprint:
                return Response({
                    'error': 'Nenhum blueprint disponível',
                    'detail': 'Configure pelo menos um blueprint ativo no sistema'
                }, status=status.HTTP_404_NOT_FOUND)

    except DocumentBlueprint.DoesNotExist:
        return Response({
            'error': 'Blueprint não encontrado',
            'detail': f'Blueprint "{blueprint_id or blueprint_name}" não existe ou está inativo'
        }, status=status.HTTP_404_NOT_FOUND)

    # Validar seções selecionadas
    if section_ids:
        available_sections = set(
            str(s.id) for s in blueprint.get_ordered_sections()
        )
        invalid_sections = set(section_ids) - available_sections
        if invalid_sections:
            return Response({
                'error': 'Seções inválidas',
                'detail': f'As seguintes seções não pertencem ao blueprint: {list(invalid_sections)}'
            }, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Importar DynamicGraphBuilder
        from ..services.dynamic_graph_builder import DynamicGraphBuilder
        from ..services.llm_provider_service import UnifiedLLMService
        from ..services.knowledge_base_service import KnowledgeBaseService

        # Inicializar serviços (multi-provider)
        llm_service = UnifiedLLMService()
        kb_service = KnowledgeBaseService.get_instance()

        # Criar builder e runner
        builder = DynamicGraphBuilder(llm_service=llm_service, kb_service=kb_service)
        runner = builder.create_runner(blueprint_id=blueprint.id)

        logger.info(f"✅ DynamicGraphBuilder criado para blueprint: {blueprint.name}")
        logger.info(f"   - Seções: {runner.sections.count()}")

        # Criar sessão de geração
        generation_session = GenerationSession.objects.create(
            user=request.user,
            blueprint=blueprint,
            objective=objective,
            status='generating'
        )

        # Selecionar seções
        if section_ids:
            sections_to_generate = BlueprintSection.objects.filter(
                id__in=section_ids,
                blueprint=blueprint,
                is_active=True
            )
        else:
            sections_to_generate = blueprint.get_ordered_sections()

        generation_session.selected_sections.set(sections_to_generate)

        # Criar registros de SectionGeneration
        for section in sections_to_generate:
            SectionGeneration.objects.create(
                session=generation_session,
                section=section,
                status='pending'
            )

        # Executar geração (síncrono por enquanto)
        # TODO: Implementar versão assíncrona com streaming
        import asyncio
        from datetime import datetime

        generation_session.started_at = datetime.now()
        generation_session.save()

        # Preparar input
        initial_state = {
            'objective': objective,
            'collection_name': collection_name,
            'user_id': str(request.user.id),
        }

        # Executar grafo
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            result = loop.run_until_complete(
                runner.run(initial_state)
            )
        finally:
            loop.close()

        # Atualizar sessão
        generation_session.status = 'completed'
        generation_session.completed_at = datetime.now()
        generation_session.save()

        # Atualizar SectionGeneration com resultados
        sections_content = {}
        for section in sections_to_generate:
            section_key = section.section_key
            content = result.get(section_key, '')

            section_gen = SectionGeneration.objects.get(
                session=generation_session,
                section=section
            )
            section_gen.content = content
            section_gen.status = 'validated' if content else 'failed'
            section_gen.is_valid = bool(content)
            section_gen.completed_at = datetime.now()
            section_gen.save()

            sections_content[section_key] = {
                'section_number': section.section_number,
                'section_name': section.section_name,
                'content': content,
                'is_valid': bool(content)
            }

        # Preparar resposta
        response_data = {
            'success': True,
            'session_id': str(generation_session.id),
            'blueprint': {
                'id': str(blueprint.id),
                'name': blueprint.name,
                'section_count': blueprint.section_count
            },
            'sections': sections_content,
            'stats': {
                'total_sections': sections_to_generate.count(),
                'generated_sections': len([s for s in sections_content.values() if s['is_valid']]),
            }
        }

        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"❌ Erro ao gerar documento dinâmico: {str(e)}")
        import traceback
        traceback.print_exc()

        # Atualizar sessão com erro
        if 'generation_session' in locals():
            generation_session.status = 'failed'
            generation_session.error_message = str(e)
            generation_session.save()

        return Response({
            'error': 'Erro ao gerar documento',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    summary="Streaming de Geração com Blueprint Dinâmico",
    description="""
    Gera peça jurídica com blueprint dinâmico usando Server-Sent Events (SSE).

    **Parâmetros (query string):**
    - `objective`: Descrição do caso e objetivo da peça (obrigatório)
    - `blueprint_id` ou `blueprint_name`: Blueprint a usar (opcional)
    - `collection_name`: ID da sessão para RAG (opcional)
    - `section_ids`: IDs das seções separados por vírgula (opcional)

    **Eventos emitidos:**
    - `started`: Início da geração
    - `section_start`: Início de uma seção
    - `section_content`: Conteúdo da seção (streaming)
    - `section_complete`: Seção finalizada
    - `progress`: Progresso geral
    - `completed`: Geração concluída
    - `error`: Erro durante geração
    """,
    tags=["Blueprints"],
    parameters=[
        OpenApiParameter(name='objective', type=str, required=True),
        OpenApiParameter(name='blueprint_id', type=str, required=False),
        OpenApiParameter(name='blueprint_name', type=str, required=False),
        OpenApiParameter(name='collection_name', type=str, required=False),
        OpenApiParameter(name='section_ids', type=str, required=False,
                        description='IDs separados por vírgula'),
    ],
    responses={
        200: OpenApiResponse(description="Stream SSE de eventos")
    }
)
@csrf_exempt
@require_http_methods(["POST"])
def generate_etp_dynamic_stream(request):
    """
    Endpoint SSE para gerar peça jurídica com blueprint dinâmico.

    POST /api/v1/intelligent-assistant/generate-stream/
    Body JSON: { objective, blueprint_id?, blueprint_name?, collection_name?,
                 session_id?, sections?, section_fields_data?, sub_section_decisions? }
    """
    # Autenticar
    user, error_response = _authenticate_request(request)
    if error_response:
        return error_response

    # Rate limiting: max 6 requisições/minuto por usuário
    rate_check = check_rate_limit(request, 'generate-stream', max_requests=6, window_seconds=60)
    if not rate_check['allowed']:
        return JsonResponse({
            'error': f'Limite de geração excedido. Tente novamente em {rate_check["retry_after"]}s.',
            'retry_after_seconds': rate_check['retry_after'],
        }, status=429)

    # Extrair parâmetros do body JSON
    try:
        data = json.loads(request.body) if request.body else {}
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Body JSON inválido'}, status=400)

    objective = data.get('objective', '').strip()
    blueprint_id = data.get('blueprint_id')
    blueprint_name = data.get('blueprint_name')
    collection_name = data.get('collection_name', 'default')
    session_id = data.get('session_id')
    sections_param = data.get('sections', '')
    etp_session_id = str(data.get('etp_session_id', '')).strip()

    # section_fields_data já vem como dict do JSON (sem duplo parse)
    section_fields_data = {}
    raw_fields = data.get('section_fields_data')
    if raw_fields and isinstance(raw_fields, dict):
        section_fields_data = {int(k): v for k, v in raw_fields.items()}

    # sub_section_decisions já vem como dict do JSON
    sub_section_decisions = {}
    raw_decisions = data.get('sub_section_decisions')
    if raw_decisions and isinstance(raw_decisions, dict):
        sub_section_decisions = raw_decisions

    if not objective:
        return JsonResponse({
            'error': 'O parâmetro "objective" é obrigatório'
        }, status=400)

    # Parsear números de seção
    section_numbers = []
    if sections_param:
        try:
            section_numbers = [int(s.strip()) for s in sections_param.split(',') if s.strip()]
        except ValueError:
            return JsonResponse({
                'error': 'O parâmetro "sections" deve conter números separados por vírgula'
            }, status=400)

    # Usar session_id como collection_name se fornecido
    if session_id:
        collection_name = session_id

    def event_stream():
        """Generator que produz eventos SSE."""
        import threading
        cancel_event = threading.Event()
        try:
            # Buscar blueprint
            _bp_qs_stream = DocumentBlueprint.objects.select_related('document_type', 'document_type__category')
            if blueprint_id:
                blueprint = _bp_qs_stream.get(id=blueprint_id, is_active=True)
            elif blueprint_name:
                blueprint = _bp_qs_stream.get(
                    name__iexact=blueprint_name,
                    is_active=True
                )
            else:
                blueprint = (
                    _bp_qs_stream.filter(is_active=True, is_default=True).first()
                    or _bp_qs_stream.filter(is_active=True).first()
                )

            if not blueprint:
                yield _format_sse_event('error', {
                    'message': 'Nenhum blueprint disponível'
                })
                return

            # Seções a gerar
            if section_numbers:
                sections = BlueprintSection.objects.filter(
                    section_number__in=section_numbers,
                    blueprint=blueprint,
                    is_active=True
                ).order_by('order')
            else:
                sections = blueprint.get_ordered_sections()

            total_sections = sections.count()

            # Evento inicial
            yield _format_sse_event('started', {
                'message': f'Iniciando geração com blueprint "{blueprint.name}"',
                'blueprint': {
                    'id': str(blueprint.id),
                    'name': blueprint.name,
                },
                'total_sections': total_sections,
                'sections': [
                    {
                        'id': str(s.id),
                        'number': s.section_number,
                        'name': s.section_name
                    }
                    for s in sections
                ]
            })

            # Importar serviços
            from ..services.dynamic_graph_builder import DynamicGraphBuilder
            from ..services.llm_provider_service import UnifiedLLMService
            from ..services.knowledge_base_service import KnowledgeBaseService
            import queue as queue_module

            llm_service = UnifiedLLMService()
            kb_service = KnowledgeBaseService.get_instance()

            # Fila de eventos granulares do pipeline (para visualização React Flow)
            pipeline_event_queue = queue_module.Queue()
            pipeline_events_log = []  # Coleção persistida no banco
            # Acumulador de tokens por seção e total
            _tokens_by_section = {}  # {section_num: {input: N, output: N}}
            _total_tokens = {'input': 0, 'output': 0}

            def pipeline_event_callback(event_type, data):
                """Callback chamado pelo DynamicGraphBuilder para eventos granulares."""
                # Interceptar llm_usage para acumular tokens (NÃO enviar ao frontend)
                if event_type == 'llm_usage':
                    inp = data.get('input_tokens', 0)
                    outp = data.get('output_tokens', 0)
                    sec = data.get('section')
                    _total_tokens['input'] += inp
                    _total_tokens['output'] += outp
                    if sec is not None:
                        if sec not in _tokens_by_section:
                            _tokens_by_section[sec] = {'input': 0, 'output': 0}
                        _tokens_by_section[sec]['input'] += inp
                        _tokens_by_section[sec]['output'] += outp
                    # Persistir LLMAuditLog no banco
                    try:
                        from ..models import LLMAuditLog
                        LLMAuditLog.objects.create(
                            user=user,
                            session=generation_session,
                            blueprint=blueprint,
                            section_number=sec,
                            section_name=data.get('section_name', ''),
                            call_type=data.get('call_type', 'generate'),
                            attempt_number=data.get('attempt', 1),
                            provider=data.get('provider', ''),
                            model=data.get('model', ''),
                            input_tokens=inp,
                            output_tokens=outp,
                            duration_ms=data.get('duration_ms', 0),
                        )
                    except Exception as e:
                        logger.error(f"Erro ao criar LLMAuditLog: {e}")
                    pipeline_events_log.append({'event': event_type, **data})
                    return  # Não enfileirar para SSE

                pipeline_event_queue.put((event_type, data))
                pipeline_events_log.append({'event': event_type, **data})

            builder = DynamicGraphBuilder(llm_service=llm_service, kb_service=kb_service)
            runner = builder.create_runner(
                blueprint_id=blueprint.id,
                event_callback=pipeline_event_callback,
            )

            # Resolver IntelligentSession - usar effective_session_id para evitar
            # UnboundLocalError causado por reatribuição de session_id no closure
            effective_session_id = session_id
            intelligent_session = None
            if effective_session_id:
                try:
                    intelligent_session = IntelligentSession.objects.get(id=effective_session_id, user=user)
                except IntelligentSession.DoesNotExist:
                    intelligent_session = IntelligentSession.objects.create(
                        user=user,
                        blueprint=blueprint,
                        objective=objective,
                        document_type=blueprint.document_type.code if blueprint.document_type else 'termo_referencia',
                        kb_collection_id='',
                    )
                    effective_session_id = str(intelligent_session.id)
                    yield _format_sse_event('session_updated', {'session_id': effective_session_id})
            else:
                intelligent_session = IntelligentSession.objects.create(
                    user=user,
                    blueprint=blueprint,
                    objective=objective,
                    document_type=blueprint.document_type.code if blueprint.document_type else 'peca_juridica',
                    kb_collection_id='',
                )
                effective_session_id = str(intelligent_session.id)
                yield _format_sse_event('session_updated', {'session_id': effective_session_id})

            # Criar sessão
            generation_session = GenerationSession.objects.create(
                user=user,
                blueprint=blueprint,
                objective=objective,
                status='generating',
                intelligent_session=intelligent_session,
            )
            yield _format_sse_event('generation_session_started', {
                'generation_session_id': str(generation_session.id),
            })
            generation_session.selected_sections.set(sections)

            # Criar registros de SectionGeneration
            for section in sections:
                SectionGeneration.objects.create(
                    session=generation_session,
                    section=section,
                    status='pending'
                )

            # Executar com streaming
            from django.utils import timezone

            generation_session.started_at = timezone.now()
            generation_session.save()

            completed_sections = 0
            processed_sections = set()
            final_state = None  # Capturar último estado para persistência
            structured_sections_content = {}  # Conteúdo de seções com campos estruturados

            _etp_sections_available = set()

            # Processar seções com campos estruturados ANTES do streaming de IA.
            # Seções com section_fields E generator_agent → enviar dados ao LLM
            # (os campos são CONTEXTO, não o conteúdo final).
            # Seções com section_fields SEM generator_agent → dados diretos.
            sections_with_structured_data = []
            sections_with_fields_for_llm = {}  # {section_num: formatted_fields}
            for section in sections:
                section_num = section.section_number
                if section.section_fields:
                    field_values = section_fields_data.get(section_num, {})
                    # Se não há dados preenchidos E ETP tem conteúdo → ETP tem prioridade.
                    # Fallback para template vazio apenas quando não há ETP disponível.
                    if not field_values and section_num in _etp_sections_available:
                        continue
                    content = _format_section_fields_content(section.section_fields, field_values)

                    # Se a seção tem agente gerador OU tem instructions (do blueprint),
                    # os campos são CONTEXTO para o LLM — NÃO conteúdo final.
                    # O LLM gerará o texto jurídico usando esses dados como input.
                    has_generation_capability = bool(section.generator_agent) or bool(
                        section.instructions and section.instructions.strip()
                    )

                    if has_generation_capability and content:
                        sections_with_fields_for_llm[section_num] = content
                        logger.info(
                            f"Seção {section_num} ({section.section_name}): "
                            f"campos estruturados serão enviados ao LLM como contexto"
                        )
                        continue  # Será processada pelo grafo de IA

                    if content:
                        sections_with_structured_data.append(section_num)
                        structured_sections_content[section_num] = {
                            'content': content,
                            'section_name': section.section_name,
                            'field_values': field_values
                        }

                        # Emitir eventos SSE para seção estruturada (sem validação)
                        yield _format_sse_event('section_start', {
                            'section': section_num,
                            'section_name': section.section_name,
                            'attempt': 1,
                            'max_attempts': 1,
                            'is_structured': True
                        })

                        yield _format_sse_event('section_content', {
                            'section': section_num,
                            'section_name': section.section_name,
                            'content': content,
                            'is_valid': True,
                            'score': 100,
                            'feedback': [],
                            'is_structured': True
                        })

                        yield _format_sse_event('section_validated', {
                            'section': section_num,
                            'section_name': section.section_name,
                            'is_valid': True,
                            'score': 100,
                            'feedback': [],
                            'is_structured': True
                        })

                        # Atualizar SectionGeneration
                        SectionGeneration.objects.filter(
                            session=generation_session,
                            section=section
                        ).update(
                            status='completed',
                            content=content,
                            is_valid=True,
                            validation_score=100
                        )

                        completed_sections += 1
                        processed_sections.add(section_num)

                        # Emitir progresso para seções estruturadas
                        yield _format_sse_event('progress', {
                            'current_section': section_num,
                            'sections_completed': completed_sections,
                            'percentage': int((completed_sections / total_sections) * 100)
                        })

                        logger.info(f"Seção {section_num} ({section.section_name}) processada com campos estruturados")

            # Preparar overrides para seções com conteúdo pré-existente (instructions fixas)
            section_overrides = {}

            # Texto padrão do instructions → injetar para seções fixed
            for section in sections:
                sec_num = section.section_number
                if sec_num in sections_with_structured_data:
                    continue
                fixed_text = (section.instructions or '').strip()
                if fixed_text and sec_num not in section_overrides and not section.generator_agent and not section.section_fields:
                    # Seção fixed sem agente E sem section_fields - inserir texto direto (PGE/Decreto)
                    # Seções COM agente recebem instructions como contexto no prompt, não como saída fixa
                    # Seções COM section_fields + instructions vão para o LLM (já tratadas acima)
                    section_overrides[sec_num] = {
                        'fixed_content': fixed_text,
                    }
                    logger.info(
                        f"TR §{sec_num}: texto padrão PGE/Decreto "
                        f"({len(fixed_text)} chars)"
                    )

            # 3. Processar seções fixed sem agente ANTES do grafo
            # (texto padrão PGE/Decreto que não precisa de IA)
            fixed_no_agent_sections = []
            for section in sections:
                sec_num = section.section_number
                if sec_num in sections_with_structured_data:
                    continue
                if sec_num in section_overrides and 'fixed_content' in section_overrides[sec_num]:
                    if not section.generator_agent:
                        fixed_no_agent_sections.append((section, sec_num))

            for section, sec_num in fixed_no_agent_sections:
                content = section_overrides[sec_num]['fixed_content']
                SectionGeneration.objects.filter(
                    session=generation_session,
                    section=section
                ).update(
                    status='completed',
                    content=content,
                    is_valid=True,
                    validation_score=100
                )

                completed_sections += 1
                processed_sections.add(sec_num)
                sections_with_structured_data.append(sec_num)
                # Incluir no structured_sections_content para entrar no final_document
                structured_sections_content[sec_num] = {
                    'content': content,
                    'section_name': section.section_name,
                    'field_values': {},
                }

                yield _format_sse_event('section_start', {
                    'section': sec_num,
                    'section_name': section.section_name,
                    'attempt': 1, 'max_attempts': 1,
                })
                yield _format_sse_event('section_content', {
                    'section': sec_num,
                    'content': content,
                    'is_valid': True,
                    'score': 100,
                    'feedback': [],
                })
                yield _format_sse_event('section_validated', {
                    'section': sec_num,
                    'section_name': section.section_name,
                    'is_valid': True, 'score': 100, 'feedback': [],
                })
                yield _format_sse_event('progress', {
                    'current_section': sec_num,
                    'sections_completed': completed_sections,
                    'percentage': int((completed_sections / total_sections) * 100),
                })
                logger.info(
                    f"Seção {sec_num} ({section.section_name}): "
                    f"texto padrão inserido sem IA ({len(content)} chars)"
                )

            # Remover do section_overrides pois já foram processadas
            for _, sec_num in fixed_no_agent_sections:
                section_overrides.pop(sec_num, None)

            # Injetar dados dos campos estruturados como contexto para seções
            # que serão processadas pela IA (têm generator_agent)
            for sec_num, formatted_fields in sections_with_fields_for_llm.items():
                if sec_num not in section_overrides:
                    section_overrides[sec_num] = {}
                section_overrides[sec_num]['section_fields_context'] = formatted_fields
                logger.info(
                    f"TR §{sec_num}: dados do formulário injetados como "
                    f"contexto para IA ({len(formatted_fields)} chars)"
                )

            # 4. Seções com section_fields que têm conteúdo ETP em section_overrides:
            # o grafo sempre pula section_fields, então processamos direto aqui.
            # Ajustar seções a gerar por IA (excluir as que já foram processadas)
            if sections_with_structured_data:
                remaining_sections = [n for n in (section_numbers or [s.section_number for s in sections])
                                     if n not in sections_with_structured_data]
                logger.info(f"Seções com dados estruturados: {sections_with_structured_data}")
                logger.info(f"Seções restantes para IA: {remaining_sections}")
            else:
                remaining_sections = section_numbers if section_numbers else None

            try:
                # Stream estados do LangGraph (síncrono) - apenas para seções sem dados estruturados
                logger.info(f"Iniciando streaming com sections_to_generate={remaining_sections}")

                # Se remaining_sections é lista vazia, não rodar o grafo
                state_queue = queue_module.Queue()

                def _run_graph_stream():
                    """Executa runner.stream() em thread separada para liberar o loop SSE."""
                    try:
                        for st in runner.stream(
                            objective=objective,
                            collection_name=collection_name,
                            user_id=str(user.id),
                            max_retries=1,
                            sections_to_generate=remaining_sections,
                            sub_section_decisions=sub_section_decisions,
                            section_overrides=section_overrides if section_overrides else None,
                        ):
                            if cancel_event.is_set():
                                logger.info("Geração cancelada pelo cliente - interrompendo grafo")
                                break
                            state_queue.put(('state', st))
                        state_queue.put(('done', None))
                    except Exception as ex:
                        state_queue.put(('error', ex))

                if remaining_sections is not None and len(remaining_sections) == 0:
                    logger.info("Nenhuma seção para IA - pulando grafo")
                    state_queue.put(('done', None))
                else:
                    graph_thread = threading.Thread(target=_run_graph_stream, daemon=True)
                    graph_thread.start()

                # Loop principal: drena pipeline_event_queue (chunks em tempo real) e state_queue (estados do grafo)
                graph_done = False
                while not graph_done:
                    # 1. Drenar TODOS os eventos da pipeline (section_chunk, node_enter, kb_query, etc.)
                    drained = True
                    while drained:
                        drained = False
                        try:
                            evt_type, evt_data = pipeline_event_queue.get_nowait()
                            yield _format_sse_event(evt_type, evt_data)
                            drained = True
                        except queue_module.Empty:
                            pass

                    # 2. Verificar se há estado do grafo (com timeout curto para voltar a drenar chunks)
                    try:
                        msg_type, msg = state_queue.get(timeout=0.05)
                    except queue_module.Empty:
                        continue

                    if msg_type == 'done':
                        graph_done = True
                        continue
                    elif msg_type == 'error':
                        raise msg

                    # msg_type == 'state' → processar estado normalmente
                    state = msg

                    # Capturar estado para uso posterior
                    if isinstance(state, dict):
                        for node_name, node_state in state.items():
                            if isinstance(node_state, dict):
                                final_state = node_state
                    logger.info(f"Estado recebido: {type(state)} - keys: {state.keys() if isinstance(state, dict) else 'N/A'}")

                    for node_name, node_state in state.items():
                        logger.info(f"  Node: {node_name}, State type: {type(node_state)}")

                        if node_name in ('__start__', '__end__', 'finalize', 'router'):
                            continue

                        section_match = re.search(r'_(\d+)$', node_name)
                        if not section_match:
                            continue

                        section_num = int(section_match.group(1))
                        section_key = f"section_{section_num:02d}"

                        if section_num in processed_sections:
                            continue

                        if node_name.startswith('generate'):
                            if section_numbers and section_num not in section_numbers:
                                continue

                            section_obj = next(
                                (s for s in sections if s.section_number == section_num),
                                None
                            )
                            yield _format_sse_event('section_start', {
                                'section': section_num,
                                'section_name': section_obj.section_name if section_obj else f'Seção {section_num}',
                                'attempt': 1,
                                'max_attempts': 2
                            })

                            if isinstance(node_state, dict):
                                section_data = node_state.get(section_key, {})
                                if isinstance(section_data, dict) and section_data.get('content'):
                                    yield _format_sse_event('section_generated', {
                                        'section': section_num,
                                        'section_name': section_data.get('section_name', f'Seção {section_num}'),
                                    })

                                    from apps.intelligent_assistant.services.dynamic_graph_builder import DynamicSectionStatus
                                    section_status = section_data.get('status')
                                    if section_status == DynamicSectionStatus.VALID and section_num not in processed_sections:
                                        content = section_data.get('content', '')
                                        validation = section_data.get('validation', {})
                                        score = validation.get('score')
                                        feedback = (
                                            validation.get('errors', [])
                                            + validation.get('warnings', [])
                                            + validation.get('suggestions', [])
                                        )
                                        yield _format_sse_event('section_content', {
                                            'section': section_num,
                                            'content': content,
                                            'is_valid': True,
                                            'score': score,
                                            'feedback': feedback,
                                        })
                                        yield _format_sse_event('section_validated', {
                                            'section': section_num,
                                            'section_name': section_data.get('section_name', f'Seção {section_num}'),
                                            'is_valid': True,
                                            'score': score,
                                            'feedback': feedback,
                                        })
                                        try:
                                            SectionGeneration.objects.filter(
                                                session=generation_session,
                                                section__section_number=section_num
                                            ).update(
                                                status='completed',
                                                content=content,
                                                is_valid=True,
                                                validation_score=score,
                                                completed_at=timezone.now(),
                                            )
                                        except Exception as e:
                                            logger.error(f"    Erro ao persistir SectionGeneration generate {section_num}: {e}")
                                        completed_sections += 1
                                        processed_sections.add(section_num)

                        elif node_name.startswith('compose'):
                            # Nó compositor de sub-seções (ex: compose_04)
                            if section_numbers and section_num not in section_numbers:
                                continue

                            section_obj = next(
                                (s for s in sections if s.section_number == section_num),
                                None
                            )
                            yield _format_sse_event('section_start', {
                                'section': section_num,
                                'section_name': section_obj.section_name if section_obj else f'Seção {section_num}',
                                'attempt': 1,
                                'max_attempts': 1
                            })

                            if isinstance(node_state, dict):
                                section_data = node_state.get(section_key, {})
                                if isinstance(section_data, dict) and section_data.get('content'):
                                    content = section_data.get('content', '')
                                    validation = section_data.get('validation', {})
                                    is_valid = validation.get('is_valid', True)
                                    score = validation.get('score') or 100.0

                                    yield _format_sse_event('section_content', {
                                        'section': section_num,
                                        'content': content,
                                        'is_valid': is_valid,
                                        'score': score,
                                        'feedback': [],
                                    })
                                    yield _format_sse_event('section_validated', {
                                        'section': section_num,
                                        'section_name': section_data.get('section_name', f'Seção {section_num}'),
                                        'is_valid': is_valid,
                                        'score': score,
                                        'feedback': [],
                                    })

                                    if section_num not in processed_sections:
                                        completed_sections += 1
                                        processed_sections.add(section_num)

                                        try:
                                            SectionGeneration.objects.filter(
                                                session=generation_session,
                                                section__section_number=section_num
                                            ).update(
                                                status='completed',
                                                content=content,
                                                is_valid=is_valid,
                                                validation_score=score,
                                                completed_at=timezone.now(),
                                            )
                                        except Exception as e:
                                            logger.error(f"    Erro ao persistir SectionGeneration compose {section_num}: {e}")

                                        yield _format_sse_event('progress', {
                                            'current_section': section_num,
                                            'sections_completed': completed_sections,
                                            'percentage': int((completed_sections / total_sections) * 100)
                                        })

                        elif node_name.startswith('validate'):
                            if section_numbers and section_num not in section_numbers:
                                continue

                            if isinstance(node_state, dict):
                                section_data = node_state.get(section_key, {})
                                if isinstance(section_data, dict):
                                    validation = section_data.get('validation', {})
                                    is_valid = validation.get('is_valid', False)
                                    score = validation.get('score', 0)
                                    feedback = (
                                        validation.get('errors', [])
                                        + validation.get('warnings', [])
                                        + validation.get('suggestions', [])
                                    )

                                    if section_num not in processed_sections:
                                        content = section_data.get('content', '')
                                        if content:
                                            yield _format_sse_event('section_content', {
                                                'section': section_num,
                                                'content': content,
                                                'is_valid': is_valid,
                                                'score': score,
                                                'feedback': feedback,
                                            })

                                    yield _format_sse_event('section_validated', {
                                        'section': section_num,
                                        'section_name': section_data.get('section_name', f'Seção {section_num}'),
                                        'is_valid': is_valid,
                                        'score': score,
                                        'feedback': feedback,
                                    })

                                    if section_num not in processed_sections:
                                        completed_sections += 1
                                        processed_sections.add(section_num)

                                        try:
                                            content = section_data.get('content', '')
                                            # Calcular tokens da seção
                                            sec_tokens = _tokens_by_section.get(section_num, {})
                                            sec_total = sec_tokens.get('input', 0) + sec_tokens.get('output', 0)
                                            SectionGeneration.objects.filter(
                                                session=generation_session,
                                                section__section_number=section_num
                                            ).update(
                                                status='completed' if is_valid else 'validated',
                                                content=content,
                                                is_valid=is_valid,
                                                validation_score=score,
                                                validation_errors=validation.get('errors', []),
                                                validation_warnings=validation.get('warnings', []),
                                                validation_feedback='\n'.join(feedback),
                                                tokens_used=sec_total,
                                                completed_at=timezone.now(),
                                            )
                                        except Exception as e:
                                            logger.error(f"    Erro ao persistir SectionGeneration {section_num}: {e}")

                                        yield _format_sse_event('progress', {
                                            'current_section': section_num,
                                            'sections_completed': completed_sections,
                                            'percentage': int((completed_sections / total_sections) * 100)
                                        })

                # Flush final de eventos do pipeline após stream completo
                while not pipeline_event_queue.empty():
                    try:
                        evt_type, evt_data = pipeline_event_queue.get_nowait()
                        yield _format_sse_event(evt_type, evt_data)
                    except queue_module.Empty:
                        break

            except Exception as e:
                logger.error(f"Erro no streaming: {str(e)}")
                import traceback
                traceback.print_exc()
                yield _format_sse_event('error', {
                    'message': str(e)
                })

            # Persistir documento e gerar PDF
            document = None
            pdf_url = ''
            document_id = ''
            average_score = 80

            if effective_session_id and intelligent_session:
                try:
                    yield _format_sse_event('saving', {
                        'message': 'Salvando documento...'
                    })

                    # intelligent_session já resolvida acima - não buscar novamente

                    # Usar persistence_service para salvar e gerar PDF
                    from ..services.persistence_service import ETPPersistenceService
                    persistence_service = ETPPersistenceService()

                    # Inicializar final_state se não existir
                    if not final_state:
                        final_state = {}

                    # Garantir que sections_to_generate inclui TODAS as seções (IA + estruturadas)
                    final_state['sections_to_generate'] = section_numbers or list(range(1, total_sections + 1))

                    # Adicionar conteúdo das seções estruturadas ao final_state
                    for section_num, section_data in structured_sections_content.items():
                        section_key = f"section_{section_num:02d}"
                        if section_key not in final_state:
                            final_state[section_key] = {}
                        final_state[section_key]['content'] = section_data['content']
                        final_state[section_key]['section_name'] = section_data['section_name']
                        final_state[section_key]['is_valid'] = True
                        final_state[section_key]['score'] = 100
                        final_state[section_key]['is_structured'] = True
                        final_state[section_key]['field_values'] = section_data.get('field_values', {})

                    # Reconstruir final_document incluindo TODAS as seções (IA + estruturadas)
                    # O finalize node só inclui seções de IA - as estruturadas ficam de fora
                    if structured_sections_content:
                        all_sections = sorted(final_state.get('sections_to_generate', []))
                        document_parts = []
                        for sec_num in all_sections:
                            sec_key = f"section_{sec_num:02d}"
                            sec_data = final_state.get(sec_key, {})
                            content = sec_data.get('content', '')
                            sec_name = sec_data.get('section_name', f'Seção {sec_num}')
                            if content:
                                document_parts.append(f"## {sec_num}. {sec_name}\n\n{content}")
                        final_state['final_document'] = "\n\n".join(document_parts)
                        logger.info(f"final_document reconstruído com {len(document_parts)} seções (IA + estruturadas)")

                    document = persistence_service.save_etp_from_state(
                        session=intelligent_session,
                        state=final_state,
                        generate_pdf=False,
                        blueprint=blueprint
                    )

                    if document:
                        pdf_url = document.pdf_url or ''
                        document_id = str(document.id)
                        average_score = document.overall_score or 80

                        logger.info(f"Documento salvo: {document_id}, PDF: {pdf_url}")

                except IntelligentSession.DoesNotExist:
                    logger.warning(f"IntelligentSession {effective_session_id} não encontrada, documento não será persistido")
                except Exception as e:
                    logger.error(f"Erro ao persistir documento: {str(e)}")
                    import traceback
                    traceback.print_exc()

            # GARANTIR que completed SEMPRE é emitido, mesmo com erros
            try:
                generation_session.status = 'completed'
                generation_session.completed_at = timezone.now()

                # Persistir dados do pipeline para visualização pós-geração
                if pipeline_events_log:
                    # Reconstruir estado final dos nós a partir dos eventos
                    graph_structure = {}
                    final_nodes = {}
                    log_entries = []

                    for evt in pipeline_events_log:
                        evt_type = evt.get('event', '')

                        if evt_type == 'graph_structure':
                            graph_structure = {'nodes': evt.get('nodes', []), 'edges': evt.get('edges', [])}
                            for node in graph_structure.get('nodes', []):
                                final_nodes[node['id']] = node

                        elif evt_type == 'node_enter':
                            if evt.get('node') in final_nodes:
                                final_nodes[evt['node']]['status'] = 'running'

                        elif evt_type == 'kb_query':
                            nid = evt.get('node')
                            if nid in final_nodes:
                                if 'kbs' not in final_nodes[nid]:
                                    final_nodes[nid]['kbs'] = []
                                final_nodes[nid]['kbs'].append({
                                    'kb': evt.get('kb', ''),
                                    'purpose': evt.get('purpose', ''),
                                    'results': evt.get('results', 0),
                                })
                            log_entries.append({
                                'type': 'kb_query',
                                'message': f'KB "{evt.get("kb")}" ({evt.get("purpose")}): {evt.get("results")} chunks',
                                'node': nid,
                            })

                        elif evt_type == 'llm_call':
                            nid = evt.get('node')
                            if nid in final_nodes:
                                final_nodes[nid]['llm'] = {
                                    'provider': evt.get('provider', ''),
                                    'model': evt.get('model', ''),
                                }
                            log_entries.append({
                                'type': 'llm_call',
                                'message': f'{evt.get("model")} ({evt.get("provider")})',
                                'node': nid,
                            })

                        elif evt_type == 'node_exit':
                            nid = evt.get('node')
                            if nid in final_nodes:
                                final_nodes[nid]['status'] = evt.get('status', 'success')
                                final_nodes[nid]['duration_ms'] = evt.get('duration_ms')
                                if 'score' in evt:
                                    final_nodes[nid]['score'] = evt['score']
                            log_entries.append({
                                'type': 'node_exit',
                                'message': f'{evt.get("status")} ({evt.get("duration_ms", 0)}ms)',
                                'node': nid,
                            })

                    # Marcar finalize como success
                    if 'finalize' in final_nodes:
                        final_nodes['finalize']['status'] = 'success'

                    generation_session.pipeline_graph = {
                        'nodes': list(final_nodes.values()),
                        'edges': graph_structure.get('edges', []),
                        'log': log_entries,
                    }

                # Salvar totais de tokens na sessão
                generation_session.total_input_tokens = _total_tokens['input']
                generation_session.total_output_tokens = _total_tokens['output']
                generation_session.total_tokens = _total_tokens['input'] + _total_tokens['output']
                # Calcular custo estimado agregado dos audit logs
                try:
                    from django.db.models import Sum
                    from ..models import LLMAuditLog
                    cost_sum = LLMAuditLog.objects.filter(
                        session=generation_session
                    ).aggregate(total=Sum('estimated_cost_usd'))
                    generation_session.estimated_cost_usd = cost_sum['total'] or 0
                except Exception:
                    logger.warning("Failed to aggregate LLM cost for session", exc_info=True)

                generation_session.save()
            except Exception as e:
                logger.error(f"Erro ao atualizar generation_session: {str(e)}")

            session_total_tokens = _total_tokens['input'] + _total_tokens['output']

            # Evento final - SEMPRE emitido
            yield _format_sse_event('completed', {
                'success': True,
                'session_id': str(generation_session.id) if generation_session else '',
                'generation_session_id': str(generation_session.id) if generation_session else '',
                'document_id': document_id,
                'pdf_url': pdf_url,
                'total_sections': total_sections,
                'completed_sections': completed_sections,
                'valid_sections': completed_sections,
                'average_score': average_score,
                'total_tokens_used': session_total_tokens,
                'total_input_tokens': _total_tokens['input'],
                'total_output_tokens': _total_tokens['output'],
                'message': f'Documento gerado com sucesso! {completed_sections}/{total_sections} seções válidas. Tokens: {session_total_tokens}'
            })

        except DocumentBlueprint.DoesNotExist:
            yield _format_sse_event('error', {
                'message': 'Blueprint não encontrado'
            })
            yield _format_sse_event('completed', {
                'success': False, 'message': 'Blueprint não encontrado',
                'total_sections': 0, 'completed_sections': 0, 'valid_sections': 0,
                'average_score': 0, 'session_id': '', 'document_id': '', 'pdf_url': '',
            })
        except Exception as e:
            logger.error(f"Erro no streaming dinâmico: {str(e)}")
            import traceback
            traceback.print_exc()
            yield _format_sse_event('error', {
                'message': str(e)
            })
            # SEMPRE emitir completed para destravar o frontend
            try:
                _ts = total_sections
                _cs = completed_sections
            except NameError:
                _ts = 0
                _cs = 0
            yield _format_sse_event('completed', {
                'success': False, 'message': str(e),
                'total_sections': _ts, 'completed_sections': _cs,
                'valid_sections': 0, 'average_score': 0,
                'session_id': '', 'document_id': '', 'pdf_url': '',
            })
        finally:
            # Sinalizar cancelamento para a thread do grafo parar
            cancel_event.set()
            logger.info("event_stream finalizado - cancel_event setado")

    response = StreamingHttpResponse(
        event_stream(),
        content_type='text/event-stream'
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    response['Access-Control-Allow-Origin'] = '*'
    return response


@csrf_exempt
@require_http_methods(["POST"])
def regenerate_section_stream(request):
    """
    Endpoint SSE para regenerar UMA seção com feedback do usuário.

    POST /api/v1/intelligent-assistant/regenerate-section-stream/
    Body JSON: { blueprint_id, section_number, feedback, objective, session_id?, sub_section_decisions? }
    """
    user, error_response = _authenticate_request(request)
    if error_response:
        return error_response

    # Rate limiting: max 10 regenerações/minuto por usuário
    rate_check = check_rate_limit(request, 'regenerate-section', max_requests=10, window_seconds=60)
    if not rate_check['allowed']:
        return JsonResponse({
            'error': f'Limite de regeneração excedido. Tente novamente em {rate_check["retry_after"]}s.',
            'retry_after_seconds': rate_check['retry_after'],
        }, status=429)

    # Extrair parâmetros do body JSON
    try:
        data = json.loads(request.body) if request.body else {}
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Body JSON inválido'}, status=400)

    blueprint_id = data.get('blueprint_id')
    section_number = data.get('section_number')
    feedback = str(data.get('feedback', '')).strip()
    objective = str(data.get('objective', '')).strip()
    session_id = data.get('session_id')
    collection_name = session_id or 'default'

    # Sub-section decisions já vem como dict do JSON
    sub_section_decisions = data.get('sub_section_decisions')
    if sub_section_decisions and not isinstance(sub_section_decisions, dict):
        sub_section_decisions = None

    if not blueprint_id or not section_number or not objective:
        return JsonResponse({
            'error': 'Parâmetros obrigatórios: blueprint_id, section_number, objective'
        }, status=400)

    try:
        section_number = int(section_number)
    except ValueError:
        return JsonResponse({'error': 'section_number deve ser um número inteiro'}, status=400)

    def event_stream():
        import queue as queue_module
        try:
            blueprint = DocumentBlueprint.objects.select_related(
                'document_type', 'document_type__category'
            ).get(id=blueprint_id, is_active=True)
            section_obj = BlueprintSection.objects.filter(
                blueprint=blueprint,
                section_number=section_number,
                is_active=True
            ).first()

            if not section_obj:
                yield _format_sse_event('error', {
                    'message': f'Seção {section_number} não encontrada no blueprint'
                })
                return

            yield _format_sse_event('started', {
                'message': f'Regenerando seção {section_number}: {section_obj.section_name}',
                'section': section_number,
                'section_name': section_obj.section_name,
            })

            from ..services.dynamic_graph_builder import DynamicGraphBuilder
            from ..services.llm_provider_service import UnifiedLLMService
            from ..services.knowledge_base_service import KnowledgeBaseService
            import threading

            llm_service = UnifiedLLMService()
            kb_service = KnowledgeBaseService.get_instance()

            # Fila de eventos para streaming de chunks
            regen_event_queue = queue_module.Queue()

            def regen_event_callback(event_type, data):
                # Interceptar llm_usage para criar audit log
                if event_type == 'llm_usage':
                    try:
                        from ..models import LLMAuditLog
                        LLMAuditLog.objects.create(
                            user=user,
                            blueprint=blueprint,
                            section_number=data.get('section'),
                            section_name=data.get('section_name', ''),
                            call_type='regenerate',
                            attempt_number=data.get('attempt', 1),
                            provider=data.get('provider', ''),
                            model=data.get('model', ''),
                            input_tokens=data.get('input_tokens', 0),
                            output_tokens=data.get('output_tokens', 0),
                            duration_ms=data.get('duration_ms', 0),
                        )
                    except Exception as e:
                        logger.error(f"Erro ao criar LLMAuditLog (regen): {e}")
                    return  # Não enfileirar para SSE
                regen_event_queue.put((event_type, data))

            builder = DynamicGraphBuilder(llm_service=llm_service, kb_service=kb_service)
            runner = builder.create_runner(
                blueprint_id=blueprint.id,
                event_callback=regen_event_callback,
            )

            # Emitir section_start
            yield _format_sse_event('section_start', {
                'section': section_number,
                'section_name': section_obj.section_name,
                'attempt': 1,
                'max_attempts': 1,
            })

            # Preparar overrides com feedback do usuário
            section_overrides = None
            if feedback:
                section_overrides = {
                    section_number: {'user_feedback': feedback}
                }

            # Executar o grafo em thread separada para streaming em tempo real
            final_state = None
            regen_state_queue = queue_module.Queue()

            def _run_regen_stream():
                try:
                    for st in runner.stream(
                        objective=objective,
                        collection_name=collection_name,
                        user_id=str(user.id),
                        max_retries=1,
                        sections_to_generate=[section_number],
                        section_overrides=section_overrides,
                        sub_section_decisions=sub_section_decisions,
                    ):
                        regen_state_queue.put(('state', st))
                    regen_state_queue.put(('done', None))
                except Exception as ex:
                    regen_state_queue.put(('error', ex))

            regen_thread = threading.Thread(target=_run_regen_stream, daemon=True)
            regen_thread.start()

            regen_done = False
            while not regen_done:
                # Drenar chunks da pipeline
                drained = True
                while drained:
                    drained = False
                    try:
                        evt_type, evt_data = regen_event_queue.get_nowait()
                        yield _format_sse_event(evt_type, evt_data)
                        drained = True
                    except queue_module.Empty:
                        pass

                try:
                    msg_type, msg = regen_state_queue.get(timeout=0.05)
                except queue_module.Empty:
                    continue

                if msg_type == 'done':
                    regen_done = True
                    continue
                elif msg_type == 'error':
                    raise msg

                state = msg
                if isinstance(state, dict):
                    for node_name, node_state in state.items():
                        if isinstance(node_state, dict):
                            final_state = node_state

                        if node_name in ('__start__', '__end__', 'finalize', 'router'):
                            continue

                        section_match = re.search(r'_(\d+)$', node_name)
                        if not section_match:
                            continue

                        sec_num = int(section_match.group(1))
                        if sec_num != section_number:
                            continue

                        section_key = f"section_{sec_num:02d}"

                        if node_name.startswith('generate'):
                            yield _format_sse_event('section_generated', {
                                'section': sec_num,
                                'section_name': section_obj.section_name,
                            })

                            if isinstance(node_state, dict):
                                section_data = node_state.get(section_key, {})
                                if isinstance(section_data, dict):
                                    from apps.intelligent_assistant.services.dynamic_graph_builder import DynamicSectionStatus
                                    section_status = section_data.get('status')
                                    if section_status == DynamicSectionStatus.VALID:
                                        content = section_data.get('content', '')
                                        validation = section_data.get('validation', {})
                                        score = validation.get('score')
                                        fb = (
                                            validation.get('errors', [])
                                            + validation.get('warnings', [])
                                            + validation.get('suggestions', [])
                                        )
                                        if content:
                                            yield _format_sse_event('section_content', {
                                                'section': sec_num,
                                                'content': content,
                                                'is_valid': True,
                                                'score': score,
                                                'feedback': fb,
                                            })
                                            yield _format_sse_event('section_validated', {
                                                'section': sec_num,
                                                'section_name': section_obj.section_name,
                                                'is_valid': True,
                                                'score': score,
                                                'feedback': fb,
                                            })

                        elif node_name.startswith('compose'):
                            # Nó compositor de sub-seções (regeneração)
                            if isinstance(node_state, dict):
                                section_data = node_state.get(section_key, {})
                                if isinstance(section_data, dict) and section_data.get('content'):
                                    content = section_data.get('content', '')
                                    validation = section_data.get('validation', {})
                                    score = validation.get('score') or 100.0

                                    yield _format_sse_event('section_content', {
                                        'section': sec_num,
                                        'content': content,
                                        'is_valid': True,
                                        'score': score,
                                        'feedback': [],
                                    })
                                    yield _format_sse_event('section_validated', {
                                        'section': sec_num,
                                        'section_name': section_obj.section_name,
                                        'is_valid': True,
                                        'score': score,
                                        'feedback': [],
                                    })

                        elif node_name.startswith('validate'):
                            if isinstance(node_state, dict):
                                section_data = node_state.get(section_key, {})
                                if isinstance(section_data, dict):
                                    validation = section_data.get('validation', {})
                                    is_valid = validation.get('is_valid', False)
                                    score = validation.get('score', 0)
                                    fb = (
                                        validation.get('errors', [])
                                        + validation.get('warnings', [])
                                        + validation.get('suggestions', [])
                                    )

                                    content = section_data.get('content', '')
                                    if content:
                                        yield _format_sse_event('section_content', {
                                            'section': sec_num,
                                            'content': content,
                                            'is_valid': is_valid,
                                            'score': score,
                                            'feedback': fb,
                                        })

                                    yield _format_sse_event('section_validated', {
                                        'section': sec_num,
                                        'section_name': section_obj.section_name,
                                        'is_valid': is_valid,
                                        'score': score,
                                        'feedback': fb,
                                    })

            # Flush final de chunks pendentes
            while not regen_event_queue.empty():
                try:
                    evt_type, evt_data = regen_event_queue.get_nowait()
                    yield _format_sse_event(evt_type, evt_data)
                except queue_module.Empty:
                    break

            # ── Persistir conteúdo regenerado no GeneratedDocument ──
            if final_state and session_id:
                try:
                    section_key = f"section_{section_number:02d}"
                    section_data = final_state.get(section_key, {})
                    regenerated_content = section_data.get('content', '') if isinstance(section_data, dict) else ''

                    if regenerated_content:
                        from ..models import GeneratedDocument
                        document = GeneratedDocument.objects.filter(
                            session_id=session_id,
                        ).order_by('-created_at').first()

                        if document and document.markdown_content:
                            import re as re_mod
                            markdown = document.markdown_content

                            patterns = [
                                rf'(## {section_number}\.\s*[^\n]+\n)(.*?)(?=## (?!{section_number}\.)\d+\.|$)',
                                rf'(## Seção {section_number}[:\s]*[^\n]*\n)(.*?)(?=## (?!Seção {section_number}[:\s])\d+\.|## Seção (?!{section_number}[:\s])\d+|$)',
                            ]

                            replaced = False
                            for pattern in patterns:
                                match = re_mod.search(pattern, markdown, re_mod.DOTALL | re_mod.IGNORECASE)
                                if match:
                                    header = match.group(1)
                                    markdown = re_mod.sub(
                                        pattern,
                                        f'{header}{regenerated_content}\n\n',
                                        markdown,
                                        count=1,
                                        flags=re_mod.DOTALL | re_mod.IGNORECASE,
                                    )
                                    replaced = True
                                    break

                            if replaced:
                                document.markdown_content = markdown
                                document.pdf_generated = False
                                document.save(update_fields=['markdown_content', 'pdf_generated', 'updated_at'])
                                logger.info(
                                    f"Seção {section_number} regenerada persistida no documento {document.id}"
                                )
                            else:
                                logger.warning(
                                    f"Seção {section_number} não encontrada no markdown do documento {document.id} para persistência"
                                )
                        else:
                            logger.warning(f"Documento não encontrado para sessão {session_id}")
                except Exception as persist_err:
                    logger.error(f"Erro ao persistir seção regenerada: {persist_err}")

                # Atualizar SectionGeneration para manter consistência com loadGenerationSession
                try:
                    gen_session = GenerationSession.objects.filter(
                        intelligent_session_id=session_id
                    ).order_by('-created_at').first()
                    if gen_session:
                        SectionGeneration.objects.filter(
                            session=gen_session,
                            section__section_number=section_number
                        ).update(
                            content=regenerated_content,
                            status='completed',
                            is_valid=True,
                        )
                        logger.info(f"SectionGeneration atualizada para seção {section_number} na sessão {gen_session.id}")
                except Exception as sg_err:
                    logger.error(f"Erro ao atualizar SectionGeneration: {sg_err}")

            yield _format_sse_event('progress', {
                'current_section': section_number,
                'sections_completed': 1,
                'percentage': 100,
            })

            yield _format_sse_event('completed', {
                'success': True,
                'section': section_number,
                'total_sections': 1,
                'completed_sections': 1,
                'valid_sections': 1,
                'average_score': 80,
                'message': f'Seção {section_number} regenerada com sucesso!',
            })

        except DocumentBlueprint.DoesNotExist:
            yield _format_sse_event('error', {'message': 'Blueprint não encontrado'})
        except Exception as e:
            logger.error(f"Erro ao regenerar seção {section_number}: {str(e)}")
            import traceback
            traceback.print_exc()
            yield _format_sse_event('error', {'message': str(e)})

    response = StreamingHttpResponse(
        event_stream(),
        content_type='text/event-stream'
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    response['Access-Control-Allow-Origin'] = '*'
    return response


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_generation_session(request, session_id):
    """
    Marca uma GenerationSession como 'cancelled'.
    Chamado pelo frontend ao interromper a geração via botão Cancelar.
    """
    try:
        gs = GenerationSession.objects.get(id=session_id, user=request.user)
    except GenerationSession.DoesNotExist:
        return Response({'error': 'Não encontrada'}, status=404)
    if gs.status == 'generating':
        gs.status = 'cancelled'
        gs.save(update_fields=['status'])
    return Response({'status': gs.status})
