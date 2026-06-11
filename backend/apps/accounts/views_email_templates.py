"""
Views para Templates de E-mail (#19).
"""
import re
import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import EmailTemplate
from .serializers_email_templates import EmailTemplateSerializer

logger = logging.getLogger(__name__)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def email_templates_list_create(request):
    """GET lista templates | POST cria template."""
    if request.method == 'GET':
        qs = EmailTemplate.objects.all()
        category = request.query_params.get('category')
        if category:
            qs = qs.filter(category=category)
        active_only = request.query_params.get('active')
        if active_only == 'true':
            qs = qs.filter(is_active=True)
        search = request.query_params.get('search')
        if search:
            qs = qs.filter(name__icontains=search)
        serializer = EmailTemplateSerializer(qs, many=True)
        return Response(serializer.data)

    serializer = EmailTemplateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save(created_by=request.user)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def email_template_detail(request, template_id):
    """GET/PATCH/DELETE template de e-mail."""
    try:
        template = EmailTemplate.objects.get(id=template_id)
    except EmailTemplate.DoesNotExist:
        return Response({'error': 'Template não encontrado.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response(EmailTemplateSerializer(template).data)

    if request.method == 'DELETE':
        template.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = EmailTemplateSerializer(template, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def email_template_preview(request):
    """POST renderiza template com variáveis substituídas."""
    template_id = request.data.get('template_id')
    variables = request.data.get('variables', {})

    if not template_id:
        return Response(
            {'error': 'Campo "template_id" é obrigatório.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        template = EmailTemplate.objects.get(id=template_id)
    except EmailTemplate.DoesNotExist:
        return Response({'error': 'Template não encontrado.'}, status=status.HTTP_404_NOT_FOUND)

    # Substituir variáveis no formato {{variavel}}
    rendered_subject = template.subject
    rendered_body = template.body_html

    for key, value in variables.items():
        pattern = r'\{\{\s*' + re.escape(key) + r'\s*\}\}'
        rendered_subject = re.sub(pattern, str(value), rendered_subject)
        rendered_body = re.sub(pattern, str(value), rendered_body)

    return Response({
        'subject': rendered_subject,
        'body_html': rendered_body,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def email_template_generate_ai(request):
    """POST gera template de e-mail com IA."""
    description = request.data.get('description', '').strip()
    category = request.data.get('category', 'general')

    if not description:
        return Response(
            {'error': 'Campo "description" é obrigatório.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        from apps.intelligent_assistant.services.llm_provider_service import UnifiedLLMService

        llm_service = UnifiedLLMService()

        system_prompt = (
            "Você é um especialista em comunicação jurídica brasileira. "
            "Gere um template de e-mail profissional em HTML para uso em escritório de advocacia. "
            "Use variáveis no formato {{nome_variavel}} para campos dinâmicos. "
            "Retorne APENAS um JSON com os campos: name, subject, body_html, variables. "
            "O campo variables deve ser uma lista de objetos com name e description. "
            "O HTML deve ser limpo e profissional, sem CSS inline complexo."
        )

        user_prompt = (
            f"Categoria: {category}\n"
            f"Descrição do template desejado: {description}"
        )

        result = llm_service.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=2000,
        )

        import json
        # Tentar extrair JSON da resposta
        content = result.get('content', '')
        # Remover blocos markdown se presentes
        content = re.sub(r'^```(?:json)?\s*', '', content.strip())
        content = re.sub(r'\s*```$', '', content.strip())

        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            return Response(
                {'error': 'Erro ao processar resposta da IA. Tente novamente.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response({
            'name': data.get('name', ''),
            'subject': data.get('subject', ''),
            'body_html': data.get('body_html', ''),
            'variables': data.get('variables', []),
        })

    except Exception as e:
        logger.error(f"Erro ao gerar template com IA: {e}")
        return Response(
            {'error': 'Erro ao gerar template com IA. Verifique a configuração do provedor LLM.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
