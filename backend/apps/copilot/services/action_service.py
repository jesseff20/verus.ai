"""
ActionService — Executa ações autônomas do Copilot.

Permite ao Copilot buscar casos, blueprints e criar sessões de geração
de documentos com preenchimento automático de campos a partir dos dados
do caso jurídico.
"""
import logging
from django.db.models import Q
from apps.cases.models import LegalCase
from apps.intelligent_assistant.models.blueprint import DocumentBlueprint, BlueprintSection
from apps.intelligent_assistant.models.session import IntelligentSession

logger = logging.getLogger(__name__)


class ActionService:
    """Serviço de ações autônomas do Copilot sobre casos e blueprints."""

    def __init__(self, user):
        self.user = user

    def find_cases(self, query):
        """Search user's cases by title, client, process number."""
        return LegalCase.objects.filter(
            Q(advogado_responsavel=self.user) | Q(created_by=self.user),
            deleted_at__isnull=True,
        ).filter(
            Q(titulo__icontains=query)
            | Q(cliente_nome__icontains=query)
            | Q(numero_processo__icontains=query)
            | Q(parte_contraria__icontains=query)
        )[:5]

    def find_blueprints(self, query=None, especialidade=None):
        """Find blueprints matching query or specialty."""
        qs = DocumentBlueprint.objects.filter(is_active=True)
        if especialidade:
            qs = qs.filter(areas__code__icontains=especialidade)
        if query:
            qs = qs.filter(
                Q(name__icontains=query) | Q(document_type__name__icontains=query)
            )
        return qs.select_related('document_type')[:10]

    def blueprints_for_case(self, case):
        """Suggest blueprints based on case specialty."""
        SPECIALTY_MAP = {
            'trabalhista': ['reclamacao', 'trabalhista'],
            'criminal': ['queixa', 'criminal', 'denuncia'],
            'consumidor': ['consumidor', 'danos'],
            'tributario': ['tributar', 'anulatoria'],
            'familia': ['familia', 'inventario', 'divorcio'],
            'civel': ['civil', 'cobranca', 'indenizacao'],
        }
        keywords = SPECIALTY_MAP.get(case.especialidade, [case.especialidade])
        q = Q()
        for kw in keywords:
            q |= Q(name__icontains=kw) | Q(document_type__name__icontains=kw)
        return (
            DocumentBlueprint.objects.filter(q, is_active=True)
            .select_related('document_type')[:5]
        )

    def create_session_for_case(self, case, blueprint):
        """Create an IntelligentSession linked to a case with auto-filled objective."""
        objective = (
            f"{blueprint.document_type.name} - {case.titulo}. {case.observacoes or ''}"
        )
        session = IntelligentSession.objects.create(
            user=self.user,
            objective=objective[:2000],
            blueprint=blueprint,
            document_type=blueprint.document_type.code if blueprint.document_type else '',
            case=case,
            status='initialized',
            kb_collection_id='',
        )
        return session

    def map_case_to_fields(self, case, blueprint):
        """Map case data to blueprint section fields for auto-fill."""
        field_data = {}
        sections = blueprint.sections.filter(is_active=True).order_by('order')
        for section in sections:
            if not section.section_fields:
                continue
            section_data = {}
            for field in section.section_fields:
                name = field.get('name', '').lower()
                label = field.get('label', '').lower()
                combined = name + ' ' + label
                # Map based on keywords in field name/label
                if any(
                    k in combined
                    for k in ['reclamante', 'autor', 'querelante', 'requerente']
                ):
                    if any(k in combined for k in ['cpf', 'cnpj', 'documento']):
                        section_data[field['name']] = case.cliente_cpf_cnpj or ''
                    elif any(k in combined for k in ['endereco', 'endereço']):
                        section_data[field['name']] = ''
                    else:
                        section_data[field['name']] = case.cliente_nome or ''
                elif any(
                    k in combined for k in ['reclamad', 'réu', 'reu', 'querelad']
                ):
                    if any(k in combined for k in ['cpf', 'cnpj']):
                        section_data[field['name']] = (
                            case.parte_contraria_cpf_cnpj or ''
                        )
                    else:
                        section_data[field['name']] = case.parte_contraria or ''
                elif any(k in combined for k in ['tribunal', 'juizo', 'juízo']):
                    section_data[field['name']] = case.tribunal or ''
                elif any(k in combined for k in ['vara']):
                    section_data[field['name']] = case.vara_juizo or ''
                elif any(k in combined for k in ['comarca']):
                    section_data[field['name']] = case.comarca or ''
                elif any(k in combined for k in ['valor', 'causa']):
                    section_data[field['name']] = str(case.valor_causa or '')
                elif any(
                    k in combined
                    for k in ['periodo', 'período', 'admiss', 'demiss']
                ):
                    section_data[field['name']] = ''
                elif any(k in combined for k in ['cargo', 'funcao', 'função']):
                    section_data[field['name']] = ''
            if section_data:
                field_data[str(section.order)] = section_data
        return field_data
