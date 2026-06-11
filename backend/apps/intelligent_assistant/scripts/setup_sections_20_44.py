"""
Configura §20 como OU (sub-seções) e §44 como fixed (instructions).
§45 já tem section_fields — não precisa de alteração.
"""
from apps.intelligent_assistant.models import (
    BlueprintSection, BlueprintSubSection, DocumentBlueprint, SectionImportConfig
)

tr_bp = DocumentBlueprint.objects.filter(
    document_type__code='termo_referencia', is_active=True
).first()
print(f"TR Blueprint: {tr_bp.name}\n")

# ============================================================
# §20 — OU: sem mão de obra / com mão de obra (Decreto 49.233)
# ============================================================
s20 = BlueprintSection.objects.filter(blueprint=tr_bp, section_number=20).first()

# Atualizar nome da seção
s20.section_name = "Previsão de percentual mínimo de mão de obra (mulheres vítimas de violência doméstica)"
s20.save(update_fields=['section_name'])

# Sub-seção 1: Sem mão de obra (padrão)
sub1, created1 = BlueprintSubSection.objects.get_or_create(
    section=s20,
    sub_key='sem_mao_de_obra',
    defaults={
        'sub_name': 'Sem contratação de mão de obra',
        'sub_number': '20',
        'order': 1,
        'is_active': True,
        'is_required': False,
        'default_text': (
            "20. PREVISÃO DE PERCENTUAL MÍNIMO DE MÃO DE OBRA RESPONSÁVEL PELA "
            "EXECUÇÃO DO OBJETO DA CONTRATAÇÃO CONSTITUÍDO POR MULHERES VÍTIMAS "
            "DE VIOLÊNCIA DOMÉSTICA\n\n"
            "20.1 Em razão das características do objeto, não haverá contratação "
            "de mão de obra para a sua execução."
        ),
    }
)
print(f"§20 sub 1 (sem_mao_de_obra): {'criada' if created1 else 'já existia'}")

# Sub-seção 2: Com mão de obra (Decreto 49.233/2024)
texto_decreto = (
    "20. PREVISÃO DE PERCENTUAL MÍNIMO DE MÃO DE OBRA RESPONSÁVEL PELA "
    "EXECUÇÃO DO OBJETO DA CONTRATAÇÃO CONSTITUÍDO POR MULHERES VÍTIMAS "
    "DE VIOLÊNCIA DOMÉSTICA\n\n"
    "20.1 Conforme disposição do Decreto estadual n° 49.233/2024, o edital de licitação "
    "para contratação de mão de obra responsável pela execução do objeto deve prever o "
    "emprego de mão de obra constituída por mulheres vítimas de violência doméstica e "
    "familiar, em percentual mínimo de 5% (cinco por cento) das vagas. Essa disposição "
    "se aplica a contratos com quantitativos mínimos de 25 (vinte e cinco) trabalhadores.\n\n"
    "20.2 O percentual de reserva de vagas para mulheres vítimas de violência doméstica "
    "e familiar de que trata o Decreto supracitado, deverá ser mantido durante toda a "
    "execução contratual, devendo a empresa contratada providenciar nova seleção de "
    "pessoal sempre que necessário.\n\n"
    "20.3 A indisponibilidade de mão de obra com a qualificação necessária para "
    "atendimento do objeto contratual não caracteriza descumprimento do percentual de "
    "reserva de vagas, desde que devidamente justificado e comprovado.\n\n"
    "20.4 Se durante a execução contratual, a empresa deixar de cumprir as obrigações "
    "previstas no Decreto estadual n° 49.233/2024, o órgão ou entidade contratante "
    "notificará a contratada para que regularize a situação.\n\n"
    "20.5 Havendo a dispensa de pessoa contratada em cumprimento ao disposto no Decreto "
    "supra, a empresa contratada deverá proceder sua comunicação ao fiscal do contrato "
    "ou ao responsável indicado pela contratante em até 5 (cinco) dias corridos.\n\n"
    "20.6 Após a dispensa ou outro fato que impeça o cumprimento do percentual da "
    "contratação de mulher vítima de violência doméstica e familiar, a contratada deverá, "
    "em até 30 (trinta) dias corridos, providenciar o preenchimento da vaga em aberto "
    "para fins de regularização.\n\n"
    "20.7 As mulheres vítimas de violência doméstica e familiar contratadas devem possuir "
    "os mesmos direitos concedidos aos demais empregados.\n\n"
    "20.8 Os contratos firmados em cumprimento ao disposto no art. 3° do Decreto de "
    "referência somente poderão ser prorrogados mediante comprovação de manutenção da "
    "contratação do número de mulheres vítimas de violência doméstica.\n\n"
    "20.9 A não observância das regras previstas no Decreto supra durante o período de "
    "execução contratual caracteriza descumprimento de cláusula contratual, sem prejuízo "
    "das sanções legais pertinentes.\n\n"
    "20.10 Serão sigilosos os dados pessoais das mulheres vítimas de violência doméstica "
    "e familiar destinadas às vagas de que trata o art. 3º do Decreto referido e o acesso "
    "às informações deve ser reservado aos órgãos competentes do poder público, conforme "
    "dispõem as Leis n° 13.709/2018 e 11.340/2006.\n\n"
    "20.11 A empresa contratada deverá adotar medidas preventivas de segurança, elaborar "
    "planos de contingência, realizar auditorias e investigar suspeitas ou incidentes de "
    "violação de dados, bem como notificar as autoridades competentes e as mulheres "
    "contratadas, caso haja violação no sigilo e segurança de seus dados.\n\n"
    "20.12 A empresa contratada deverá manter políticas e práticas atualizadas para "
    "acompanhar mudanças nas leis de proteção de dados e ameaças à segurança da informação "
    "e observar durante a execução contratual, as demais disposições do Decreto estadual "
    "n° 49.233/2024."
)

sub2, created2 = BlueprintSubSection.objects.get_or_create(
    section=s20,
    sub_key='com_mao_de_obra',
    defaults={
        'sub_name': 'Com contratação de mão de obra (Decreto 49.233/2024)',
        'sub_number': '20',
        'order': 2,
        'is_active': True,
        'is_required': False,
        'default_text': texto_decreto,
    }
)
print(f"§20 sub 2 (com_mao_de_obra): {'criada' if created2 else 'já existia'}")

# Atualizar SectionImportConfig para OU
cfg20 = SectionImportConfig.objects.filter(target_section=s20).first()
if cfg20:
    cfg20.import_type = 'ou'
    cfg20.label = 'OU: sem/com mão de obra (Decreto 49.233/2024)'
    cfg20.save(update_fields=['import_type', 'label'])
    print(f"§20 SectionImportConfig atualizado para 'ou'")

print()

# ============================================================
# §44 — Fixed (texto padrão)
# ============================================================
s44 = BlueprintSection.objects.filter(blueprint=tr_bp, section_number=44).first()

texto_44 = (
    "44. ANEXOS\n\n"
    "44.1 Abaixo, estão listados os documentos anexos cujas disposições estão em plena "
    "concordância com este Termo de Referência, do qual correspondem a parte integrante "
    "e indissociável:\n\n"
    "I - ESPECIFICAÇÕES TÉCNICAS DO OBJETO (indexador);\n"
    "II - PROVA DE CONCEITO (indexador);\n"
    "III - MODELO DE AUTORIZAÇÃO DE FORNECIMENTO/ORDEM DE SERVIÇO (indexador);\n"
    "IV - MODELO DE TERMO DE RECEBIMENTO PROVISÓRIO (indexador);\n"
    "V - MODELO DE TERMO DE RECEBIMENTO DEFINITIVO (indexador);\n"
    "VI - MODELO DE TERMO DE CONFIDENCIALIDADE (indexador);\n"
    "VII - MODELO DE PLANILHA DE COMPOSIÇÃO DE LANCES (indexador)"
)

s44.instructions = texto_44
s44.save(update_fields=['instructions'])
print(f"§44: instructions preenchido ({len(texto_44)} chars)")

# Atualizar SectionImportConfig para fixed
cfg44 = SectionImportConfig.objects.filter(target_section=s44).first()
if cfg44:
    cfg44.import_type = 'fixed'
    cfg44.label = 'Texto padrão (Anexos)'
    cfg44.save(update_fields=['import_type', 'label'])
    print(f"§44 SectionImportConfig atualizado para 'fixed'")

print()

# ============================================================
# §45 — Já tem section_fields. Só confirmar que está OK.
# ============================================================
s45 = BlueprintSection.objects.filter(blueprint=tr_bp, section_number=45).first()
print(f"§45: section_fields já configurado com {len(s45.section_fields)} campo(s)")
print(f"  → Preenchimento manual (tabela dinâmica). Status 'Aguardando' é CORRETO.")

print("\n✅ Concluído.")
