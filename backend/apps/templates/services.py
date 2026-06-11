"""
Serviços para renderização de templates
"""
import re
from typing import Dict, Any, List
from django.core.files.uploadedfile import UploadedFile


class TemplateRenderService:
    """
    Serviço para renderização inteligente de templates SEM lógica if/else.

    Regras:
    1. Placeholders vazios → linha removida automaticamente
    2. Placeholders preenchidos → linha mantida com valor
    3. Preserva formatação original
    """

    @staticmethod
    def extract_placeholders(content: str) -> List[str]:
        """
        Extrai todos os placeholders {{field}} do conteúdo

        Args:
            content: Conteúdo do template (texto ou HTML)

        Returns:
            Lista de IDs de placeholders encontrados
        """
        placeholders = re.findall(r'\{\{(\w+)\}\}', content)
        return list(set(placeholders))  # Remove duplicatas

    @staticmethod
    def render_smart(content: str, data: Dict[str, Any]) -> str:
        """
        Renderiza template removendo linhas vazias automaticamente.
        NENHUMA lógica if/else é necessária no template!

        Args:
            content: Conteúdo do template com placeholders {{field}}
            data: Dicionário com valores dos campos

        Returns:
            Conteúdo renderizado (linhas vazias removidas)

        Exemplo:
            Template:
                Nome: {{nome}}
                Email: {{email}}
                Telefone: {{telefone}}

            Data: {'nome': 'João', 'email': '', 'telefone': '123'}

            Resultado:
                Nome: João
                Telefone: 123
                (linha do email foi removida pois estava vazia)
        """
        lines = content.split('\n')
        result = []

        for line in lines:
            # Extrai placeholders da linha
            placeholders = re.findall(r'\{\{(\w+)\}\}', line)

            # Se a linha tem placeholders
            if placeholders:
                # Verifica se todos os placeholders da linha estão vazios
                all_empty = all(
                    not str(data.get(p, '')).strip()
                    for p in placeholders
                )

                # Se todos vazios, pula linha inteira
                if all_empty:
                    continue

            # Substitui placeholders pelos valores
            rendered_line = line
            for placeholder in placeholders:
                value = str(data.get(placeholder, ''))
                rendered_line = rendered_line.replace(
                    f'{{{{{placeholder}}}}}',
                    value
                )

            result.append(rendered_line)

        return '\n'.join(result)

    @staticmethod
    def render_html_smart(html_content: str, data: Dict[str, Any]) -> str:
        """
        Renderiza templates HTML com lógica inteligente.
        Remove parágrafos/divs inteiros se todos os placeholders estiverem vazios.

        Args:
            html_content: HTML com placeholders
            data: Dicionário com valores

        Returns:
            HTML renderizado (elementos vazios removidos)
        """
        # Para HTML, vamos processar elemento por elemento
        # Identifica blocos <p>, <div>, <li>, etc com placeholders

        # Regex para capturar elementos HTML com placeholders
        pattern = r'(<(?:p|div|li|td|th|h[1-6])[^>]*>)(.*?)(<\/(?:p|div|li|td|th|h[1-6])>)'

        def replace_element(match):
            opening_tag = match.group(1)
            content = match.group(2)
            closing_tag = match.group(3)

            # Extrai placeholders do conteúdo
            placeholders = re.findall(r'\{\{(\w+)\}\}', content)

            if placeholders:
                # Verifica se todos estão vazios
                all_empty = all(
                    not str(data.get(p, '')).strip()
                    for p in placeholders
                )

                if all_empty:
                    return ''  # Remove elemento inteiro

            # Substitui placeholders
            rendered_content = content
            for placeholder in placeholders:
                value = str(data.get(placeholder, ''))
                rendered_content = rendered_content.replace(
                    f'{{{{{placeholder}}}}}',
                    value
                )

            return f'{opening_tag}{rendered_content}{closing_tag}'

        # Processa elementos HTML
        result = re.sub(pattern, replace_element, html_content, flags=re.DOTALL)

        # Substitui placeholders restantes (fora de elementos)
        for placeholder in re.findall(r'\{\{(\w+)\}\}', result):
            value = str(data.get(placeholder, ''))
            result = result.replace(f'{{{{{placeholder}}}}}', value)

        return result

    @staticmethod
    def extract_text_from_docx(file_path: str) -> str:
        """
        Extrai conteúdo de arquivo .docx e converte para HTML preservando formatação.

        Preserva:
        - Negrito, itálico, sublinhado
        - Títulos e parágrafos
        - Listas (numeradas e com marcadores)
        - Tabelas
        - Imagens (convertidas para base64 inline)
        - Espaçamento e indentação

        Args:
            file_path: Caminho para o arquivo .docx

        Returns:
            HTML com formatação preservada

        Note:
            Requer biblioteca mammoth instalada
        """
        try:
            import mammoth
        except ImportError:
            raise ImportError(
                "Biblioteca mammoth não instalada. "
                "Execute: pip install mammoth"
            )

        import logging
        logger = logging.getLogger(__name__)

        try:
            # Abre e converte .docx para HTML
            with open(file_path, 'rb') as docx_file:
                result = mammoth.convert_to_html(docx_file)
                html = result.value

                # Log de avisos (caso haja elementos não suportados)
                if result.messages:
                    for message in result.messages:
                        logger.warning(f'Mammoth conversion warning: {message}')

                return html

        except Exception as e:
            logger.error(f'Erro ao converter .docx para HTML: {e}')
            # Fallback: tenta extrair apenas texto simples
            try:
                from docx import Document
                doc = Document(file_path)
                paragraphs = [para.text.strip() for para in doc.paragraphs if para.text.strip()]
                return '<br>'.join(paragraphs)
            except Exception as e:
                logger.warning(f"Fallback de extração de texto .docx também falhou: {e}")
                return ''

    @staticmethod
    def validate_compatibility(
        template_placeholders: List[str],
        form_fields: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Valida compatibilidade entre template e formulário

        Args:
            template_placeholders: Lista de placeholders do template
            form_fields: Lista de campos do formulário (dict com 'id')

        Returns:
            Dict com:
                - compatible: bool
                - missing_fields: List[str] (placeholders sem campo correspondente)
                - extra_fields: List[str] (campos sem placeholder correspondente)
        """
        template_set = set(template_placeholders)
        form_set = set(field['id'] for field in form_fields)

        missing = template_set - form_set  # Placeholders que não têm campo
        extra = form_set - template_set    # Campos que não têm placeholder

        return {
            'compatible': len(missing) == 0,
            'missing_fields': list(missing),
            'extra_fields': list(extra),
            'match_count': len(template_set & form_set),
            'total_placeholders': len(template_set),
            'total_form_fields': len(form_set),
        }


# Instância global do serviço (singleton)
template_service = TemplateRenderService()
