"""Verifica estado atual das seções 20, 44, 45 do TR e ETP §30 (campos tabela)."""
from apps.intelligent_assistant.models import (
    BlueprintSection, BlueprintSubSection, DocumentBlueprint
)
import json

# TR
tr_bp = DocumentBlueprint.objects.filter(
    document_type__code='termo_referencia', is_active=True
).first()
print(f"TR Blueprint: {tr_bp.name} (id={tr_bp.id})\n")

for num in [20, 44, 45]:
    s = BlueprintSection.objects.filter(blueprint=tr_bp, section_number=num).first()
    if s:
        print(f"§{num}: {s.section_name}")
        print(f"  generator_agent: {s.generator_agent}")
        print(f"  validator_agent: {s.validator_agent}")
        print(f"  instructions: {len(s.instructions or '')} chars")
        print(f"  section_fields: {s.section_fields}")
        subs = BlueprintSubSection.objects.filter(section=s, is_active=True)
        print(f"  sub_sections: {subs.count()}")
        for sub in subs:
            print(f"    {sub.sub_key}: {sub.title} (default_text={len(sub.default_text or '')} chars)")
    print()

# ETP §30 - para copiar padrão de section_fields
etp_bp = DocumentBlueprint.objects.filter(
    document_type__code='etp', is_active=True
).first()
print(f"\nETP Blueprint: {etp_bp.name} (id={etp_bp.id})")
etp30 = BlueprintSection.objects.filter(blueprint=etp_bp, section_number=30).first()
if etp30:
    print(f"ETP §30: {etp30.section_name}")
    print(f"  section_fields: {json.dumps(etp30.section_fields, indent=2, ensure_ascii=False)}")
