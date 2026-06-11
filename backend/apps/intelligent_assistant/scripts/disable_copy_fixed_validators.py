"""
Desvincula validator_agent de BlueprintSections cujo SectionImportConfig
tem import_type 'copy' ou 'fixed'. NÃO deleta os SectionAgentConfig.
"""
from apps.intelligent_assistant.models import SectionImportConfig

configs = SectionImportConfig.objects.filter(
    import_type__in=['copy', 'fixed'],
    is_active=True,
).select_related('target_section', 'target_section__validator_agent')

count = 0
for cfg in configs:
    section = cfg.target_section
    if section.validator_agent:
        agent_name = section.validator_agent.name
        section.validator_agent = None
        section.save(update_fields=['validator_agent'])
        count += 1
        print(f"  §{section.section_number} ({cfg.import_type}): validador '{agent_name}' desvinculado")
    else:
        print(f"  §{section.section_number} ({cfg.import_type}): já sem validador")

print(f"\nTotal: {count} validadores desvinculados")
