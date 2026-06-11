"""
View genérica para aprimoramento de texto com IA.

POST /api/v1/intelligent-assistant/enhance-text/
Aceita qualquer texto e contexto, retorna versão aprimorada.
"""
import logging

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.intelligent_assistant.services.llm_provider_service import UnifiedLLMService

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def enhance_text(request):
    """
    POST /api/v1/intelligent-assistant/enhance-text/
    Aprimora qualquer texto usando IA.

    Body:
      - text (str, required): texto a aprimorar
      - context (str, optional): contexto da página/campo (ex: "prompt de agente jurídico")
      - objective (str, optional): objetivo (ex: "melhorar clareza e fundamentação jurídica")
    """
    text = request.data.get('text', '').strip()
    context = request.data.get('context', 'texto jurídico')
    objective = request.data.get(
        'objective',
        'Melhore a clareza, precisão e qualidade do texto mantendo o sentido original',
    )

    if not text:
        return Response(
            {'error': 'O campo "text" não pode estar vazio.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    system_prompt = (
        "Você é um especialista em redação jurídica brasileira com vasta experiência. "
        "Seu papel é aprimorar textos mantendo todos os fatos essenciais, mas melhorando "
        "a clareza, precisão terminológica e qualidade da linguagem. "
        "Preserve nomes, datas, valores, referências legais e variáveis de template "
        "(como {{variavel}}). "
        "Retorne APENAS o texto aprimorado, sem explicações, prefácios ou marcações extras."
    )

    user_prompt = (
        f"Contexto: {context}\n"
        f"Objetivo: {objective}\n\n"
        f"TEXTO ORIGINAL:\n{text}"
    )

    try:
        llm_service = UnifiedLLMService()
        result = llm_service.generate(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            provider='watsonx',
            model='mistralai/mistral-medium-2505',
            temperature=0.4,
            max_tokens=4096,
            user=request.user if request.user.is_authenticated else None,
            usage_type='copilot',
            description='Aprimoramento de texto',
        )
        enhanced_text = result.get('content', '').strip()
        if not enhanced_text:
            return Response(
                {'error': 'A IA não retornou conteúdo. Tente novamente.'},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        return Response({
            'enhanced_text': enhanced_text,
            'original_text': text,
        })
    except Exception as exc:
        logger.error(f"[enhance_text] Erro: {exc}", exc_info=True)
        return Response(
            {'error': 'Erro ao processar com IA. Tente novamente em instantes.'},
            status=status.HTTP_502_BAD_GATEWAY,
        )
