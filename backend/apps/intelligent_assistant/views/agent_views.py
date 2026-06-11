"""
Views CRUD e execução de agentes de seção (SectionAgentConfig).
"""
import logging

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse

from ..models import (
    DocumentBlueprint,
    BlueprintSection,
    SectionAgentConfig,
)
from ..serializers import (
    SectionAgentConfigListSerializer,
    SectionAgentConfigDetailSerializer,
    SectionAgentConfigWriteSerializer,
    SectionAgentListSerializer,
)
from ..services.pgvector_service import PgVectorService

logger = logging.getLogger(__name__)


@extend_schema(
    summary="Listar Agentes de Seção do Blueprint",
    description="""
    Lista TODOS os agentes (SectionAgentConfig) vinculados a um blueprint:
    geradores e validadores de seções, e geradores de sub-seções.

    Retorna dados completos (prompts, LLM, RAG) com contexto de onde
    cada agente está vinculado (seção/sub-seção e papel).
    """,
    tags=["Blueprints"],
    responses={
        200: OpenApiResponse(description="Lista completa de agentes do blueprint"),
        404: OpenApiResponse(description="Blueprint não encontrado"),
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_blueprint_agents(request, blueprint_id):
    """
    GET /api/v1/intelligent-assistant/blueprints/{id}/agents/

    Retorna todos os agentes do blueprint (geradores, validadores, sub-seções)
    com detalhe completo e contexto de vinculação.
    """
    try:
        blueprint = DocumentBlueprint.objects.get(id=blueprint_id)
    except DocumentBlueprint.DoesNotExist:
        return Response(
            {'error': 'Blueprint não encontrado'},
            status=status.HTTP_404_NOT_FOUND,
        )

    sections = blueprint.sections.select_related(
        'generator_agent', 'validator_agent'
    ).prefetch_related(
        'sub_sections__generator_agent'
    ).order_by('section_number')

    # Mapa: agent_id -> { serialized data + linked_sections + linked_sub_sections }
    agents_map = {}

    def _ensure_agent(agent):
        aid = str(agent.id)
        if aid not in agents_map:
            data = SectionAgentConfigDetailSerializer(agent).data
            data['linked_sections'] = []
            data['linked_sub_sections'] = []
            agents_map[aid] = data
        return agents_map[aid]

    for section in sections:
        # Generator agent
        if section.generator_agent:
            entry = _ensure_agent(section.generator_agent)
            entry['linked_sections'].append({
                'section_id': str(section.id),
                'section_number': section.section_number,
                'section_name': section.section_name,
                'role': 'generator',
            })
        # Validator agent
        if section.validator_agent:
            entry = _ensure_agent(section.validator_agent)
            entry['linked_sections'].append({
                'section_id': str(section.id),
                'section_number': section.section_number,
                'section_name': section.section_name,
                'role': 'validator',
            })
        # Sub-section generator agents
        for sub in section.sub_sections.all():
            if sub.generator_agent:
                entry = _ensure_agent(sub.generator_agent)
                entry['linked_sub_sections'].append({
                    'sub_section_id': str(sub.id),
                    'sub_number': sub.sub_number,
                    'sub_name': sub.sub_name,
                    'parent_section_number': section.section_number,
                    'parent_section_name': section.section_name,
                    'role': 'generator',
                })

    agents_list = list(agents_map.values())

    return Response({
        'blueprint_id': str(blueprint.id),
        'blueprint_name': blueprint.name,
        'agents': agents_list,
        'total': len(agents_list),
    })


@extend_schema(
    summary="Detalhe de Agente de Seção",
    tags=["Blueprint Management"],
    responses={
        200: SectionAgentConfigDetailSerializer,
        404: OpenApiResponse(description="Agente não encontrado"),
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_section_agent(request, agent_id):
    """GET /api/v1/intelligent-assistant/agents/{agent_id}/"""
    try:
        agent = SectionAgentConfig.objects.get(id=agent_id)
    except SectionAgentConfig.DoesNotExist:
        return Response(
            {'error': 'Agente não encontrado'},
            status=status.HTTP_404_NOT_FOUND,
        )
    return Response(SectionAgentConfigDetailSerializer(agent).data)


@extend_schema(
    summary="Atualizar Agente de Seção",
    tags=["Blueprint Management"],
    request=SectionAgentConfigWriteSerializer,
    responses={
        200: SectionAgentConfigDetailSerializer,
        404: OpenApiResponse(description="Agente não encontrado"),
    }
)
@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_section_agent(request, agent_id):
    """PUT/PATCH /api/v1/intelligent-assistant/agents/{agent_id}/update/"""
    try:
        agent = SectionAgentConfig.objects.get(id=agent_id)
    except SectionAgentConfig.DoesNotExist:
        return Response(
            {'error': 'Agente não encontrado'},
            status=status.HTTP_404_NOT_FOUND,
        )
    partial = request.method == 'PATCH'
    serializer = SectionAgentConfigWriteSerializer(agent, data=request.data, partial=partial)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(SectionAgentConfigDetailSerializer(agent).data)


@extend_schema(
    summary="Criar Agente de Seção",
    tags=["Blueprint Management"],
    request=SectionAgentConfigWriteSerializer,
    responses={
        201: SectionAgentConfigDetailSerializer,
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_section_agent(request):
    """POST /api/v1/intelligent-assistant/agents/create/"""
    serializer = SectionAgentConfigWriteSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    agent = serializer.save(created_by=request.user)
    return Response(
        SectionAgentConfigDetailSerializer(agent).data,
        status=status.HTTP_201_CREATED,
    )


@extend_schema(
    summary="Deletar Agente de Seção",
    tags=["Blueprint Management"],
    responses={
        204: OpenApiResponse(description="Agente deletado"),
        404: OpenApiResponse(description="Agente não encontrado"),
    }
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_section_agent(request, agent_id):
    """DELETE /api/v1/intelligent-assistant/agents/{agent_id}/delete/"""
    try:
        agent = SectionAgentConfig.objects.get(id=agent_id)
    except SectionAgentConfig.DoesNotExist:
        return Response(
            {'error': 'Agente não encontrado'},
            status=status.HTTP_404_NOT_FOUND,
        )
    agent.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    summary="Executar Agente de Seção",
    description="""
    Executa um agente de seção (SectionAgentConfig) individualmente.

    Este endpoint permite executar um agente de seção fora do fluxo de geração
    completa de documentos. Útil para o "Formulário Guiado" onde o usuário
    pode solicitar assistência de IA para uma seção específica.

    **Parâmetros:**
    - `objective`: Objetivo geral do documento
    - `context`: Contexto com dados já preenchidos no formulário
    - `section_data`: Dados específicos da seção (campos já preenchidos)
    """,
    tags=["Blueprints"],
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'objective': {'type': 'string', 'description': 'Objetivo do documento'},
                'context': {'type': 'string', 'description': 'Contexto geral do formulário'},
                'section_data': {'type': 'object', 'description': 'Dados da seção'},
            }
        }
    },
    responses={
        200: OpenApiResponse(description="Conteúdo gerado pelo agente"),
        404: OpenApiResponse(description="Agente não encontrado")
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def execute_section_agent(request, agent_id):
    """
    Executa um agente de seção (SectionAgentConfig) individualmente.

    POST /api/v1/intelligent-assistant/agents/{agent_id}/execute/

    Permite usar os agentes configurados para geração/validação de seções
    de forma isolada, útil para o modo "Formulário Guiado".

    Suporta:
    - Variáveis de campo (field_name, field_value, current_content)
    - Busca RAG nas knowledge_bases associadas ao agente
    """
    try:
        agent = SectionAgentConfig.objects.get(id=agent_id, is_active=True)
    except SectionAgentConfig.DoesNotExist:
        return Response({
            'error': 'Agente não encontrado ou inativo'
        }, status=status.HTTP_404_NOT_FOUND)

    # Extrair dados da requisição
    objective = request.data.get('objective', '')
    context = request.data.get('context', '')
    section_data = request.data.get('section_data', {})
    field_name = request.data.get('field_name', '')
    field_value = request.data.get('field_value', '')

    # ========== BUSCA RAG ==========
    rag_context = ''
    rag_sources = []

    if agent.use_rag and agent.knowledge_bases.exists():
        try:
            pgvector_service = PgVectorService()

            # Montar query para RAG
            if agent.rag_query_template:
                rag_query = agent.rag_query_template
                rag_query = rag_query.replace('{{objective}}', objective)
                rag_query = rag_query.replace('{{field_name}}', field_name)
                rag_query = rag_query.replace('{{field_value}}', field_value)
                rag_query = rag_query.replace('{{context}}', context)
            else:
                # Query padrão: combina objetivo + nome do campo + valor atual
                rag_query = f"{objective} {field_name} {field_value}".strip()

            # Buscar em cada knowledge_base associada ao agente
            all_results = []
            for kb in agent.knowledge_bases.filter(is_active=True):
                results = pgvector_service.search_knowledge_base(
                    knowledge_base_name=kb.name,
                    query=rag_query,
                    n_results=agent.rag_top_k,
                    min_similarity=agent.rag_similarity_threshold
                )
                for r in results:
                    r['knowledge_base'] = kb.name
                all_results.extend(results)

            # Ordenar por similaridade e pegar top_k
            all_results.sort(key=lambda x: x.get('similarity', 0), reverse=True)
            top_results = all_results[:agent.rag_top_k]

            if top_results:
                # Formatar contexto RAG
                rag_chunks = []
                for idx, r in enumerate(top_results, 1):
                    source = r.get('source_name', r.get('knowledge_base', 'Desconhecido'))
                    similarity = r.get('similarity', 0)
                    chunk_text = r.get('chunk_text', '')
                    rag_chunks.append(f"[Exemplo {idx} - {source} (relevância: {similarity:.0%})]:\n{chunk_text}")
                    rag_sources.append({
                        'source': source,
                        'similarity': similarity,
                        'knowledge_base': r.get('knowledge_base', '')
                    })

                rag_context = "\n\n---\n\n".join(rag_chunks)
                logger.info(f"RAG: {len(top_results)} chunks encontrados para agente {agent.name}")

        except Exception as e:
            logger.warning(f"Erro na busca RAG para agente {agent.name}: {str(e)}")
            # Continua sem RAG se houver erro

    # ========== PREPARAR VARIÁVEIS ==========
    variables = {
        'objective': objective,
        'context': context,
        'section_data': str(section_data) if section_data else '',
        'previous_sections': '',  # Vazio quando executando isoladamente
        'section_name': field_name,  # Usar field_name como section_name
        'section_number': '',
        # Novas variáveis para campos
        'field_name': field_name,
        'field_value': field_value,
        'current_content': field_value,  # Alias para field_value
        # Contexto RAG
        'rag_context': rag_context,
        'examples': rag_context,  # Alias para rag_context
    }

    # Substituir variáveis no user_prompt_template
    user_prompt = agent.user_prompt_template
    for key, value in variables.items():
        user_prompt = user_prompt.replace(f'{{{{{key}}}}}', str(value))

    # Se há contexto RAG mas não está no template, adicionar automaticamente
    if rag_context and '{{rag_context}}' not in agent.user_prompt_template and '{{examples}}' not in agent.user_prompt_template:
        user_prompt = f"""## Exemplos de Referência (Base de Conhecimento)

{rag_context}

---

## Solicitação

{user_prompt}"""

    try:
        # Executar o agente usando o provider/model configurado no próprio agente
        from apps.intelligent_assistant.services.llm_provider_service import UnifiedLLMService
        llm_service = UnifiedLLMService()
        llm_response = llm_service.generate(
            system_prompt=agent.system_prompt,
            user_prompt=user_prompt,
            temperature=agent.temperature,
            max_tokens=agent.max_tokens,
            provider=agent.llm_provider,
            model=agent.model_name,
            user=request.user if request.user.is_authenticated else None,
            usage_type='agent',
            description=f'Agente IA: {agent.name}',
        )
        content = llm_response['content']

        return Response({
            'success': True,
            'agent_id': str(agent.id),
            'agent_name': agent.name,
            'agent_type': agent.agent_type,
            'content': content,
            'provider': agent.llm_provider,
            'model': agent.model_name,
            'rag_used': bool(rag_context),
            'rag_sources': rag_sources,
        })

    except Exception as e:
        logger.error(f"Erro ao executar agente {agent.name}: {str(e)}")
        return Response({
            'error': f'Erro ao executar agente: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    summary="Listar todos os agentes de seção",
    tags=["Knowledge Base Management"],
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_section_agents(request):
    """
    GET /api/v1/intelligent-assistant/section-agents/
    Retorna lista de agentes para popular selects no frontend.
    """
    agents = SectionAgentConfig.objects.filter(
        is_active=True
    ).prefetch_related(
        'generator_for_sections__blueprint',
        'validator_for_sections__blueprint',
        'generator_for_sub_sections__section__blueprint',
    ).order_by('name')

    return Response({
        'agents': SectionAgentListSerializer(agents, many=True).data,
        'total': agents.count(),
    })
