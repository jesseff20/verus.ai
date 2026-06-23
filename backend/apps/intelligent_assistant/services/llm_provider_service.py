"""
UnifiedLLMService - Serviço unificado multi-provider para LLMs.

Busca credenciais do banco (core.LLMProvider) em vez de variáveis de ambiente.
Despacha para Anthropic, OpenAI ou IBM watsonx mantendo a mesma interface
do ClaudeService.generate() para backward compatibility.

Usage:
    service = UnifiedLLMService()
    response = service.generate(
        user_prompt="...",
        system_prompt="...",
        provider="anthropic",
        model="claude-haiku-4-5",
    )
"""
import logging
import time
from decimal import Decimal
from typing import Dict, Generator, List, Optional, Tuple

from django.conf import settings

logger = logging.getLogger(__name__)


class UnifiedLLMService:
    """
    Serviço unificado que roteia chamadas para o provider correto.

    Credenciais são buscadas em core.LLMProvider (banco de dados).
    Fallback para settings (variáveis de ambiente) se o provider
    não existir no banco.

    Providers suportados:
    - anthropic: Claude (SDK anthropic)
    - openai: GPT (SDK openai)
    - watsonx: IBM watsonx.ai (SDK ibm-watsonx-ai, lazy import)
    """

    def __init__(self, max_retries: int = 3, retry_delay: int = 2):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._anthropic_client = None
        self._openai_client = None
        self._watsonx_credentials = None
        self._watsonx_models = {}  # Cache de ModelInference por model_id
        self._provider_cache = {}  # Cache de credenciais por code

    # Modelos watsonx que exigem endpoint /text/chat (não suportam /text/generation)
    WATSONX_CHAT_MODELS = {
        'mistral-large-2512',
    }

    def _get_provider_credentials(self, provider_code: str) -> dict:
        """
        Busca credenciais do provider no banco (core.LLMProvider).
        Retorna dict com api_key, api_url, extra_config.
        Fallback para settings se não encontrar no banco.
        """
        if provider_code in self._provider_cache:
            return self._provider_cache[provider_code]

        try:
            from apps.core.models import LLMProvider
            provider = LLMProvider.objects.filter(
                code=provider_code, is_active=True
            ).first()

            if provider and provider.api_key:
                creds = {
                    'api_key': provider.api_key,
                    'api_url': provider.api_url,
                    'extra_config': provider.extra_config or {},
                }
                self._provider_cache[provider_code] = creds
                logger.info(f"[{provider_code}] Credenciais carregadas do banco")
                return creds
        except Exception as e:
            logger.warning(f"[{provider_code}] Erro ao buscar do banco: {e}")

        # Fallback: settings / variáveis de ambiente
        creds = self._get_fallback_credentials(provider_code)
        self._provider_cache[provider_code] = creds
        return creds

    def _get_fallback_credentials(self, provider_code: str) -> dict:
        """Fallback para credenciais via settings (variáveis de ambiente)."""
        if provider_code == 'anthropic':
            return {
                'api_key': getattr(settings, 'ANTHROPIC_API_KEY', ''),
                'api_url': '',
                'extra_config': {},
            }
        elif provider_code == 'openai':
            return {
                'api_key': getattr(settings, 'OPENAI_API_KEY', ''),
                'api_url': '',
                'extra_config': {},
            }
        elif provider_code == 'watsonx':
            return {
                'api_key': getattr(settings, 'WATSONX_API_KEY', ''),
                'api_url': getattr(settings, 'WATSONX_URL', 'https://us-south.ml.cloud.ibm.com'),
                'extra_config': {
                    'project_id': getattr(settings, 'WATSONX_PROJECT_ID', ''),
                },
            }
        return {'api_key': '', 'api_url': '', 'extra_config': {}}

    @staticmethod
    def _estimate_cost(provider: str, total_tokens: int) -> Decimal:
        """Estima custo em USD baseado no provider e total de tokens."""
        rates = {'openai': 0.00003, 'anthropic': 0.00004, 'watsonx': 0.00002}
        return Decimal(str(total_tokens * rates.get(provider, 0.00003))).quantize(Decimal('0.0001'))

    def _log_token_usage(
        self,
        provider: str,
        model: str,
        result: Dict,
        user=None,
        usage_type: str = 'other',
        description: str = '',
    ):
        """Registra uso de tokens no banco de dados."""
        try:
            from apps.core.models import TokenUsageLog

            input_tokens = result.get('usage', {}).get('input_tokens', 0)
            output_tokens = result.get('usage', {}).get('output_tokens', 0)
            total_tokens = input_tokens + output_tokens

            TokenUsageLog.objects.create(
                user=user,
                model_provider=provider,
                model_name=model,
                usage_type=usage_type,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
                cost_estimate=self._estimate_cost(provider, total_tokens),
                description=description or f'{usage_type} request',
            )
        except Exception:
            logger.warning("Failed to log LLM usage audit entry", exc_info=True)

    def generate(
        self,
        user_prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        context_documents: Optional[List[str]] = None,
        provider: str = 'anthropic',
        model: str = 'claude-haiku-4-5',
        user=None,
        usage_type: str = 'other',
        description: str = '',
    ) -> Dict:
        """
        Gera texto usando o provider/modelo especificado.

        Retorna dict compatível com ClaudeService:
            {content, usage: {input_tokens, output_tokens}, model, reasoning}
        """
        if not user_prompt:
            raise ValueError("user_prompt não pode ser vazio")

        full_prompt = self._build_prompt_with_context(user_prompt, context_documents)

        dispatch = {
            'anthropic': self._call_anthropic,
            'openai': self._call_openai,
            'watsonx': self._call_watsonx,
        }

        handler = dispatch.get(provider)
        if not handler:
            raise ValueError(f"Provider '{provider}' não suportado. Use: {list(dispatch.keys())}")

        for attempt in range(self.max_retries):
            try:
                logger.info(
                    f"[{provider}/{model}] Chamando LLM (tentativa {attempt + 1}/{self.max_retries})"
                )

                result = handler(
                    user_prompt=full_prompt,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    model=model,
                )

                logger.info(
                    f"[{provider}/{model}] Sucesso. "
                    f"Tokens: {result['usage']['input_tokens']} in / "
                    f"{result['usage']['output_tokens']} out"
                )

                # Log token usage after successful call
                self._log_token_usage(
                    provider=provider,
                    model=model,
                    result=result,
                    user=user,
                    usage_type=usage_type,
                    description=description,
                )

                return result

            except Exception as e:
                logger.warning(
                    f"[{provider}/{model}] Erro (tentativa {attempt + 1}): {e}"
                )
                if attempt < self.max_retries - 1 and self._is_retryable(e):
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    raise

        raise RuntimeError(f"[{provider}/{model}] Máximo de tentativas excedido")

    def generate_stream(
        self,
        user_prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        context_documents: Optional[List[str]] = None,
        provider: str = 'anthropic',
        model: str = 'claude-haiku-4-5',
        user=None,
        usage_type: str = 'other',
        description: str = '',
    ) -> Generator[Tuple[str, Optional[Dict]], None, None]:
        """
        Gera texto com streaming token-a-token.

        Yields:
            Tuplas (chunk_text, final_result):
            - Durante streaming: ("texto parcial", None)
            - No final: ("", {content, usage, model, reasoning})
        """
        if not user_prompt:
            raise ValueError("user_prompt não pode ser vazio")

        full_prompt = self._build_prompt_with_context(user_prompt, context_documents)

        dispatch = {
            'anthropic': self._stream_anthropic,
            'openai': self._stream_openai,
            'watsonx': self._stream_watsonx,
        }

        handler = dispatch.get(provider)
        if not handler:
            raise ValueError(f"Provider '{provider}' não suportado. Use: {list(dispatch.keys())}")

        try:
            logger.info(
                f"[{provider}/{model}] Chamando LLM stream"
            )
            for chunk_text, final_result in handler(
                user_prompt=full_prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                model=model,
            ):
                yield (chunk_text, final_result)
                # Log token usage when we get the final result
                if final_result is not None:
                    self._log_token_usage(
                        provider=provider,
                        model=model,
                        result=final_result,
                        user=user,
                        usage_type=usage_type,
                        description=description,
                    )

        except Exception as e:
            logger.error(
                f"[{provider}/{model}] Erro no streaming: {e}"
            )
            raise

    # =========================================================================
    # ANTHROPIC
    # =========================================================================

    def _get_anthropic_client(self):
        if self._anthropic_client is None:
            from anthropic import Anthropic
            creds = self._get_provider_credentials('anthropic')
            api_key = creds['api_key']
            if not api_key:
                raise ValueError(
                    "API Key da Anthropic não configurada. "
                    "Configure no admin (Core > Provedores LLM) ou na variável ANTHROPIC_API_KEY."
                )
            self._anthropic_client = Anthropic(api_key=api_key)
        return self._anthropic_client

    def _call_anthropic(
        self, user_prompt: str, system_prompt: Optional[str],
        temperature: float, max_tokens: int, model: str,
    ) -> Dict:
        client = self._get_anthropic_client()

        api_params = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": user_prompt}],
        }
        if system_prompt:
            api_params["system"] = system_prompt

        response = client.messages.create(**api_params)

        content = response.content[0].text if response.content else ""
        return {
            "content": content,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
            "model": response.model,
            "reasoning": self._extract_reasoning(content),
        }

    def _stream_anthropic(
        self, user_prompt: str, system_prompt: Optional[str],
        temperature: float, max_tokens: int, model: str,
    ) -> Generator[Tuple[str, Optional[Dict]], None, None]:
        client = self._get_anthropic_client()

        api_params = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": user_prompt}],
        }
        if system_prompt:
            api_params["system"] = system_prompt

        full_content = ""
        input_tokens = 0
        output_tokens = 0

        with client.messages.stream(**api_params) as stream:
            for text in stream.text_stream:
                full_content += text
                yield (text, None)

            # Pegar usage do response final
            response = stream.get_final_message()
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens

        yield ("", {
            "content": full_content,
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            },
            "model": model,
            "reasoning": self._extract_reasoning(full_content),
        })

    # =========================================================================
    # OPENAI
    # =========================================================================

    def _get_openai_client(self):
        if self._openai_client is None:
            import openai
            creds = self._get_provider_credentials('openai')
            api_key = creds['api_key']
            if not api_key:
                raise ValueError(
                    "API Key da OpenAI não configurada. "
                    "Configure no admin (Core > Provedores LLM) ou na variável OPENAI_API_KEY."
                )
            self._openai_client = openai.OpenAI(api_key=api_key)
        return self._openai_client

    def _call_openai(
        self, user_prompt: str, system_prompt: Optional[str],
        temperature: float, max_tokens: int, model: str,
    ) -> Dict:
        client = self._get_openai_client()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        content = response.choices[0].message.content or ""
        usage = response.usage

        return {
            "content": content,
            "usage": {
                "input_tokens": usage.prompt_tokens if usage else 0,
                "output_tokens": usage.completion_tokens if usage else 0,
            },
            "model": response.model,
            "reasoning": "",
        }

    def _stream_openai(
        self, user_prompt: str, system_prompt: Optional[str],
        temperature: float, max_tokens: int, model: str,
    ) -> Generator[Tuple[str, Optional[Dict]], None, None]:
        client = self._get_openai_client()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        stream = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            stream_options={"include_usage": True},
        )

        full_content = ""
        input_tokens = 0
        output_tokens = 0

        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                text = chunk.choices[0].delta.content
                full_content += text
                yield (text, None)
            if chunk.usage:
                input_tokens = chunk.usage.prompt_tokens or 0
                output_tokens = chunk.usage.completion_tokens or 0

        yield ("", {
            "content": full_content,
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            },
            "model": model,
            "reasoning": "",
        })

    # =========================================================================
    # IBM WATSONX (lazy import)
    # =========================================================================

    def _get_watsonx_model(self, model: str):
        """Retorna ModelInference cacheado (evita re-auth IAM a cada chamada)."""
        if model not in self._watsonx_models:
            from ibm_watsonx_ai.foundation_models import ModelInference
            from ibm_watsonx_ai import Credentials

            creds = self._get_provider_credentials('watsonx')
            api_key = creds['api_key']
            url = creds['api_url'] or 'https://us-south.ml.cloud.ibm.com'
            project_id = creds['extra_config'].get('project_id', '')
            space_id = creds['extra_config'].get('space_id', '')

            if not api_key:
                raise ValueError(
                    "API Key do watsonx não configurada. "
                    "Configure no admin (Core > Provedores LLM)."
                )
            if not project_id and not space_id:
                raise ValueError(
                    "project_id ou space_id do watsonx não configurado. "
                    "Configure em extra_config: {\"space_id\": \"...\"}"
                )

            if self._watsonx_credentials is None:
                self._watsonx_credentials = Credentials(
                    url=url, api_key=api_key,
                )
                logger.info("[watsonx] Credenciais inicializadas (cache)")

            model_kwargs = dict(model_id=model, credentials=self._watsonx_credentials)
            if space_id:
                model_kwargs['space_id'] = space_id
            else:
                model_kwargs['project_id'] = project_id

            self._watsonx_models[model] = ModelInference(**model_kwargs)
            logger.info(f"[watsonx] Client cacheado para modelo: {model}")

        return self._watsonx_models[model]

    def _call_watsonx(
        self, user_prompt: str, system_prompt: Optional[str],
        temperature: float, max_tokens: int, model: str,
    ) -> Dict:
        if model in self.WATSONX_CHAT_MODELS:
            return self._call_watsonx_chat(user_prompt, system_prompt, temperature, max_tokens, model)

        watsonx_model = self._get_watsonx_model(model)

        if system_prompt:
            full_prompt = f"<|system|>\n{system_prompt}\n<|user|>\n{user_prompt}\n<|assistant|>\n"
        else:
            full_prompt = user_prompt

        params = {
            "max_new_tokens": max_tokens,
            "temperature": temperature,
            "repetition_penalty": 1.1,
        }

        response = watsonx_model.generate_text(
            prompt=full_prompt,
            params=params,
        )

        content = response if isinstance(response, str) else str(response)

        estimated_input = len(full_prompt) // 4
        estimated_output = len(content) // 4

        return {
            "content": content,
            "usage": {
                "input_tokens": estimated_input,
                "output_tokens": estimated_output,
            },
            "model": model,
            "reasoning": "",
        }

    def _call_watsonx_chat(
        self, user_prompt: str, system_prompt: Optional[str],
        temperature: float, max_tokens: int, model: str,
    ) -> Dict:
        watsonx_model = self._get_watsonx_model(model)

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        params = {
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        response = watsonx_model.chat(
            messages=messages,
            params=params,
        )

        choices = response.get('choices', [])
        content = choices[0]['message']['content'] if choices else ''
        usage = response.get('usage', {})

        return {
            "content": content,
            "usage": {
                "input_tokens": usage.get('prompt_tokens', 0),
                "output_tokens": usage.get('completion_tokens', 0),
            },
            "model": model,
            "reasoning": "",
        }

    def _stream_watsonx(
        self, user_prompt: str, system_prompt: Optional[str],
        temperature: float, max_tokens: int, model: str,
    ) -> Generator[Tuple[str, Optional[Dict]], None, None]:
        """Streaming nativo via generate_text_stream() da SDK watsonx."""
        if model in self.WATSONX_CHAT_MODELS:
            yield from self._stream_watsonx_chat(user_prompt, system_prompt, temperature, max_tokens, model)
            return

        watsonx_model = self._get_watsonx_model(model)

        if system_prompt:
            full_prompt = f"<|system|>\n{system_prompt}\n<|user|>\n{user_prompt}\n<|assistant|>\n"
        else:
            full_prompt = user_prompt

        params = {
            "max_new_tokens": max_tokens,
            "temperature": temperature,
            "repetition_penalty": 1.1,
        }

        full_content = []
        for chunk in watsonx_model.generate_text_stream(
            prompt=full_prompt,
            params=params,
        ):
            if chunk:
                full_content.append(chunk)
                yield (chunk, None)

        # Emitir resultado final com metadados
        content = "".join(full_content)
        estimated_input = len(full_prompt) // 4
        estimated_output = len(content) // 4

        yield ("", {
            "content": content,
            "usage": {
                "input_tokens": estimated_input,
                "output_tokens": estimated_output,
            },
            "model": model,
            "reasoning": "",
        })

    def _stream_watsonx_chat(
        self, user_prompt: str, system_prompt: Optional[str],
        temperature: float, max_tokens: int, model: str,
    ) -> Generator[Tuple[str, Optional[Dict]], None, None]:
        """Streaming via chat_stream() para modelos chat-only do watsonx."""
        watsonx_model = self._get_watsonx_model(model)

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        params = {
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        full_content = []
        input_tokens = 0
        output_tokens = 0

        for chunk in watsonx_model.chat_stream(
            messages=messages,
            params=params,
        ):
            choices = chunk.get('choices', [])
            if choices:
                delta = choices[0].get('delta', {})
                text = delta.get('content', '')
                if text:
                    full_content.append(text)
                    yield (text, None)
            if 'usage' in chunk:
                input_tokens = chunk['usage'].get('prompt_tokens', 0)
                output_tokens = chunk['usage'].get('completion_tokens', 0)

        content = "".join(full_content)
        yield ("", {
            "content": content,
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            },
            "model": model,
            "reasoning": "",
        })

    # =========================================================================
    # UTILS
    # =========================================================================

    def _build_prompt_with_context(
        self, user_prompt: str, context_documents: Optional[List[str]] = None
    ) -> str:
        if not context_documents:
            return user_prompt

        context_section = "\n\n## DOCUMENTOS DE REFERÊNCIA\n\n"
        for i, doc in enumerate(context_documents, 1):
            context_section += f"### Documento {i}\n{doc}\n\n"

        return f"{context_section}\n## TAREFA\n\n{user_prompt}"

    def _extract_reasoning(self, content: str) -> str:
        if "<thinking>" in content and "</thinking>" in content:
            start = content.find("<thinking>") + len("<thinking>")
            end = content.find("</thinking>")
            return content[start:end].strip()
        return ""

    def _is_retryable(self, error: Exception) -> bool:
        error_str = str(error).lower()
        retryable_keywords = ['rate limit', 'timeout', '529', '503', '500', 'overloaded']
        return any(kw in error_str for kw in retryable_keywords)

    def clear_cache(self):
        """Limpa cache de credenciais (útil após atualizar API keys no admin)."""
        self._provider_cache.clear()
        self._anthropic_client = None
        self._openai_client = None
        self._watsonx_credentials = None
        self._watsonx_models = {}
