"""Remove TODOS os validadores de seções do blueprint TR."""
from apps.intelligent_assistant.models import BlueprintSection, DocumentBlueprint

tr_bp = DocumentBlueprint.objects.filter(
    document_type__code='termo_referencia', is_active=True
).first()

if not tr_bp:
    print("Blueprint TR não encontrado")
else:
    sections = BlueprintSection.objects.filter(
        blueprint=tr_bp, validator_agent__isnull=False
    ).select_related('validator_agent')
    count = 0
    for s in sections:
        name = s.validator_agent.name
        s.validator_agent = None
        s.save(update_fields=['validator_agent'])
        count += 1
        print(f"  §{s.section_number}: validador '{name}' removido")
    print(f"\nTotal: {count} validadores removidos de seções TR")
