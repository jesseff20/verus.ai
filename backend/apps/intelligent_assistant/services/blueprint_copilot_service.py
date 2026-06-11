"""
Serviço Blueprint Copilot — cria blueprints completos via linguagem natural.

O Copilot conhece todas as APIs, estruturas e configurações.
Quando o usuário faz um pedido em linguagem natural, o Copilot:
1. Analisa se o pedido é claro o suficiente
2. Se não for, faz perguntas de clarificação (RARNESS)
3. Se for claro, gera o blueprint completo com todas as seções, agentes, configurações
4. O usuário pode editar depois
"""
import logging
import json
from django.conf import settings

logger = logging.getLogger(__name__)


class BlueprintCopilotService:
    """Cria blueprints de documentos via linguagem natural com IA."""

    DOCUMENT_TYPES_KNOWLEDGE = {
        'etp': {
            'name': 'Estudo Técnico Preliminar',
            'typical_sections': ['objeto', 'necessidade', 'requisitos', 'estimativa_custo', 'riscos', 'conclusao'],
            'base_legal': 'Lei 14.133/2021, Art. 18',
        },
        'termo_referencia': {
            'name': 'Termo de Referência',
            'typical_sections': ['objeto', 'justificativa', 'especificacoes', 'quantitativo', 'prazo', 'obrigacoes'],
            'base_legal': 'Lei 14.133/2021, Art. 6°, XXIII',
        },
        'peticao': {
            'name': 'Petição',
            'typical_sections': ['qualificacao', 'fatos', 'direito', 'pedidos', 'provas', 'encerramento'],
        },
        'contrato': {
            'name': 'Contrato',
            'typical_sections': ['partes', 'objeto', 'prazo', 'valor', 'obrigacoes', 'rescisao', 'foro'],
        },
        'parecer': {
            'name': 'Parecer Jurídico',
            'typical_sections': ['ementa', 'relatorio', 'fundamentacao', 'conclusao'],
        },
    }

    @classmethod
    def process_natural_language_request(cls, user_request: str, user=None, conversation_history: list = None) -> dict:
        """
        Processa pedido em linguagem natural para criar blueprint.

        Se o pedido não for claro, retorna perguntas de clarificação (RARNESS).
        Se for claro, gera o blueprint completo.
        """
        from apps.intelligent_assistant.services.llm_provider_service import UnifiedLLMService

        history_context = ''
        if conversation_history:
            history_context = '\n'.join([
                f"{'Usuário' if msg['role'] == 'user' else 'Copilot'}: {msg['content']}"
                for msg in conversation_history[-10:]  # Last 10 messages
            ])

        system_prompt = """Você é o Blueprint Copilot do Verus.AI — um assistente especializado em criar blueprints (modelos) de documentos jurídicos e administrativos.

Você conhece profundamente:
- Todas as APIs e estruturas do Verus.AI
- Tipos de documentos: ETP, Termo de Referência, Petições, Contratos, Pareceres, etc.
- Configurações de agentes IA por seção
- Tipografia, formatação e padrões de PDF

SUAS RESPONSABILIDADES:
1. ANALISAR se o pedido do usuário é claro e específico o suficiente
2. Se NÃO for claro: fazer perguntas de clarificação (máximo 3 perguntas)
3. Se FOR claro: gerar o blueprint completo em JSON

CRITÉRIOS DE CLAREZA (RARNESS):
- R: Relevância — o pedido se refere a um tipo de documento real?
- A: Adequação — tem informações suficientes para criar o blueprint?
- R: Razoabilidade — o pedido faz sentido no contexto jurídico/administrativo?
- N: Necessidade — quais seções são necessárias para este tipo de documento?
- E: Especificidade — tem detalhes suficientes sobre organização, base legal, etc.?
- S: Suficiência — tem contexto bastante para configurar os agentes IA?
- S: Sanidade — o pedido não contém contradições ou impossibilidades?

FORMATO DE RESPOSTA (JSON):

Se precisar de clarificação:
{
    "action": "clarify",
    "message": "mensagem amigável explicando o que precisa ser esclarecido",
    "questions": [
        {"id": "q1", "question": "pergunta 1", "options": ["opção A", "opção B"]},
        {"id": "q2", "question": "pergunta 2"}
    ]
}

Se puder gerar o blueprint:
{
    "action": "generate",
    "blueprint": {
        "name": "Nome do Blueprint",
        "description": "Descrição detalhada",
        "document_type": "tipo do documento (slug)",
        "version": "1.0",
        "legal_basis": "Base legal",
        "organization_name": "Nome da organização (se mencionado)",
        "sections": [
            {
                "order": 1,
                "title": "Título da Seção",
                "description": "O que deve conter esta seção",
                "is_required": true,
                "field_type": "rich_text",
                "agent_config": {
                    "agent_type": "writer",
                    "system_prompt": "Prompt do agente para esta seção",
                    "temperature": 0.3,
                    "max_tokens": 2000,
                    "required_inputs": ["campo1", "campo2"],
                    "output_format": "markdown"
                },
                "typography": {
                    "font_family": "Times New Roman",
                    "font_size": 12,
                    "alignment": "justify",
                    "heading_style": "bold_uppercase"
                }
            }
        ],
        "pdf_config": {
            "page_size": "A4",
            "margins": {"top": 3, "bottom": 2, "left": 3, "right": 2},
            "header_text": "",
            "footer_text": "",
            "include_cover": true,
            "include_toc": false,
            "numbering_style": "roman"
        },
        "metadata": {}
    },
    "message": "Mensagem explicando o blueprint gerado e como o usuário pode editá-lo"
}
"""

        user_prompt = f"""{'HISTÓRICO DA CONVERSA:\n' + history_context + '\n\n' if history_context else ''}PEDIDO DO USUÁRIO:
{user_request}

Analise o pedido e responda em JSON conforme as instruções."""

        try:
            llm_service = UnifiedLLMService()
            response = llm_service.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=6000,
                temperature=0.4,
                user=user,
                usage_type='copilot',
                description='Blueprint Copilot',
            )

            content = response.get('content', '')

            # Parse JSON from response
            parsed = cls._extract_json(content)

            if parsed:
                if parsed.get('action') == 'generate' and parsed.get('blueprint'):
                    # Validate and enrich the blueprint
                    parsed['blueprint'] = cls._enrich_blueprint(parsed['blueprint'])
                return {
                    'success': True,
                    **parsed,
                    'tokens_used': response.get('total_tokens', 0),
                }
            else:
                return {
                    'success': True,
                    'action': 'clarify',
                    'message': content,
                    'questions': [],
                }

        except Exception as e:
            logger.error(f"Blueprint Copilot error: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    @classmethod
    def create_blueprint_from_copilot(cls, blueprint_data: dict, user) -> dict:
        """
        Cria o blueprint no banco de dados a partir dos dados gerados pelo Copilot.
        """
        from apps.intelligent_assistant.models import DocumentBlueprint, SectionAgentConfig
        from apps.core.models import DocumentType

        try:
            # Find or create document type
            doc_type_slug = blueprint_data.get('document_type', 'custom')
            doc_type, _ = DocumentType.objects.get_or_create(
                slug=doc_type_slug,
                defaults={
                    'name': blueprint_data.get('name', 'Documento Personalizado'),
                    'description': blueprint_data.get('description', ''),
                }
            )

            # Create blueprint
            blueprint = DocumentBlueprint.objects.create(
                name=blueprint_data['name'],
                description=blueprint_data.get('description', ''),
                document_type=doc_type,
                version=blueprint_data.get('version', '1.0'),
                legal_basis=blueprint_data.get('legal_basis', ''),
                organization_name=blueprint_data.get('organization_name', ''),
                metadata={
                    'created_by_copilot': True,
                    'pdf_config': blueprint_data.get('pdf_config', {}),
                },
            )

            # Create sections with agent configs
            sections = blueprint_data.get('sections', [])
            created_sections = []
            for section_data in sections:
                agent_config = SectionAgentConfig.objects.create(
                    blueprint=blueprint,
                    section_order=section_data['order'],
                    section_title=section_data['title'],
                    section_description=section_data.get('description', ''),
                    is_required=section_data.get('is_required', True),
                    agent_type=section_data.get('agent_config', {}).get('agent_type', 'writer'),
                    system_prompt=section_data.get('agent_config', {}).get('system_prompt', ''),
                    temperature=section_data.get('agent_config', {}).get('temperature', 0.3),
                    max_tokens=section_data.get('agent_config', {}).get('max_tokens', 2000),
                    metadata={
                        'required_inputs': section_data.get('agent_config', {}).get('required_inputs', []),
                        'output_format': section_data.get('agent_config', {}).get('output_format', 'markdown'),
                        'typography': section_data.get('typography', {}),
                    },
                )
                created_sections.append({
                    'id': str(agent_config.id),
                    'order': agent_config.section_order,
                    'title': agent_config.section_title,
                })

            return {
                'success': True,
                'blueprint_id': str(blueprint.id),
                'blueprint_name': blueprint.name,
                'sections_count': len(created_sections),
                'sections': created_sections,
            }

        except Exception as e:
            logger.error(f"Error creating blueprint from copilot: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    @staticmethod
    def _extract_json(text: str) -> dict:
        """Extrai JSON de texto que pode conter markdown."""
        import re
        # Try direct parse
        try:
            return json.loads(text)
        except (json.JSONDecodeError, TypeError):
            pass

        # Try extracting from code blocks
        patterns = [
            r'```json\s*(.*?)\s*```',
            r'```\s*(.*?)\s*```',
            r'\{[\s\S]*\}',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1) if '```' in pattern else match.group(0))
                except (json.JSONDecodeError, TypeError):
                    continue
        return None

    @classmethod
    def _enrich_blueprint(cls, blueprint: dict) -> dict:
        """Enriquece blueprint com defaults e validações."""
        # Ensure all sections have required fields
        for i, section in enumerate(blueprint.get('sections', [])):
            if 'order' not in section:
                section['order'] = i + 1
            if 'is_required' not in section:
                section['is_required'] = True
            if 'field_type' not in section:
                section['field_type'] = 'rich_text'
            if 'agent_config' not in section:
                section['agent_config'] = {
                    'agent_type': 'writer',
                    'temperature': 0.3,
                    'max_tokens': 2000,
                }
            if 'typography' not in section:
                section['typography'] = {
                    'font_family': 'Times New Roman',
                    'font_size': 12,
                    'alignment': 'justify',
                }

        # Ensure pdf_config exists
        if 'pdf_config' not in blueprint:
            blueprint['pdf_config'] = {
                'page_size': 'A4',
                'margins': {'top': 3, 'bottom': 2, 'left': 3, 'right': 2},
            }

        return blueprint
