"""
View para extração automática de campos de formulário a partir de
documentos já enviados na sessão.

POST /api/v1/intelligent-assistant/sessions/{session_id}/extract-fields/
Usa os documentos já carregados na sessão (UploadedDocument.extracted_text)
para preencher todos os section_fields do blueprint associado.
"""
import json
import logging
import re

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import IntelligentSession, BlueprintSection
from ..services.llm_provider_service import UnifiedLLMService

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def extract_fields_from_session(request, session_id):
    """
    POST /api/v1/intelligent-assistant/sessions/{session_id}/extract-fields/

    Extrai valores dos documentos já enviados na sessão para preencher
    automaticamente os campos de formulário (section_fields) do blueprint.

    Retorna:
    {
      "extracted": {
        "<section_number>": {
          "<field_name>": "valor extraído",
          ...
        },
        ...
      },
      "sections_filled": 2,
      "fields_filled": 8,
      "fields_total": 12
    }
    """
    # 1. Buscar sessão do usuário
    try:
        session = IntelligentSession.objects.select_related('blueprint').get(
            id=session_id,
            user=request.user,
        )
    except IntelligentSession.DoesNotExist:
        return Response(
            {'error': 'Sessão não encontrada'},
            status=status.HTTP_404_NOT_FOUND,
        )

    # 2. Validar que há blueprint e documentos
    if not session.blueprint:
        return Response(
            {'error': 'Sessão não possui blueprint associado'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    uploaded_docs = session.uploaded_documents.filter(
        extraction_status='completed',
    ).exclude(extracted_text='')

    if not uploaded_docs.exists():
        return Response(
            {'error': 'Nenhum documento com texto extraído encontrado na sessão'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # 3. Coletar campos do blueprint (somente seções com section_fields)
    sections = BlueprintSection.objects.filter(
        blueprint=session.blueprint,
        is_active=True,
    ).order_by('order')

    sections_with_fields = []
    for sec in sections:
        fields = sec.section_fields or []
        if not fields:
            continue
        sections_with_fields.append({
            'section_number': sec.section_number,
            'section_name': sec.section_name,
            'fields': fields,
        })

    if not sections_with_fields:
        return Response({
            'extracted': {},
            'sections_filled': 0,
            'fields_filled': 0,
            'fields_total': 0,
        })

    # 4. Consolidar texto de todos os documentos
    all_texts = []
    for doc in uploaded_docs[:5]:  # limitar a 5 documentos
        text = doc.extracted_text or ''
        if text:
            all_texts.append(f"--- DOCUMENTO: {doc.filename} ---\n{text}")

    combined_text = '\n\n'.join(all_texts)

    # Limitar para não exceder contexto da LLM
    max_chars = 30000
    if len(combined_text) > max_chars:
        combined_text = combined_text[:max_chars] + '\n\n[... texto truncado ...]'

    # 5. Construir prompt
    field_spec_lines = []
    total_fields = 0
    for sec_info in sections_with_fields:
        field_spec_lines.append(
            f"\nSEÇÃO {sec_info['section_number']} - {sec_info['section_name']}:"
        )
        for f in sec_info['fields']:
            if f.get('type') == 'array':
                continue  # arrays são complexos demais para auto-fill
            total_fields += 1
            line = f"  - {f.get('label', f.get('name', '?'))} (name={f.get('name')}, type={f.get('type', 'text')})"
            if f.get('required'):
                line += ' [obrigatório]'
            if f.get('options'):
                opts = ', '.join(
                    [o.get('label', o.get('value', '')) for o in f['options'][:10]]
                )
                line += f' [opções: {opts}]'
            field_spec_lines.append(line)

    field_spec = '\n'.join(field_spec_lines)

    blueprint_name = session.blueprint.name or 'Documento Jurídico'

    system_prompt = (
        "Você é um assistente jurídico especializado em análise de documentos brasileiros. "
        "Sua tarefa é extrair informações de documentos jurídicos e preencher campos de formulário. "
        "Retorne APENAS o JSON solicitado, sem explicações, prefácios ou marcações extras. "
        "Seja preciso na extração. Para campos com opções, use exatamente o valor da opção correspondente. "
        "Analise TODOS os documentos fornecidos para encontrar as informações."
    )

    user_prompt = f"""Analise os documentos jurídicos abaixo e extraia informações para preencher os campos do formulário de "{blueprint_name}".

CAMPOS DO FORMULÁRIO POR SEÇÃO:
{field_spec}

DOCUMENTOS:
{combined_text}

Retorne um JSON com a seguinte estrutura. Use os valores "name" dos campos como chaves.
Para campos não encontrados nos documentos, use null.
Para campos de data, use formato AAAA-MM-DD.
Para campos numéricos, use apenas o número (sem formatação).
Para campos com opções (select), use o value exato da opção que melhor se encaixa.

Formato de resposta (JSON puro, sem markdown):
{{
  "<section_number>": {{
    "<field_name>": "valor encontrado ou null"
  }}
}}

Exemplo:
{{
  "1": {{
    "reclamante_nome": "João Silva",
    "reclamante_cpf": "123.456.789-00"
  }},
  "3": {{
    "periodo_trabalho_inicio": "2020-01-15",
    "periodo_trabalho_fim": null
  }}
}}"""

    # 6. Chamar LLM
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
            usage_type='analysis',
            description='Extracao de campos de documento',
        )
        raw_content = result.get('content', '').strip()
    except Exception as exc:
        logger.error(f"[extract_fields] Erro na LLM: {exc}", exc_info=True)
        return Response(
            {'error': 'Erro ao processar com IA. Tente novamente em instantes.'},
            status=status.HTTP_502_BAD_GATEWAY,
        )

    if not raw_content:
        return Response(
            {'error': 'A IA não retornou conteúdo. Tente novamente.'},
            status=status.HTTP_502_BAD_GATEWAY,
        )

    # 7. Parse do JSON
    try:
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', raw_content)
        if json_match:
            json_str = json_match.group(1).strip()
        else:
            json_str = raw_content

        parsed = json.loads(json_str)
    except json.JSONDecodeError:
        logger.warning(
            f"[extract_fields] Falha ao parsear JSON da LLM: {raw_content[:500]}"
        )
        return Response(
            {'error': 'A IA retornou um formato inválido. Tente novamente.'},
            status=status.HTTP_502_BAD_GATEWAY,
        )

    # 8. Limpar nulls e contar campos preenchidos
    extracted = {}
    fields_filled = 0
    sections_filled = 0

    for sec_info in sections_with_fields:
        sec_num = str(sec_info['section_number'])
        sec_data = parsed.get(sec_num, {})
        if not isinstance(sec_data, dict):
            continue

        clean_fields = {}
        sec_has_value = False
        for f in sec_info['fields']:
            if f.get('type') == 'array':
                continue
            name = f.get('name', '')
            value = sec_data.get(name)

            # Tentar também pelo label
            if value is None:
                label = f.get('label', '')
                value = sec_data.get(label)

            if value is not None and str(value).lower() != 'null' and str(value).strip():
                clean_fields[name] = value
                fields_filled += 1
                sec_has_value = True

        if clean_fields:
            extracted[sec_num] = clean_fields
        if sec_has_value:
            sections_filled += 1

    return Response({
        'extracted': extracted,
        'sections_filled': sections_filled,
        'fields_filled': fields_filled,
        'fields_total': total_fields,
    })
