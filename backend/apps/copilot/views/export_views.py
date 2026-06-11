"""
export_views - Exportação de respostas do Copilot para DOCX / PDF / ODT.
"""
import json
import logging

from django.http import HttpResponse, JsonResponse
from rest_framework.views import APIView

from apps.intelligent_assistant.views._helpers import _authenticate_request
from ..serializers import ExportRequestSerializer
from ..services import session_service

logger = logging.getLogger(__name__)

_MIME_MAP = {
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'odt': 'application/vnd.oasis.opendocument.text',
    'pdf': 'application/pdf',
}

_EXT_MAP = {
    'docx': 'docx',
    'odt': 'odt',
    'pdf': 'pdf',
}


class ExportView(APIView):
    """
    POST /api/v1/copilot/export/

    Body: { text: "...", format: "docx|pdf|odt", title: "..." }
    Retorna bytes do documento gerado.
    """

    authentication_classes = []
    permission_classes = []

    def post(self, request):
        user, error = _authenticate_request(request)
        if error:
            return error

        serializer = ExportRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return JsonResponse({'error': serializer.errors}, status=400)

        text: str = serializer.validated_data['text']
        fmt: str = serializer.validated_data['format']
        title: str = serializer.validated_data['title']

        # Configuração mínima de blueprint para os serviços de exportação
        blueprint_config = {
            'organization_name': 'Verus.AI',
            'organization_acronym': '',
            'logo_url': None,
            'header_text': title.upper(),
            'header_subtitle': '',
            'footer_text': '',
            'legal_basis': '',
            'primary_color': '#7030A0',
            'secondary_color': '#5B2EE0',
            'custom_css': '',
            'cover_page_enabled': False,
            'cover_logo_url': None,
            'cover_title': title.upper(),
            'cover_subtitle': '',
            'cover_organization_text': '',
            'cover_footer_text': '',
            'cover_background_color': '#FFFFFF',
            'pdf_font_family': 'Times New Roman',
            'pdf_font_size': '12pt',
            'pdf_line_height': '1.5',
            'pdf_text_align': 'justify',
            'pdf_paragraph_indent': '1.5cm',
            'pdf_paragraph_spacing': '12pt',
            'pdf_page_margin_top': '2.5cm',
            'pdf_page_margin_bottom': '2.5cm',
            'pdf_page_margin_left': '3cm',
            'pdf_page_margin_right': '2cm',
        }

        try:
            file_bytes = _generate(text, title, fmt, blueprint_config)
        except Exception as e:
            logger.exception(f'[copilot] Erro ao exportar: {e}')
            return JsonResponse({'error': f'Erro ao gerar documento: {str(e)}'}, status=500)

        safe_title = title.replace(' ', '_')[:50]
        filename = f'copilot_{safe_title}.{_EXT_MAP[fmt]}'

        response = HttpResponse(file_bytes, content_type=_MIME_MAP[fmt])
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


class ExportSessionView(APIView):
    """
    POST /api/v1/copilot/export-session/

    Exporta sessão completa do histórico.
    Body: { session_id: "uuid", format: "docx|pdf|odt" }
    """

    authentication_classes = []
    permission_classes = []

    def post(self, request):
        user, error = _authenticate_request(request)
        if error:
            return error

        try:
            body = json.loads(request.body) if request.body else {}
        except (json.JSONDecodeError, Exception):
            body = {}

        session_id = body.get('session_id')
        fmt = body.get('format', 'docx')

        if not session_id:
            return JsonResponse({'error': 'session_id é obrigatório'}, status=400)

        # Obter histórico da sessão
        history = session_service.get_history(user.id, str(session_id))
        if history is None:
            return JsonResponse({'error': 'Sessão não encontrada ou expirada'}, status=404)

        # Format messages as markdown
        text_parts = ['# Conversa Copilot\n\n']
        for msg in history:
            role = 'Usuário' if msg.get('role') == 'user' else 'Copilot'
            content = msg.get('content', '')
            text_parts.append(f'## {role}\n\n{content}\n\n---\n\n')

        text = ''.join(text_parts)
        title = f'Conversa {session_id[:8]}'

        blueprint_config = {
            'organization_name': 'Verus.AI',
            'organization_acronym': '',
            'logo_url': None,
            'header_text': 'COPILOT JURÍDICO',
            'header_subtitle': 'Exportação de Conversa',
            'footer_text': '',
            'legal_basis': '',
            'primary_color': '#7030A0',
            'secondary_color': '#5B2EE0',
            'custom_css': '',
            'cover_page_enabled': True,
            'cover_logo_url': None,
            'cover_title': 'COPILOT JURÍDICO',
            'cover_subtitle': f'Conversa de {session_id[:8]}',
            'cover_organization_text': 'Verus.AI - Sistema Jurídico',
            'cover_footer_text': '',
            'cover_background_color': '#FFFFFF',
            'pdf_font_family': 'Times New Roman',
            'pdf_font_size': '12pt',
            'pdf_line_height': '1.5',
            'pdf_text_align': 'justify',
            'pdf_paragraph_indent': '1.5cm',
            'pdf_paragraph_spacing': '12pt',
            'pdf_page_margin_top': '2.5cm',
            'pdf_page_margin_bottom': '2.5cm',
            'pdf_page_margin_left': '3cm',
            'pdf_page_margin_right': '2cm',
        }

        try:
            file_bytes = _generate(text, title, fmt, blueprint_config)
        except Exception as e:
            logger.exception(f'[copilot] Erro ao exportar sessão: {e}')
            return JsonResponse({'error': f'Erro ao gerar documento: {str(e)}'}, status=500)

        safe_id = session_id.replace('-', '_')[:8]
        filename = f'copilot_conversa_{safe_id}.{_EXT_MAP[fmt]}'

        response = HttpResponse(file_bytes, content_type=_MIME_MAP[fmt])
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


def _generate(text: str, title: str, fmt: str, config: dict) -> bytes:
    if fmt == 'pdf':
        from apps.intelligent_assistant.services.pdf_service import PDFService
        service = PDFService()
        return service.markdown_to_pdf(
            markdown_content=text,
            title=title,
        )

    from apps.intelligent_assistant.services.document_export_service import DocumentExportService
    service = DocumentExportService()

    if fmt == 'docx':
        return service.generate_docx(
            markdown_content=text,
            objective=title,
            blueprint_config=config,
        )
    else:  # odt
        return service.generate_odt(
            markdown_content=text,
            objective=title,
            blueprint_config=config,
        )
