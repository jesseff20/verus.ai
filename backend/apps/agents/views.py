"""
Views para Prompts de Agentes
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse
from .models import AgentPrompt
from .serializers import (
    AgentPromptListSerializer,
    AgentPromptDetailSerializer,
    AgentPromptCreateSerializer,
    AgentPromptUpdateSerializer,
    AgentExecuteSerializer,
)
from .permissions import CanManageAgentPrompts

import logging
logger = logging.getLogger(__name__)


def _invalidate_agent_cache():
    """
    Helper para invalidar cache de agentes (compatível com Redis e LocMemCache)

    LocMemCache não suporta delete_pattern(), então usamos try/except
    para garantir compatibilidade com ambos backends.
    """
    from django.core.cache import cache

    # Deletar chaves específicas conhecidas
    cache.delete('agent_prompts_stats')

    # Tentar delete_pattern (Redis), mas ignorar se não existir (LocMemCache)
    try:
        cache.delete_pattern('agent_prompts_*')
    except AttributeError:
        # LocMemCache não suporta delete_pattern - OK em desenvolvimento
        pass


@extend_schema_view(
    list=extend_schema(
        summary="Listar prompts de agentes",
        description="Retorna lista de todos os prompts configurados",
        tags=["Agents - Prompts"],
        responses={200: AgentPromptListSerializer(many=True)}
    ),
    retrieve=extend_schema(
        summary="Buscar prompt por ID",
        description="Retorna detalhes completos de um prompt",
        tags=["Agents - Prompts"],
        responses={200: AgentPromptDetailSerializer}
    ),
    create=extend_schema(
        summary="Criar prompt",
        description="Cria novo prompt de agente (admin/manager)",
        tags=["Agents - Prompts"],
        request=AgentPromptCreateSerializer,
        responses={201: AgentPromptDetailSerializer}
    ),
    update=extend_schema(
        summary="Atualizar prompt",
        description="Atualiza prompt (admin/manager)",
        tags=["Agents - Prompts"],
        request=AgentPromptUpdateSerializer,
        responses={200: AgentPromptDetailSerializer}
    ),
    partial_update=extend_schema(
        summary="Atualizar parcialmente prompt",
        description="Atualiza campos específicos (admin/manager)",
        tags=["Agents - Prompts"],
        request=AgentPromptUpdateSerializer,
        responses={200: AgentPromptDetailSerializer}
    ),
    destroy=extend_schema(
        summary="Deletar prompt",
        description="Remove prompt (admin/manager)",
        tags=["Agents - Prompts"],
        responses={204: None}
    ),
)
class AgentPromptViewSet(viewsets.ModelViewSet):
    """ViewSet para gerenciamento de prompts de agentes"""
    queryset = AgentPrompt.objects.all()
    permission_classes = [CanManageAgentPrompts]

    def get_serializer_class(self):
        if self.action == 'list':
            return AgentPromptListSerializer
        elif self.action == 'create':
            return AgentPromptCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return AgentPromptUpdateSerializer
        return AgentPromptDetailSerializer

    def get_queryset(self):
        from apps.accounts.permissions import is_admin_or_manager

        queryset = AgentPrompt.objects.select_related('created_by')

        # Non-admin users only see their own prompts
        if not is_admin_or_manager(self.request.user):
            queryset = queryset.filter(created_by=self.request.user)

        # Filtro por agent_type
        agent_type = self.request.query_params.get('agent_type')
        if agent_type:
            queryset = queryset.filter(agent_type=agent_type)

        # Filtro por provider
        llm_provider = self.request.query_params.get('llm_provider')
        if llm_provider:
            queryset = queryset.filter(llm_provider=llm_provider)

        # Apenas ativos (padrão: true)
        if self.request.query_params.get('active_only', 'true').lower() == 'true':
            queryset = queryset.filter(is_active=True)

        # Ordenação customizada
        ordering = self.request.query_params.get('ordering', 'default')
        if ordering == 'default':
            # Ordenar por: display_order, is_default, nome
            return queryset.order_by('display_order', '-is_default', 'name')
        elif ordering == 'name':
            return queryset.order_by('name')
        elif ordering == 'created':
            return queryset.order_by('-created_at')
        else:
            return queryset.order_by('display_order', '-is_default', 'name')

    def perform_create(self, serializer):
        """Invalida cache ao criar agente"""
        serializer.save()
        # Invalidar caches relacionados
        _invalidate_agent_cache()

    def perform_update(self, serializer):
        """Invalida cache ao atualizar agente"""
        serializer.save()
        # Invalidar caches relacionados
        _invalidate_agent_cache()

    def perform_destroy(self, instance):
        """Invalida cache ao deletar agente"""
        instance.delete()
        # Invalidar caches relacionados
        _invalidate_agent_cache()

    def create(self, request, *args, **kwargs):
        """Sobrescreve create para retornar AgentPromptDetailSerializer na resposta"""

        logger.info(f"=== DEBUG: Recebendo request POST em /api/v1/agents/ ===")
        logger.info(f"Request data: {request.data}")
        logger.info(f"Request user: {request.user}")

        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            logger.error(f"=== DEBUG: Validação falhou ===")
            logger.error(f"Errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        logger.info(f"=== DEBUG: Validação passou ===")
        logger.info(f"Validated data: {serializer.validated_data}")

        self.perform_create(serializer)

        # Retorna com DetailSerializer para incluir todos os campos (incluindo id)
        instance = serializer.instance
        detail_serializer = AgentPromptDetailSerializer(instance, context={'request': request})
        headers = self.get_success_headers(detail_serializer.data)

        logger.info(f"=== DEBUG: Agente criado com sucesso ===")
        logger.info(f"Response data: {detail_serializer.data}")

        return Response(detail_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @extend_schema(
        summary="Executar agente",
        description="Executa o agente com as variáveis fornecidas (chama LLM)",
        tags=["Agents - Execução"],
        request=AgentExecuteSerializer,
        responses={200: OpenApiResponse(description="Resposta do agente")}
    )
    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """Executa agente com chamada real ao LLM"""
        from .services import LLMService
        import time

        prompt = self.get_object()
        serializer = AgentExecuteSerializer(data=request.data)

        if serializer.is_valid():
            variables = serializer.validated_data.get('variables', {})
            user_input = serializer.validated_data.get('user_input', '')

            # Substituir variáveis no user_prompt_template
            user_prompt = prompt.user_prompt_template
            for key, value in variables.items():
                placeholder = f'{{{{{key}}}}}'
                user_prompt = user_prompt.replace(placeholder, str(value))

            # Adicionar user_input se fornecido
            if user_input:
                user_prompt = f"{user_prompt}\n\n{user_input}"

            try:
                # Chamar LLM
                start_time = time.time()

                result = LLMService.call(
                    provider=prompt.llm_provider,
                    model=prompt.model_name,
                    system_prompt=prompt.system_prompt,
                    user_prompt=user_prompt,
                    temperature=prompt.temperature,
                    max_tokens=prompt.max_tokens
                )

                execution_time = int((time.time() - start_time) * 1000)

                return Response({
                    'agent_name': prompt.name,
                    'agent_type': prompt.agent_type,
                    'response': result['response'],
                    'llm_provider': result['provider'],
                    'model': result['model'],
                    'tokens_used': result['tokens_used'],
                    'execution_time_ms': execution_time
                }, status=status.HTTP_200_OK)

            except Exception as e:
                return Response({
                    'error': str(e),
                    'agent_name': prompt.name
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Agentes agrupados por categoria",
        description="Retorna apenas agentes chat_assistant. Para outros tipos, use /api/v1/form-assistants/ ou /api/v1/document-generators/",
        tags=["Agents - Dashboard"],
        responses={200: OpenApiResponse(description="Agentes agrupados por categoria")}
    )
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """
        OTIMIZADO: Retorna agentes agrupados por categoria (apenas chat_assistant)
        GET /api/v1/agents/by_category/

        NOTA: form_assistant tem sua própria API
        - FormAssistant: /api/v1/form-assistants/

        OTIMIZAÇÕES:
        - Busca todos os agentes em uma query com select_related
        - Cache de 2 minutos
        """
        from django.core.cache import cache

        # Tentar buscar do cache primeiro (2 minutos)
        cache_key = f'agent_prompts_list_{request.GET.urlencode()}'
        cached_result = cache.get(cache_key)
        if cached_result:
            return Response(cached_result)

        # Buscar todos os agentes (já são todos chat)
        queryset = self.filter_queryset(self.get_queryset())
        agents = list(queryset)

        # Montar resposta
        grouped = {
            'chat_assistant': {
                'name': 'Assistente Pessoal/Chat',
                'code': 'chat_assistant',
                'count': len(agents),
                'agents': AgentPromptListSerializer(agents, many=True, context={'request': request}).data
            }
        }

        # Cache por 2 minutos
        cache.set(cache_key, grouped, 120)

        return Response(grouped)

    @extend_schema(
        summary="Listar agentes de chat",
        description="Retorna lista de todos os agentes de chat (AgentPrompt)",
        tags=["Agents - Chat"],
        responses={200: AgentPromptListSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], url_path='chat_assistants')
    def chat_assistants(self, request):
        """
        Listar apenas agentes de chat (AgentPrompt)
        GET /api/v1/agents/chat_assistants/

        Equivalente aos endpoints:
        - FormAssistant: /api/v1/forms/assistants/
        """
        queryset = self.filter_queryset(self.get_queryset())
        serializer = AgentPromptListSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    @extend_schema(
        summary="Estatísticas dos agentes",
        description="Retorna estatísticas gerais sobre os agentes cadastrados",
        tags=["Agents - Dashboard"],
        responses={200: OpenApiResponse(description="Estatísticas")}
    )
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        OTIMIZADO: Estatísticas dos agentes (apenas chat_assistant)
        GET /api/v1/agents/stats/

        NOTA: form_assistant tem sua própria API
        - FormAssistant: /api/v1/form-assistants/stats/

        OTIMIZAÇÕES:
        - Usa aggregate com Count + Q filters para evitar múltiplas queries
        - Reduz de ~15 queries para 1 query única
        - Cache de 2 minutos
        """
        from django.core.cache import cache
        from django.db.models import Count, Q

        # Tentar buscar do cache primeiro (2 minutos)
        cache_key = 'agent_prompts_stats'
        cached_result = cache.get(cache_key)
        if cached_result:
            return Response(cached_result)

        queryset = self.get_queryset()

        # OTIMIZAÇÃO: Calcular todos os agentes (já são todos chat)
        aggregate_dict = {
            'total': Count('id'),
            'active': Count('id', filter=Q(is_active=True)),
        }

        # Por provider
        for provider_code, _ in AgentPrompt.LLM_PROVIDER_CHOICES:
            aggregate_dict[f'prov_{provider_code}_count'] = Count('id', filter=Q(llm_provider=provider_code))

        # Executar aggregate único
        result = queryset.aggregate(**aggregate_dict)

        # Montar resposta
        stats = {
            'total': result['total'],
            'active': result['active'],
            'by_category': {
                'chat_assistant': {
                    'name': 'Assistente Pessoal/Chat',
                    'count': result['total'],  # Todos são chat
                    'active': result['active']
                }
            },
            'by_provider': {},
        }

        # Por provider
        for provider_code, provider_name in AgentPrompt.LLM_PROVIDER_CHOICES:
            stats['by_provider'][provider_code] = {
                'name': provider_name,
                'count': result[f'prov_{provider_code}_count']
            }

        # Cache por 2 minutos
        cache.set(cache_key, stats, 120)

        return Response(stats)

    # ACTIONS REMOVIDAS: form_assistants(), chat_assistants()
    # Use as novas APIs:
    # - FormAssistant: /api/v1/form-assistants/
    # - Chat Assistant: /api/v1/agents/?category=chat_assistant

    @extend_schema(
        summary="Duplicar agente",
        description="Cria uma cópia de um agente existente para criar nova versão",
        tags=["Agents - Prompts"],
        responses={200: AgentPromptDetailSerializer}
    )
    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """Duplica um agente para criar nova versão"""
        agent = self.get_object()

        new_agent = AgentPrompt.objects.create(
            name=f"{agent.name} (cópia)",
            description=agent.description,
            agent_type=agent.agent_type,
            system_prompt=agent.system_prompt,
            user_prompt_template=agent.user_prompt_template,
            llm_provider=agent.llm_provider,
            model_name=agent.model_name,
            temperature=agent.temperature,
            max_tokens=agent.max_tokens,
            use_rag=agent.use_rag,
            rag_query_template=agent.rag_query_template,
            icon=agent.icon,
            color=agent.color,
            display_order=agent.display_order + 1,
            is_active=False,  # Inativo por padrão
            is_default=False,
            created_by=request.user
        )

        # Copiar knowledge_bases M2M
        if agent.knowledge_bases.exists():
            new_agent.knowledge_bases.set(agent.knowledge_bases.all())

        serializer = AgentPromptDetailSerializer(new_agent, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="Chat com assistente IA (com RAG e RLHF)",
        description="Endpoint de chat com consulta à Base de Conhecimento e salvamento de conversas para RLHF",
        tags=["Agents - Chat"],
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'message': {'type': 'string', 'description': 'Mensagem do usuário'},
                    'session_id': {'type': 'string', 'description': 'ID da sessão (gerado no frontend)'},
                    'conversation_id': {'type': 'string', 'description': 'ID da conversa existente (para continuar)'},
                    'document_type': {'type': 'string', 'description': 'Tipo do documento (ex: ETP)'},
                    'document_id': {'type': 'string', 'description': 'ID do documento sendo editado'},
                    'current_field': {'type': 'string', 'description': 'Campo atual sendo preenchido'},
                }
            }
        },
        responses={200: OpenApiResponse(description="Resposta do assistente com KB sources")}
    )
    @action(detail=False, methods=['post'], url_path='chat')
    def chat(self, request):
        """
        Endpoint de chat com RAG (Base de Conhecimento) e salvamento de conversas/mensagens para RLHF
        """
        from .services import LLMService
        from apps.kb.services import VectorSearchService
        from .models_assistant import AssistantConversation, AssistantMessage, AssistantKnowledgeQuery
        import time
        import uuid

        # === 1. VALIDAR ENTRADA ===
        message = request.data.get('message', '').strip()
        if not message:
            return Response({
                'error': 'Mensagem é obrigatória'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Parâmetros de contexto
        session_id = request.data.get('session_id', str(uuid.uuid4()))
        conversation_id = request.data.get('conversation_id')
        document_type = request.data.get('document_type')
        document_id = request.data.get('document_id')
        current_field = request.data.get('current_field')

        # === 2. BUSCAR OU CRIAR CONVERSA ===
        if conversation_id:
            try:
                conversation = AssistantConversation.objects.get(id=conversation_id, user=request.user)
            except AssistantConversation.DoesNotExist:
                # Se não encontrar, criar nova
                conversation = AssistantConversation.objects.create(
                    user=request.user,
                    session_id=session_id,
                    document_type=document_type,
                    document_id=document_id,
                    current_field=current_field
                )
        else:
            # Criar nova conversa
            conversation = AssistantConversation.objects.create(
                user=request.user,
                session_id=session_id,
                document_type=document_type,
                document_id=document_id,
                current_field=current_field
            )

        # === 3. SALVAR MENSAGEM DO USUÁRIO ===
        user_message = AssistantMessage.objects.create(
            conversation=conversation,
            role='user',
            content=message
        )

        try:
            # === 4. BUSCAR ASSISTENTE DO BANCO ===
            # Buscar assistente ativo (padrão ou específico)
            # NOTA: Todos os AgentPrompts agora são chat assistants
            try:
                assistant = AgentPrompt.objects.filter(
                    is_active=True,
                    is_default=True
                ).first()

                if not assistant:
                    # Fallback: qualquer assistente ativo
                    assistant = AgentPrompt.objects.filter(
                        is_active=True
                    ).first()

                if not assistant:
                    return Response({
                        'error': 'Nenhum assistente de chat configurado. Entre em contato com o administrador.'
                    }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

            except Exception as e:
                logger.error(f"Erro ao buscar assistente: {str(e)}")
                return Response({
                    'error': 'Erro ao buscar configuração do assistente'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # === 5. DETECTAR MENÇÃO A PROCESSOS ===
            from .services import ProcessoDetectionService

            processo_number = ProcessoDetectionService.detect_processo_context(message)
            should_filter = ProcessoDetectionService.should_filter_by_processo(message)

            # === 6. CONSULTAR BASE DE CONHECIMENTO (RAG) ===
            # Preparar filtro de tags para processo (se detectado)
            filter_tags = []
            if processo_number and should_filter:
                filter_tags.append(f'processo:{processo_number}')
                logger.debug(f"Processo detectado: {processo_number} - Filtrando documentos")

            # Decidir se filtra por KBs específicas ou busca em toda a base
            kb_document_ids = None  # Por padrão, buscar em toda a base

            # Apenas filtrar por KBs específicas se NÃO houver filtro de processo
            if not filter_tags:
                kb_document_ids = list(assistant.knowledge_bases.values_list('id', flat=True))

            kb_start = time.time()
            kb_results = VectorSearchService.search(
                query_text=message,
                top_k=5,
                similarity_threshold=0.3,  # Threshold baixo para documentos específicos
                document_ids=kb_document_ids if kb_document_ids else None,
                tags=filter_tags if filter_tags else None
            )
            kb_query_time = int((time.time() - kb_start) * 1000)

            used_kb = len(kb_results) > 0
            kb_context = ""
            kb_sources = []

            if used_kb:
                kb_context = "\n\n=== CONTEXTO DA BASE DE CONHECIMENTO ===\n"
                for i, result in enumerate(kb_results, 1):
                    kb_context += f"\n[Documento {i}: {result['document_title']}]\n{result['content']}\n"
                    kb_sources.append({
                        'document_id': result['document_id'],
                        'document_title': result['document_title'],
                        'document_category': result['document_category'],
                        'content': result['content'][:200] + '...',  # Preview
                        'similarity': result['similarity']
                    })

                # Salvar query na KB
                AssistantKnowledgeQuery.objects.create(
                    message=user_message,
                    query_text=message,
                    query_embedding=[],  # Opcional: salvar embedding depois
                    results_count=len(kb_results),
                    top_results=kb_sources,
                    query_time_ms=kb_query_time
                )

            # === 7. MONTAR PROMPT COM CONTEXTO ===
            context_values = {
                'document_type': document_type or 'não especificado',
                'current_field': current_field or 'nenhum',
                'kb_context': kb_context,
                'message': message
            }

            # Substituir variáveis no system_prompt do assistente
            system_prompt = assistant.system_prompt
            for key, value in context_values.items():
                placeholder = f'{{{{{key}}}}}'
                system_prompt = system_prompt.replace(placeholder, str(value))

            # Substituir variáveis no user_prompt_template (se existir)
            user_prompt = message
            if assistant.user_prompt_template:
                user_prompt = assistant.user_prompt_template
                for key, value in context_values.items():
                    placeholder = f'{{{{{key}}}}}'
                    user_prompt = user_prompt.replace(placeholder, str(value))

            # === 6. CHAMAR LLM COM CONFIGURAÇÕES DO ASSISTENTE ===
            llm_start = time.time()
            result = LLMService.call(
                provider=assistant.llm_provider,
                model=assistant.model_name,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=assistant.temperature,
                max_tokens=assistant.max_tokens
            )
            response_time_ms = int((time.time() - llm_start) * 1000)

            # === 7. SALVAR RESPOSTA DO ASSISTENTE ===
            kb_documents_used = [src['document_id'] for src in kb_sources] if kb_sources else []
            kb_relevance_scores = [src['similarity'] for src in kb_sources] if kb_sources else []

            assistant_message = AssistantMessage.objects.create(
                conversation=conversation,
                role='assistant',
                content=result['response'],
                llm_provider=result['provider'],
                model_name=result['model'],
                tokens_used=result['tokens_used'],
                response_time_ms=response_time_ms,
                used_kb=used_kb,
                kb_documents_used=kb_documents_used,
                kb_relevance_scores=kb_relevance_scores
            )

            # === 8. ATUALIZAR MÉTRICAS DA CONVERSA ===
            conversation.total_messages += 2  # user + assistant
            conversation.total_tokens_used += result['tokens_used']

            # Atualizar tempo médio de resposta
            if conversation.avg_response_time_ms == 0:
                conversation.avg_response_time_ms = response_time_ms
            else:
                # Média ponderada
                total_responses = (conversation.total_messages // 2)
                conversation.avg_response_time_ms = int(
                    (conversation.avg_response_time_ms * (total_responses - 1) + response_time_ms) / total_responses
                )

            conversation.save()

            # === 9. RETORNAR RESPOSTA ===
            return Response({
                'conversation_id': str(conversation.id),
                'message_id': str(assistant_message.id),
                'response': result['response'],
                'message': result['response'],  # Compatibilidade com frontend antigo
                'llm_provider': result['provider'],
                'model': result['model'],
                'tokens_used': result['tokens_used'],
                'response_time_ms': response_time_ms,
                'used_kb': used_kb,
                'kb_sources': kb_sources if used_kb else [],
            }, status=status.HTTP_200_OK)

        except Exception as e:
            import traceback
            logger.error(f"Erro no chat: {str(e)}")
            logger.error(traceback.format_exc())

            return Response({
                'error': str(e),
                'message': 'Desculpe, ocorreu um erro ao processar sua mensagem. Tente novamente.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        summary="Enviar feedback sobre resposta do assistente (RLHF)",
        description="Permite que usuário dê feedback positivo/negativo sobre resposta do assistente",
        tags=["Agents - Feedback"],
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'message_id': {'type': 'string', 'description': 'ID da mensagem do assistente'},
                    'feedback_type': {'type': 'string', 'enum': ['positive', 'negative'], 'description': 'Tipo de feedback'},
                    'reason': {
                        'type': 'string',
                        'enum': ['incorrect', 'incomplete', 'irrelevant', 'unclear', 'outdated', 'formatting', 'other'],
                        'description': 'Motivo (apenas para feedback negativo)'
                    },
                    'comment': {'type': 'string', 'description': 'Comentário adicional (opcional)'},
                    'suggested_response': {'type': 'string', 'description': 'Resposta sugerida pelo usuário (opcional)'},
                }
            }
        },
        responses={201: OpenApiResponse(description="Feedback registrado com sucesso")}
    )
    @action(detail=False, methods=['post'], url_path='feedback')
    def feedback(self, request):
        """
        Endpoint para receber feedback do usuário sobre respostas do assistente (RLHF)
        """
        from .models_assistant import AssistantMessage, AssistantFeedback, AssistantConversation
        from django.utils import timezone

        # Validar dados de entrada
        message_id = request.data.get('message_id')
        feedback_type = request.data.get('feedback_type')

        if not message_id or not feedback_type:
            return Response({
                'error': 'message_id e feedback_type são obrigatórios'
            }, status=status.HTTP_400_BAD_REQUEST)

        if feedback_type not in ['positive', 'negative']:
            return Response({
                'error': 'feedback_type deve ser "positive" ou "negative"'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Buscar mensagem
            message = AssistantMessage.objects.get(id=message_id, role='assistant')

            # Verificar se usuário já deu feedback para esta mensagem
            existing_feedback = AssistantFeedback.objects.filter(
                message=message,
                user=request.user
            ).first()

            if existing_feedback:
                # Atualizar feedback existente
                existing_feedback.feedback_type = feedback_type
                existing_feedback.reason = request.data.get('reason')
                existing_feedback.comment = request.data.get('comment')
                existing_feedback.suggested_response = request.data.get('suggested_response')
                existing_feedback.save()

                feedback = existing_feedback
                created = False
            else:
                # Criar novo feedback
                feedback = AssistantFeedback.objects.create(
                    message=message,
                    user=request.user,
                    feedback_type=feedback_type,
                    reason=request.data.get('reason') if feedback_type == 'negative' else None,
                    comment=request.data.get('comment'),
                    suggested_response=request.data.get('suggested_response')
                )
                created = True

            # Atualizar satisfaction score da conversa
            conversation = message.conversation
            feedbacks = AssistantFeedback.objects.filter(
                message__conversation=conversation
            )

            if feedbacks.exists():
                positive_count = feedbacks.filter(feedback_type='positive').count()
                total_count = feedbacks.count()
                conversation.user_satisfaction_score = positive_count / total_count
                conversation.save()

            return Response({
                'detail': 'Feedback registrado com sucesso' if created else 'Feedback atualizado com sucesso',
                'feedback_id': str(feedback.id),
                'created': created
            }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

        except AssistantMessage.DoesNotExist:
            return Response({
                'error': 'Mensagem não encontrada'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            import traceback
            logger.error(f"Erro ao salvar feedback: {str(e)}")
            logger.error(traceback.format_exc())

            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ===== ANALYTICS VIEWSET =====

from .models_assistant import AssistantAnalytics
from .serializers import AssistantAnalyticsSerializer
from django.db.models import Sum, Avg
from datetime import timedelta, datetime as _datetime
from django.utils import timezone


@extend_schema_view(
    list=extend_schema(
        summary="Listar analytics do assistente",
        description="Retorna analytics agregados por data",
        tags=["Agents - Analytics"],
        responses={200: AssistantAnalyticsSerializer(many=True)}
    ),
)
class AssistantAnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para visualizar analytics do assistente (somente leitura)"""
    queryset = AssistantAnalytics.objects.all().order_by('-date')
    serializer_class = AssistantAnalyticsSerializer
    permission_classes = [CanManageAgentPrompts]

    @extend_schema(
        summary="Resumo de analytics dos últimos 30 dias",
        description="Retorna métricas agregadas dos últimos 30 dias",
        tags=["Agents - Analytics"],
        responses={200: OpenApiResponse(description="Resumo de analytics")}
    )
    @action(detail=False, methods=['get'], url_path='summary')
    def summary(self, request):
        """
        OTIMIZADO: Retorna resumo dos últimos 30 dias - auto-calcula dados do dia atual

        OTIMIZAÇÕES:
        - Uso de aggregate() único em vez de múltiplos .count()
        - Cache de 5 minutos para o resultado final
        - Reduz de ~10 queries para ~3 queries
        """
        from django.core.cache import cache
        from .models_assistant import AssistantConversation, AssistantMessage, AssistantFeedback, AssistantKnowledgeQuery
        from django.db.models import Count, Avg, Sum, Q

        # Tentar buscar do cache primeiro (5 minutos)
        cache_key = 'assistant_analytics_summary'
        cached_result = cache.get(cache_key)
        if cached_result:
            return Response(cached_result, status=status.HTTP_200_OK)

        # Auto-calcular analytics do dia atual (se ainda não existir)
        today = timezone.localtime().date()  # Usa timezone de São Paulo
        today_analytics, created = AssistantAnalytics.objects.get_or_create(
            date=today,
            defaults={'calculated_at': timezone.now()}
        )

        # Se foi criado agora OU se tem mais de 1 hora, recalcular
        needs_recalculation = created or (
            timezone.now() - today_analytics.calculated_at > timedelta(hours=1)
        )

        if needs_recalculation:
            # Calcular período do dia
            start_datetime = timezone.make_aware(
                _datetime.combine(today, _datetime.min.time())
            )
            end_datetime = timezone.now()

            # OTIMIZAÇÃO: Calcular tudo em uma única passada com aggregate
            conversations_stats = AssistantConversation.objects.filter(
                started_at__gte=start_datetime,
                started_at__lt=end_datetime
            ).aggregate(
                total_conversations=Count('id'),
                unique_users=Count('user', distinct=True)
            )

            messages_stats = AssistantMessage.objects.filter(
                created_at__gte=start_datetime,
                created_at__lt=end_datetime
            ).aggregate(
                total_messages=Count('id'),
                avg_response_time=Avg('response_time_ms', filter=Q(role='assistant')),
                total_tokens=Sum('tokens_used', filter=Q(role='assistant'))
            )

            feedbacks_stats = AssistantFeedback.objects.filter(
                created_at__gte=start_datetime,
                created_at__lt=end_datetime
            ).aggregate(
                total_feedbacks=Count('id'),
                positive_feedbacks=Count('id', filter=Q(feedback_type='positive')),
                negative_feedbacks=Count('id', filter=Q(feedback_type='negative')),
                incorrect_count=Count('id', filter=Q(reason='incorrect')),
                incomplete_count=Count('id', filter=Q(reason='incomplete')),
                irrelevant_count=Count('id', filter=Q(reason='irrelevant')),
                unclear_count=Count('id', filter=Q(reason='unclear')),
                outdated_count=Count('id', filter=Q(reason='outdated'))
            )

            kb_queries_count = AssistantKnowledgeQuery.objects.filter(
                created_at__gte=start_datetime,
                created_at__lt=end_datetime
            ).count()

            # Atualizar analytics
            total_conversations = conversations_stats['total_conversations'] or 0
            total_messages = messages_stats['total_messages'] or 0
            total_feedbacks = feedbacks_stats['total_feedbacks'] or 0
            positive_feedbacks = feedbacks_stats['positive_feedbacks'] or 0

            today_analytics.total_conversations = total_conversations
            today_analytics.total_messages = total_messages
            today_analytics.unique_users = conversations_stats['unique_users'] or 0
            today_analytics.avg_messages_per_conversation = (
                (total_messages / total_conversations) if total_conversations > 0 else 0
            )
            today_analytics.avg_response_time_ms = int(messages_stats['avg_response_time'] or 0)
            today_analytics.total_tokens_used = messages_stats['total_tokens'] or 0
            today_analytics.total_kb_queries = kb_queries_count
            today_analytics.total_feedbacks = total_feedbacks
            today_analytics.positive_feedbacks = positive_feedbacks
            today_analytics.negative_feedbacks = feedbacks_stats['negative_feedbacks'] or 0
            today_analytics.satisfaction_rate = (
                (positive_feedbacks / total_feedbacks * 100) if total_feedbacks > 0 else 0
            )
            today_analytics.incorrect_count = feedbacks_stats['incorrect_count'] or 0
            today_analytics.incomplete_count = feedbacks_stats['incomplete_count'] or 0
            today_analytics.irrelevant_count = feedbacks_stats['irrelevant_count'] or 0
            today_analytics.unclear_count = feedbacks_stats['unclear_count'] or 0
            today_analytics.outdated_count = feedbacks_stats['outdated_count'] or 0

            today_analytics.calculated_at = timezone.now()
            today_analytics.save()

        # Buscar últimos 30 dias
        thirty_days_ago = today - timedelta(days=30)
        recent_analytics = AssistantAnalytics.objects.filter(
            date__gte=thirty_days_ago
        ).order_by('date')

        # OTIMIZAÇÃO: Totais dos últimos 30 dias em um único aggregate
        totals = recent_analytics.aggregate(
            total_conversations=Sum('total_conversations'),
            total_messages=Sum('total_messages'),
            total_feedbacks=Sum('total_feedbacks'),
            positive_feedbacks=Sum('positive_feedbacks'),
            negative_feedbacks=Sum('negative_feedbacks'),
            avg_satisfaction=Avg('satisfaction_rate'),
            total_tokens=Sum('total_tokens_used'),
            avg_response_time=Avg('avg_response_time_ms'),
        )

        # Chart data em ordem crescente por data
        chart_data = list(recent_analytics.values(
            'date',
            'total_conversations',
            'total_messages',
            'satisfaction_rate',
            'total_feedbacks',
            'total_tokens_used'
        ))

        result = {
            'summary': {
                'total_conversations': totals['total_conversations'] or 0,
                'total_messages': totals['total_messages'] or 0,
                'total_feedbacks': totals['total_feedbacks'] or 0,
                'positive_feedbacks': totals['positive_feedbacks'] or 0,
                'negative_feedbacks': totals['negative_feedbacks'] or 0,
                'avg_satisfaction': round(totals['avg_satisfaction'] or 0, 1),
                'total_tokens': totals['total_tokens'] or 0,
                'avg_response_time': int(totals['avg_response_time'] or 0),
            },
            'chart_data': chart_data,
            'feedback_timeline': list(recent_analytics.values(
                'date',
                'positive_feedbacks',
                'negative_feedbacks'
            )),
            'period': {
                'start': thirty_days_ago.isoformat(),
                'end': today.isoformat(),
                'days': 30
            }
        }

        # Cache por 5 minutos
        cache.set(cache_key, result, 300)

        return Response(result, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Word Cloud de mensagens do assistente",
        description="Retorna as palavras mais frequentes das mensagens de entrada (usuários) e saída (assistente)",
        tags=["Agents - Analytics"],
        responses={200: OpenApiResponse(description="Dados para word cloud")}
    )
    @action(detail=False, methods=['get'], url_path='wordcloud')
    def wordcloud(self, request):
        """Retorna palavras mais frequentes para word cloud"""
        from .models_assistant import AssistantMessage
        from collections import Counter
        import re

        # Stopwords em português
        stopwords = {
            'a', 'o', 'e', 'de', 'da', 'do', 'em', 'um', 'uma', 'os', 'as', 'dos', 'das',
            'para', 'com', 'por', 'que', 'não', 'se', 'na', 'no', 'ao', 'à', 'pelo', 'pela',
            'mais', 'ou', 'mas', 'como', 'ser', 'esta', 'este', 'esse', 'essa', 'isso',
            'qual', 'quais', 'quando', 'onde', 'porque', 'porquê', 'quem', 'seu', 'sua',
            'seus', 'suas', 'ele', 'ela', 'eles', 'elas', 'você', 'vocês', 'nós',
            'já', 'foi', 'são', 'é', 'está', 'estão', 'tem', 'têm', 'pode', 'podem',
            'sobre', 'após', 'antes', 'durante', 'entre', 'até', 'desde', 'sem'
        }

        # Período dos últimos 30 dias
        thirty_days_ago = timezone.now() - timedelta(days=30)

        # Buscar mensagens do usuário (entrada)
        user_messages = AssistantMessage.objects.filter(
            role='user',
            created_at__gte=thirty_days_ago
        ).values_list('content', flat=True)

        # Buscar mensagens do assistente (saída)
        assistant_messages = AssistantMessage.objects.filter(
            role='assistant',
            created_at__gte=thirty_days_ago
        ).values_list('content', flat=True)

        def extract_words(messages):
            """Extrai palavras de uma lista de mensagens"""
            all_text = ' '.join(messages)
            # Remove pontuação e converte para minúsculas
            words = re.findall(r'\b[a-záàâãéèêíïóôõöúçñA-ZÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇÑ]{3,}\b', all_text.lower())
            # Remove stopwords
            filtered_words = [w for w in words if w not in stopwords]
            return Counter(filtered_words)

        # Processar mensagens de entrada (usuário)
        input_word_count = extract_words(user_messages)
        input_wordcloud = [
            {'text': word, 'value': count}
            for word, count in input_word_count.most_common(50)
        ]

        # Processar mensagens de saída (assistente)
        output_word_count = extract_words(assistant_messages)
        output_wordcloud = [
            {'text': word, 'value': count}
            for word, count in output_word_count.most_common(50)
        ]

        return Response({
            'input_words': input_wordcloud,
            'output_words': output_wordcloud,
            'period': {
                'start': thirty_days_ago.date().isoformat(),
                'end': timezone.localtime().date().isoformat(),
                'days': 30
            },
            'total_messages_analyzed': {
                'input': len(user_messages),
                'output': len(assistant_messages)
            }
        }, status=status.HTTP_200_OK)
