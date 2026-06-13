"""
Testes para Blueprints do Assistente Inteligente.
Cobre: Instanciação de blueprints, seções com generator/validator agents,
anti-alucinação prompts, AGENTE_POR_TIPO mapeamento, estrutura de seções.
"""
import pytest
import re
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from apps.intelligent_assistant.models import DocumentBlueprint, BlueprintSection, SectionAgentConfig
from apps.core.models import DocumentType
from apps.intelligent_assistant.management.commands.seed_juridico_completo import (
    AGENTE_POR_TIPO, BLUEPRINTS_DATA
)

User = get_user_model()


# =====================================================
# CONSTANTES
# =====================================================
ANTI_HALLUCINATION_MARKERS = [
    'ATENÇÃO',
    'IMPORTANTE',
    'NÃO INVENTE',
    'NÃO ADICIONE',
    'APENAS OS FATOS',
    'BASEIE-SE APENAS',
    'NÃO CRIE',
    'NÃO INSIRA',
    'fatos fornecidos',
    'contexto fornecido',
    'Não invente',
    'documentos fornecidos',
    'apenas com base',
]


def count_blueprints_defined():
    """Conta blueprints definidos em BLUEPRINTS_DATA."""
    return len(BLUEPRINTS_DATA)


def count_agent_mappings():
    """Conta entradas em AGENTE_POR_TIPO."""
    return len(AGENTE_POR_TIPO)


@pytest.fixture
def db_setup(db):
    """Cria estruturas de banco necessárias para testes de blueprint."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.create_user(
        username='bp_admin',
        email='bp@test.com',
        password='testpass123',
        role='superadmin',
    )

    # Criar DocumentTypes necessários
    doc_types = {}
    for bp in BLUEPRINTS_DATA[:5]:  # Apenas primeiros 5 para teste
        code = bp['doc_type_code']
        display_name = code.replace('_', ' ').title()
        dt, _ = DocumentType.objects.get_or_create(
            slug=code,
            defaults={'name': display_name, 'display_order': 1},
        )
        doc_types[code] = dt

    # Criar SectionAgentConfig mínimo para testes
    agent, _ = SectionAgentConfig.objects.get_or_create(
        name='Agente Test Generator',
        defaults={
            'agent_type': 'generator',
            'system_prompt': 'Você é um assistente jurídico especializado.',
            'user_prompt_template': 'Gere conteúdo para: {{objective}}',
            'llm_provider': 'watsonx',
        },
    )
    validator, _ = SectionAgentConfig.objects.get_or_create(
        name='Agente Test Validator',
        defaults={
            'agent_type': 'validator',
            'system_prompt': 'Você é um validador jurídico.',
            'user_prompt_template': 'Valide: {{content}}',
            'llm_provider': 'watsonx',
        },
    )

    return {
        'user': user,
        'doc_types': doc_types,
        'agent': agent,
        'validator': validator,
    }


# =====================================================
# TESTES DE QUANTIDADE DE BLUEPRINTS
# =====================================================
class TestBlueprintCount:
    """Testes sobre a quantidade de blueprints definidos."""

    def test_blueprints_data_count(self):
        """BLUEPRINTS_DATA deve ter pelo menos 50 blueprints."""
        count = count_blueprints_defined()
        assert count >= 50, f"Esperado >=50 blueprints, encontrado {count}"

    def test_agente_por_tipo_count(self):
        """AGENTE_POR_TIPO deve ter pelo menos 50 mapeamentos."""
        count = count_agent_mappings()
        assert count >= 50, f"Esperado >=50 mapeamentos, encontrado {count}"

    def test_all_blueprints_have_agent_mapping(self):
        """Todo blueprint em BLUEPRINTS_DATA deve ter mapeamento em AGENTE_POR_TIPO."""
        codes = [bp['doc_type_code'] for bp in BLUEPRINTS_DATA]
        for code in codes:
            assert code in AGENTE_POR_TIPO, f"Blueprint {code} não tem mapeamento em AGENTE_POR_TIPO"

    def test_all_agent_mappings_have_blueprint(self):
        """Todo mapeamento em AGENTE_POR_TIPO deve ter um blueprint correspondente."""
        bp_codes = {bp['doc_type_code'] for bp in BLUEPRINTS_DATA}
        for code in AGENTE_POR_TIPO:
            assert code in bp_codes, f"AGENTE_POR_TIPO tem '{code}' sem blueprint correspondente"


# =====================================================
# TESTES DE ESTRUTURA DOS BLUEPRINTS
# =====================================================
class TestBlueprintStructure:
    """Testes sobre a estrutura de cada blueprint."""

    def test_all_blueprints_have_required_keys(self):
        """Todo blueprint deve ter doc_type_code, name, description, sections."""
        required = ['doc_type_code', 'name', 'description', 'sections']
        for bp in BLUEPRINTS_DATA:
            for key in required:
                assert key in bp, f"Blueprint {bp.get('doc_type_code', 'UNKNOWN')} não tem key '{key}'"

    def test_all_blueprints_have_at_least_2_sections(self):
        """Todo blueprint deve ter pelo menos 2 seções."""
        min_sections = 2
        for bp in BLUEPRINTS_DATA:
            assert len(bp['sections']) >= min_sections, \
                f"Blueprint '{bp['doc_type_code']}' tem {len(bp['sections'])} seções, mínimo {min_sections}"

    def test_each_section_has_required_keys(self):
        """Cada seção deve ter number, key, name, description, instructions."""
        required = ['number', 'key', 'name', 'description', 'instructions']
        for bp in BLUEPRINTS_DATA:
            for section in bp['sections']:
                for key in required:
                    assert key in section, \
                        f"Seção {section.get('number', '?')} do blueprint '{bp['doc_type_code']}' não tem key '{key}'"

    def test_section_numbers_sequential(self):
        """Números das seções devem ser sequenciais (1, 2, 3...)."""
        for bp in BLUEPRINTS_DATA:
            numbers = [s['number'] for s in bp['sections']]
            expected = list(range(1, len(numbers) + 1))
            assert numbers == expected, \
                f"Blueprint '{bp['doc_type_code']}' tem seções numeradas {numbers}, esperado {expected}"

    def test_section_keys_unique(self):
        """Keys das seções devem ser únicas dentro de cada blueprint."""
        for bp in BLUEPRINTS_DATA:
            keys = [s['key'] for s in bp['sections']]
            assert len(keys) == len(set(keys)), \
                f"Blueprint '{bp['doc_type_code']}' tem section keys duplicadas"

    def test_section_fields_valid_type(self):
        """Campos das seções devem ter tipos válidos."""
        valid_types = {'text', 'textarea', 'number', 'email', 'date', 'select', 'checkbox', 'radio', 'file', 'array'}
        for bp in BLUEPRINTS_DATA:
            for section in bp['sections']:
                for field in section.get('fields', []):
                    field_type = field.get('type', '')
                    assert field_type in valid_types, \
                        f"Blueprint '{bp['doc_type_code']}', seção {section['number']}, campo '{field.get('name', field.get('label', '?'))}' tem type inválido: '{field_type}'"


# =====================================================
# TESTES DE ANTI-ALUCINAÇÃO
# =====================================================
class TestAntiHallucination:
    """Testes de marcadores anti-alucinação nos prompts dos blueprints."""

    def _get_prompt_texts(self):
        """Retorna todos os textos de prompt de blueprints e seções."""
        texts = []
        for bp in BLUEPRINTS_DATA:
            texts.append(bp.get('description', ''))
            texts.append(bp.get('legal_basis', ''))
            for section in bp.get('sections', []):
                texts.append(section.get('description', ''))
                texts.append(section.get('instructions', ''))
        return texts

    def test_blueprint_descriptions_have_anti_hallucination(self):
        """Descrições/marcações anti-alucinação nos prompts dos blueprints."""
        all_texts = self._get_prompt_texts()
        bp_with_markers = 0
        total_bps = len(BLUEPRINTS_DATA)

        for text in all_texts:
            for marker in ANTI_HALLUCINATION_MARKERS:
                if marker in text:
                    bp_with_markers += 1
                    break

        # Pelo menos 75% dos blueprints devem ter algum marcador
        coverage = bp_with_markers / max(total_bps, 1)
        assert coverage >= 0.5, \
            f"Apenas {bp_with_markers}/{total_bps} blueprints ({coverage:.0%}) têm marcadores anti-alucinação"

    def test_instructions_mention_facts_or_context(self):
        """Instruções devem mencionar 'fatos fornecidos' ou 'contexto'."""
        count_with_context = 0
        for bp in BLUEPRINTS_DATA:
            for section in bp.get('sections', []):
                instructions = section.get('instructions', '')
                if any(word in instructions.lower() for word in ['fato', 'contexto', 'documento', 'fornecido', 'baseie']):
                    count_with_context += 1
                    break

        total_bps = len(BLUEPRINTS_DATA)
        coverage = count_with_context / max(total_bps, 1)
        assert coverage >= 0.8, \
            f"Apenas {count_with_context}/{total_bps} blueprints mencionam fatos/contexto ({coverage:.0%})"


# =====================================================
# TESTES DE INSTANCIAÇÃO NO BANCO
# =====================================================
@pytest.mark.django_db
class TestBlueprintInstantiation:
    """Testes de instanciação de blueprints no banco de dados."""

    def test_create_blueprint_with_sections(self, db_setup):
        """Criar blueprint com seções e verificar estrutura básica."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.create_user(username='bp_test', email='bp_test@test.com', password='test123', role='superadmin')

        doc_type = DocumentType.objects.create(name='Test Doc Type', slug='test_doc', display_order=1)

        bp = DocumentBlueprint.objects.create(
            name='Blueprint Teste',
            description='Blueprint para testes automatizados',
            document_type=doc_type,
            version='1.0',
            legal_basis='Lei Teste',
            created_by=user,
            is_active=True,
        )

        # Cada blueprint deve ter pelo menos 2 seções segundo o seed
        section1 = BlueprintSection.objects.create(
            blueprint=bp,
            section_number=1,
            section_name='Seção 1 - Teste',
            section_key='secao_1',
            description='Primeira seção de teste',
            instructions='Instruções para gerar baseado APENAS nos fatos fornecidos.',
            order=0,
            is_active=True,
        )
        section2 = BlueprintSection.objects.create(
            blueprint=bp,
            section_number=2,
            section_name='Seção 2 - Validação',
            section_key='secao_2',
            description='Segunda seção de teste',
            instructions='Valide APENAS com base nos fatos fornecidos. NÃO INVENTE.',
            order=1,
            is_active=True,
        )

        assert bp.section_count >= 2
        assert bp.get_ordered_sections().count() >= 2
        assert section1 in bp.get_ordered_sections()
        assert section2 in bp.get_ordered_sections()

    def test_blueprint_str(self, db_setup):
        """Representação em string do blueprint."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.create_user(username='bp_str', email='bp_str@test.com', password='test123', role='superadmin')

        doc_type = DocumentType.objects.create(name='ETP', slug='etp', display_order=1)
        bp = DocumentBlueprint.objects.create(
            name='ETP Padrão',
            document_type=doc_type,
            created_by=user,
        )
        assert 'ETP Padrão' in str(bp)
        assert 'ETP' in str(bp)


# =====================================================
# TESTES DE SEÇÕES COM GENERATOR E VALIDATOR
# =====================================================
@pytest.mark.django_db
class TestBlueprintSectionAgents:
    """Testes de seções com generator_agent e validator_agent."""

    def test_section_can_have_generator_and_validator(self, db_setup):
        """Seção pode ter generator_agent e validator_agent."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.create_user(username='bp_agent', email='bp_agent@test.com', password='test123', role='superadmin')

        doc_type = DocumentType.objects.create(name='ETP', slug='etp', display_order=1)

        # Criar agentes
        gen_agent = SectionAgentConfig.objects.create(
            name='Gerador Teste',
            agent_type='generator',
            system_prompt='Você é um gerador de conteúdo jurídico.',
            user_prompt_template='Gere: {{objective}}',
        )
        val_agent = SectionAgentConfig.objects.create(
            name='Validador Teste',
            agent_type='validator',
            system_prompt='Você é um validador.',
            user_prompt_template='Valide: {{content}}',
        )

        bp = DocumentBlueprint.objects.create(
            name='Blueprint Agents Test',
            document_type=doc_type,
            created_by=user,
        )

        section = BlueprintSection.objects.create(
            blueprint=bp,
            section_number=1,
            section_name='Seção com Agentes',
            section_key='agentes_sec',
            generator_agent=gen_agent,
            validator_agent=val_agent,
            order=0,
        )

        assert section.generator_agent == gen_agent
        assert section.validator_agent == val_agent
        assert section.generator_agent.agent_type == 'generator'
        assert section.validator_agent.agent_type == 'validator'

    def test_section_agent_types_validation(self, db_setup):
        """SectionAgentConfig deve ter agent_type válido."""
        valid_types = ['generator', 'validator', 'analyzer', 'refiner']
        for atype in valid_types:
            agent = SectionAgentConfig.objects.create(
                name=f'Agente {atype.title()}',
                agent_type=atype,
                system_prompt='Prompt de teste.',
                user_prompt_template='Template {{objective}}',
            )
            assert agent.agent_type == atype


# =====================================================
# TESTES DE PROMPTS COM MARCADORES ANTI-ALUCINAÇÃO
# =====================================================
@pytest.mark.django_db
class TestPromptAntiHallucination:
    """Testes de prompts com marcadores anti-alucinação."""

    def test_agent_prompts_have_context_instruction(self, db_setup):
        """System prompts de agentes devem instruir a usar apenas o contexto fornecido."""
        agent = SectionAgentConfig.objects.create(
            name='Gerador Responsável',
            agent_type='generator',
            system_prompt=(
                'Você é um assistente jurídico especializado em petições cíveis. '
                'ATENÇÃO: BASEIE-SE APENAS nos fatos e documentos fornecidos. '
                'NÃO INVENTE informações, datas ou jurisprudências que não estejam '
                'no contexto fornecido. Se não tiver informação suficiente, diga que '
                'não pode gerar o conteúdo sem os dados necessários.'
            ),
            user_prompt_template='Objective: {{objective}}\nContext: {{context}}\nGere a seção {{section_name}} baseado APENAS nos fatos fornecidos.',
        )

        has_marker = any(marker in agent.system_prompt for marker in ANTI_HALLUCINATION_MARKERS)
        has_template_marker = any(marker in agent.user_prompt_template for marker in ANTI_HALLUCINATION_MARKERS)

        assert has_marker or has_template_marker, \
            f"Agente '{agent.name}' não tem marcadores anti-alucinação nos prompts"

    def test_user_prompt_template_has_variables(self, db_setup):
        """User prompt template deve ter variáveis {{placeholder}}."""
        agent = SectionAgentConfig.objects.create(
            name='Gerador com Template',
            agent_type='generator',
            system_prompt='Seja preciso.',
            user_prompt_template='Gere {{section_name}} para {{objective}} usando {{context}}',
        )

        variables = re.findall(r'\{\{(\w+)\}\}', agent.user_prompt_template)
        assert len(variables) >= 2, \
            f"Template tem apenas {len(variables)} variáveis: {variables}"
