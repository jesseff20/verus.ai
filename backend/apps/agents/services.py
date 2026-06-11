"""
Serviços para integração com LLMs
"""
import logging
import time
from typing import Dict, List, Optional
from django.conf import settings
import openai
import anthropic
import re

logger = logging.getLogger(__name__)


class LLMService:
    """Serviço abstrato para chamadas a LLMs"""

    @staticmethod
    def call(
        provider: str,
        model: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> Dict:
        """
        Chama LLM e retorna resposta

        Args:
            provider: 'openai' ou 'anthropic'
            model: Nome do modelo
            system_prompt: Prompt do sistema
            user_prompt: Prompt do usuário
            temperature: Temperatura (0.0-1.0)
            max_tokens: Máximo de tokens na resposta

        Returns:
            {
                'response': str,
                'tokens_used': int,
                'model': str,
                'provider': str
            }
        """
        if provider == 'openai':
            return LLMService._call_openai(
                model, system_prompt, user_prompt, temperature, max_tokens
            )
        elif provider == 'anthropic':
            return LLMService._call_anthropic(
                model, system_prompt, user_prompt, temperature, max_tokens
            )
        else:
            raise ValueError(f"Provider '{provider}' não suportado")

    @staticmethod
    def _call_openai(
        model: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> Dict:
        """Chama OpenAI API"""
        try:
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )

            return {
                'response': response.choices[0].message.content,
                'tokens_used': response.usage.total_tokens,
                'model': model,
                'provider': 'openai'
            }

        except Exception as e:
            raise Exception(f"Erro ao chamar OpenAI: {str(e)}")

    @staticmethod
    def _call_anthropic(
        model: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_tokens: int,
    ) -> Dict:
        """Chama Anthropic API"""
        try:
            client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

            response = client.messages.create(
                model=model,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )

            # Anthropic retorna tokens separados
            tokens_used = response.usage.input_tokens + response.usage.output_tokens

            return {
                'response': response.content[0].text,
                'tokens_used': tokens_used,
                'model': model,
                'provider': 'anthropic'
            }

        except Exception as e:
            raise Exception(f"Erro ao chamar Anthropic: {str(e)}")


class EmbeddingService:
    """
    Serviço para geração de embeddings via IBM watsonx (E5-Large).

    O modelo intfloat/multilingual-e5-large exige prefixos:
    - "query: "   → para buscas (quando o usuário pesquisa)
    - "passage: " → para indexação (quando armazenamos documentos)

    Métodos:
    - generate(text)              → prefixo "query: " (busca)
    - generate_for_indexing(text)  → prefixo "passage: " (indexar 1 texto)
    - generate_batch(texts)        → prefixo "passage: " (indexar em lote)
    """

    _client = None

    @classmethod
    def _get_credentials(cls) -> dict:
        """
        Busca credenciais watsonx do banco (core.LLMProvider), fallback para settings.
        Mesmo padrão usado pelo LLMProviderService.
        """
        try:
            from apps.core.models import LLMProvider
            provider = LLMProvider.objects.filter(
                code='watsonx', is_active=True
            ).first()

            if provider and provider.api_key:
                return {
                    'api_key': provider.api_key,
                    'url': provider.api_url or 'https://us-south.ml.cloud.ibm.com',
                    'project_id': (provider.extra_config or {}).get('project_id', ''),
                    'space_id': (provider.extra_config or {}).get('space_id', ''),
                }
        except Exception as e:
            logger.warning(f"[Embeddings] Erro ao buscar credenciais do banco: {e}")

        # Fallback: settings
        return {
            'api_key': getattr(settings, 'WATSONX_API_KEY', ''),
            'url': getattr(settings, 'WATSONX_URL', 'https://us-south.ml.cloud.ibm.com'),
            'project_id': getattr(settings, 'WATSONX_PROJECT_ID', ''),
            'space_id': getattr(settings, 'WATSONX_SPACE_ID', ''),
        }

    @classmethod
    def _get_client(cls):
        """Retorna client watsonx como singleton (lazy init)."""
        if cls._client is None:
            try:
                from ibm_watsonx_ai.foundation_models import Embeddings
                from ibm_watsonx_ai import Credentials
            except ImportError:
                raise ImportError(
                    "ibm-watsonx-ai não instalado. Execute: pip install ibm-watsonx-ai"
                )

            from .constants import EMBEDDING_MODEL_ID

            creds = cls._get_credentials()
            api_key = creds['api_key']
            url = creds['url']
            project_id = creds['project_id']
            space_id = creds['space_id']

            if not api_key:
                raise ValueError(
                    "API Key do watsonx não encontrada. "
                    "Configure no admin (Core > Provedores LLM) ou em settings."
                )
            if not project_id and not space_id:
                raise ValueError(
                    "project_id ou space_id do watsonx não encontrado. "
                    "Configure em extra_config: {\"space_id\": \"...\"}"
                )

            credentials = Credentials(url=url, api_key=api_key)
            embed_kwargs = dict(model_id=EMBEDDING_MODEL_ID, credentials=credentials)
            if space_id:
                embed_kwargs['space_id'] = space_id
            else:
                embed_kwargs['project_id'] = project_id
            cls._client = Embeddings(**embed_kwargs)
            logger.info(f"[Embeddings] Cliente watsonx inicializado (modelo={EMBEDDING_MODEL_ID})")

        return cls._client

    @staticmethod
    def generate(text: str) -> List[float]:
        """
        Gera embedding para BUSCA (prefixo "query: ").

        Use este método quando o usuário faz uma pesquisa/query.

        Args:
            text: Texto da busca

        Returns:
            Lista de floats (vetor de 1024 dimensões)
        """
        from .constants import E5_QUERY_PREFIX, EMBEDDING_MODEL_ID

        try:
            client = EmbeddingService._get_client()
            prefixed_text = f"{E5_QUERY_PREFIX}{text}"

            t0 = time.time()
            response = client.embed_documents(texts=[prefixed_text])
            elapsed = round(time.time() - t0, 2)

            embedding = response[0]
            logger.debug(
                f"[Embeddings] Query embedding gerado ({len(embedding)} dims) em {elapsed}s"
            )
            return embedding

        except Exception as e:
            logger.error(f"[Embeddings] Erro ao gerar query embedding: {str(e)}")
            raise Exception(f"Erro ao gerar embedding: {str(e)}")

    @staticmethod
    def generate_for_indexing(text: str) -> List[float]:
        """
        Gera embedding para INDEXAÇÃO (prefixo "passage: ").

        Use este método quando for armazenar/indexar um único texto.

        Args:
            text: Texto para indexar

        Returns:
            Lista de floats (vetor de 1024 dimensões)
        """
        from .constants import E5_PASSAGE_PREFIX

        try:
            client = EmbeddingService._get_client()
            prefixed_text = f"{E5_PASSAGE_PREFIX}{text}"

            t0 = time.time()
            response = client.embed_documents(texts=[prefixed_text])
            elapsed = round(time.time() - t0, 2)

            embedding = response[0]
            logger.debug(
                f"[Embeddings] Passage embedding gerado ({len(embedding)} dims) em {elapsed}s"
            )
            return embedding

        except Exception as e:
            logger.error(f"[Embeddings] Erro ao gerar passage embedding: {str(e)}")
            raise Exception(f"Erro ao gerar embedding para indexação: {str(e)}")

    @staticmethod
    def generate_batch(texts: List[str]) -> List[List[float]]:
        """
        Gera embeddings em lote para INDEXAÇÃO (prefixo "passage: ").

        Use este método quando for indexar múltiplos textos de uma vez.

        Args:
            texts: Lista de textos para indexar

        Returns:
            Lista de embeddings (cada um com 1024 dimensões)
        """
        from .constants import E5_PASSAGE_PREFIX, EMBEDDING_BATCH_SIZE, EMBEDDING_MODEL_ID

        try:
            if not texts:
                raise ValueError("Lista de textos não pode ser vazia")

            valid_texts = [text.strip() for text in texts if text and text.strip()]

            if not valid_texts:
                raise ValueError("Nenhum texto válido encontrado na lista")

            # Adicionar prefixo "passage: " a cada texto
            prefixed_texts = [f"{E5_PASSAGE_PREFIX}{t}" for t in valid_texts]

            logger.info(
                f"[Embeddings] Gerando batch para {len(prefixed_texts)} textos "
                f"({EMBEDDING_MODEL_ID})"
            )

            client = EmbeddingService._get_client()

            # Dividir em lotes se necessário
            if len(prefixed_texts) <= EMBEDDING_BATCH_SIZE:
                t0 = time.time()
                all_embeddings = client.embed_documents(texts=prefixed_texts)
                elapsed = round(time.time() - t0, 2)
                logger.info(
                    f"[Embeddings] Batch concluído: {len(all_embeddings)} embeddings em {elapsed}s"
                )
                return all_embeddings

            # Múltiplos lotes
            all_embeddings = []
            total_batches = (len(prefixed_texts) + EMBEDDING_BATCH_SIZE - 1) // EMBEDDING_BATCH_SIZE
            batch_start = time.time()

            for i in range(0, len(prefixed_texts), EMBEDDING_BATCH_SIZE):
                batch = prefixed_texts[i:i + EMBEDDING_BATCH_SIZE]
                batch_num = (i // EMBEDDING_BATCH_SIZE) + 1

                t0 = time.time()
                logger.info(
                    f"[Embeddings] Batch {batch_num}/{total_batches} "
                    f"({len(batch)} textos)..."
                )
                embeddings = client.embed_documents(texts=batch)
                all_embeddings.extend(embeddings)
                elapsed = round(time.time() - t0, 2)
                logger.info(
                    f"[Embeddings] Batch {batch_num}/{total_batches} concluído em {elapsed}s"
                )

            total_elapsed = round(time.time() - batch_start, 2)
            logger.info(
                f"[Embeddings] Total: {len(all_embeddings)} embeddings em "
                f"{total_batches} batches | {total_elapsed}s"
            )
            return all_embeddings

        except Exception as e:
            logger.error(f"[Embeddings] Erro batch: {str(e)}")
            raise Exception(f"Erro ao gerar embeddings em batch: {str(e)}")


class ProcessoDetectionService:
    """Serviço para detectar menções a processos nas mensagens"""

    @staticmethod
    def extract_processo_numbers(text: str) -> List[str]:
        """
        Extrai números de processo do texto

        Padrões suportados:
        - 2025/001
        - processo 2025/001
        - proc 2025/001
        - número 2025/001

        Args:
            text: Texto para analisar

        Returns:
            Lista de números de processo encontrados (formato: YYYY/NNN)
        """
        # Padrão: 4 dígitos + / + 3 ou mais dígitos
        pattern = r'\b(\d{4})/(\d{3,})\b'
        matches = re.findall(pattern, text)

        # Retornar no formato YYYY/NNN
        return [f"{year}/{num}" for year, num in matches]

    @staticmethod
    def detect_processo_context(message: str) -> Optional[str]:
        """
        Detecta se a mensagem está perguntando sobre um processo específico
        e retorna o número do processo

        Args:
            message: Mensagem do usuário

        Returns:
            Número do processo (ex: "2025/002") ou None
        """
        processos = ProcessoDetectionService.extract_processo_numbers(message)

        if processos:
            # Retornar o primeiro processo encontrado
            return processos[0]

        return None

    @staticmethod
    def should_filter_by_processo(message: str) -> bool:
        """
        Verifica se a mensagem indica que deve filtrar por processo

        Args:
            message: Mensagem do usuário

        Returns:
            True se deve filtrar por processo
        """
        # Palavras-chave que indicam consulta a processo específico
        keywords = [
            'processo', 'proc.', 'autos', 'ação', 'acao',
            'caso', 'cliente', 'prazo', 'audiência', 'audiencia',
            'status do', 'andamento do',
            'documentos do', 'informações sobre', 'informacoes sobre'
        ]

        message_lower = message.lower()

        # Se tem número de processo E palavra-chave relacionada
        if ProcessoDetectionService.extract_processo_numbers(message):
            return any(keyword in message_lower for keyword in keywords)

        return False
