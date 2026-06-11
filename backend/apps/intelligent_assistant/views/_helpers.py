"""
Funções utilitárias internas compartilhadas entre os módulos de views.
"""
import json
import logging

from django.http import JsonResponse
from rest_framework_simplejwt.authentication import JWTAuthentication

from ..models import DocumentBlueprint

logger = logging.getLogger(__name__)


def _format_sse_event(event_type: str, data: dict) -> str:
    """Formata um evento SSE com event dentro do JSON para compatibilidade com frontend."""
    # Incluir event dentro do data para o frontend processar corretamente
    data_with_event = {'event': event_type, **data}
    json_data = json.dumps(data_with_event, ensure_ascii=False)
    return f"data: {json_data}\n\n"


def _format_section_fields_content(section_fields: list, field_values: dict) -> str:
    """
    Formata os dados dos campos estruturados em texto para incluir no documento.

    Args:
        section_fields: Lista de definições de campos da seção (do Blueprint)
        field_values: Valores preenchidos pelo usuário

    Returns:
        Texto formatado para a seção
    """
    if field_values is None:
        field_values = {}

    lines = []

    # Quando ha um unico campo simples (nao-array), o label da SECAO ja
    # identifica o conteudo - prefixar "**Label:** valor" fica redundante.
    # Multiplos campos preservam o label como cabecalho.
    simple_fields_count = sum(
        1 for f in section_fields if f.get('type') != 'array'
    )
    omit_labels_for_simple = simple_fields_count == 1

    for field in section_fields:
        field_name = field.get('name', '')
        field_label = field.get('label', field_name)
        field_type = field.get('type', 'text')
        value = field_values.get(field_name, '')

        if field_type == 'array':
            # Campo de array (ex: Equipe de Planejamento)
            # Gera tabela HTML estilizada para renderização correta no frontend e exportação
            item_fields = field.get('item_fields', [])
            items = value if isinstance(value, list) else []

            # Sempre gera a tabela - com dados ou vazia (só cabeçalho)
            if True:
                # Montar headers a partir dos item_fields
                header_labels = [
                    if_def.get('label', if_def.get('name', ''))
                    for if_def in item_fields
                ]

                table_html = (
                    '<table border="1" cellpadding="8" cellspacing="0" '
                    'width="100%" style="border-collapse: collapse; font-size: 14px;">'
                )
                # Header row
                table_html += '<thead><tr style="background-color: #e0e0e0;">'
                for label in header_labels:
                    table_html += (
                        f'<th style="padding: 8px; font-weight: bold; '
                        f'text-align: center;">{label}</th>'
                    )
                table_html += '</tr></thead>'

                # Data rows
                table_html += '<tbody>'
                for item in items:
                    table_html += '<tr>'
                    for if_def in item_fields:
                        fname = if_def.get('name', '')
                        fvalue = item.get(fname, '-') or '-'
                        table_html += f'<td style="padding: 8px; text-align: center;">{fvalue}</td>'
                    table_html += '</tr>'
                table_html += '</tbody></table>'

                lines.append(table_html)
                lines.append("")
        else:
            # Campo simples
            if value:
                if omit_labels_for_simple:
                    lines.append(value)
                else:
                    lines.append(f"**{field_label}:** {value}")

    return "\n".join(lines)


def _authenticate_request(request):
    """
    Autentica request usando JWT.
    Retorna (user, error_response).
    """
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')

    if not auth_header:
        return None, JsonResponse({'error': 'Token de autenticação não fornecido'}, status=401)

    try:
        # Extrair token do header
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return None, JsonResponse({'error': 'Formato de token inválido'}, status=401)

        token = parts[1]

        # Validar token JWT
        jwt_auth = JWTAuthentication()
        validated_token = jwt_auth.get_validated_token(token)
        user = jwt_auth.get_user(validated_token)

        return user, None

    except Exception as e:
        logger.error(f"Erro de autenticação: {str(e)}")
        return None, JsonResponse({'error': 'Token inválido ou expirado'}, status=401)


def _build_blueprint_config(blueprint) -> dict:
    """
    Extrai configuração do blueprint para os serviços de exportação.
    Reutilizado por PDF, DOCX e ODT.
    """
    return {
        'organization_name': blueprint.organization_name or 'Órgão Público',
        'organization_acronym': blueprint.organization_acronym or '',
        'logo_url': blueprint.logo.url if blueprint.logo else None,
        'header_text': blueprint.document_type.name.upper() if blueprint.document_type else 'DOCUMENTO',
        'header_subtitle': blueprint.header_text or '',
        'footer_text': blueprint.footer_text or '',
        'legal_basis': blueprint.legal_basis or '',
        'primary_color': blueprint.primary_color or '#7030A0',
        'secondary_color': blueprint.secondary_color or '#5B2EE0',
        'custom_css': blueprint.custom_css or '',
        'cover_page_enabled': blueprint.cover_page_enabled,
        'cover_logo_url': blueprint.cover_logo.url if blueprint.cover_logo else None,
        'cover_title': blueprint.cover_title or (blueprint.document_type.name.upper() if blueprint.document_type else 'DOCUMENTO'),
        'cover_subtitle': blueprint.cover_subtitle or '',
        'cover_organization_text': blueprint.cover_organization_text or blueprint.organization_name or '',
        'cover_footer_text': blueprint.cover_footer_text or '',
        'cover_background_color': blueprint.cover_background_color or '#FFFFFF',
        'pdf_font_family': blueprint.pdf_font_family or 'Times New Roman',
        'pdf_font_size': blueprint.pdf_font_size or '12pt',
        'pdf_line_height': blueprint.pdf_line_height or '1.5',
        'pdf_text_align': blueprint.pdf_text_align or 'justify',
        'pdf_paragraph_indent': blueprint.pdf_paragraph_indent or '1.5cm',
        'pdf_paragraph_spacing': blueprint.pdf_paragraph_spacing or '12pt',
        'pdf_page_margin_top': blueprint.pdf_page_margin_top or '2.5cm',
        'pdf_page_margin_bottom': blueprint.pdf_page_margin_bottom or '2.5cm',
        'pdf_page_margin_left': blueprint.pdf_page_margin_left or '3cm',
        'pdf_page_margin_right': blueprint.pdf_page_margin_right or '2cm',
    }
