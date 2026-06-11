"""
BaseAgent - Classe abstrata para todos os agentes do assistente inteligente.

Implementa Template Method pattern, definindo a estrutura comum
para geradores e validadores de seções.
"""
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from apps.intelligent_assistant.services import ClaudeService, KnowledgeBaseService

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Classe abstrata base para todos os agentes.

    Define a interface e comportamento comum para:
    - Agentes geradores de seções
    - Agentes validadores de seções

    Implementa Template Method pattern.
    """

    def __init__(
        self,
        name: str,
        claude_service: Optional[ClaudeService] = None,
        kb_service: Optional[KnowledgeBaseService] = None
    ):
        """
        Inicializa o agente base.

        Args:
            name: Nome identificador do agente
            claude_service: Instância do ClaudeService (opcional)
            kb_service: Instância do KnowledgeBaseService (opcional)
        """
        self.name = name
        self.claude_service = claude_service or ClaudeService()
        self.kb_service = kb_service or KnowledgeBaseService.get_instance()
        self._reasoning_log = []

    @abstractmethod
    def generate(self, **kwargs) -> Dict:
        """
        Método abstrato para geração/validação.

        Deve ser implementado por cada agente específico.

        Args:
            **kwargs: Parâmetros específicos de cada agente

        Returns:
            Dict com resultado da operação
        """
        pass

    def _get_context_from_kb(
        self,
        collection_name: str,
        query: str,
        n_results: int = 5
    ) -> List[str]:
        """
        Busca documentos relevantes na Knowledge Base (PgVector).

        Args:
            collection_name: ID da sessão (UUID) para buscar embeddings
            query: Query para busca semântica
            n_results: Número máximo de resultados

        Returns:
            Lista de documentos relevantes
        """
        try:
            results = self.kb_service.query(
                collection_name=collection_name,
                query_text=query,
                n_results=n_results
            )

            documents = results.get('documents', [])

            if documents:
                self._log_reasoning(
                    f"Recuperados {len(documents)} documentos da KB (PgVector) "
                    f"para query: '{query[:50]}...'"
                )
            else:
                self._log_reasoning(
                    f"Nenhum documento encontrado na sessão para query: '{query[:50]}...' "
                    f"- gerando sem contexto RAG"
                )

            return documents

        except Exception as e:
            logger.warning(f"Erro ao buscar contexto na KB: {str(e)} - continuando sem contexto")
            self._log_reasoning(f"KB indisponível, gerando sem contexto RAG")
            return []

    def _log_reasoning(self, message: str):
        """
        Registra uma etapa do raciocínio do agente.

        Args:
            message: Mensagem descrevendo o raciocínio
        """
        self._reasoning_log.append(message)
        logger.debug(f"[{self.name}] {message}")

    def get_reasoning_log(self) -> str:
        """
        Obtém o log completo do raciocínio do agente.

        Returns:
            String com todas as etapas do raciocínio
        """
        return "\n".join(self._reasoning_log)

    def clear_reasoning_log(self):
        """Limpa o log de raciocínio."""
        self._reasoning_log = []

    def _call_claude(
        self,
        user_prompt: str,
        system_prompt: str,
        context_documents: Optional[List[str]] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> Dict:
        """
        Chama o Claude com os prompts fornecidos.

        Args:
            user_prompt: Prompt do usuário
            system_prompt: Prompt de sistema
            context_documents: Documentos de contexto da KB
            temperature: Temperatura para geração
            max_tokens: Máximo de tokens na resposta

        Returns:
            Dict com resposta do Claude
        """
        self._log_reasoning(
            f"Chamando Claude com temperatura={temperature}, "
            f"max_tokens={max_tokens}"
        )

        try:
            response = self.claude_service.generate(
                user_prompt=user_prompt,
                system_prompt=system_prompt,
                context_documents=context_documents,
                temperature=temperature,
                max_tokens=max_tokens
            )

            self._log_reasoning(
                f"Claude respondeu. Tokens: "
                f"{response['usage']['input_tokens']} in / "
                f"{response['usage']['output_tokens']} out"
            )

            return response

        except Exception as e:
            logger.error(f"Erro ao chamar Claude: {str(e)}")
            self._log_reasoning(f"ERRO ao chamar Claude: {str(e)}")
            raise

    def _extract_thinking_from_response(self, content: str) -> tuple[str, str]:
        """
        Extrai pensamento e conteúdo de uma resposta do Claude.

        O Claude pode incluir tags <thinking> no início da resposta.
        Este método separa o pensamento do conteúdo final.

        Args:
            content: Conteúdo completo da resposta

        Returns:
            Tupla (thinking, content) onde:
                - thinking: Raciocínio do modelo (ou string vazia)
                - content: Conteúdo limpo sem tags de pensamento
        """
        thinking = ""
        clean_content = content

        # Verificar se há tag <thinking>
        if "<thinking>" in content and "</thinking>" in content:
            start = content.find("<thinking>") + len("<thinking>")
            end = content.find("</thinking>")
            thinking = content[start:end].strip()

            # Remover seção de thinking do conteúdo
            clean_content = content[:content.find("<thinking>")] + content[end + len("</thinking>"):]
            clean_content = clean_content.strip()

            self._log_reasoning(f"Thinking extraído: {len(thinking)} caracteres")

        return thinking, clean_content

    def __str__(self):
        """Representação em string do agente."""
        return f"{self.__class__.__name__}(name='{self.name}')"

    def __repr__(self):
        """Representação técnica do agente."""
        return self.__str__()
