"""
PDF Service - Conversão de Markdown para PDF.

Utiliza WeasyPrint para gerar PDFs profissionais a partir de Markdown.
Suporta personalização por blueprint (logo, cores, cabeçalho/rodapé).
"""
import logging
from typing import Optional, Dict, Any
import markdown
from io import BytesIO
import base64

from ..utils import normalize_subsection_breaks

logger = logging.getLogger(__name__)


class PDFService:
    """
    Serviço para conversão de Markdown para PDF.

    Utiliza:
    - markdown: Para converter MD -> HTML
    - weasyprint: Para converter HTML -> PDF

    Uso:
        >>> pdf_service = PDFService()
        >>> pdf_bytes = pdf_service.markdown_to_pdf(markdown_content, "Título")
        >>> with open("output.pdf", "wb") as f:
        ...     f.write(pdf_bytes)
    """

    # CSS para estilização do PDF (estilo profissional para documentos oficiais)
    DEFAULT_CSS = """
    @page {
        size: A4;
        margin: 2.5cm 2cm 2.5cm 3cm;
        @top-center {
            content: none;
        }
        @bottom-center {
            content: "Página " counter(page) " de " counter(pages);
            font-size: 9pt;
            color: #666;
        }
    }

    body {
        font-family: 'Times New Roman', Times, serif;
        font-size: 12pt;
        line-height: 1.5;
        color: #000000;
        text-align: justify;
    }

    h1 {
        font-size: 16pt;
        font-weight: bold;
        text-align: center;
        color: #000000;
        margin-top: 0;
        margin-bottom: 24pt;
        padding-bottom: 12pt;
    }

    h2 {
        font-size: 14pt;
        font-weight: bold;
        color: #000000;
        margin-top: 24pt;
        margin-bottom: 12pt;
        page-break-after: avoid;
    }

    h3 {
        font-size: 12pt;
        font-weight: bold;
        color: #000000;
        margin-top: 18pt;
        margin-bottom: 6pt;
    }

    p {
        margin-bottom: 12pt;
        text-indent: 2cm;
    }

    p:first-of-type {
        text-indent: 0;
    }

    ul, ol {
        margin-left: 1cm;
        margin-bottom: 12pt;
    }

    li {
        margin-bottom: 6pt;
    }

    table {
        width: 100%;
        border-collapse: collapse;
        margin: 12pt 0;
        font-size: 10pt;
    }

    th {
        background-color: #d3d3d3;
        color: #000000;
        padding: 8pt;
        text-align: left;
        font-weight: bold;
        border: 1px solid #000000;
    }

    td {
        border: 1px solid #000000;
        padding: 8pt;
        color: #000000;
    }

    blockquote {
        margin: 12pt 0;
        padding: 12pt;
        background-color: #f7fafc;
        border-left: 4px solid #333;
        font-style: italic;
    }

    code {
        font-family: 'Courier New', monospace;
        font-size: 10pt;
        background-color: #f7fafc;
        padding: 2pt 4pt;
    }

    pre {
        background-color: #f7fafc;
        padding: 12pt;
        overflow-x: auto;
        font-size: 10pt;
    }

    hr {
        display: none;
    }

    strong {
        font-weight: bold;
    }

    em {
        font-style: italic;
    }

    /* Cabeçalho do documento */
    .document-header {
        text-align: center;
        margin-bottom: 24pt;
    }

    .document-header img {
        max-width: 150px;
        margin-bottom: 12pt;
    }

    /* Assinaturas */
    .signature-block {
        margin-top: 48pt;
        page-break-inside: avoid;
    }

    .signature-line {
        border-top: 1px solid #333;
        width: 60%;
        margin: 36pt auto 6pt auto;
    }

    .signature-name {
        text-align: center;
        font-weight: bold;
    }

    .signature-role {
        text-align: center;
        font-size: 10pt;
        color: #666;
    }

    /* Avisos e notas */
    .note {
        background-color: #f7fafc;
        border-left: 4px solid #333;
        padding: 12pt;
        margin: 12pt 0;
    }

    .warning {
        background-color: #fffaf0;
        border-left: 4px solid #dd6b20;
        padding: 12pt;
        margin: 12pt 0;
    }

    /* Rodapé */
    .document-footer {
        margin-top: 24pt;
        font-size: 9pt;
        color: #666;
        text-align: center;
        font-style: italic;
    }
    """

    def __init__(self, custom_css: Optional[str] = None):
        """
        Inicializa o serviço.

        Args:
            custom_css: CSS customizado (opcional)
        """
        self.css = custom_css or self.DEFAULT_CSS

    def markdown_to_pdf(
        self,
        markdown_content: str,
        title: Optional[str] = None,
        header_html: Optional[str] = None,
        footer_html: Optional[str] = None
    ) -> Optional[bytes]:
        """
        Converte Markdown para PDF.

        Args:
            markdown_content: Conteúdo em Markdown
            title: Título do documento (opcional)
            header_html: HTML customizado para cabeçalho (opcional)
            footer_html: HTML customizado para rodapé (opcional)

        Returns:
            Bytes do PDF ou None se falhar
        """
        try:
            from weasyprint import HTML, CSS

            markdown_content = normalize_subsection_breaks(markdown_content)

            # Converte Markdown para HTML
            html_content = self._markdown_to_html(
                markdown_content,
                title,
                header_html,
                footer_html
            )

            # Gera PDF
            pdf_buffer = BytesIO()
            HTML(string=html_content).write_pdf(
                pdf_buffer,
                stylesheets=[CSS(string=self.css)]
            )

            pdf_bytes = pdf_buffer.getvalue()
            logger.info(f"PDF gerado com sucesso: {len(pdf_bytes)} bytes")

            return pdf_bytes

        except ImportError:
            raise RuntimeError(
                "WeasyPrint não instalado. "
                "Instale com: pip install weasyprint"
            )
        except Exception as e:
            raise RuntimeError(f"Erro ao gerar PDF: {str(e)}") from e

    def _markdown_to_html(
        self,
        markdown_content: str,
        title: Optional[str] = None,
        header_html: Optional[str] = None,
        footer_html: Optional[str] = None
    ) -> str:
        """
        Converte Markdown para HTML estruturado.

        Args:
            markdown_content: Conteúdo Markdown
            title: Título do documento
            header_html: HTML do cabeçalho
            footer_html: HTML do rodapé

        Returns:
            HTML completo
        """
        # Extensões do markdown para tabelas, etc
        md = markdown.Markdown(
            extensions=[
                'tables',
                'fenced_code',
                'toc',
            ]
        )

        # Converte markdown para HTML
        body_html = md.convert(markdown_content)

        # Monta documento HTML completo
        html = f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <title>{title or 'Documento Jurídico'}</title>
        </head>
        <body>
            {header_html or ''}
            {body_html}
            {footer_html or ''}
        </body>
        </html>
        """

        return html

    def html_to_pdf(self, html_content: str) -> Optional[bytes]:
        """
        Converte HTML diretamente para PDF.

        Args:
            html_content: HTML completo

        Returns:
            Bytes do PDF ou None
        """
        try:
            from weasyprint import HTML, CSS

            pdf_buffer = BytesIO()
            HTML(string=html_content).write_pdf(
                pdf_buffer,
                stylesheets=[CSS(string=self.css)]
            )

            return pdf_buffer.getvalue()

        except ImportError:
            logger.error("WeasyPrint não instalado")
            return None
        except Exception as e:
            logger.error(f"Erro ao gerar PDF: {str(e)}")
            return None

    def generate_etp_pdf(
        self,
        markdown_content: str,
        objective: str,
        organization_name: str = "Órgão Contratante",
        logo_path: Optional[str] = None
    ) -> Optional[bytes]:
        """
        Gera PDF de ETP com formatação oficial.

        Args:
            markdown_content: Conteúdo do ETP em Markdown
            objective: Objetivo da contratação
            organization_name: Nome da organização
            logo_path: Caminho para logo (opcional)

        Returns:
            Bytes do PDF
        """
        # Cabeçalho oficial
        header_html = f"""
        <div class="document-header">
            <h1>ESTUDO TÉCNICO PRELIMINAR</h1>
            <p><strong>Órgão:</strong> {organization_name}</p>
        </div>
        """

        # Rodapé
        footer_html = """
        <div class="document-footer">
            <p>Lei 14.133/2021</p>
        </div>
        """

        return self.markdown_to_pdf(
            markdown_content=markdown_content,
            title=f"Estudo Técnico Preliminar - {objective[:50]}",
            header_html=header_html,
            footer_html=footer_html
        )

    def generate_pdf_from_blueprint(
        self,
        markdown_content: str,
        objective: str,
        blueprint_config: Dict[str, Any]
    ) -> Optional[bytes]:
        """
        Gera PDF com personalização baseada no blueprint.

        Args:
            markdown_content: Conteúdo em Markdown
            objective: Objetivo da contratação
            blueprint_config: Configurações do blueprint (todos os campos do modelo)

        Returns:
            Bytes do PDF
        """
        markdown_content = normalize_subsection_breaks(markdown_content)
        try:
            from weasyprint import HTML, CSS

            # ========================================
            # EXTRAIR CONFIGURAÇÕES DO BLUEPRINT
            # ========================================
            # Organização
            org_name = blueprint_config.get(
                'organization_name', 'Órgão Público')
            org_acronym = blueprint_config.get('organization_acronym', '')
            logo_url = blueprint_config.get('logo_url')

            # Cabeçalho/Rodapé
            header_text = blueprint_config.get(
                'header_text', 'ESTUDO TÉCNICO PRELIMINAR')
            header_subtitle = blueprint_config.get('header_subtitle', '')
            footer_text = blueprint_config.get('footer_text', '')
            legal_basis = blueprint_config.get('legal_basis', '')

            # Cores
            primary_color = blueprint_config.get('primary_color', '#7030A0')
            secondary_color = blueprint_config.get(
                'secondary_color', '#5B2EE0')
            custom_css = blueprint_config.get('custom_css', '')

            # Página de Rosto
            cover_enabled = blueprint_config.get('cover_page_enabled', True)
            cover_logo_url = blueprint_config.get('cover_logo_url') or logo_url
            cover_title = blueprint_config.get('cover_title', header_text)
            cover_subtitle = blueprint_config.get('cover_subtitle', '')
            cover_org_text = blueprint_config.get(
                'cover_organization_text', org_name)
            cover_footer = blueprint_config.get('cover_footer_text', '')
            cover_bg_color = blueprint_config.get(
                'cover_background_color', '#FFFFFF')

            # Tipografia
            font_family = blueprint_config.get(
                'pdf_font_family', 'Times New Roman')
            font_size = blueprint_config.get('pdf_font_size', '12pt')
            line_height = blueprint_config.get('pdf_line_height', '1.5')
            text_align = blueprint_config.get('pdf_text_align', 'justify')
            paragraph_indent = blueprint_config.get(
                'pdf_paragraph_indent', '2cm')
            paragraph_spacing = blueprint_config.get(
                'pdf_paragraph_spacing', '12pt')

            # Margens
            margin_top = blueprint_config.get('pdf_page_margin_top', '2.5cm')
            margin_bottom = blueprint_config.get(
                'pdf_page_margin_bottom', '2.5cm')
            margin_left = blueprint_config.get('pdf_page_margin_left', '3cm')
            margin_right = blueprint_config.get('pdf_page_margin_right', '2cm')

            # ========================================
            # GERAR CSS DINÂMICO
            # ========================================
            dynamic_css = self._generate_dynamic_css(
                primary_color=primary_color,
                secondary_color=secondary_color,
                header_text=header_text,
                font_family=font_family,
                font_size=font_size,
                line_height=line_height,
                text_align=text_align,
                paragraph_indent=paragraph_indent,
                paragraph_spacing=paragraph_spacing,
                margin_top=margin_top,
                margin_bottom=margin_bottom,
                margin_left=margin_left,
                margin_right=margin_right
            )

            # CSS final = base + dinâmico + customizado
            final_css = self.DEFAULT_CSS + "\n" + dynamic_css
            if custom_css:
                final_css += "\n" + custom_css

            # ========================================
            # MONTAR PÁGINA DE ROSTO (se habilitada)
            # ========================================
            cover_html = ""
            if cover_enabled:
                cover_html = self._generate_cover_page(
                    logo_url=cover_logo_url,
                    organization_text=cover_org_text,
                    title=cover_title,
                    subtitle=cover_subtitle,
                    objective=objective,
                    footer_text=cover_footer,
                    background_color=cover_bg_color,
                    primary_color=primary_color,
                    secondary_color=secondary_color
                )

            # ========================================
            # MONTAR CABEÇALHO DO DOCUMENTO
            # (skip quando capa habilitada - info já está na capa)
            # ========================================
            header_html = ""
            if not cover_enabled:
                logo_html = ""
                if logo_url:
                    logo_html = f'<img src="{logo_url}" alt="Logo" class="document-logo">'

                subtitle_html = f'<div class="header-subtitle">{header_subtitle}</div>' if header_subtitle else ''

                header_html = f"""
                <div class="document-header">
                    {logo_html}
                    <div class="header-org-name">{org_name}</div>
                    {f'<div class="header-acronym">{org_acronym}</div>' if org_acronym else ''}
                    {subtitle_html}
                    <h1>{header_text}</h1>
                </div>
                """

            # ========================================
            # MONTAR RODAPÉ DO DOCUMENTO
            # ========================================
            footer_inner = ''
            if footer_text:
                footer_inner += f'<p>{footer_text}</p>'
            if legal_basis:
                footer_inner += f'<p class="footer-legal">{legal_basis}</p>'
            footer_html = f'<div class="document-footer">{footer_inner}</div>' if footer_inner else ''

            # ========================================
            # GERAR HTML COMPLETO
            # ========================================
            html_content = self._markdown_to_html_with_cover(
                markdown_content=markdown_content,
                title=f"{header_text} - {objective[:50]}",
                cover_html=cover_html,
                header_html=header_html,
                footer_html=footer_html
            )

            # ========================================
            # GERAR PDF
            # ========================================
            pdf_buffer = BytesIO()
            HTML(string=html_content).write_pdf(
                pdf_buffer,
                stylesheets=[CSS(string=final_css)]
            )

            pdf_bytes = pdf_buffer.getvalue()
            logger.info(f"PDF personalizado gerado: {len(pdf_bytes)} bytes")

            return pdf_bytes

        except Exception as e:
            logger.error(f"Erro ao gerar PDF personalizado: {str(e)}")
            return None

    def _generate_cover_page(
        self,
        logo_url: Optional[str],
        organization_text: str,
        title: str,
        subtitle: str,
        objective: str,
        footer_text: str,
        background_color: str,
        primary_color: str,
        secondary_color: str
    ) -> str:
        """
        Gera HTML da página de rosto.

        Args:
            logo_url: URL da logo
            organization_text: Texto da organização (pode ter quebras de linha)
            title: Título principal
            subtitle: Subtítulo (ex: Lei 14.133/2021)
            objective: Objetivo da contratação
            footer_text: Texto do rodapé (ex: Local - Ano)
            background_color: Cor de fundo
            primary_color: Cor primária
            secondary_color: Cor secundária

        Returns:
            HTML da página de rosto
        """
        logo_html = f'<img src="{logo_url}" alt="Logo" class="cover-logo">' if logo_url else ''

        # Processar texto da organização (quebras de linha)
        org_lines = organization_text.replace('\r\n', '\n').split('\n')
        org_html = '<br>'.join(line.strip()
                               for line in org_lines if line.strip())

        return f"""
        <div class="cover-page" style="background-color: {background_color};">
            <div class="cover-content">
                {logo_html}

                <div class="cover-organization" style="color: #000000;">
                    {org_html}
                </div>

                <div class="cover-divider" style="border-color: #000000;"></div>

                <h1 class="cover-title" style="color: #000000;">
                    {title}
                </h1>

                {f'<div class="cover-subtitle" style="color: #000000;">{subtitle}</div>' if subtitle else ''}

                <div class="cover-divider" style="border-color: #000000;"></div>

                {f'<div class="cover-footer">{footer_text}</div>' if footer_text else ''}
            </div>
        </div>
        """

    def _markdown_to_html_with_cover(
        self,
        markdown_content: str,
        title: str,
        cover_html: str,
        header_html: str,
        footer_html: str
    ) -> str:
        """
        Converte Markdown para HTML com página de rosto.

        Args:
            markdown_content: Conteúdo Markdown
            title: Título do documento
            cover_html: HTML da página de rosto
            header_html: HTML do cabeçalho
            footer_html: HTML do rodapé

        Returns:
            HTML completo
        """
        md = markdown.Markdown(
            extensions=[
                'tables',
                'fenced_code',
                'toc',
            ]
        )

        body_html = md.convert(markdown_content)

        return f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <title>{title}</title>
        </head>
        <body>
            {cover_html}
            {header_html}
            {body_html}
            {footer_html}
        </body>
        </html>
        """

    def _generate_dynamic_css(
        self,
        primary_color: str = "#7030A0",
        secondary_color: str = "#5B2EE0",
        header_text: str = "ESTUDO TÉCNICO PRELIMINAR",
        font_family: str = "Times New Roman",
        font_size: str = "12pt",
        line_height: str = "1.5",
        text_align: str = "justify",
        paragraph_indent: str = "2cm",
        paragraph_spacing: str = "12pt",
        margin_top: str = "2.5cm",
        margin_bottom: str = "2.5cm",
        margin_left: str = "3cm",
        margin_right: str = "2cm"
    ) -> str:
        """
        Gera CSS dinâmico baseado nas configurações do blueprint.

        Args:
            primary_color: Cor primária (hex)
            secondary_color: Cor secundária (hex)
            header_text: Texto do cabeçalho da página
            font_family: Família de fonte
            font_size: Tamanho da fonte
            line_height: Altura da linha
            text_align: Alinhamento do texto
            paragraph_indent: Recuo do parágrafo
            paragraph_spacing: Espaçamento entre parágrafos
            margin_*: Margens da página

        Returns:
            String CSS
        """
        return f"""
        /* ========================================
         * CSS Dinâmico - Configurações do Blueprint
         * ======================================== */

        /* Configuração da Página */
        @page {{
            size: A4;
            margin: {margin_top} {margin_right} {margin_bottom} {margin_left};
            @top-center {{
                content: "{header_text}";
                font-size: 9pt;
                color: #666;
            }}
            @bottom-center {{
                content: "Página " counter(page) " de " counter(pages);
                font-size: 9pt;
                color: #666;
            }}
        }}

        /* Página de Rosto - sem cabeçalho/rodapé */
        @page cover {{
            margin: 0;
            @top-center {{ content: none; }}
            @bottom-center {{ content: none; }}
        }}

        /* Tipografia do Corpo */
        body {{
            font-family: '{font_family}', serif;
            font-size: {font_size};
            line-height: {line_height};
            text-align: {text_align};
        }}

        p {{
            margin-bottom: {paragraph_spacing};
            text-indent: {paragraph_indent};
        }}

        p:first-of-type {{
            text-indent: 0;
        }}

        /* Cores do Documento — texto sempre preto (padrão judiciário) */
        h1 {{
            color: #000000;
        }}

        h2 {{
            color: #000000;
            background-color: #e8e8e8;
        }}

        th {{
            background-color: #e8e8e8;
            color: #000000;
        }}

        blockquote {{
            border-left-color: #333333;
        }}

        .note {{
            border-left-color: #333333;
        }}

        /* ========================================
         * PÁGINA DE ROSTO
         * ======================================== */
        .cover-page {{
            page: cover;
            page-break-after: always;
            width: 100%;
            text-align: center;
            padding: 4cm 3cm 3cm 3cm;
            box-sizing: border-box;
        }}

        .cover-content {{
            width: 100%;
        }}

        .cover-logo {{
            max-width: 180px;
            max-height: 120px;
            margin-bottom: 24pt;
        }}

        .cover-organization {{
            font-size: 14pt;
            font-weight: bold;
            line-height: 1.4;
            margin-bottom: 36pt;
            text-transform: uppercase;
        }}

        .cover-divider {{
            width: 60%;
            height: 0;
            border-top: 2px solid;
            margin: 24pt 0;
        }}

        .cover-title {{
            font-size: 24pt;
            font-weight: bold;
            margin: 24pt 0 12pt 0;
            text-transform: uppercase;
            letter-spacing: 2pt;
        }}

        .cover-subtitle {{
            font-size: 14pt;
            font-style: italic;
            margin-bottom: 24pt;
        }}

        .cover-objective {{
            font-size: 12pt;
            max-width: 80%;
            margin: 36pt auto;
            line-height: 1.6;
        }}

        .cover-footer {{
            position: absolute;
            bottom: 3cm;
            font-size: 12pt;
            color: #666;
        }}

        /* ========================================
         * CABEÇALHO DO DOCUMENTO
         * ======================================== */
        .document-header {{
            text-align: center;
            margin-bottom: 24pt;
            padding-bottom: 12pt;
            /* border-bottom: 2px solid {primary_color}; */
        }}

        .document-logo {{
            max-width: 120px;
            max-height: 80px;
            margin-bottom: 12pt;
        }}

        .header-org-name {{
            font-size: 14pt;
            font-weight: bold;
            color: #000000;
            margin-bottom: 4pt;
        }}

        .header-acronym {{
            font-size: 11pt;
            color: #000000;
            margin-bottom: 12pt;
        }}

        .header-subtitle {{
            font-size: 11pt;
            color: #000000;
            margin-bottom: 8pt;
        }}

        .header-objective {{
            font-size: 11pt;
            margin-top: 12pt;
        }}

        /* ========================================
         * RODAPÉ DO DOCUMENTO
         * ======================================== */
        .document-footer {{
            margin-top: 24pt;
            padding-top: 12pt;
            border-top: 1px solid #cbd5e0;
            font-size: 9pt;
            color: #666;
            text-align: center;
        }}

        .footer-legal {{
            font-size: 8pt;
            color: #888;
            margin-top: 4pt;
        }}
        """
