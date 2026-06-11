"""
Garante que todas as BlueprintSection têm generator_agent e validator_agent.

Lógica de vinculação:
1. Determina o tipo do documento do blueprint (doc_type_code)
2. Seleciona o agente gerador mais adequado para aquele tipo
3. Seleciona o validador especializado para aquela área
4. Vincula à seção se não estiver vinculado

Mapeamento usado:
- peticao_inicial, contestacao, recurso, tutela_urgencia → gerador_civel + validador_civel
- habeas_corpus, mandado_seguranca → gerador_constitucional + validador_civel
- apelacao, agravo_instrumento, embargos → gerador_recursal + validador_civel
- queixa_crime, alegacoes_finais_criminais → gerador_criminal + validador_criminal
- reclamacao_trabalhista, contestacao_trabalhista → gerador_trabalhista + validador_trabalhista
- notificacao_extrajudicial, parecer, contrato, procuracao → gerador_extrajudicial + validador_extrajudicial
- acao_alimentos, divorcio_*, guarda, inventario → gerador_familia + validador_familia
- consumidor, indenizacao_consumidor → gerador_consumidor + validador_consumidor
- previdenciario, inss, bpc → gerador_previdenciario + validador_previdenciario
- lgpd, digital, privacidade → gerador_digital_lgpd + validador_lgpd
- tributario, auto_infracao → gerador_constitucional + validador_tributario
- administrativo, recurso_adm → gerador_extrajudicial + validador_administrativo

Usage:
    python manage.py ensure_blueprint_agents
    python manage.py ensure_blueprint_agents --dry-run
    python manage.py ensure_blueprint_agents --force   # Sobrescreve vínculos existentes
"""
from django.core.management.base import BaseCommand
from apps.intelligent_assistant.models.blueprint import DocumentBlueprint, BlueprintSection
from apps.intelligent_assistant.models.agent import SectionAgentConfig


# Mapeamento: padrões de nome no doc_type_code → chave do agente gerador
GENERATOR_MAP = {
    # Cível geral
    'peticao_inicial': 'gerador_civel',
    'contestacao': 'gerador_civel',
    'recurso': 'gerador_recursal',
    'tutela_urgencia': 'gerador_constitucional',
    'impugnacao': 'gerador_civel',
    'embargos_declaracao': 'gerador_recursal',
    'embargos_execucao': 'gerador_civel',
    'acao_execucao': 'gerador_civel',
    'impugnacao_cumprimento': 'gerador_civel',
    'excecao_pre_executividade': 'gerador_civel',
    'reconvencao': 'gerador_civel',
    # Constitucional / Remédios
    'habeas_corpus': 'gerador_constitucional',
    'mandado_seguranca': 'gerador_constitucional',
    'acao_popular': 'gerador_constitucional',
    'acao_civil_publica': 'gerador_civel',
    # Recursos
    'apelacao': 'gerador_recursal',
    'agravo_instrumento': 'gerador_recursal',
    'agravo_interno': 'gerador_recursal',
    'agravo_peticao': 'gerador_trabalhista',
    'contrarrazoes_apelacao': 'gerador_recursal',
    'recurso_especial': 'gerador_recursal',
    'recurso_extraordinario': 'gerador_recursal',
    'recurso_ordinario': 'gerador_recursal',
    # Criminal
    'queixa_crime': 'gerador_criminal',
    'alegacoes_finais_criminais': 'gerador_criminal',
    'alegacoes_finais': 'gerador_criminal',
    'defesa_preliminar_criminal': 'gerador_criminal',
    'memoriais': 'gerador_criminal',
    # Trabalhista
    'reclamacao_trabalhista': 'gerador_trabalhista',
    'contestacao_trabalhista': 'gerador_trabalhista',
    'contrato_trabalho': 'gerador_trabalhista',
    'acao_consignacao_trabalhista': 'gerador_trabalhista',
    # Extrajudicial
    'notificacao_extrajudicial': 'gerador_extrajudicial',
    'parecer': 'gerador_extrajudicial',
    'parecer_juridico': 'gerador_extrajudicial',
    'nota_juridica': 'gerador_extrajudicial',
    'contrato': 'gerador_extrajudicial',
    'contrato_particular': 'gerador_extrajudicial',
    'procuracao': 'gerador_extrajudicial',
    # Família / Sucessões
    'acao_alimentos': 'gerador_familia',
    'revisional_alimentos': 'gerador_familia',
    'exoneracao_alimentos': 'gerador_familia',
    'execucao_alimentos': 'gerador_familia',
    'divorcio_consensual': 'gerador_familia',
    'divorcio_litigioso': 'gerador_familia',
    'regulamentacao_guarda': 'gerador_familia',
    'inventario_judicial': 'gerador_familia',
    'inventario_extrajudicial': 'gerador_familia',
    # Consumidor
    'reclamacao_consumerista': 'gerador_consumidor',
    'acao_indenizacao_consumidor': 'gerador_consumidor',
    # Previdenciário
    'peticao_inicial_previdenciaria': 'gerador_previdenciario',
    'bpc_loas': 'gerador_previdenciario',
    'aposentadoria_especial': 'gerador_previdenciario',
    'revisao_beneficio_previdenciario': 'gerador_previdenciario',
    'recurso_administrativo_inss': 'gerador_previdenciario',
    # LGPD / Digital
    'politica_privacidade_lgpd': 'gerador_digital_lgpd',
    'termo_uso_plataforma': 'gerador_digital_lgpd',
    'dpa_tratamento_dados': 'gerador_digital_lgpd',
    'resposta_titular_dados': 'gerador_digital_lgpd',
    'notificacao_incidente_lgpd': 'gerador_digital_lgpd',
    # Constitucional
    'adi': 'gerador_constitucional',
    'adpf': 'gerador_constitucional',
    'habeas_data': 'gerador_constitucional',
    'mandado_injuncao': 'gerador_constitucional',
    'reclamacao_constitucional': 'gerador_constitucional',
    'tutela_cautelar_antecedente': 'gerador_constitucional',
    'tutela_evidencia': 'gerador_constitucional',
    'mandado_seguranca_coletivo': 'gerador_constitucional',
    # Ambiental
    'acao_civil_publica_ambiental': 'gerador_civel',
    'tac_ambiental': 'gerador_extrajudicial',
    'acao_dano_ambiental': 'gerador_civel',
    # Eleitoral
    'aije_eleitoral': 'gerador_civel',
    'aime_eleitoral': 'gerador_civel',
    'recurso_eleitoral': 'gerador_recursal',
    'impugnacao_registro_candidatura': 'gerador_civel',
    # Militar
    'habeas_corpus_militar': 'gerador_criminal',
    'conselho_disciplina_militar': 'gerador_criminal',
    # Internacional
    'carta_rogatoria': 'gerador_civel',
    'homologacao_sentenca_estrangeira': 'gerador_civel',
    'exequatur': 'gerador_civel',
    # Empresarial complemento
    'recuperacao_judicial': 'gerador_civel',
    'falencia': 'gerador_civel',
    'habilitacao_credito_falencia': 'gerador_civel',
    'contrato_social': 'gerador_extrajudicial',
    'acordo_socios': 'gerador_extrajudicial',
    'nda_confidencialidade': 'gerador_extrajudicial',
    # Previdenciário complemento
    'auxilio_doenca_judicial': 'gerador_previdenciario',
    'pensao_morte': 'gerador_previdenciario',
    # Tributário complemento
    'acao_declaratoria_tributaria': 'gerador_constitucional',
    'acao_consignatoria_tributaria': 'gerador_civel',
    # Cível complemento
    'replica_civel': 'gerador_civel',
    'embargos_terceiro': 'gerador_civel',
    'acao_possessoria': 'gerador_civel',
    'usucapiao': 'gerador_civel',
    'acao_rescisoria': 'gerador_civel',
    'obrigacao_fazer_nao_fazer': 'gerador_civel',
    'cumprimento_sentenca': 'gerador_civel',
    'producao_antecipada_provas': 'gerador_civel',
    'embargos_arrematacao': 'gerador_civel',
    'excecao_suspeicao': 'gerador_civel',
    'assistencia_litisconsorcial': 'gerador_civel',
    'contestacao_desapropriacao': 'gerador_civel',
    # Recursal complemento
    'contrarrazoes_agravo_instrumento': 'gerador_recursal',
    'contrarrazoes_recurso_especial': 'gerador_recursal',
    'contrarrazoes_recurso_extraordinario': 'gerador_recursal',
    'embargos_divergencia': 'gerador_recursal',
    'recurso_inominado': 'gerador_recursal',
    'conflito_competencia': 'gerador_recursal',
    'recurso_stjd': 'gerador_recursal',
    # JEC
    'peticao_jec': 'gerador_civel',
    'pedido_contraposto_jec': 'gerador_civel',
    'peticao_jefaz': 'gerador_civel',
    # Agrário
    'usucapiao_rural': 'gerador_civel',
    'possessoria_rural': 'gerador_civel',
    # Sanitário
    'acao_medicamento_sus': 'gerador_civel',
    # Administrativo
    'acao_improbidade': 'gerador_civel',
    'acao_desapropriacao': 'gerador_civel',
}

# Mapeamento: doc_type_code → chave parcial do validador especializado
VALIDATOR_MAP = {
    'peticao_inicial': 'Validador Cível',
    'contestacao': 'Validador Cível',
    'recurso': 'Validador Cível',
    'tutela_urgencia': 'Validador Cível',
    'impugnacao': 'Validador Cível',
    'embargos': 'Validador Cível',
    'acao_execucao': 'Validador Cível',
    'reconvencao': 'Validador Cível',
    'excecao': 'Validador Cível',
    'habeas_corpus': 'Validador Criminal',
    'queixa_crime': 'Validador Criminal',
    'alegacoes_finais': 'Validador Criminal',
    'defesa_preliminar': 'Validador Criminal',
    'memoriais': 'Validador Criminal',
    'mandado_seguranca': 'Validador Administrativo',
    'acao_popular': 'Validador Cível',
    'acao_civil_publica': 'Validador Cível',
    'apelacao': 'Validador Cível',
    'agravo': 'Validador Cível',
    'contrarrazoes': 'Validador Cível',
    'recurso_especial': 'Validador Cível',
    'recurso_extraordinario': 'Validador Cível',
    'reclamacao_trabalhista': 'Validador Trabalhista',
    'contestacao_trabalhista': 'Validador Trabalhista',
    'contrato_trabalho': 'Validador Trabalhista',
    'acao_consignacao_trabalhista': 'Validador Trabalhista',
    'notificacao_extrajudicial': 'Validador Extrajudicial',
    'parecer': 'Validador Extrajudicial',
    'contrato': 'Validador Extrajudicial',
    'procuracao': 'Validador Extrajudicial',
    'acao_alimentos': 'Validador Família',
    'divorcio': 'Validador Família',
    'guarda': 'Validador Família',
    'inventario': 'Validador Família',
    'alimentos': 'Validador Família',
    'consumidor': 'Validador Consumidor',
    'indenizacao_consumidor': 'Validador Consumidor',
    'previdenciario': 'Validador Previdenciário',
    'inss': 'Validador Previdenciário',
    'bpc': 'Validador Previdenciário',
    'aposentadoria': 'Validador Previdenciário',
    'lgpd': 'Validador LGPD',
    'privacidade': 'Validador LGPD',
    'digital': 'Validador LGPD',
    'tributario': 'Validador Tributário',
    'auto_infracao': 'Validador Tributário',
    'administrativo': 'Validador Administrativo',
    'recurso_adm': 'Validador Administrativo',
    # Constitucional
    'adi': 'Validador Constitucional',
    'adpf': 'Validador Constitucional',
    'habeas_data': 'Validador Constitucional',
    'mandado_injuncao': 'Validador Constitucional',
    'reclamacao_constitucional': 'Validador Constitucional',
    'tutela_cautelar_antecedente': 'Validador Constitucional',
    'tutela_evidencia': 'Validador Constitucional',
    'mandado_seguranca_coletivo': 'Validador Constitucional',
    # Ambiental
    'acao_civil_publica_ambiental': 'Validador Ambiental',
    'tac_ambiental': 'Validador Ambiental',
    'acao_dano_ambiental': 'Validador Ambiental',
    # Eleitoral
    'aije_eleitoral': 'Validador Eleitoral',
    'aime_eleitoral': 'Validador Eleitoral',
    'recurso_eleitoral': 'Validador Eleitoral',
    'impugnacao_registro_candidatura': 'Validador Eleitoral',
    # Militar
    'habeas_corpus_militar': 'Validador Criminal',
    'conselho_disciplina_militar': 'Validador Criminal',
    # Internacional
    'carta_rogatoria': 'Validador Cível',
    'homologacao_sentenca_estrangeira': 'Validador Cível',
    'exequatur': 'Validador Cível',
    # Empresarial
    'recuperacao_judicial': 'Validador Empresarial',
    'falencia': 'Validador Empresarial',
    'habilitacao_credito_falencia': 'Validador Empresarial',
    'contrato_social': 'Validador Empresarial',
    'acordo_socios': 'Validador Empresarial',
    'nda_confidencialidade': 'Validador Empresarial',
    # Previdenciário complemento
    'auxilio_doenca_judicial': 'Validador Previdenciário',
    'pensao_morte': 'Validador Previdenciário',
    # Tributário complemento
    'acao_declaratoria_tributaria': 'Validador Tributário',
    'acao_consignatoria_tributaria': 'Validador Tributário',
    # Cível complemento
    'replica_civel': 'Validador Cível',
    'embargos_terceiro': 'Validador Cível',
    'acao_possessoria': 'Validador Cível',
    'usucapiao': 'Validador Cível',
    'acao_rescisoria': 'Validador Cível',
    'obrigacao_fazer_nao_fazer': 'Validador Cível',
    'cumprimento_sentenca': 'Validador Cível',
    'producao_antecipada_provas': 'Validador Cível',
    'embargos_arrematacao': 'Validador Cível',
    'excecao_suspeicao': 'Validador Cível',
    'assistencia_litisconsorcial': 'Validador Cível',
    'contestacao_desapropriacao': 'Validador Cível',
    # Recursal complemento
    'contrarrazoes_agravo_instrumento': 'Validador Cível',
    'contrarrazoes_recurso_especial': 'Validador Cível',
    'contrarrazoes_recurso_extraordinario': 'Validador Cível',
    'embargos_divergencia': 'Validador Cível',
    'recurso_inominado': 'Validador Cível',
    'conflito_competencia': 'Validador Cível',
    # JEC
    'peticao_jec': 'Validador Cível',
    'pedido_contraposto_jec': 'Validador Cível',
    'peticao_jefaz': 'Validador Cível',
    # Agrário
    'usucapiao_rural': 'Validador Cível',
    'possessoria_rural': 'Validador Cível',
    # Sanitário
    'acao_medicamento_sus': 'Validador Cível',
    # Administrativo complemento
    'acao_improbidade': 'Validador Administrativo',
    'acao_desapropriacao': 'Validador Administrativo',
    # Desportivo
    'recurso_stjd': 'Validador Cível',
}

FALLBACK_GENERATOR_KEY = 'gerador_civel'
FALLBACK_VALIDATOR_PARTIAL = 'Validador Jurídico'


def _get_generator(doc_type_code: str) -> SectionAgentConfig | None:
    """Retorna o gerador mais adequado para o doc_type_code."""
    key = GENERATOR_MAP.get(doc_type_code)
    if not key:
        # Busca por substring
        for pattern, agent_key in GENERATOR_MAP.items():
            if pattern in doc_type_code or doc_type_code in pattern:
                key = agent_key
                break
    if not key:
        key = FALLBACK_GENERATOR_KEY

    agent = SectionAgentConfig.objects.filter(
        name__icontains=key.replace('_', ' ').replace('gerador ', ''),
        agent_type='generator',
        is_active=True,
    ).first()

    if not agent:
        # Busca pelo nome exato da chave
        agent = SectionAgentConfig.objects.filter(
            agent_type='generator',
            is_active=True,
        ).first()

    return agent


def _get_validator(doc_type_code: str) -> SectionAgentConfig | None:
    """Retorna o validador especializado para o doc_type_code."""
    partial = None
    for pattern, val_partial in VALIDATOR_MAP.items():
        if pattern in doc_type_code or doc_type_code in pattern:
            partial = val_partial
            break

    if partial:
        agent = SectionAgentConfig.objects.filter(
            name__icontains=partial,
            agent_type='validator',
            is_active=True,
        ).first()
        if agent:
            return agent

    # Fallback: validador jurídico geral
    return SectionAgentConfig.objects.filter(
        name__icontains=FALLBACK_VALIDATOR_PARTIAL,
        agent_type='validator',
        is_active=True,
    ).first()


class Command(BaseCommand):
    help = 'Vincula generator_agent e validator_agent a todas as BlueprintSection'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true',
                            help='Simula sem salvar')
        parser.add_argument('--force', action='store_true',
                            help='Sobrescreve vínculos existentes')

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        force = options.get('force', False)

        self.stdout.write('\n' + '=' * 65)
        self.stdout.write('LINK: Vinculando agentes a seções de blueprints')
        if dry_run:
            self.stdout.write('  [DRY-RUN — nada será salvo]')
        self.stdout.write('=' * 65 + '\n')

        total_agents = SectionAgentConfig.objects.count()
        if total_agents == 0:
            self.stdout.write(self.style.ERROR(
                '  ERRO: Nenhum SectionAgentConfig encontrado.\n'
                '  Execute primeiro: python manage.py seed_juridico_completo\n'
                '  E depois:         python manage.py update_agents_watsonx\n'
            ))
            return

        blueprints = DocumentBlueprint.objects.filter(is_active=True).prefetch_related('sections')
        total_sections = 0
        linked_generator = 0
        linked_validator = 0
        skipped = 0

        for bp in blueprints:
            doc_type_code = ''
            if hasattr(bp, 'document_type') and bp.document_type:
                doc_type_code = bp.document_type.code if hasattr(bp.document_type, 'code') else str(bp.document_type)

            generator = _get_generator(doc_type_code)
            validator = _get_validator(doc_type_code)

            sections = bp.sections.filter(is_active=True) if hasattr(bp, 'sections') else []

            for section in sections:
                total_sections += 1
                changed = False

                if (not section.generator_agent or force) and generator:
                    if not dry_run:
                        section.generator_agent = generator
                    linked_generator += 1
                    changed = True

                if (not section.validator_agent or force) and validator:
                    if not dry_run:
                        section.validator_agent = validator
                    linked_validator += 1
                    changed = True

                if changed and not dry_run:
                    section.save(update_fields=['generator_agent', 'validator_agent'])
                elif not changed:
                    skipped += 1

            self.stdout.write(self.style.HTTP_INFO(
                f'  Blueprint: {bp.name[:50]:<50} '
                f'[{doc_type_code:>30}] '
                f'{sections.count() if hasattr(sections, "count") else "?"} seções'
            ))

        self.stdout.write('\n' + '=' * 65)
        self.stdout.write(self.style.SUCCESS('RESUMO'))
        self.stdout.write('=' * 65)
        self.stdout.write(f'  Blueprints processados: {blueprints.count()}')
        self.stdout.write(f'  Seções total:           {total_sections}')
        self.stdout.write(f'  Geradores vinculados:   {linked_generator}')
        self.stdout.write(f'  Validadores vinculados: {linked_validator}')
        self.stdout.write(f'  Já vinculados (skip):   {skipped}')
        if dry_run:
            self.stdout.write(self.style.WARNING('  [DRY-RUN — nenhuma alteração salva]'))
        self.stdout.write('\n' + '=' * 65 + '\n')
        self.stdout.write(self.style.SUCCESS(
            '\nPara executar em produção:\n'
            '  1. python manage.py seed_juridico_completo --force\n'
            '  2. python manage.py criar_agentes_especializados --force\n'
            '  3. python manage.py update_agents_watsonx --force\n'
            '  4. python manage.py ensure_blueprint_agents --force\n'
            '  5. python manage.py seed_watsonx_agents --force\n'
        ))
