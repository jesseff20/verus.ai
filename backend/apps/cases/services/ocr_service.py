"""
Serviço de OCR — extração de texto de PDFs escaneados e imagens.
Usa pytesseract/Tesseract OCR e pdf2image como fallback.
"""
import logging
import tempfile
import os

logger = logging.getLogger(__name__)


class OCRService:
    """Extrai texto de PDFs escaneados e imagens de documentos."""

    SUPPORTED_FORMATS = ['pdf', 'png', 'jpg', 'jpeg', 'tiff', 'bmp']

    @staticmethod
    def extract_text(file_path: str, language: str = 'por') -> dict:
        """
        Extrai texto de arquivo usando OCR.

        Args:
            file_path: Caminho do arquivo
            language: Idioma para OCR (por = português)

        Returns:
            dict com text, pages, confidence, method
        """
        ext = file_path.rsplit('.', 1)[-1].lower() if '.' in file_path else ''

        if ext not in OCRService.SUPPORTED_FORMATS:
            return {
                'success': False,
                'error': f'Formato não suportado: {ext}. Suportados: {OCRService.SUPPORTED_FORMATS}',
                'text': '',
            }

        try:
            if ext == 'pdf':
                return OCRService._extract_from_pdf(file_path, language)
            else:
                return OCRService._extract_from_image(file_path, language)
        except ImportError as e:
            logger.warning(f"OCR dependency not installed: {e}")
            return {
                'success': False,
                'error': f'Dependência OCR não instalada: {str(e)}. Instale: pip install pytesseract pdf2image Pillow',
                'text': '',
            }
        except Exception as e:
            logger.error(f"OCR error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'text': '',
            }

    @staticmethod
    def _extract_from_pdf(file_path: str, language: str) -> dict:
        """Extrai texto de PDF — tenta texto direto primeiro, depois OCR."""
        # Try direct text extraction first (PyPDF2 / pdfplumber)
        text = ''
        try:
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                pages_text = []
                for page in pdf.pages:
                    page_text = page.extract_text() or ''
                    pages_text.append(page_text)
                text = '\n\n'.join(pages_text)

                if text.strip() and len(text.strip()) > 50:
                    return {
                        'success': True,
                        'text': text.strip(),
                        'pages': len(pages_text),
                        'method': 'text_extraction',
                        'confidence': 1.0,
                    }
        except Exception:
            logger.warning("PDF text extraction failed for %s, falling back to OCR", file_path, exc_info=True)

        # Fallback: OCR with Tesseract
        try:
            from pdf2image import convert_from_path
            import pytesseract

            images = convert_from_path(file_path, dpi=300)
            pages_text = []
            total_confidence = 0

            for i, image in enumerate(images):
                data = pytesseract.image_to_data(image, lang=language, output_type=pytesseract.Output.DICT)
                page_text = ' '.join([
                    word for word, conf in zip(data['text'], data['conf'])
                    if int(conf) > 30 and word.strip()
                ])
                pages_text.append(page_text)

                # Average confidence for this page
                confs = [int(c) for c in data['conf'] if int(c) > 0]
                if confs:
                    total_confidence += sum(confs) / len(confs)

            avg_confidence = total_confidence / len(images) if images else 0

            return {
                'success': True,
                'text': '\n\n'.join(pages_text).strip(),
                'pages': len(pages_text),
                'method': 'ocr_tesseract',
                'confidence': round(avg_confidence / 100, 2),
            }
        except ImportError as e:
            raise e

    @staticmethod
    def _extract_from_image(file_path: str, language: str) -> dict:
        """Extrai texto de imagem com Tesseract."""
        import pytesseract
        from PIL import Image

        image = Image.open(file_path)
        data = pytesseract.image_to_data(image, lang=language, output_type=pytesseract.Output.DICT)

        text = ' '.join([
            word for word, conf in zip(data['text'], data['conf'])
            if int(conf) > 30 and word.strip()
        ])

        confs = [int(c) for c in data['conf'] if int(c) > 0]
        avg_confidence = sum(confs) / len(confs) if confs else 0

        return {
            'success': True,
            'text': text.strip(),
            'pages': 1,
            'method': 'ocr_tesseract',
            'confidence': round(avg_confidence / 100, 2),
        }

    @staticmethod
    def extract_from_upload(uploaded_file, language: str = 'por') -> dict:
        """Extrai texto de arquivo uploaded (InMemoryUploadedFile)."""
        ext = uploaded_file.name.rsplit('.', 1)[-1].lower() if '.' in uploaded_file.name else ''

        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{ext}') as tmp:
            for chunk in uploaded_file.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name

        try:
            result = OCRService.extract_text(tmp_path, language)
            result['filename'] = uploaded_file.name
            result['file_size'] = uploaded_file.size
            return result
        finally:
            os.unlink(tmp_path)
