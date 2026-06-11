"""
View para preencher formularios de blueprint a partir de documento anexado.

POST /api/v1/intelligent-assistant/fill-form-from-document/
Recebe arquivo (PDF/DOCX/TXT/ODT) + lista de campos do formulario,
usa IA para extrair dados e preencher automaticamente.
"""
import json
import logging
import re

from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.kb.services import DocumentProcessingService
from apps.intelligent_assistant.services.llm_provider_service import UnifiedLLMService

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def fill_form_from_document(request):
    """
    POST /api/v1/intelligent-assistant/fill-form-from-document/
    Preenche campos de formulario de blueprint a partir de documento anexado.

    Body (multipart/form-data):
      - file (File, required): documento PDF, DOCX, DOC, ODT ou TXT
      - fields (str/JSON, required): lista de campos do formulario
      - blueprint_name (str, optional): nome do blueprint/peca
    """
    file = request.FILES.get('file')
    fields_json = request.data.get('fields', '[]')
    blueprint_name = request.data.get('blueprint_name', '')

    if not file:
        return Response(
            {'error': 'Nenhum arquivo enviado. Envie um PDF, DOCX, DOC, ODT ou TXT.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Determinar tipo do arquivo pela extensao
    file_name = file.name.lower()
    ext = file_name.rsplit('.', 1)[-1] if '.' in file_name else ''
    supported_exts = ('pdf', 'docx', 'doc', 'odt', 'txt')
    if ext not in supported_exts:
        return Response(
            {'error': f'Tipo de arquivo nao suportado: .{ext}. Use: {", ".join(supported_exts)}'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Parse dos campos
    try:
        fields = json.loads(fields_json) if isinstance(fields_json, str) else fields_json
    except (json.JSONDecodeError, TypeError):
        return Response(
            {'error': 'O campo "fields" deve ser um JSON valido.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not fields or not isinstance(fields, list):
        return Response(
            {'error': 'A lista de campos esta vazia ou invalida.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # 1. Extrair texto do documento
    try:
        file_content = file.read()
        text = DocumentProcessingService.extract_text_from_bytes(file_content, ext)
    except Exception as exc:
        logger.error(f"[fill_form] Erro ao extrair texto: {exc}", exc_info=True)
        return Response(
            {'error': f'Erro ao extrair texto do documento: {str(exc)}'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not text or not text.strip():
        return Response(
            {'error': 'Nenhum texto pode ser extraido do documento. Verifique se o arquivo nao esta vazio ou corrompido.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Limitar texto para evitar exceder contexto da LLM
    max_chars = 15000
    if len(text) > max_chars:
        text = text[:max_chars] + '\n\n[... texto truncado por limite de tamanho ...]'

    # 2. Construir prompt com os campos do formulario
    field_list_lines = []
    for f in fields:
        line = f'- {f.get("label", f.get("name", "?"))} ({f.get("type", "text")})'
        if f.get('required'):
            line += ' [obrigatorio]'
        if f.get('options'):
            opts = ', '.join([o.get('label', o.get('value', '')) for o in f['options'][:10]])
            line += f' [opcoes: {opts}]'
        field_list_lines.append(line)
    field_list = '\n'.join(field_list_lines)

    system_prompt = (
        "Voce e um assistente juridico especializado em analise de documentos brasileiros. "
        "Sua tarefa e extrair informacoes de documentos juridicos e preencher campos de formulario. "
        "Retorne APENAS o JSON solicitado, sem explicacoes, prefacios ou marcacoes extras. "
        "Seja preciso na extracao. Para campos com opcoes, use exatamente o valor da opcao correspondente."
    )

    user_prompt = f"""Analise o documento juridico abaixo e extraia informacoes para preencher os campos do formulario.

TIPO DE PECA: {blueprint_name}

CAMPOS DO FORMULARIO:
{field_list}

DOCUMENTO:
{text}

Retorne um JSON com os campos preenchidos. Use EXATAMENTE os mesmos labels como chaves.
Para campos nao encontrados no documento, use null.
Para campos de data, use formato AAAA-MM-DD.
Para campos numericos, use apenas o numero (sem formatacao).
Para campos com opcoes (select), use o value exato da opcao que melhor se encaixa.

Formato de resposta (JSON puro, sem markdown):
{{
  "Label do Campo 1": "valor encontrado",
  "Label do Campo 2": "valor encontrado",
  "Label do Campo 3": null
}}"""

    # 3. Chamar LLM
    try:
        llm_service = UnifiedLLMService()
        result = llm_service.generate(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            provider='watsonx',
            model='mistralai/mistral-medium-2505',
            temperature=0.1,
            max_tokens=4096,
            user=request.user if request.user.is_authenticated else None,
            usage_type='document_gen',
            description='Preenchimento automatico de formulario',
        )
        raw_content = result.get('content', '').strip()
    except Exception as exc:
        logger.error(f"[fill_form] Erro na LLM: {exc}", exc_info=True)
        return Response(
            {'error': 'Erro ao processar com IA. Tente novamente em instantes.'},
            status=status.HTTP_502_BAD_GATEWAY,
        )

    if not raw_content:
        return Response(
            {'error': 'A IA nao retornou conteudo. Tente novamente.'},
            status=status.HTTP_502_BAD_GATEWAY,
        )

    # 4. Parse do JSON retornado pela LLM
    try:
        # Tentar extrair JSON de dentro de markdown code blocks se necessario
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', raw_content)
        if json_match:
            json_str = json_match.group(1).strip()
        else:
            json_str = raw_content

        parsed = json.loads(json_str)
    except json.JSONDecodeError:
        logger.warning(f"[fill_form] Falha ao parsear JSON da LLM: {raw_content[:500]}")
        return Response(
            {'error': 'A IA retornou um formato invalido. Tente novamente.'},
            status=status.HTTP_502_BAD_GATEWAY,
        )

    # 5. Mapear labels -> field names e contar
    filled_fields = {}
    fields_found = 0
    fields_not_found = []

    for field_def in fields:
        label = field_def.get('label', field_def.get('name', ''))
        name = field_def.get('name', '')
        value = parsed.get(label)

        if value is None:
            # Tentar pelo name tambem
            value = parsed.get(name)

        if value is not None and value != '' and str(value).lower() != 'null':
            filled_fields[name] = value
            fields_found += 1
        else:
            fields_not_found.append(label)

    return Response({
        'filled_fields': filled_fields,
        'fields_found': fields_found,
        'fields_total': len(fields),
        'fields_not_found': fields_not_found,
    })
