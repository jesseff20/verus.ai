"""
ClaudeService - Wrapper para integração com a API do Claude (Anthropic).

Este serviço fornece uma interface simplificada para chamadas à API do Claude,
incluindo retry logic, logging de tokens e tratamento de erros.
"""
import logging
import time
from typing import Dict, List, Optional
from anthropic import Anthropic, APIError, RateLimitError
from django.conf import settings

logger = logging.getLogger(__name__)


class ClaudeService:
    """
    Serviço para interação com a API do Claude (Anthropic).

    Fornece métodos para gerar texto usando Claude com suporte a:
    - System prompts e user prompts
    - Retry automático em caso de rate limit
    - Logging de uso de tokens
    - Controle de temperatura e max_tokens
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-haiku-4-5",
        max_retries: int = 3,
        retry_delay: int = 2
    ):
        """
        Inicializa o serviço do Claude.

        Args:
            api_key: Chave da API Anthropic. Se None, usa settings.ANTHROPIC_API_KEY
            model: Modelo do Claude a ser usado
            max_retries: Número máximo de tentativas em caso de erro
            retry_delay: Delay em segundos entre retries
        """
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY não configurada")

        self.client = Anthropic(api_key=self.api_key)
        self.model = model
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def generate(
        self,
        user_prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        context_documents: Optional[List[str]] = None
    ) -> Dict:
        """
        Gera texto usando Claude.

        Args:
            user_prompt: Prompt do usuário
            system_prompt: Prompt de sistema (opcional)
            temperature: Controle de criatividade (0.0 a 1.0)
            max_tokens: Número máximo de tokens na resposta
            context_documents: Lista de documentos para contexto (opcional)

        Returns:
            Dict contendo:
                - content: Texto gerado
                - usage: Dicionário com input_tokens e output_tokens
                - model: Modelo usado
                - reasoning: Raciocínio do modelo (se disponível)

        Raises:
            APIError: Erro na chamada da API
            ValueError: Parâmetros inválidos
        """
        if not user_prompt:
            raise ValueError("user_prompt não pode ser vazio")

        # Montar mensagem com contexto se fornecido
        full_prompt = self._build_prompt_with_context(user_prompt, context_documents)

        # Configurar mensagens
        messages = [{"role": "user", "content": full_prompt}]

        # Preparar parâmetros da API
        api_params = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages
        }

        # Adicionar system prompt se fornecido
        if system_prompt:
            api_params["system"] = system_prompt

        # Executar com retry logic
        for attempt in range(self.max_retries):
            try:
                logger.info(
                    f"Chamando Claude (tentativa {attempt + 1}/{self.max_retries})"
                )

                response = self.client.messages.create(**api_params)

                # Extrair conteúdo
                content = response.content[0].text if response.content else ""

                # Montar resposta
                result = {
                    "content": content,
                    "usage": {
                        "input_tokens": response.usage.input_tokens,
                        "output_tokens": response.usage.output_tokens
                    },
                    "model": response.model,
                    "reasoning": self._extract_reasoning(content)
                }

                # Log de sucesso
                logger.info(
                    f"Claude respondeu com sucesso. "
                    f"Tokens: {result['usage']['input_tokens']} in / "
                    f"{result['usage']['output_tokens']} out"
                )

                return result

            except RateLimitError as e:
                logger.warning(
                    f"Rate limit atingido (tentativa {attempt + 1}). "
                    f"Aguardando {self.retry_delay}s..."
                )
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    raise

            except APIError as e:
                logger.error(f"Erro na API do Claude: {str(e)}")
                if attempt < self.max_retries - 1 and self._is_retryable_error(e):
                    time.sleep(self.retry_delay)
                else:
                    raise

        raise APIError("Número máximo de tentativas excedido")

    def _build_prompt_with_context(
        self,
        user_prompt: str,
        context_documents: Optional[List[str]] = None
    ) -> str:
        """
        Constrói o prompt completo incluindo documentos de contexto.

        Args:
            user_prompt: Prompt base do usuário
            context_documents: Lista de documentos para contexto

        Returns:
            Prompt completo formatado
        """
        if not context_documents:
            return user_prompt

        context_section = "\n\n## DOCUMENTOS DE REFERÊNCIA\n\n"
        for i, doc in enumerate(context_documents, 1):
            context_section += f"### Documento {i}\n{doc}\n\n"

        return f"{context_section}\n## TAREFA\n\n{user_prompt}"

    def _extract_reasoning(self, content: str) -> str:
        """
        Extrai o raciocínio do modelo se presente no conteúdo.

        Args:
            content: Conteúdo gerado pelo Claude

        Returns:
            Raciocínio extraído ou string vazia
        """
        # Se o modelo usar tags <thinking>, extrair
        if "<thinking>" in content and "</thinking>" in content:
            start = content.find("<thinking>") + len("<thinking>")
            end = content.find("</thinking>")
            return content[start:end].strip()
        return ""

    def _is_retryable_error(self, error: APIError) -> bool:
        """
        Verifica se o erro é recuperável e deve ser retentado.

        Args:
            error: Erro da API

        Returns:
            True se o erro pode ser retentado
        """
        # Erros 5xx são temporários do servidor
        if hasattr(error, 'status_code'):
            return 500 <= error.status_code < 600
        return False

    def estimate_tokens(self, text: str) -> int:
        """
        Estima o número de tokens em um texto.

        Usa aproximação: 1 token ≈ 4 caracteres para português.

        Args:
            text: Texto para estimar

        Returns:
            Número estimado de tokens
        """
        return len(text) // 4
