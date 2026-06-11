"""
DynamicGraphBuilder - Construtor dinâmico de grafos LangGraph.

Este serviço constrói grafos LangGraph dinamicamente baseados em
DocumentBlueprints configurados no banco de dados.

Permite:
- ETP padrão com 15 seções
- ETP Rio de Janeiro com 29 seções
- Qualquer outro template configurado

Usage:
    from apps.intelligent_assistant.services.dynamic_graph_builder import DynamicGraphBuilder

    builder = DynamicGraphBuilder(claude_service, kb_service)
    runner = builder.create_runner(blueprint_id="...")
    result = runner.run(objective="...")
"""
import re
import time
import logging
from typing import Dict, Any, Optional, List, TypedDict, Callable
from collections import OrderedDict
from datetime import datetime
from enum import Enum

from langgraph.graph import StateGraph, END

from apps.intelligent_assistant.models import (
    DocumentBlueprint,
    BlueprintSection,
    BlueprintSubSection,
    SectionAgentConfig,
    SectionPipelineStep,
)
from apps.intelligent_assistant.utils import strip_generation_suffix

logger = logging.getLogger(__name__)


class DynamicSectionStatus(str, Enum):
    """Status de processamento de uma seção."""
    PENDING = "pending"
    GENERATING = "generating"
    ANALYZING = "analyzing"
    REFINING = "refining"
    VALIDATING = "validating"
    VALID = "valid"
    INVALID = "invalid"
    REGENERATING = "regenerating"
    ERROR = "error"
    SKIPPED = "skipped"


STEP_TYPE_STATUS_MAP = {
    'analyze': DynamicSectionStatus.ANALYZING,
    'generate': DynamicSectionStatus.GENERATING,
    'validate': DynamicSectionStatus.VALIDATING,
    'refine': DynamicSectionStatus.REFINING,
}


class DynamicGraphBuilder:
    """
    Construtor dinâmico de grafos LangGraph.

    Carrega um DocumentBlueprint do banco e constrói um grafo
    com o número correto de seções e agentes configurados.
    """

    def __init__(self, claude_service=None, kb_service=None, llm_service=None):
        """
        Inicializa o builder.

        Args:
            claude_service: Serviço legado Claude (backward compat)
            kb_service: Serviço de Knowledge Base (PgVector)
            llm_service: UnifiedLLMService (novo, multi-provider)
        """
        self.claude_service = claude_service
        self.kb_service = kb_service
        self.llm_service = llm_service

    def create_runner(
        self,
        blueprint_id: Optional[str] = None,
        blueprint_name: Optional[str] = None,
        checkpointer=None,
        event_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    ) -> 'DynamicGraphRunner':
        """
        Cria um runner para um blueprint específico.

        Args:
            blueprint_id: UUID do blueprint
            blueprint_name: Nome do blueprint (alternativa ao ID)
            checkpointer: Checkpointer opcional para persistência
            event_callback: Callback para eventos granulares do pipeline

        Returns:
            DynamicGraphRunner configurado

        Raises:
            ValueError: Se blueprint não encontrado
        """
        # Carrega blueprint
        if blueprint_id:
            blueprint = DocumentBlueprint.objects.filter(
                id=blueprint_id,
                is_active=True
            ).prefetch_related('sections').first()
        elif blueprint_name:
            blueprint = DocumentBlueprint.objects.filter(
                name=blueprint_name,
                is_active=True
            ).prefetch_related('sections').first()
        else:
            # Usa o blueprint padrão
            blueprint = DocumentBlueprint.objects.filter(
                is_default=True,
                is_active=True
            ).prefetch_related('sections').first()

        if not blueprint:
            raise ValueError(
                f"Blueprint não encontrado. ID: {blueprint_id}, Nome: {blueprint_name}"
            )

        logger.info(f"Criando runner para blueprint: {blueprint.name}")

        return DynamicGraphRunner(
            blueprint=blueprint,
            claude_service=self.claude_service,
            kb_service=self.kb_service,
            llm_service=self.llm_service,
            checkpointer=checkpointer,
            event_callback=event_callback,
        )


class DynamicGraphRunner:
    """
    Executor de grafo dinâmico.

    Gera documentos baseados em um blueprint específico.
    """

    def __init__(
        self,
        blueprint: DocumentBlueprint,
        claude_service=None,
        kb_service=None,
        llm_service=None,
        checkpointer=None,
        event_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    ):
        """
        Inicializa o runner.

        Args:
            blueprint: Blueprint carregado do banco
            claude_service: Serviço legado Claude (backward compat)
            kb_service: Serviço Knowledge Base
            llm_service: UnifiedLLMService (novo, multi-provider)
            checkpointer: Checkpointer opcional
            event_callback: Callback para eventos granulares do pipeline.
                           Assinatura: callback(event_type: str, data: dict)
        """
        self.blueprint = blueprint
        self.claude_service = claude_service
        self.kb_service = kb_service
        self.llm_service = llm_service
        self.checkpointer = checkpointer
        self.event_callback = event_callback
        self._compiled_graph = None
        self._sections = None

        # ── Token buffering for section_chunk events ──
        # Reduces SSE event frequency by ~20x: flush every 150ms or 20 chunks.
        self._CHUNK_FLUSH_INTERVAL = 0.15   # seconds between flushes
        self._CHUNK_FLUSH_COUNT = 20        # max chunks before forced flush
        self._chunk_buffers: Dict[Any, list] = {}  # keyed by (section, sub_key?)
        self._chunk_last_flush: Dict[Any, float] = {}

    def _emit(self, event_type: str, data: Dict[str, Any]) -> None:
        """Emite evento granular do pipeline se callback configurado.

        section_chunk events are buffered and flushed every 150ms or 20
        accumulated chunks to reduce SSE overhead by ~20x.
        """
        if not self.event_callback:
            return

        if event_type == 'section_chunk':
            # Buffer key = (section, sub_key) to support sub-section streaming
            buf_key = (data.get('section'), data.get('sub_key'))
            self._chunk_buffers.setdefault(buf_key, [])
            self._chunk_buffers[buf_key].append(data.get('chunk', ''))
            now = time.time()
            last = self._chunk_last_flush.get(buf_key, now)
            if (now - last >= self._CHUNK_FLUSH_INTERVAL
                    or len(self._chunk_buffers[buf_key]) >= self._CHUNK_FLUSH_COUNT):
                merged = ''.join(self._chunk_buffers[buf_key])
                self._chunk_buffers[buf_key] = []
                self._chunk_last_flush[buf_key] = now
                flushed_data = {**data, 'chunk': merged}
                try:
                    self.event_callback(event_type, flushed_data)
                except Exception as e:
                    logger.warning(f"Erro ao emitir evento {event_type}: {e}")
            return

        try:
            self.event_callback(event_type, data)
        except Exception as e:
            logger.warning(f"Erro ao emitir evento {event_type}: {e}")

    def _flush_chunk_buffers(self) -> None:
        """Force-flush any remaining buffered section_chunk data."""
        if not self.event_callback:
            return
        for buf_key, chunks in list(self._chunk_buffers.items()):
            if chunks:
                merged = ''.join(chunks)
                self._chunk_buffers[buf_key] = []
                flushed_data = {'section': buf_key[0], 'chunk': merged}
                if buf_key[1] is not None:
                    flushed_data['sub_key'] = buf_key[1]
                try:
                    self.event_callback('section_chunk', flushed_data)
                except Exception as e:
                    logger.warning(f"Erro ao flush chunk buffer: {e}")

    @property
    def sections(self) -> List[BlueprintSection]:
        """Retorna as seções ordenadas do blueprint."""
        if self._sections is None:
            self._sections = list(
                self.blueprint.sections.filter(is_active=True)
                .select_related('generator_agent', 'validator_agent')
                .order_by('order', 'section_number')
            )
        return self._sections

    def _create_dynamic_state_class(self) -> type:
        """
        Cria dinamicamente a classe de estado TypedDict.

        Returns:
            Classe TypedDict com campos para todas as seções
        """
        # Campos base
        annotations = {
            'objective': str,
            'objective_summary': str,
            'collection_name': Optional[str],
            'user_id': Optional[str],
            'blueprint_id': str,
            'blueprint_name': str,
            'created_at': str,
            'updated_at': str,
            'status': str,
            'current_section': int,
            'max_retries': int,
            'errors': List[str],
            'sections_to_generate': List[int],
            'sub_section_decisions': Dict[str, Any],
            'final_document': Optional[str],
            'overall_validation': Optional[Dict[str, Any]],
        }

        # Adiciona campos para cada seção
        for section in self.sections:
            field_name = f"section_{section.section_number:02d}"
            annotations[field_name] = Dict[str, Any]

        # Cria TypedDict dinamicamente
        DynamicState = TypedDict('DynamicState', annotations, total=False)
        return DynamicState

    def _create_initial_state(
        self,
        objective: str,
        collection_name: Optional[str] = None,
        user_id: Optional[str] = None,
        max_retries: int = 3,
        sections_to_generate: Optional[List[int]] = None,
        sub_section_decisions: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Cria o estado inicial do grafo.

        Args:
            objective: Objetivo da contratação
            collection_name: ID da collection para RAG
            user_id: ID do usuário
            max_retries: Máximo de tentativas por seção
            sections_to_generate: Lista de seções a gerar (números)
            sub_section_decisions: Decisões do usuário sobre sub-seções.
                Formato: {
                    "sub_key": {
                        "action": "generate" | "default",
                        "fields_data": {"campo": "valor", ...},
                        "feedback": "texto de regeneração (opcional)"
                    }
                }

        Returns:
            Estado inicial
        """
        now = datetime.utcnow().isoformat()

        # Números de todas as seções disponíveis
        all_section_numbers = [s.section_number for s in self.sections]

        # Se não especificou (None), gera todas. Lista vazia = nenhuma seção.
        sections = sections_to_generate if sections_to_generate is not None else all_section_numbers
        first_section = min(sections) if sections else (all_section_numbers[0] if all_section_numbers else 1)

        # Resumir objetivo para queries RAG (embedding max 512 tokens)
        objective_summary = self._summarize_objective_for_rag(objective)

        state = {
            'objective': objective,
            'objective_summary': objective_summary,
            'collection_name': collection_name,
            'user_id': user_id,
            'blueprint_id': str(self.blueprint.id),
            'blueprint_name': self.blueprint.name,
            'created_at': now,
            'updated_at': now,
            'status': 'draft',
            'current_section': first_section,
            'max_retries': max_retries,
            'errors': [],
            'sections_to_generate': sections,
            'sub_section_decisions': sub_section_decisions or {},
            'final_document': None,
            'overall_validation': None,
        }

        # Inicializa estado de cada seção
        for section in self.sections:
            field_name = f"section_{section.section_number:02d}"
            is_selected = section.section_number in sections

            state[field_name] = {
                'content': '',
                'status': DynamicSectionStatus.PENDING if is_selected else DynamicSectionStatus.SKIPPED,
                'validation': {},
                'generation_attempts': 0,
                'last_updated': now,
                'error_message': None,
                'section_name': section.section_name,
                'section_key': section.section_key,
                'step_outputs': {},
                'previous_step_output': '',
            }

        return state

    def _summarize_objective_for_rag(self, objective: str) -> str:
        """
        Resume objetivo longo em palavras-chave para query RAG.

        O modelo de embedding (intfloat/multilingual-e5-large) aceita max 512 tokens.
        Quando o objetivo é longo (>1500 chars ≈ 400 tokens), usa LLM para
        extrair palavras-chave e conceitos principais em até 300 tokens.
        O resultado é cacheado no state para não chamar LLM a cada seção.
        """
        MAX_CHARS = 1500

        if len(objective) <= MAX_CHARS:
            return objective

        logger.info(
            f"Objetivo longo ({len(objective)} chars) — resumindo para RAG"
        )

        try:
            prompt = (
                "Extraia as palavras-chave e conceitos principais do texto abaixo. "
                "Retorne APENAS um resumo conciso de no máximo 200 palavras, "
                "focando em: objeto da contratação, tecnologias mencionadas, "
                "requisitos principais, órgão demandante e finalidade.\n\n"
                f"TEXTO:\n{objective}\n\n"
                "RESUMO COM PALAVRAS-CHAVE:"
            )

            result = self.llm_service.generate(
                user_prompt=prompt,
                system_prompt="Você é um extrator de palavras-chave. Responda apenas com o resumo solicitado.",
                temperature=0.1,
                max_tokens=500,
                provider='watsonx',
                model='mistralai/mistral-medium-2505',
            )

            summary = result.get('content', '').strip()
            if summary and len(summary) < len(objective):
                logger.info(
                    f"Objetivo resumido: {len(objective)} → {len(summary)} chars"
                )
                return summary

        except Exception as e:
            logger.warning(f"Erro ao resumir objetivo para RAG: {e}")

        # Fallback: truncar nos primeiros 1500 chars
        return objective[:MAX_CHARS]

    def _render_template(self, template: str, variables: Dict[str, Any]) -> str:
        """
        Renderiza um template substituindo {{variavel}} pelos valores.

        Args:
            template: String com placeholders {{variavel}}
            variables: Dict com valores das variáveis

        Returns:
            Template renderizado
        """
        result = template
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            result = result.replace(placeholder, str(value) if value else "")
        return result

    def _create_generate_node(self, section: BlueprintSection) -> Callable:
        """
        Cria função de nó de geração para uma seção.

        Args:
            section: Configuração da seção

        Returns:
            Função de nó para LangGraph
        """
        section_num = section.section_number
        section_key = f"section_{section_num:02d}"
        agent_config = section.generator_agent

        def generate_node(state: Dict[str, Any]) -> Dict[str, Any]:
            now = datetime.utcnow().isoformat()

            # Verifica se deve gerar
            sections_to_generate = state.get('sections_to_generate', [])
            if section_num not in sections_to_generate:
                logger.info(f"Pulando seção {section_num}: não selecionada")
                state[section_key]['status'] = DynamicSectionStatus.SKIPPED
                state[section_key]['last_updated'] = now
                return state

            logger.info(f"Gerando seção {section_num}: {section.section_name}")

            # Atualiza status
            state[section_key]['status'] = DynamicSectionStatus.GENERATING
            state[section_key]['generation_attempts'] += 1
            state['updated_at'] = now
            node_id = f"generate_{section_num:02d}"
            t_start = time.monotonic()

            self._emit('node_enter', {
                'node': node_id,
                'agent': agent_config.name if agent_config else f"Gerador Seção {section_num}",
                'type': 'generate',
                'section': section_num,
                'section_name': section.section_name,
            })

            try:
                # Prepara contexto do RAG se configurado
                context = ""
                improvements_context = ""
                purpose_variables = {}  # Variáveis separadas por purpose

                # Ler feedback do usuário ANTES da query RAG para enriquecer busca
                user_feedback = state[section_key].get('user_feedback', '')

                # Quando a seção é import_type='copy', a tarefa do agente é
                # transcrever literal o conteúdo importado — RAG só contamina
                # com chunks de outras contratações. Suprimir nesse caso.
                is_copy_import = state[section_key].get('etp_import_type') == 'copy'

                if agent_config and agent_config.use_rag and self.kb_service and not is_copy_import:
                    rag_vars = {'objective': state['objective_summary'], 'section_name': section.section_name, 'user_feedback': user_feedback}
                    query = self._render_template(
                        agent_config.rag_query_template or section.section_name,
                        rag_vars
                    )
                    # Enriquecer query com feedback do usuário para busca mais relevante
                    if user_feedback:
                        query = f"{query} | Foco: {user_feedback}"

                    # Resolver sessão para query_by_links
                    session = None
                    if state.get('collection_name') and state['collection_name'] != 'default':
                        from apps.intelligent_assistant.models import IntelligentSession
                        try:
                            session = IntelligentSession.objects.get(id=state['collection_name'])
                        except (IntelligentSession.DoesNotExist, ValueError):
                            pass

                    results_by_purpose = self.kb_service.query_by_links(
                        agent_config=agent_config,
                        query_text=query,
                        session=session,
                        blueprint=self.blueprint,
                        section_name=section.section_name,
                    )

                    # Construir variáveis separadas por purpose
                    all_docs = []
                    for purpose, data in results_by_purpose.items():
                        docs_text = "\n\n".join(data.get('documents', []))
                        purpose_variables[purpose] = docs_text
                        purpose_variables[f"{purpose}_instruction"] = data.get('instruction', '')
                        all_docs.extend(data.get('documents', []))
                        n_results = len(data.get('documents', []))
                        metadata_list = data.get('metadata', [])
                        kb_name = metadata_list[0].get('knowledge_base', purpose) if metadata_list else purpose
                        self._emit('kb_query', {
                            'node': node_id,
                            'kb': kb_name,
                            'purpose': purpose,
                            'results': n_results,
                        })

                    # context = todos os docs concatenados (compatibilidade)
                    context = "\n\n".join(all_docs)

                    # improvements = evaluation + examples (retrocompat)
                    improvements_context = purpose_variables.get('evaluation', '')
                    if purpose_variables.get('examples'):
                        improvements_context += "\n\n" + purpose_variables.get('examples', '')

                # Executar Agent Tools (busca web, PNCP) se habilitados
                from .agent_tools_service import AgentToolsService
                tool_context = AgentToolsService.execute_agent_tools(
                    agent_config=agent_config,
                    objective_summary=state.get('objective_summary', state['objective'][:200]),
                    section_name=section.section_name,
                )

                # Salvar resultados dos tools no state para seções futuras
                if tool_context:
                    state[section_key]['tool_results'] = tool_context
                    logger.info(f"Seção {section_num}: tool_results salvos ({len(tool_context)} chars)")
                else:
                    # Herdar tool_results de seções anteriores (mini-DAG)
                    for prev_sec in self.sections:
                        if prev_sec.section_number >= section_num:
                            break
                        prev_key = f"section_{prev_sec.section_number:02d}"
                        prev_tools = state.get(prev_key, {}).get('tool_results', '')
                        if prev_tools:
                            tool_context = prev_tools
                            logger.info(
                                f"Seção {section_num}: herdou tool_results da §{prev_sec.section_number} "
                                f"({len(prev_tools)} chars)"
                            )
                            break

                full_context = context
                if tool_context:
                    full_context = tool_context + "\n\n" + full_context

                # Injetar conteúdo importado como contexto prioritário
                imported_content = state[section_key].get('etp_imported_content', '')
                import_label = state[section_key].get('etp_import_label', '')
                if imported_content:
                    import_header = f"## CONTEÚDO IMPORTADO ({import_label})\n\n"
                    import_header += "O texto abaixo foi importado de outro documento. "
                    import_header += "TRANSCREVA INTEGRALMENTE este conteúdo. "
                    import_header += "Você NÃO PODE alterar, resumir, reescrever ou omitir NENHUMA linha. "
                    import_header += "A ÚNICA alteração permitida é ajustar a numeração dos itens "
                    import_header += f"para refletir a seção {section_num} deste documento. "
                    import_header += "TODO o restante deve ser copiado EXATAMENTE como está.\n\n"
                    import_header += imported_content
                    full_context = import_header + ("\n\n" + full_context if full_context else "")
                    logger.info(f"Seção {section_num}: conteúdo importado injetado ({import_label}): {len(imported_content)} chars")

                # Injetar texto padrão PGE/Decreto (seções fixed sem ETP)
                fixed_content = state[section_key].get('fixed_content', '')
                if fixed_content and not imported_content:
                    # Seção com texto padrão — inserir direto sem IA
                    state[section_key]['content'] = fixed_content
                    state[section_key]['status'] = DynamicSectionStatus.VALID
                    state[section_key]['last_updated'] = now

                    self._emit('section_content', {
                        'section': section_num,
                        'section_name': section.section_name,
                        'content': fixed_content,
                        'is_valid': True,
                        'score': 100,
                        'feedback': [],
                    })

                    duration_ms = int((time.monotonic() - t_start) * 1000)
                    self._emit('node_exit', {
                        'node': node_id,
                        'status': 'success',
                        'duration_ms': duration_ms,
                        'score': 100,
                    })
                    logger.info(f"Seção {section_num}: texto padrão PGE/Decreto inserido ({len(fixed_content)} chars)")
                    return state

                # Concatenar feedback do usuário ao contexto de melhorias
                if user_feedback:
                    improvements_context += f"\n\n## Orientações do Usuário para Regeneração:\n{user_feedback}"

                # Injetar dados do formulário (section_fields) como contexto
                # para o LLM gerar o conteúdo jurídico completo
                section_fields_context = state[section_key].get('section_fields_context', '')
                if section_fields_context:
                    fields_header = (
                        "\n\n## DADOS DO FORMULÁRIO PREENCHIDOS PELO USUÁRIO:\n\n"
                        f"{section_fields_context}\n\n"
                        "IMPORTANTE: Use TODOS os dados acima como base para "
                        "gerar o conteúdo jurídico COMPLETO desta seção. "
                        "NÃO repita apenas os dados — elabore o texto jurídico "
                        "profissional e fundamentado utilizando essas informações."
                    )
                    full_context = fields_header + ("\n\n" + full_context if full_context else "")
                    logger.info(
                        f"Seção {section_num}: dados do formulário injetados "
                        f"como contexto ({len(section_fields_context)} chars)"
                    )

                # Output do step anterior (para pipeline multi-step)
                previous_step_output = state[section_key].get('previous_step_output', '')

                # Prepara variáveis para o template
                variables = {
                    'objective': state['objective'],
                    'context': full_context,
                    'section_name': section.section_name,
                    'section_number': section_num,
                    'previous_sections': self._get_previous_sections_content(state, section_num),
                    'improvements': improvements_context,
                    'previous_step_output': previous_step_output,
                    'instructions': (section.instructions or '').strip(),
                    # Variáveis por purpose (novo pipeline)
                    **{k: v for k, v in purpose_variables.items()},
                }

                # Renderiza prompts: usa agent_config se disponível,
                # senão gera com prompt genérico baseado nas instructions da seção
                if agent_config:
                    system_prompt = agent_config.system_prompt
                    user_prompt = self._render_template(
                        agent_config.user_prompt_template,
                        variables
                    )
                    provider = agent_config.llm_provider
                    model = agent_config.model_name
                    temperature = agent_config.temperature
                    max_tokens = agent_config.max_tokens
                else:
                    # Fallback genérico: usar instructions da seção como guia
                    section_instructions = (section.instructions or '').strip()
                    system_prompt = (
                        "Você é um advogado brasileiro especializado em redação "
                        "de peças e documentos jurídicos. Gere textos profissionais, "
                        "fundamentados juridicamente e prontos para uso."
                    )
                    user_prompt = f"""INSTRUÇÕES DA SEÇÃO:
{section_instructions}

DADOS DE CONTEXTO:
{full_context if full_context else 'Nenhum contexto adicional disponível.'}

OBJETIVO DO DOCUMENTO:
{state['objective']}

SEÇÃO: {section_num}. {section.section_name}

Com base nos dados e instruções acima, gere o conteúdo jurídico COMPLETO desta seção.
O texto deve ser profissional, fundamentado juridicamente e pronto para uso.
NÃO repita apenas os dados — elabore o texto jurídico completo."""
                    provider = 'watsonx'
                    model = 'mistralai/mistral-medium-2505'
                    temperature = 0.3
                    max_tokens = 4096
                    logger.info(
                        f"Seção {section_num}: sem generator_agent, usando prompt "
                        f"genérico com instructions ({len(section_instructions)} chars)"
                    )

                # Sempre incluir feedback do usuário no prompt final,
                # independente do template usar {{improvements}} ou não
                if user_feedback:
                    user_prompt += (
                        f"\n\n## ORIENTAÇÕES DO USUÁRIO PARA ESTA REGENERAÇÃO:\n"
                        f"{user_feedback}\n\n"
                        f"ATENÇÃO: Siga rigorosamente estas orientações ao gerar o conteúdo desta seção."
                    )

                # Chama LLM (multi-provider: usa config do agente ou defaults)
                self._emit('llm_call', {
                    'node': node_id,
                    'provider': provider,
                    'model': model,
                })

                if self.llm_service:
                    # Usar streaming para emitir chunks em tempo real
                    response = None
                    content_chunks = []
                    generate_kwargs = {
                        'system_prompt': system_prompt,
                        'user_prompt': user_prompt,
                        'temperature': temperature,
                        'max_tokens': max_tokens,
                        'provider': provider,
                        'model': model,
                    }

                    try:
                        for chunk_text, final_result in self.llm_service.generate_stream(
                            **generate_kwargs,
                        ):
                            if final_result is not None:
                                response = final_result
                            elif chunk_text:
                                content_chunks.append(chunk_text)
                                self._emit('section_chunk', {
                                    'section': section_num,
                                    'chunk': chunk_text,
                                })
                    except Exception as stream_err:
                        logger.warning(f"Streaming falhou, fallback para generate síncrono: {stream_err}")
                        response = self.llm_service.generate(
                            **generate_kwargs,
                        )

                    # Flush remaining buffered chunks before processing response
                    self._flush_chunk_buffers()

                    if response is None:
                        # Montar response a partir dos chunks
                        response = {
                            'content': ''.join(content_chunks),
                            'usage': {'input_tokens': 0, 'output_tokens': 0},
                            'model': model,
                        }
                else:
                    # Fallback legado: ClaudeService
                    response = self.claude_service.generate(
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )

                # Atualiza estado
                content = response.get('content', '')
                state[section_key]['content'] = content
                state[section_key]['last_updated'] = now
                state[section_key]['error_message'] = None

                # Se tem validador → status VALIDATING; se não → VALID direto
                has_validator = section.validator_agent is not None
                if has_validator:
                    state[section_key]['status'] = DynamicSectionStatus.VALIDATING
                else:
                    state[section_key]['status'] = DynamicSectionStatus.VALID
                    state[section_key]['validation'] = {
                        'is_valid': True,
                        'score': None,
                        'errors': [],
                        'warnings': [],
                        'suggestions': [],
                    }

                duration_ms = int((time.monotonic() - t_start) * 1000)

                # Emitir auditoria de tokens
                usage = response.get('usage', {})
                self._emit('llm_usage', {
                    'node': node_id,
                    'call_type': 'generate',
                    'section': section_num,
                    'section_name': section.section_name,
                    'provider': provider,
                    'model': model,
                    'input_tokens': usage.get('input_tokens', 0),
                    'output_tokens': usage.get('output_tokens', 0),
                    'duration_ms': duration_ms,
                    'attempt': state[section_key].get('generation_attempts', 1),
                })

                self._emit('node_exit', {
                    'node': node_id,
                    'status': 'success',
                    'duration_ms': duration_ms,
                    'content_length': len(content),
                })

                if has_validator:
                    self._emit('edge_traverse', {
                        'source': node_id,
                        'target': f"validate_{section_num:02d}",
                        'data_size': len(content),
                    })

                logger.info(f"Seção {section_num} gerada com sucesso ({duration_ms}ms)")

            except Exception as e:
                duration_ms = int((time.monotonic() - t_start) * 1000)
                logger.error(f"Erro ao gerar seção {section_num}: {e}")
                state[section_key]['status'] = DynamicSectionStatus.ERROR
                state[section_key]['error_message'] = str(e)
                state['errors'].append(f"Seção {section_num}: {str(e)}")
                self._emit('node_exit', {
                    'node': node_id,
                    'status': 'error',
                    'duration_ms': duration_ms,
                    'error': str(e),
                })

            return state

        return generate_node

    def _create_validate_node(self, section: BlueprintSection) -> Callable:
        """
        Cria função de nó de validação para uma seção.

        Args:
            section: Configuração da seção

        Returns:
            Função de nó para LangGraph
        """
        section_num = section.section_number
        section_key = f"section_{section_num:02d}"
        validator_config = section.validator_agent

        def validate_node(state: Dict[str, Any]) -> Dict[str, Any]:
            now = datetime.utcnow().isoformat()

            # Verifica se deve validar
            sections_to_generate = state.get('sections_to_generate', [])
            if section_num not in sections_to_generate:
                return state

            logger.info(f"Validando seção {section_num}: {section.section_name}")
            node_id = f"validate_{section_num:02d}"
            t_start = time.monotonic()

            self._emit('node_enter', {
                'node': node_id,
                'agent': validator_config.name if validator_config else f"Validador Seção {section_num}",
                'type': 'validate',
                'section': section_num,
                'section_name': section.section_name,
            })

            try:
                content = state[section_key].get('content', '')

                if not content:
                    state[section_key]['status'] = DynamicSectionStatus.INVALID
                    state[section_key]['validation'] = {
                        'is_valid': False,
                        'score': 0,
                        'errors': ['Conteúdo vazio'],
                        'warnings': [],
                        'suggestions': ['Regenerar a seção'],
                    }
                    self._emit('node_exit', {
                        'node': node_id, 'status': 'error',
                        'duration_ms': int((time.monotonic() - t_start) * 1000),
                        'error': 'Conteúdo vazio',
                    })
                    return state

                # Se não tem validador, aceita automaticamente
                if not validator_config:
                    state[section_key]['status'] = DynamicSectionStatus.VALID
                    state[section_key]['validation'] = {
                        'is_valid': True,
                        'score': 80,
                        'errors': [],
                        'warnings': ['Validação automática não configurada'],
                        'suggestions': [],
                    }
                    state[section_key]['last_updated'] = now
                    self._emit('node_exit', {
                        'node': node_id, 'status': 'success',
                        'duration_ms': int((time.monotonic() - t_start) * 1000),
                        'score': 80,
                    })
                    return state

                # Prepara variáveis
                variables = {
                    'objective': state['objective'],
                    'current_content': content,
                    'section_name': section.section_name,
                    'section_number': section_num,
                }

                # Renderiza prompts
                user_prompt = self._render_template(
                    validator_config.user_prompt_template,
                    variables
                )

                # Chama LLM para validação (multi-provider)
                v_provider = validator_config.llm_provider
                v_model = validator_config.model_name

                self._emit('llm_call', {
                    'node': node_id,
                    'provider': v_provider,
                    'model': v_model,
                })

                if self.llm_service:
                    response = self.llm_service.generate(
                        system_prompt=validator_config.system_prompt,
                        user_prompt=user_prompt,
                        temperature=validator_config.temperature,
                        max_tokens=validator_config.max_tokens,
                        provider=v_provider,
                        model=v_model,
                    )
                else:
                    response = self.claude_service.generate(
                        system_prompt=validator_config.system_prompt,
                        user_prompt=user_prompt,
                        temperature=validator_config.temperature,
                        max_tokens=validator_config.max_tokens,
                    )

                # Parse do resultado (espera JSON)
                validation_result = self._parse_validation_response(response.get('content', ''))

                state[section_key]['validation'] = validation_result
                state[section_key]['last_updated'] = now

                score = round(validation_result.get('score', 0), 2)
                duration_ms = int((time.monotonic() - t_start) * 1000)

                # Emitir auditoria de tokens da validação
                v_usage = response.get('usage', {})
                self._emit('llm_usage', {
                    'node': node_id,
                    'call_type': 'validate',
                    'section': section_num,
                    'section_name': section.section_name,
                    'provider': v_provider,
                    'model': v_model,
                    'input_tokens': v_usage.get('input_tokens', 0),
                    'output_tokens': v_usage.get('output_tokens', 0),
                    'duration_ms': duration_ms,
                    'attempt': state[section_key].get('generation_attempts', 1),
                })

                if validation_result.get('is_valid', False) or score >= 70:
                    state[section_key]['status'] = DynamicSectionStatus.VALID
                    validation_result['is_valid'] = True
                    logger.info(f"Seção {section_num}: APROVADA (score={score})")
                    self._emit('node_exit', {
                        'node': node_id, 'status': 'success',
                        'duration_ms': duration_ms, 'score': score,
                    })
                else:
                    attempts = state[section_key]['generation_attempts']
                    max_retries = state.get('max_retries', 3)

                    if attempts < max_retries:
                        state[section_key]['status'] = DynamicSectionStatus.REGENERATING
                        logger.info(f"Seção {section_num}: REPROVADA score={score} (tentativa {attempts}/{max_retries})")
                    else:
                        state[section_key]['status'] = DynamicSectionStatus.INVALID
                        logger.warning(f"Seção {section_num}: REPROVADA score={score} (máximo de tentativas)")

                    self._emit('node_exit', {
                        'node': node_id, 'status': 'rejected',
                        'duration_ms': duration_ms, 'score': score,
                    })

            except Exception as e:
                logger.error(f"Erro ao validar seção {section_num}: {e}")
                state[section_key]['status'] = DynamicSectionStatus.ERROR
                state[section_key]['error_message'] = str(e)
                state['errors'].append(f"Validação seção {section_num}: {str(e)}")
                self._emit('node_exit', {
                    'node': node_id, 'status': 'error',
                    'duration_ms': int((time.monotonic() - t_start) * 1000),
                    'error': str(e),
                })

            return state

        return validate_node

    def _create_step_node(self, section: BlueprintSection, pipeline_step: 'SectionPipelineStep') -> Callable:
        """
        Cria nó genérico para um step do pipeline.

        Diferente de _create_generate_node/_create_validate_node (que usam
        generator_agent/validator_agent da seção), este método usa o agente
        configurado diretamente no SectionPipelineStep.
        """
        section_num = section.section_number
        section_key = f"section_{section_num:02d}"
        agent_config = pipeline_step.agent
        step_type = pipeline_step.step_type
        output_var = pipeline_step.output_variable
        step_order = pipeline_step.step_order

        def step_node(state: Dict[str, Any]) -> Dict[str, Any]:
            now = datetime.utcnow().isoformat()

            sections_to_generate = state.get('sections_to_generate', [])
            if section_num not in sections_to_generate:
                logger.info(f"Pulando step {step_order} da seção {section_num}: não selecionada")
                state[section_key]['status'] = DynamicSectionStatus.SKIPPED
                state[section_key]['last_updated'] = now
                return state

            status = STEP_TYPE_STATUS_MAP.get(step_type, DynamicSectionStatus.GENERATING)
            logger.info(f"[Pipeline] Seção {section_num} | Step {step_order} ({step_type}): {section.section_name}")

            node_id = f"step_{section_num:02d}_{step_order:02d}"
            t_start = time.monotonic()

            state[section_key]['status'] = status
            state['updated_at'] = now

            self._emit('node_enter', {
                'node': node_id,
                'agent': agent_config.name if agent_config else f"Step {step_order}",
                'type': step_type,
                'section': section_num,
                'section_name': section.section_name,
                'step_order': step_order,
            })

            if step_type == 'generate':
                state[section_key]['generation_attempts'] += 1

            try:
                # RAG: query_by_links se agente tiver links, senão query legado
                context = ""
                purpose_variables = {}

                # Ler feedback do usuário ANTES da query RAG para enriquecer busca
                user_feedback = state[section_key].get('user_feedback', '')

                # Quando a seção é import_type='copy', suprimir RAG (a tarefa é
                # transcrever literal o conteúdo importado).
                is_copy_import = state[section_key].get('etp_import_type') == 'copy'

                if agent_config and agent_config.use_rag and self.kb_service and not is_copy_import:
                    rag_vars = {'objective': state['objective_summary'], 'section_name': section.section_name, 'user_feedback': user_feedback}
                    query = self._render_template(
                        agent_config.rag_query_template or section.section_name,
                        rag_vars
                    )
                    # Enriquecer query com feedback do usuário para busca mais relevante
                    if user_feedback:
                        query = f"{query} | Foco: {user_feedback}"

                    # Resolver sessão para query_by_links
                    session = None
                    if state.get('collection_name') and state['collection_name'] != 'default':
                        from apps.intelligent_assistant.models import IntelligentSession
                        try:
                            session = IntelligentSession.objects.get(id=state['collection_name'])
                        except (IntelligentSession.DoesNotExist, ValueError):
                            pass

                    results_by_purpose = self.kb_service.query_by_links(
                        agent_config=agent_config,
                        query_text=query,
                        session=session,
                        blueprint=self.blueprint,
                        section_name=section.section_name,
                    )

                    all_docs = []
                    for purpose, data in results_by_purpose.items():
                        docs_text = "\n\n".join(data.get('documents', []))
                        purpose_variables[purpose] = docs_text
                        purpose_variables[f"{purpose}_instruction"] = data.get('instruction', '')
                        all_docs.extend(data.get('documents', []))
                        metadata_list = data.get('metadata', [])
                        kb_name = metadata_list[0].get('knowledge_base', purpose) if metadata_list else purpose
                        self._emit('kb_query', {
                            'node': node_id,
                            'kb': kb_name,
                            'purpose': purpose,
                            'results': len(data.get('documents', [])),
                        })
                    context = "\n\n".join(all_docs)

                # Ler output do step anterior
                previous_step_output = state[section_key].get('previous_step_output', '')

                # Conteúdo atual da seção (para steps de validate/refine)
                current_content = state[section_key].get('content', '')

                # Todos os outputs anteriores do pipeline
                step_outputs = state[section_key].get('step_outputs', {})

                # Injetar dados do formulário como contexto
                section_fields_context = state[section_key].get('section_fields_context', '')
                if section_fields_context:
                    fields_header = (
                        "\n\n## DADOS DO FORMULÁRIO PREENCHIDOS PELO USUÁRIO:\n\n"
                        f"{section_fields_context}\n\n"
                        "IMPORTANTE: Use TODOS os dados acima como base para "
                        "gerar o conteúdo jurídico COMPLETO desta seção."
                    )
                    context = fields_header + ("\n\n" + context if context else "")

                variables = {
                    'objective': state['objective'],
                    'context': context,
                    'section_name': section.section_name,
                    'section_number': section_num,
                    'previous_sections': self._get_previous_sections_content(state, section_num),
                    'previous_step_output': previous_step_output,
                    'current_content': current_content,
                    'improvements': user_feedback,
                    'instructions': (section.instructions or '').strip(),
                    **{k: v for k, v in purpose_variables.items()},
                    **{k: v for k, v in step_outputs.items()},
                }

                if not agent_config:
                    raise ValueError(f"Step {step.step_order} da seção {section_num} sem agente configurado")

                system_prompt = agent_config.system_prompt
                user_prompt = self._render_template(
                    agent_config.user_prompt_template,
                    variables
                )

                provider = agent_config.llm_provider
                model = agent_config.model_name

                self._emit('llm_call', {
                    'node': node_id,
                    'provider': provider,
                    'model': model,
                })

                if self.llm_service:
                    response = self.llm_service.generate(
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        temperature=agent_config.temperature,
                        max_tokens=agent_config.max_tokens,
                        provider=provider,
                        model=model,
                    )
                else:
                    response = self.claude_service.generate(
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        temperature=agent_config.temperature,
                        max_tokens=agent_config.max_tokens,
                    )

                output = response.get('content', '')
                duration_ms = int((time.monotonic() - t_start) * 1000)

                # Salvar output no step_outputs e como previous_step_output
                state[section_key]['step_outputs'][output_var] = output
                state[section_key]['previous_step_output'] = output

                # Steps de generate/refine atualizam o content da seção
                if step_type in ('generate', 'refine'):
                    state[section_key]['content'] = output

                # Steps de validate parseiam o resultado como validação
                if step_type == 'validate':
                    validation_result = self._parse_validation_response(output)
                    state[section_key]['validation'] = validation_result
                    score = round(validation_result.get('score', 0), 2)
                    if validation_result.get('is_valid', False) or score >= 70:
                        state[section_key]['status'] = DynamicSectionStatus.VALID
                        validation_result['is_valid'] = True
                        self._emit('node_exit', {
                            'node': node_id, 'status': 'success',
                            'duration_ms': duration_ms, 'score': score,
                        })
                    else:
                        attempts = state[section_key]['generation_attempts']
                        max_retries = state.get('max_retries', 3)
                        if attempts < max_retries:
                            state[section_key]['status'] = DynamicSectionStatus.REGENERATING
                        else:
                            state[section_key]['status'] = DynamicSectionStatus.INVALID
                        self._emit('node_exit', {
                            'node': node_id, 'status': 'rejected',
                            'duration_ms': duration_ms, 'score': score,
                        })
                else:
                    # Steps não-validate avançam normalmente
                    state[section_key]['status'] = DynamicSectionStatus.VALIDATING
                    self._emit('node_exit', {
                        'node': node_id, 'status': 'success',
                        'duration_ms': duration_ms,
                        'content_length': len(output),
                    })

                state[section_key]['last_updated'] = now
                state[section_key]['error_message'] = None

                logger.info(f"[Pipeline] Step {step_order} ({step_type}) concluído | output_var={output_var} ({duration_ms}ms)")

            except Exception as e:
                duration_ms = int((time.monotonic() - t_start) * 1000)
                logger.error(f"[Pipeline] Erro step {step_order} seção {section_num}: {e}")
                state[section_key]['status'] = DynamicSectionStatus.ERROR
                state[section_key]['error_message'] = str(e)
                state['errors'].append(f"Seção {section_num} step {step_order}: {str(e)}")
                self._emit('node_exit', {
                    'node': node_id, 'status': 'error',
                    'duration_ms': duration_ms,
                    'error': str(e),
                })

            return state

        return step_node

    def _create_routing_function(
        self,
        section: BlueprintSection,
        next_section: Optional[BlueprintSection]
    ) -> Callable:
        """
        Cria função de roteamento após validação.

        Args:
            section: Seção atual
            next_section: Próxima seção (ou None se última)

        Returns:
            Função de roteamento
        """
        section_num = section.section_number
        section_key = f"section_{section_num:02d}"
        next_node = f"generate_{next_section.section_number:02d}" if next_section else "finalize"

        def route(state: Dict[str, Any]) -> str:
            status = state[section_key].get('status')

            if status == DynamicSectionStatus.ERROR:
                return "error"
            elif status == DynamicSectionStatus.REGENERATING:
                return "regenerate"
            elif status in [DynamicSectionStatus.VALID, DynamicSectionStatus.SKIPPED]:
                return "next"
            elif status == DynamicSectionStatus.INVALID:
                # Mesmo inválido, segue para próxima (já atingiu max_retries)
                return "next"
            else:
                return "next"

        return route

    def _create_finalize_node(self) -> Callable:
        """Cria nó de finalização."""

        def finalize(state: Dict[str, Any]) -> Dict[str, Any]:
            logger.info("Finalizando documento")
            now = datetime.utcnow().isoformat()

            try:
                sections_to_generate = state.get('sections_to_generate', [])
                document_parts = []
                valid_count = 0
                total_score = 0.0

                for section in self.sections:
                    if section.section_number not in sections_to_generate:
                        continue

                    section_key = f"section_{section.section_number:02d}"
                    content = state.get(section_key, {}).get('content', '')

                    if content:
                        # Strip heading duplicado do conteúdo LLM
                        # (o LLM pode gerar "## 3. Demanda" ou "**3. Demanda**" no início)
                        cleaned = content.strip()
                        sec_num = section.section_number
                        sec_name = re.escape(section.section_name)
                        # Remove heading markdown (## N. Nome)
                        cleaned = re.sub(
                            rf'^#{1,3}\s*{sec_num}\.?\s*{sec_name}\s*\n+',
                            '', cleaned, count=1, flags=re.IGNORECASE
                        )
                        # Remove heading bold (**N. Nome**)
                        cleaned = re.sub(
                            rf'^\*\*\s*{sec_num}\.?\s*{sec_name}\s*\*\*\s*\n+',
                            '', cleaned, count=1, flags=re.IGNORECASE
                        )

                        document_parts.append(
                            f"## {section.section_number}. {strip_generation_suffix(section.section_name)}\n\n{cleaned.strip()}"
                        )

                    section_state = state.get(section_key, {})
                    validation = section_state.get('validation', {})
                    # Contar como gerada se tem conteúdo (IA, estruturada, fixa, importada)
                    if content:
                        valid_count += 1
                    score = validation.get('score') or section_state.get('score') or 0
                    total_score += score

                state['final_document'] = "\n\n".join(document_parts)

                total_sections = len(sections_to_generate)
                state['overall_validation'] = {
                    'valid_sections': valid_count,
                    'invalid_sections': total_sections - valid_count,
                    'total_sections': total_sections,
                    'average_score': round(total_score / total_sections, 2) if total_sections else 0,
                    'is_complete': valid_count == total_sections,
                }

                state['status'] = 'completed' if valid_count == total_sections else 'completed_with_issues'
                state['updated_at'] = now

                logger.info(f"Documento finalizado: {valid_count}/{total_sections} seções válidas")

            except Exception as e:
                logger.error(f"Erro ao finalizar: {e}")
                state['status'] = 'error'
                state['errors'].append(f"Finalização: {str(e)}")

            return state

        return finalize

    def _create_error_node(self) -> Callable:
        """Cria nó de tratamento de erros."""

        def handle_error(state: Dict[str, Any]) -> Dict[str, Any]:
            logger.error(f"Erros encontrados: {state.get('errors', [])}")
            state['status'] = 'error'
            state['updated_at'] = datetime.utcnow().isoformat()
            return state

        return handle_error

    def _has_dependencies(self) -> bool:
        """Verifica se alguma seção possui dependências configuradas."""
        for section in self.sections:
            if section.depends_on.exists():
                return True
        return False

    def _topological_sort(self) -> List[List[BlueprintSection]]:
        """
        Ordena seções por dependências em níveis.

        Retorna lista de listas (níveis):
        - Nível 0: seções sem dependências
        - Nível 1: seções que dependem apenas de nível 0
        - etc.

        Raises:
            ValueError: Se houver dependência circular
        """
        # Mapeia id -> seção
        section_map = {s.id: s for s in self.sections}
        active_ids = set(section_map.keys())

        # Conta dependências (apenas dentro das seções ativas)
        in_degree = {}
        deps_map = {}
        for section in self.sections:
            dep_ids = set(section.depends_on.values_list('id', flat=True)) & active_ids
            in_degree[section.id] = len(dep_ids)
            deps_map[section.id] = dep_ids

        levels = []
        remaining = set(active_ids)

        while remaining:
            # Seções sem dependências pendentes
            level = [
                section_map[sid] for sid in remaining
                if in_degree.get(sid, 0) == 0
            ]

            if not level:
                cycle_sections = [section_map[sid].section_name for sid in remaining]
                raise ValueError(
                    f"Dependência circular detectada entre seções: {', '.join(cycle_sections)}"
                )

            # Ordena dentro do nível por order/section_number
            level.sort(key=lambda s: (s.order, s.section_number))
            levels.append(level)

            # Remove do grafo
            resolved_ids = {s.id for s in level}
            remaining -= resolved_ids

            # Atualiza in_degree
            for sid in remaining:
                deps_map[sid] -= resolved_ids
                in_degree[sid] = len(deps_map[sid])

        return levels

    def _build_graph_structure(self) -> Dict[str, Any]:
        """
        Gera payload {nodes, edges} descrevendo a estrutura do grafo
        para visualização no frontend (React Flow).

        Emitido 1x no início via evento 'graph_structure'.
        """
        nodes = []
        edges = []
        y_offset = 0

        # Filtrar seções válidas (mesma lógica do _build_linear_graph)
        valid_sections = [s for s in self.sections if not self._should_skip_section(s)]
        prev_last_node_id = None

        for i, section in enumerate(valid_sections):
            sec_num = section.section_number
            pipeline_steps = self._get_pipeline_steps(section)

            if self._has_sub_sections(section):
                # Seção com sub-seções → nó compositor + nós de sub-seção
                comp_id = f"compose_{sec_num:02d}"
                sub_sections = self._get_sub_sections(section)

                nodes.append({
                    'id': comp_id,
                    'type': 'compose',
                    'label': f"Compositor Seção {sec_num}",
                    'section': sec_num,
                    'section_name': section.section_name,
                    'status': 'pending',
                    'position': {'x': 0, 'y': y_offset},
                    'sub_sections_count': len(sub_sections),
                })

                x_offset = 300
                prev_sub_id = comp_id
                last_sub_id = comp_id

                for j, sub in enumerate(sub_sections):
                    sub_id = f"sub_{sec_num:02d}_{j+1:02d}"
                    has_agent = sub.generator_agent is not None
                    sub_label = f"{sub.sub_number} {sub.sub_name[:25]}"
                    if not has_agent:
                        sub_label += " (N/A)"

                    nodes.append({
                        'id': sub_id,
                        'type': 'sub_section',
                        'label': sub_label,
                        'section': sec_num,
                        'section_name': section.section_name,
                        'sub_key': sub.sub_key,
                        'sub_number': sub.sub_number,
                        'has_agent': has_agent,
                        'agent_name': sub.generator_agent.name if has_agent else None,
                        'status': 'pending',
                        'position': {'x': x_offset, 'y': y_offset + (j * 60)},
                    })
                    edges.append({
                        'id': f"e_{prev_sub_id}_{sub_id}",
                        'source': prev_sub_id,
                        'target': sub_id,
                        'animated': False,
                    })
                    prev_sub_id = sub_id
                    last_sub_id = sub_id

                first_node_in_section = comp_id
                last_node_in_section = last_sub_id
                y_offset += max(160, len(sub_sections) * 60 + 60)

            elif pipeline_steps:
                prev_node_id = None
                last_node_in_section = None
                for j, step in enumerate(pipeline_steps):
                    node_id = f"step_{sec_num:02d}_{step.step_order:02d}"
                    agent_name = step.agent.name if step.agent else f"Step {step.step_order}"
                    nodes.append({
                        'id': node_id,
                        'type': step.step_type,
                        'label': agent_name,
                        'section': sec_num,
                        'section_name': section.section_name,
                        'step_order': step.step_order,
                        'status': 'pending',
                        'position': {'x': j * 300, 'y': y_offset},
                    })
                    if prev_node_id:
                        edges.append({
                            'id': f"e_{prev_node_id}_{node_id}",
                            'source': prev_node_id,
                            'target': node_id,
                            'animated': False,
                        })
                    prev_node_id = node_id
                    last_node_in_section = node_id
                first_node_in_section = f"step_{sec_num:02d}_{pipeline_steps[0].step_order:02d}"
            else:
                gen_id = f"generate_{sec_num:02d}"
                gen_agent = section.generator_agent

                nodes.append({
                    'id': gen_id,
                    'type': 'generate',
                    'label': gen_agent.name if gen_agent else f"Gerador Seção {sec_num}",
                    'section': sec_num,
                    'section_name': section.section_name,
                    'status': 'pending',
                    'position': {'x': 0, 'y': y_offset},
                })

                first_node_in_section = gen_id

                if self._has_validator(section):
                    val_id = f"validate_{sec_num:02d}"
                    val_agent = section.validator_agent
                    nodes.append({
                        'id': val_id,
                        'type': 'validate',
                        'label': val_agent.name,
                        'section': sec_num,
                        'section_name': section.section_name,
                        'status': 'pending',
                        'position': {'x': 300, 'y': y_offset},
                    })
                    edges.append({
                        'id': f"e_{gen_id}_{val_id}",
                        'source': gen_id,
                        'target': val_id,
                        'animated': False,
                    })
                    last_node_in_section = val_id
                else:
                    last_node_in_section = gen_id

            # Edge entre seções
            if prev_last_node_id:
                edges.append({
                    'id': f"e_section_{prev_last_node_id}_{first_node_in_section}",
                    'source': prev_last_node_id,
                    'target': first_node_in_section,
                    'animated': False,
                    'type': 'section_link',
                })

            prev_last_node_id = last_node_in_section
            y_offset += 160

        # Nó finalize
        nodes.append({
            'id': 'finalize',
            'type': 'finalize',
            'label': 'Finalizar Documento',
            'section': 0,
            'section_name': '',
            'status': 'pending',
            'position': {'x': 150, 'y': y_offset},
        })

        # Edge última seção → finalize
        if prev_last_node_id:
            edges.append({
                'id': f"e_{prev_last_node_id}_finalize",
                'source': prev_last_node_id,
                'target': 'finalize',
                'animated': False,
            })

        return {'nodes': nodes, 'edges': edges}

    def _build_graph(self) -> StateGraph:
        """
        Constrói o grafo LangGraph dinamicamente.

        Se não há dependências entre seções: grafo linear (backward compat).
        Se há dependências: grafo com topological sort por níveis.
        """
        has_deps = self._has_dependencies()

        if has_deps:
            logger.info(f"Construindo grafo COM dependências para {self.blueprint.name}")
            return self._build_dependency_graph()
        else:
            logger.info(f"Construindo grafo linear para {self.blueprint.name} com {len(self.sections)} seções")
            return self._build_linear_graph()

    def _get_pipeline_steps(self, section: BlueprintSection) -> List['SectionPipelineStep']:
        """Retorna pipeline steps ativos de uma seção, ou lista vazia."""
        return list(
            SectionPipelineStep.objects.filter(
                section=section, is_active=True
            ).select_related('agent').order_by('step_order')
        )

    def _has_sub_sections(self, section: BlueprintSection) -> bool:
        """Verifica se a seção tem sub-seções ativas."""
        return section.sub_sections.filter(is_active=True).exists()

    def _get_sub_sections(self, section: BlueprintSection) -> List[BlueprintSubSection]:
        """Retorna sub-seções ativas ordenadas."""
        return list(
            section.sub_sections.filter(is_active=True)
            .select_related('generator_agent')
            .order_by('order', 'sub_number')
        )

    def _should_skip_section(self, section: BlueprintSection) -> Optional[str]:
        """
        Verifica se uma seção deve ser pulada na geração.

        Returns:
            None se pode gerar, ou string com motivo do skip.
        """
        # Seção com sub-seções → NÃO skip, será tratada pelo compose node
        if self._has_sub_sections(section):
            return None

        # Seção sem agente gerador → verifica se tem instructions ou pipeline
        if not section.generator_agent:
            pipeline_steps = self._get_pipeline_steps(section)
            has_instructions = bool(section.instructions and section.instructions.strip())
            if not pipeline_steps and not has_instructions:
                return f"Seção {section.section_number} sem agente gerador configurado"

        # Seção com campos estruturados → preenchimento manual
        # (a menos que tenha agente ou instructions, caso em que os campos são contexto para o LLM)
        if section.section_fields:
            has_generation_capability = bool(section.generator_agent) or bool(
                section.instructions and section.instructions.strip()
            )
            if not has_generation_capability:
                return f"Seção {section.section_number} é de preenchimento manual (campos estruturados)"

        return None

    def _format_sub_section_fields(self, sub: BlueprintSubSection, fields_data: dict) -> str:
        """Formata os campos preenchidos pelo usuário numa sub-seção em texto legível."""
        if not sub.section_fields or not fields_data:
            return ""
        parts = []
        for field_def in sub.section_fields:
            name = field_def.get('name', '')
            label = field_def.get('label', name)
            value = fields_data.get(name, '')
            if value:
                parts.append(f"**{label}:** {value}")
        return "\n".join(parts)

    def _create_compose_subsections_node(self, section: BlueprintSection) -> Callable:
        """
        Cria nó que compõe uma seção a partir de suas sub-seções.

        Para cada sub-seção:
        - Se o usuário escolheu "generate" e há agente → chama LLM com context do usuário
        - Se escolheu "default" ou não há decisão → usa default_text
        - Se é required e não tem default_text → sempre gera

        O conteúdo final é a concatenação de todas as sub-seções.
        """
        section_num = section.section_number
        section_key = f"section_{section_num:02d}"
        sub_sections = self._get_sub_sections(section)

        def compose_node(state: Dict[str, Any]) -> Dict[str, Any]:
            now = datetime.utcnow().isoformat()

            # Verifica se deve gerar
            sections_to_generate = state.get('sections_to_generate', [])
            if section_num not in sections_to_generate:
                logger.info(f"Pulando seção {section_num} (sub-seções): não selecionada")
                state[section_key]['status'] = DynamicSectionStatus.SKIPPED
                state[section_key]['last_updated'] = now
                return state

            logger.info(
                f"Compondo seção {section_num} ({section.section_name}) "
                f"a partir de {len(sub_sections)} sub-seções"
            )

            state[section_key]['status'] = DynamicSectionStatus.GENERATING
            state[section_key]['generation_attempts'] += 1
            state['updated_at'] = now
            node_id = f"compose_{section_num:02d}"
            t_start = time.monotonic()

            self._emit('node_enter', {
                'node': node_id,
                'agent': f"Compositor Seção {section_num}",
                'type': 'compose_subsections',
                'section': section_num,
                'section_name': section.section_name,
                'sub_sections_count': len(sub_sections),
            })

            decisions = state.get('sub_section_decisions', {})
            # Feedback de regeneração (vem via section_overrides → state[section_key]['user_feedback'])
            section_level_feedback = state[section_key].get('user_feedback', '')
            content_parts = []
            generated_count = 0
            default_count = 0

            # ── Filtrar OU groups: manter apenas a opção selecionada ──
            # Agrupa sub_sections por sub_number. Se grupo tem 2+, é OU.
            # Só processa a sub que tem decision; se nenhuma tem, usa a última (negativa).
            _by_num: OrderedDict[str, list] = OrderedDict()
            for _s in sub_sections:
                _by_num.setdefault(_s.sub_number, []).append(_s)

            filtered_subs = []
            for _num, _group in _by_num.items():
                if len(_group) == 1:
                    filtered_subs.append(_group[0])
                else:
                    # OU group — achar a selecionada (tem decision no dict)
                    selected = None
                    for _s in _group:
                        if _s.sub_key in decisions:
                            selected = _s
                            break
                    # Se selecionada: só ela. Se nenhuma: todas (comportamento "OU")
                    if selected:
                        filtered_subs.append(selected)
                    else:
                        filtered_subs.extend(_group)

            try:
                for j, sub in enumerate(filtered_subs):
                    decision = decisions.get(sub.sub_key, {})
                    action = decision.get('action', 'default')
                    fields_data = decision.get('fields_data', {})
                    # Feedback: da decisão individual OU da regeneração da seção inteira
                    user_feedback = decision.get('feedback', '') or section_level_feedback
                    sub_node_id = f"sub_{section_num:02d}_{j+1:02d}"

                    sub_header = f"### {sub.sub_number} {strip_generation_suffix(sub.sub_name)}"

                    # Montar texto dos campos preenchidos pelo usuário
                    input_text = self._format_sub_section_fields(sub, fields_data)

                    # Decidir: gerar com IA, usar campos preenchidos, ou texto padrão
                    should_generate = (
                        action == 'generate'
                        and sub.generator_agent is not None
                    )

                    # Sub-seção com formulário preenchido mas sem agente →
                    # montar conteúdo com default_text + campos (sem IA)
                    should_use_fields_only = (
                        action == 'generate'
                        and sub.generator_agent is None
                        and bool(input_text)
                    )

                    # Sub-seção sem default_text e com agente → forçar geração se não há decisão explícita
                    if not sub.default_text and sub.generator_agent:
                        if not decision:  # Sem decisão explícita → forçar geração
                            should_generate = True

                    # DEBUG: Log detalhado da decisão de cada sub-seção
                    logger.warning(
                        f"[DEBUG SUB-SECTION] {sub.sub_number} '{sub.sub_name}' | "
                        f"sub_key={sub.sub_key} | action={action} | "
                        f"decision={decision} | "
                        f"has_agent={sub.generator_agent is not None} | "
                        f"has_default_text={bool(sub.default_text)} | "
                        f"should_generate={should_generate}"
                    )

                    if should_generate:
                        # --- GERAR COM IA ---
                        agent = sub.generator_agent
                        generated_count += 1

                        self._emit('sub_section_start', {
                            'node': node_id,
                            'sub_node': sub_node_id,
                            'section': section_num,
                            'sub_key': sub.sub_key,
                            'sub_number': sub.sub_number,
                            'sub_name': sub.sub_name,
                            'agent_name': agent.name,
                            'action': 'generate',
                        })

                        # Variáveis para o prompt (inclui {{input}} com campos preenchidos)
                        variables = {
                            'objective': state['objective'],
                            'section_name': section.section_name,
                            'section_number': section_num,
                            'sub_section_name': sub.sub_name,
                            'sub_section_number': sub.sub_number,
                            'sub_section_description': sub.description,
                            'user_input': input_text,
                            'input': input_text,
                            'fields_data': input_text,
                            'previous_sections': self._get_previous_sections_content(state, section_num),
                            'context': '',
                        }

                        # RAG context se configurado no agente
                        if agent.use_rag and self.kb_service:
                            rag_vars = {'objective': state['objective_summary'], 'section_name': sub.sub_name, 'user_feedback': user_feedback}
                            query = self._render_template(
                                agent.rag_query_template or sub.sub_name,
                                rag_vars
                            )
                            # Enriquecer query com feedback do usuário para busca mais relevante
                            if user_feedback:
                                query = f"{query} | Foco: {user_feedback}"
                            # Resolver sessão para query_by_links
                            session = None
                            if state.get('collection_name') and state['collection_name'] != 'default':
                                from apps.intelligent_assistant.models import IntelligentSession
                                try:
                                    session = IntelligentSession.objects.get(id=state['collection_name'])
                                except (IntelligentSession.DoesNotExist, ValueError):
                                    pass
                            results_by_purpose = self.kb_service.query_by_links(
                                agent_config=agent,
                                query_text=query,
                                session=session,
                                blueprint=self.blueprint,
                                section_name=sub.sub_name,
                            )
                            all_docs = []
                            for purpose, data in results_by_purpose.items():
                                all_docs.extend(data.get('documents', []))
                            variables['context'] = "\n\n".join(all_docs)

                        # Renderizar prompts
                        system_prompt = agent.system_prompt
                        user_prompt = self._render_template(
                            agent.user_prompt_template,
                            variables
                        )

                        # Anexar feedback de regeneração se houver
                        if user_feedback:
                            user_prompt += (
                                f"\n\n## ORIENTAÇÕES DO USUÁRIO:\n{user_feedback}\n\n"
                                f"ATENÇÃO: Siga rigorosamente estas orientações."
                            )

                        # Chamar LLM
                        provider = agent.llm_provider
                        model = agent.model_name

                        self._emit('llm_call', {
                            'node': node_id,
                            'provider': provider,
                            'model': model,
                            'sub_key': sub.sub_key,
                        })

                        if self.llm_service:
                            response = None
                            content_chunks = []
                            try:
                                for chunk_text, final_result in self.llm_service.generate_stream(
                                    system_prompt=system_prompt,
                                    user_prompt=user_prompt,
                                    temperature=agent.temperature,
                                    max_tokens=agent.max_tokens,
                                    provider=provider,
                                    model=model,
                                ):
                                    if final_result is not None:
                                        response = final_result
                                    elif chunk_text:
                                        content_chunks.append(chunk_text)
                                        self._emit('section_chunk', {
                                            'section': section_num,
                                            'sub_key': sub.sub_key,
                                            'chunk': chunk_text,
                                        })
                            except Exception as stream_err:
                                logger.warning(f"Streaming falhou para sub-seção {sub.sub_key}: {stream_err}")
                                response = self.llm_service.generate(
                                    system_prompt=system_prompt,
                                    user_prompt=user_prompt,
                                    temperature=agent.temperature,
                                    max_tokens=agent.max_tokens,
                                    provider=provider,
                                    model=model,
                                )

                            # Flush remaining buffered chunks for this sub-section
                            self._flush_chunk_buffers()

                            if response is None:
                                response = {
                                    'content': ''.join(content_chunks),
                                    'usage': {'input_tokens': 0, 'output_tokens': 0},
                                    'model': model,
                                }
                        elif self.claude_service:
                            response = self.claude_service.generate(
                                system_prompt=system_prompt,
                                user_prompt=user_prompt,
                                temperature=agent.temperature,
                                max_tokens=agent.max_tokens,
                            )
                        else:
                            raise ValueError("Nenhum LLM service configurado")

                        sub_content = response.get('content', '')
                        content_parts.append(f"{sub_header}\n\n{sub_content}")

                        self._emit('sub_section_complete', {
                            'node': node_id,
                            'sub_node': sub_node_id,
                            'section': section_num,
                            'sub_key': sub.sub_key,
                            'sub_number': sub.sub_number,
                            'action': 'generate',
                            'content_length': len(sub_content),
                        })

                        logger.info(f"  Sub-seção {sub.sub_number} gerada por IA ({len(sub_content)} chars)")

                    elif should_use_fields_only:
                        # --- CAMPOS PREENCHIDOS SEM AGENTE ---
                        # Mostra só os campos preenchidos (sem default_text)
                        generated_count += 1
                        sub_content = input_text
                        content_parts.append(sub_content)

                        logger.info(
                            f"  Sub-seção {sub.sub_number} → campos preenchidos sem agente "
                            f"({len(sub_content)} chars)"
                        )

                        self._emit('sub_section_complete', {
                            'node': node_id,
                            'sub_node': sub_node_id,
                            'section': section_num,
                            'sub_key': sub.sub_key,
                            'sub_number': sub.sub_number,
                            'action': 'fields_only',
                            'content_length': len(sub_content),
                        })

                    else:
                        # --- TEXTO PADRÃO (OU) ---
                        default_count += 1
                        if sub.default_text:
                            # default_text já contém o número (ex: "4.9 Não há...")
                            # Não adicionar sub_header para evitar duplicação
                            content_parts.append(sub.default_text)
                            logger.info(f"  Sub-seção {sub.sub_number} → texto padrão")

                            self._emit('sub_section_complete', {
                                'node': node_id,
                                'sub_node': sub_node_id,
                                'section': section_num,
                                'sub_key': sub.sub_key,
                                'sub_number': sub.sub_number,
                                'action': 'default',
                                'content_length': len(sub.default_text),
                            })
                        else:
                            # Sem default_text e não gera → sub-seção vazia (omitida)
                            logger.info(f"  Sub-seção {sub.sub_number} → omitida (sem texto padrão)")

                # Montar conteúdo final da seção
                final_content = "\n\n".join(content_parts)
                state[section_key]['content'] = final_content
                state[section_key]['last_updated'] = now
                state[section_key]['error_message'] = None

                # Seções compostas → VALID direto (validação individual das sub-seções
                # pode ser adicionada no futuro)
                state[section_key]['status'] = DynamicSectionStatus.VALID
                state[section_key]['validation'] = {
                    'is_valid': True,
                    'score': 100.0,
                    'errors': [],
                    'warnings': [],
                    'suggestions': [],
                }

                duration_ms = int((time.monotonic() - t_start) * 1000)

                self._emit('node_exit', {
                    'node': node_id,
                    'status': 'success',
                    'duration_ms': duration_ms,
                    'content_length': len(final_content),
                    'generated_count': generated_count,
                    'default_count': default_count,
                })

                logger.info(
                    f"Seção {section_num} composta: {generated_count} geradas, "
                    f"{default_count} padrão ({duration_ms}ms)"
                )

            except Exception as e:
                duration_ms = int((time.monotonic() - t_start) * 1000)
                logger.error(f"Erro ao compor seção {section_num}: {e}")
                state[section_key]['status'] = DynamicSectionStatus.ERROR
                state[section_key]['error_message'] = str(e)
                state['errors'].append(f"Seção {section_num}: {str(e)}")
                self._emit('node_exit', {
                    'node': node_id,
                    'status': 'error',
                    'duration_ms': duration_ms,
                    'error': str(e),
                })

            return state

        return compose_node

    def _has_validator(self, section: BlueprintSection) -> bool:
        """Verifica se a seção tem agente validador configurado."""
        return section.validator_agent is not None

    def _build_linear_graph(self) -> StateGraph:
        """
        Grafo linear: seções em sequência.

        Para cada seção:
        - Se deve ser pulada (sem agente ou com section_fields) → skip
        - Se tem SectionPipelineStep configurados → cria nós do pipeline
        - Se não tem → usa generate (→ validate se tiver validador) legado
        """
        StateClass = self._create_dynamic_state_class()
        graph = StateGraph(StateClass)

        # Mapear seções → seus nós (primeiro e último nó de cada seção)
        section_nodes = []  # [(first_node, last_node, last_is_validate, section)]

        for section in self.sections:
            sec_num = section.section_number
            skip_reason = self._should_skip_section(section)

            if skip_reason:
                logger.info(f"Pulando seção {sec_num}: {skip_reason}")
                continue

            # SUB-SEÇÕES: seção com sub-itens → nó compositor
            if self._has_sub_sections(section):
                comp_name = f"compose_{sec_num:02d}"
                graph.add_node(comp_name, self._create_compose_subsections_node(section))
                section_nodes.append((comp_name, comp_name, False, section))
                sub_count = section.sub_sections.filter(is_active=True).count()
                logger.info(f"Seção {sec_num}: composição de {sub_count} sub-seções")
                continue

            pipeline_steps = self._get_pipeline_steps(section)

            if pipeline_steps:
                # PIPELINE: criar um nó por step
                step_names = []
                for step in pipeline_steps:
                    node_name = f"step_{sec_num:02d}_{step.step_order:02d}"
                    graph.add_node(node_name, self._create_step_node(section, step))
                    step_names.append((node_name, step))

                # Encadear steps internos: step1 → step2 → step3
                for j in range(len(step_names) - 1):
                    current_name, current_step = step_names[j]
                    next_name, _ = step_names[j + 1]
                    # Steps não-validate seguem direto para o próximo
                    if current_step.step_type != 'validate':
                        graph.add_edge(current_name, next_name)

                first_node = step_names[0][0]
                last_node_name, last_step = step_names[-1]
                last_is_validate = last_step.step_type == 'validate'

                # Se tem validate no meio do pipeline, adicionar routing
                for j, (name, step) in enumerate(step_names):
                    if step.step_type == 'validate' and j < len(step_names) - 1:
                        next_name = step_names[j + 1][0]
                        # Encontrar o nó generate mais recente para regeneração
                        regen_node = first_node
                        for k in range(j - 1, -1, -1):
                            if step_names[k][1].step_type == 'generate':
                                regen_node = step_names[k][0]
                                break
                        graph.add_conditional_edges(
                            name,
                            self._create_pipeline_routing(section),
                            {
                                "regenerate": regen_node,
                                "next": next_name,
                                "error": "handle_error",
                            }
                        )

                section_nodes.append((first_node, last_node_name, last_is_validate, section))

                logger.info(f"Seção {sec_num}: pipeline com {len(pipeline_steps)} steps")
            else:
                # LEGADO: generate (→ validate se tiver validador)
                gen_name = f"generate_{sec_num:02d}"
                graph.add_node(gen_name, self._create_generate_node(section))

                if self._has_validator(section):
                    val_name = f"validate_{sec_num:02d}"
                    graph.add_node(val_name, self._create_validate_node(section))
                    graph.add_edge(gen_name, val_name)
                    section_nodes.append((gen_name, val_name, True, section))
                else:
                    logger.info(f"Seção {sec_num}: sem validador, geração direta")
                    section_nodes.append((gen_name, gen_name, False, section))

        if not section_nodes:
            raise ValueError("Nenhuma seção válida para gerar. Verifique se as seções selecionadas têm agentes configurados.")

        graph.add_node("finalize", self._create_finalize_node())
        graph.add_node("handle_error", self._create_error_node())

        # Entry point
        graph.set_entry_point(section_nodes[0][0])

        # Conectar seções entre si
        for i, (first_node, last_node, last_is_validate, section) in enumerate(section_nodes):
            next_first = section_nodes[i + 1][0] if i + 1 < len(section_nodes) else "finalize"

            if last_is_validate:
                # Último nó é validate → routing condicional (regenerate/next/error)
                regen_node = first_node
                graph.add_conditional_edges(
                    last_node,
                    self._create_routing_function(section,
                        section_nodes[i + 1][3] if i + 1 < len(section_nodes) else None),
                    {
                        "regenerate": regen_node,
                        "next": next_first,
                        "error": "handle_error",
                    }
                )
            else:
                # Último nó não é validate → segue direto
                graph.add_edge(last_node, next_first)

        graph.add_edge("finalize", END)
        graph.add_edge("handle_error", END)

        logger.info("Grafo linear construído com sucesso")
        return graph

    def _create_pipeline_routing(self, section: BlueprintSection) -> Callable:
        """Routing para steps de validate dentro do pipeline."""
        section_key = f"section_{section.section_number:02d}"

        def route(state: Dict[str, Any]) -> str:
            status = state[section_key].get('status')
            if status == DynamicSectionStatus.ERROR:
                return "error"
            elif status == DynamicSectionStatus.REGENERATING:
                return "regenerate"
            else:
                return "next"

        return route

    def _build_dependency_graph(self) -> StateGraph:
        """
        Grafo com dependências: topological sort por níveis.

        Seções no mesmo nível executam em sequência (LangGraph não suporta
        paralelismo real dentro do grafo), mas a ordem respeita as dependências.

        Suporta pipeline multi-step: se uma seção tem SectionPipelineStep
        configurados, cria nós do pipeline ao invés de generate→validate.
        """
        levels = self._topological_sort()

        logger.info(f"Topological sort: {len(levels)} níveis")
        for i, level in enumerate(levels):
            names = [s.section_name for s in level]
            logger.info(f"  Nível {i}: {names}")

        # Flatten para ordem de execução
        ordered_sections = []
        for level in levels:
            ordered_sections.extend(level)

        StateClass = self._create_dynamic_state_class()
        graph = StateGraph(StateClass)

        # Mapear seções → seus nós (primeiro e último nó de cada seção)
        section_nodes = []  # [(first_node, last_node, last_is_validate, section)]

        for section in ordered_sections:
            sec_num = section.section_number
            skip_reason = self._should_skip_section(section)

            if skip_reason:
                logger.info(f"Pulando seção {sec_num}: {skip_reason}")
                continue

            # SUB-SEÇÕES: seção com sub-itens → nó compositor
            if self._has_sub_sections(section):
                comp_name = f"compose_{sec_num:02d}"
                graph.add_node(comp_name, self._create_compose_subsections_node(section))
                section_nodes.append((comp_name, comp_name, False, section))
                sub_count = section.sub_sections.filter(is_active=True).count()
                logger.info(f"Seção {sec_num}: composição de {sub_count} sub-seções")
                continue

            pipeline_steps = self._get_pipeline_steps(section)

            if pipeline_steps:
                # PIPELINE: criar um nó por step
                step_names = []
                for step in pipeline_steps:
                    node_name = f"step_{sec_num:02d}_{step.step_order:02d}"
                    graph.add_node(node_name, self._create_step_node(section, step))
                    step_names.append((node_name, step))

                # Encadear steps internos
                for j in range(len(step_names) - 1):
                    current_name, current_step = step_names[j]
                    next_name, _ = step_names[j + 1]
                    if current_step.step_type != 'validate':
                        graph.add_edge(current_name, next_name)

                first_node = step_names[0][0]
                last_node_name, last_step = step_names[-1]
                last_is_validate = last_step.step_type == 'validate'

                # Validate no meio do pipeline → routing
                for j, (name, step) in enumerate(step_names):
                    if step.step_type == 'validate' and j < len(step_names) - 1:
                        next_name = step_names[j + 1][0]
                        regen_node = first_node
                        for k in range(j - 1, -1, -1):
                            if step_names[k][1].step_type == 'generate':
                                regen_node = step_names[k][0]
                                break
                        graph.add_conditional_edges(
                            name,
                            self._create_pipeline_routing(section),
                            {
                                "regenerate": regen_node,
                                "next": next_name,
                                "error": "handle_error",
                            }
                        )

                section_nodes.append((first_node, last_node_name, last_is_validate, section))
                logger.info(f"Seção {sec_num}: pipeline com {len(pipeline_steps)} steps")
            else:
                # LEGADO: generate (→ validate se tiver validador)
                gen_name = f"generate_{sec_num:02d}"
                graph.add_node(gen_name, self._create_generate_node(section))

                if self._has_validator(section):
                    val_name = f"validate_{sec_num:02d}"
                    graph.add_node(val_name, self._create_validate_node(section))
                    graph.add_edge(gen_name, val_name)
                    section_nodes.append((gen_name, val_name, True, section))
                else:
                    logger.info(f"Seção {sec_num}: sem validador, geração direta")
                    section_nodes.append((gen_name, gen_name, False, section))

        if not section_nodes:
            raise ValueError("Nenhuma seção válida para gerar. Verifique se as seções selecionadas têm agentes configurados.")

        graph.add_node("finalize", self._create_finalize_node())
        graph.add_node("handle_error", self._create_error_node())

        # Entry point
        graph.set_entry_point(section_nodes[0][0])

        # Conectar seções entre si
        for i, (first_node, last_node, last_is_validate, section) in enumerate(section_nodes):
            next_first = section_nodes[i + 1][0] if i + 1 < len(section_nodes) else "finalize"

            if last_is_validate:
                regen_node = first_node
                graph.add_conditional_edges(
                    last_node,
                    self._create_routing_function(section,
                        section_nodes[i + 1][3] if i + 1 < len(section_nodes) else None),
                    {
                        "regenerate": regen_node,
                        "next": next_first,
                        "error": "handle_error",
                    }
                )
            else:
                graph.add_edge(last_node, next_first)

        graph.add_edge("finalize", END)
        graph.add_edge("handle_error", END)

        logger.info("Grafo com dependências construído com sucesso")
        return graph

    def _calculate_recursion_limit(self, max_retries: int) -> int:
        """Calcula recursion_limit considerando pipeline steps e seções filtradas."""
        total_nodes = 0
        for section in self.sections:
            if self._should_skip_section(section):
                continue
            pipeline_steps = self._get_pipeline_steps(section)
            if pipeline_steps:
                total_nodes += len(pipeline_steps)
            elif self._has_validator(section):
                total_nodes += 2  # generate + validate
            else:
                total_nodes += 1  # generate only
        return (total_nodes * max_retries) + 20

    @property
    def graph(self):
        """Retorna o grafo compilado (lazy loading)."""
        if self._compiled_graph is None:
            state_graph = self._build_graph()
            if self.checkpointer:
                self._compiled_graph = state_graph.compile(checkpointer=self.checkpointer)
            else:
                self._compiled_graph = state_graph.compile()
            # Emitir estrutura do grafo para visualização
            self._emit('graph_structure', self._build_graph_structure())
        return self._compiled_graph

    def run(
        self,
        objective: str,
        collection_name: Optional[str] = None,
        user_id: Optional[str] = None,
        max_retries: int = 2,
        sections_to_generate: Optional[List[int]] = None,
        config: Optional[dict] = None,
        sub_section_decisions: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Executa o grafo de geração.

        Args:
            objective: Objetivo da contratação
            collection_name: Collection para RAG
            user_id: ID do usuário
            max_retries: Máximo de tentativas por seção
            sections_to_generate: Lista de números das seções a gerar
            config: Configuração adicional do LangGraph
            sub_section_decisions: Decisões do usuário sobre sub-seções (gerar vs default)

        Returns:
            Estado final
        """
        logger.info(f"Iniciando geração com {self.blueprint.name}")

        # Filtrar seções para o grafo (só cria nós para as seções pedidas)
        if sections_to_generate:
            self._sections = [s for s in self.sections if s.section_number in sections_to_generate]
            self._compiled_graph = None  # Forçar reconstrução do grafo
            logger.info(f"Grafo filtrado para {len(self._sections)} seções: {sections_to_generate}")

        initial_state = self._create_initial_state(
            objective=objective,
            collection_name=collection_name,
            user_id=user_id,
            max_retries=max_retries,
            sections_to_generate=sections_to_generate,
            sub_section_decisions=sub_section_decisions,
        )

        run_config = config or {}
        if "recursion_limit" not in run_config:
            run_config["recursion_limit"] = self._calculate_recursion_limit(max_retries)

        final_state = self.graph.invoke(initial_state, config=run_config)

        logger.info(f"Geração concluída. Status: {final_state.get('status')}")
        return final_state

    def stream(
        self,
        objective: str,
        collection_name: Optional[str] = None,
        user_id: Optional[str] = None,
        max_retries: int = 2,
        sections_to_generate: Optional[List[int]] = None,
        config: Optional[dict] = None,
        section_overrides: Optional[Dict[int, Dict[str, Any]]] = None,
        sub_section_decisions: Optional[Dict[str, Any]] = None,
    ):
        """
        Executa o grafo com streaming.

        Args:
            section_overrides: Dict de {section_number: {key: value}} para injetar
                              dados extras no estado inicial de seções específicas.
                              Ex: {3: {'user_feedback': 'Detalhar mais...'}}
            sub_section_decisions: Decisões do usuário sobre sub-seções (gerar vs default)

        Yields:
            Estados intermediários
        """
        logger.info(f"Iniciando geração (stream) com {self.blueprint.name}")

        # Filtrar seções para o grafo (só cria nós para as seções pedidas)
        if sections_to_generate:
            self._sections = [s for s in self.sections if s.section_number in sections_to_generate]
            self._compiled_graph = None  # Forçar reconstrução do grafo
            logger.info(f"Grafo filtrado para {len(self._sections)} seções: {sections_to_generate}")

        initial_state = self._create_initial_state(
            objective=objective,
            collection_name=collection_name,
            user_id=user_id,
            max_retries=max_retries,
            sections_to_generate=sections_to_generate,
            sub_section_decisions=sub_section_decisions,
        )

        # Injetar overrides no estado inicial das seções
        if section_overrides:
            for sec_num, overrides in section_overrides.items():
                sec_key = f"section_{sec_num:02d}"
                if sec_key in initial_state:
                    initial_state[sec_key].update(overrides)
                    logger.info(f"Override injetado na seção {sec_num}: {list(overrides.keys())}")

        run_config = config or {}
        if "recursion_limit" not in run_config:
            run_config["recursion_limit"] = self._calculate_recursion_limit(max_retries)

        for state in self.graph.stream(initial_state, config=run_config):
            yield state

    # === Métodos auxiliares ===

    def _get_previous_sections_content(self, state: Dict[str, Any], current_num: int) -> str:
        """
        Obtém conteúdo das seções anteriores.

        Se há dependências configuradas para a seção atual, retorna apenas
        o conteúdo das seções das quais ela depende. Caso contrário, retorna
        o conteúdo de todas as seções com número menor (comportamento original).
        """
        current_section = None
        for s in self.sections:
            if s.section_number == current_num:
                current_section = s
                break

        parts = []

        # Limite de chars por secao no contexto previous_sections.
        # 500 chars era insuficiente pra tabelas HTML completas (Mapa de Riscos
        # gera tabela com ~8000 chars, agente da secao seguinte recebia so o
        # cabecalho e gerava conteudo divergente). 15000 cobre tabelas grandes
        # (~50 linhas) sem estourar contexto do LLM mesmo com varias secoes.
        SECTION_CONTEXT_LIMIT = 15000

        # Se a seção tem dependências explícitas, usa apenas elas
        if current_section and current_section.depends_on.exists():
            dep_ids = set(current_section.depends_on.values_list('id', flat=True))
            for section in self.sections:
                if section.id in dep_ids:
                    section_key = f"section_{section.section_number:02d}"
                    content = state.get(section_key, {}).get('content', '')
                    if content:
                        truncated = content[:SECTION_CONTEXT_LIMIT]
                        suffix = '...' if len(content) > SECTION_CONTEXT_LIMIT else ''
                        parts.append(f"### {section.section_name}\n{truncated}{suffix}")
        else:
            # Comportamento original: todas as seções anteriores
            for section in self.sections:
                if section.section_number >= current_num:
                    break
                section_key = f"section_{section.section_number:02d}"
                content = state.get(section_key, {}).get('content', '')
                if content:
                    truncated = content[:SECTION_CONTEXT_LIMIT]
                    suffix = '...' if len(content) > SECTION_CONTEXT_LIMIT else ''
                    parts.append(f"### {section.section_name}\n{truncated}{suffix}")

        return "\n\n".join(parts)

    def _get_default_system_prompt(self, section: BlueprintSection) -> str:
        """Retorna prompt de sistema padrão."""
        return f"""Você é um especialista em elaboração de documentos técnicos.
Sua tarefa é gerar a seção "{section.section_name}".

Fundamentação: {section.legal_reference or 'Não especificada'}

Seja objetivo, técnico e profissional."""

    def _get_default_user_template(self, section: BlueprintSection) -> str:
        """Retorna template de usuário padrão."""
        return f"""## OBJETIVO

{{{{objective}}}}

## TAREFA

Gere a seção "{section.section_name}" do documento.

Comece diretamente com o conteúdo, sem incluir título."""

    def _parse_validation_response(self, response: str) -> Dict[str, Any]:
        """Parse do JSON de validação."""
        import json

        # Tenta extrair JSON
        json_match = re.search(r'\{.*\}', response, re.DOTALL)

        if not json_match:
            return {
                'is_valid': True,
                'score': 75,
                'errors': [],
                'warnings': ['Não foi possível parsear resposta de validação'],
                'suggestions': [],
            }

        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            return {
                'is_valid': True,
                'score': 75,
                'errors': [],
                'warnings': ['JSON de validação inválido'],
                'suggestions': [],
            }
