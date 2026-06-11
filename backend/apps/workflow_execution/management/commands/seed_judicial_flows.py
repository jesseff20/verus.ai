"""
Management command para criar templates de fluxo judicial pré-definidos.

Uso: python manage.py seed_judicial_flows
     python manage.py seed_judicial_flows --organ <slug>  (para órgão específico)

Cria 6 templates publicados:
  1. Processo Judicial — 1º Grau (Cível/Criminal)
  2. Processo Judicial — 2º Grau (Recursal)
  3. Processo Administrativo
  4. Avocação de Processo
  5. Elaboração de Parecer Jurídico
  6. Controle de Prazos com Alerta
"""
import uuid
from django.core.management.base import BaseCommand
from apps.workflow_definition.models import FlowTemplate, FlowNode, FlowEdge


def _node(tpl, node_id, node_type, label, role='', order=0, description=''):
    return FlowNode.objects.create(
        template=tpl, node_id=node_id, node_type=node_type,
        label=label, role=role, order=order, description=description,
        position={'x': order * 180, 'y': 100},
    )


def _edge(tpl, edge_id, source, target, handle='', label=''):
    return FlowEdge.objects.create(
        template=tpl, edge_id=edge_id,
        source_node_id=source, target_node_id=target,
        source_handle=handle, label=label,
    )


def _publish(tpl):
    tpl.status = 'published'
    tpl.save(update_fields=['status'])
    return tpl


TEMPLATES = [
    # ── 1. Processo Judicial 1º Grau ──────────────────────────────
    {
        'name': 'Processo Judicial — 1º Grau',
        'description': 'Fluxo padrão para tramitação de processos judiciais em primeira instância cível ou criminal.',
        'category': 'judicial_1',
        'nodes': [
            ('start', 'start_event', 'Recebimento', '', 0, 'Processo recebido na distribuição.'),
            ('t_distribuir', 'user_task', 'Distribuição do Processo', 'distribuidor', 1,
             'Distribuidor verifica dados do processo (número CNJ, tipo, vara) e atribui ao procurador responsável.'),
            ('t_analisar', 'user_task', 'Análise Inicial', 'procurador', 2,
             'Procurador analisa o processo, verifica documentos e decide a estratégia processual.'),
            ('gw_contestar', 'exclusive_gateway', 'Requer Manifestação?', '', 3, ''),
            ('t_elaborar', 'user_task', 'Elaborar Peça/Manifestação', 'procurador', 4,
             'Redação da peça processual (contestação, resposta, recurso, etc.).'),
            ('t_revisar', 'user_task', 'Revisão e Assinatura', 'procurador_geral', 5,
             'Gerente ou Procurador-Geral revisa e autoriza o peticionamento.'),
            ('t_protocolar', 'user_task', 'Protocolar no Sistema', 'servidor', 6,
             'Servidor protocoliza a peça no sistema eletrônico (PJe/EPROC).'),
            ('t_arquivar', 'user_task', 'Arquivar/Aguardar Prazo', 'servidor', 7,
             'Processo arquivado aguardando próxima movimentação do tribunal.'),
            ('end', 'end_event', 'Concluído', '', 8, ''),
        ],
        'edges': [
            ('e1', 'start', 't_distribuir', '', ''),
            ('e2', 't_distribuir', 't_analisar', '', ''),
            ('e3', 't_analisar', 'gw_contestar', '', ''),
            ('e4', 'gw_contestar', 't_elaborar', 'yes', 'Sim'),
            ('e5', 'gw_contestar', 't_arquivar', 'no', 'Não (aguardar)'),
            ('e6', 't_elaborar', 't_revisar', '', ''),
            ('e7', 't_revisar', 't_protocolar', '', ''),
            ('e8', 't_protocolar', 't_arquivar', '', ''),
            ('e9', 't_arquivar', 'end', '', ''),
        ],
    },
    # ── 2. Processo Judicial 2º Grau ─────────────────────────────
    {
        'name': 'Processo Judicial — 2º Grau (Recursal)',
        'description': 'Fluxo para tramitação de recursos em segunda instância (TRF, TRT, TJ).',
        'category': 'judicial_2',
        'nodes': [
            ('start', 'start_event', 'Recebimento do Recurso', '', 0, ''),
            ('t_triagem', 'user_task', 'Triagem do Recurso', 'distribuidor', 1,
             'Verificar admissibilidade, tipo de recurso e prazo.'),
            ('gw_admissivel', 'exclusive_gateway', 'Recurso Admissível?', '', 2, ''),
            ('t_contrarrazoar', 'user_task', 'Elaborar Contrarrazões', 'procurador', 3,
             'Redação das contrarrazões ao recurso interposto pela parte contrária.'),
            ('t_parecer', 'user_task', 'Parecer Técnico', 'procurador_geral', 4,
             'Procurador-Geral ou Subprocurador-Geral emite parecer sobre o mérito recursal.'),
            ('t_protocolar', 'user_task', 'Protocolar Contrarrazões', 'servidor', 5, ''),
            ('t_inadmitir', 'user_task', 'Informar Inadmissibilidade', 'procurador', 6,
             'Documentar e comunicar a inadmissibilidade do recurso.'),
            ('end', 'end_event', 'Concluído', '', 7, ''),
        ],
        'edges': [
            ('e1', 'start', 't_triagem', '', ''),
            ('e2', 't_triagem', 'gw_admissivel', '', ''),
            ('e3', 'gw_admissivel', 't_contrarrazoar', 'yes', 'Admissível'),
            ('e4', 'gw_admissivel', 't_inadmitir', 'no', 'Inadmissível'),
            ('e5', 't_contrarrazoar', 't_parecer', '', ''),
            ('e6', 't_parecer', 't_protocolar', '', ''),
            ('e7', 't_protocolar', 'end', '', ''),
            ('e8', 't_inadmitir', 'end', '', ''),
        ],
    },
    # ── 3. Processo Administrativo ────────────────────────────────
    {
        'name': 'Processo Administrativo',
        'description': 'Fluxo para tramitação de processos administrativos, licitações, contratos e normas.',
        'category': 'administrative',
        'nodes': [
            ('start', 'start_event', 'Recebimento', '', 0, ''),
            ('t_triagem', 'user_task', 'Triagem Administrativa', 'distribuidor', 1,
             'Classificar o processo (licitação, contrato, servidor, etc.) e direcionar.'),
            ('t_analisar', 'user_task', 'Análise Jurídica', 'procurador', 2,
             'Análise da legalidade, conformidade e risco jurídico.'),
            ('t_nota', 'user_task', 'Elaborar Nota Técnica / Parecer', 'procurador', 3,
             'Elaboração da nota técnica ou parecer jurídico fundamentado.'),
            ('t_aprovar', 'user_task', 'Aprovação da Nota', 'procurador_geral', 4,
             'Procurador-Geral ou Gerente aprova, solicita ajustes ou rejeita o parecer.'),
            ('gw_aprovado', 'exclusive_gateway', 'Nota Aprovada?', '', 5, ''),
            ('t_publicar', 'user_task', 'Publicar / Arquivar', 'servidor', 6,
             'Publicação da nota no diário oficial ou arquivamento com número de parecer.'),
            ('t_revisar', 'user_task', 'Revisar Nota', 'procurador', 7, 'Corrigir conforme orientação do superior.'),
            ('end', 'end_event', 'Concluído', '', 8, ''),
        ],
        'edges': [
            ('e1', 'start', 't_triagem', '', ''),
            ('e2', 't_triagem', 't_analisar', '', ''),
            ('e3', 't_analisar', 't_nota', '', ''),
            ('e4', 't_nota', 't_aprovar', '', ''),
            ('e5', 't_aprovar', 'gw_aprovado', '', ''),
            ('e6', 'gw_aprovado', 't_publicar', 'yes', 'Aprovada'),
            ('e7', 'gw_aprovado', 't_revisar', 'no', 'Ajustes'),
            ('e8', 't_revisar', 't_aprovar', '', ''),
            ('e9', 't_publicar', 'end', '', ''),
        ],
    },
    # ── 4. Avocação de Processo ───────────────────────────────────
    {
        'name': 'Avocação de Processo',
        'description': 'Fluxo para avocação formal de processo pelo Procurador-Geral ou Subprocurador.',
        'category': 'judicial_1',
        'nodes': [
            ('start', 'start_event', 'Solicitação de Avocação', '', 0, ''),
            ('t_justificar', 'user_task', 'Justificar Avocação', 'procurador_geral', 1,
             'PG ou Subprocurador documenta a motivação para avocar o processo.'),
            ('t_notificar', 'user_task', 'Notificar Procurador Anterior', 'distribuidor', 2,
             'Notificação formal ao procurador que estava com o processo.'),
            ('t_transferir', 'user_task', 'Transferir Responsabilidade', 'distribuidor', 3,
             'Registro da transferência no sistema e atribuição ao novo responsável.'),
            ('t_assumir', 'user_task', 'Assumir o Processo', 'procurador_geral', 4,
             'PG ou Subprocurador assume formalmente e registra os próximos passos.'),
            ('end', 'end_event', 'Concluído', '', 5, ''),
        ],
        'edges': [
            ('e1', 'start', 't_justificar', '', ''),
            ('e2', 't_justificar', 't_notificar', '', ''),
            ('e3', 't_notificar', 't_transferir', '', ''),
            ('e4', 't_transferir', 't_assumir', '', ''),
            ('e5', 't_assumir', 'end', '', ''),
        ],
    },
    # ── 5. Elaboração de Parecer Jurídico ─────────────────────────
    {
        'name': 'Elaboração de Parecer Jurídico',
        'description': 'Fluxo para solicitação, elaboração, revisão e publicação de pareceres jurídicos.',
        'category': 'administrative',
        'nodes': [
            ('start', 'start_event', 'Solicitação de Parecer', '', 0, ''),
            ('t_distribuir', 'user_task', 'Distribuir para Procurador', 'gerente', 1,
             'Gerente recebe a solicitação e distribui conforme competência e especialidade.'),
            ('t_pesquisar', 'user_task', 'Pesquisa Jurídica', 'procurador', 2,
             'Levantamento doutrinário, jurisprudencial e normativo sobre a matéria.'),
            ('t_redigir', 'user_task', 'Redigir Parecer', 'procurador', 3,
             'Redação completa do parecer com fundamentação, análise e conclusão.'),
            ('t_revisar_gerente', 'user_task', 'Revisão pelo Gerente', 'gerente', 4,
             'Gerente revisa qualidade técnica, conformidade e clareza.'),
            ('gw_ok', 'exclusive_gateway', 'Aprovado?', '', 5, ''),
            ('t_assinar', 'user_task', 'Assinar e Registrar', 'procurador_geral', 6,
             'PG ou Subprocurador assina e registra o número do parecer.'),
            ('t_ajustar', 'user_task', 'Ajustar Parecer', 'procurador', 7, 'Corrigir conforme orientação do gerente.'),
            ('end', 'end_event', 'Publicado', '', 8, ''),
        ],
        'edges': [
            ('e1', 'start', 't_distribuir', '', ''),
            ('e2', 't_distribuir', 't_pesquisar', '', ''),
            ('e3', 't_pesquisar', 't_redigir', '', ''),
            ('e4', 't_redigir', 't_revisar_gerente', '', ''),
            ('e5', 't_revisar_gerente', 'gw_ok', '', ''),
            ('e6', 'gw_ok', 't_assinar', 'yes', 'Aprovado'),
            ('e7', 'gw_ok', 't_ajustar', 'no', 'Ajustes necessários'),
            ('e8', 't_ajustar', 't_revisar_gerente', '', ''),
            ('e9', 't_assinar', 'end', '', ''),
        ],
    },
    # ── 6. Controle de Prazo com Escalação ───────────────────────
    {
        'name': 'Controle de Prazo Processual',
        'description': 'Fluxo para monitoramento e cumprimento de prazos com alerta e escalação automática.',
        'category': 'judicial_1',
        'nodes': [
            ('start', 'start_event', 'Alerta de Prazo', '', 0, ''),
            ('t_verificar', 'user_task', 'Verificar Prazo no Tribunal', 'servidor', 1,
             'Servidor acessa o sistema do tribunal e confirma o prazo exato.'),
            ('t_atribuir', 'user_task', 'Atribuir ao Procurador', 'distribuidor', 2,
             'Distribuidor atribui urgência e procurador responsável.'),
            ('t_cumprir', 'user_task', 'Cumprir Prazo (Elaborar Peça)', 'procurador', 3,
             'Procurador elabora manifestação dentro do prazo.'),
            ('gw_prazo', 'exclusive_gateway', 'Peça elaborada a tempo?', '', 4, ''),
            ('t_protocolar', 'user_task', 'Protocolar no Prazo', 'servidor', 5, ''),
            ('t_urgencia', 'user_task', 'Acionar Gerência (Urgência)', 'gerente', 6,
             'Prazo em risco — gerente é notificado e toma providências imediatas.'),
            ('end', 'end_event', 'Prazo Cumprido', '', 7, ''),
        ],
        'edges': [
            ('e1', 'start', 't_verificar', '', ''),
            ('e2', 't_verificar', 't_atribuir', '', ''),
            ('e3', 't_atribuir', 't_cumprir', '', ''),
            ('e4', 't_cumprir', 'gw_prazo', '', ''),
            ('e5', 'gw_prazo', 't_protocolar', 'yes', 'A tempo'),
            ('e6', 'gw_prazo', 't_urgencia', 'no', 'Risco de perda'),
            ('e7', 't_urgencia', 't_protocolar', '', ''),
            ('e8', 't_protocolar', 'end', '', ''),
        ],
    },
]


class Command(BaseCommand):
    help = 'Cria templates de fluxo judicial pré-definidos (sistema).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--organ', type=str, default=None,
            help='Slug do órgão. Se omitido, templates ficam como sistema (organ=None).'
        )
        parser.add_argument(
            '--force', action='store_true',
            help='Recria templates mesmo que já existam (por nome).'
        )

    def handle(self, *args, **options):
        organ = None
        if options['organ']:
            from apps.organization.models import Organ
            try:
                organ = Organ.objects.get(slug=options['organ'])
                self.stdout.write(f'Órgão: {organ.name}')
            except Organ.DoesNotExist:
                self.stderr.write(f'Órgão "{options["organ"]}" não encontrado.')
                return

        created = 0
        skipped = 0

        for tdata in TEMPLATES:
            name = tdata['name']
            if not options['force'] and FlowTemplate.objects.filter(
                name=name, is_system_template=True
            ).exists():
                self.stdout.write(f'  Já existe: {name}')
                skipped += 1
                continue

            # Remove se --force
            if options['force']:
                FlowTemplate.objects.filter(name=name, is_system_template=True).delete()

            tpl = FlowTemplate.objects.create(
                name=name,
                description=tdata['description'],
                category=tdata['category'],
                organ=organ,
                is_system_template=True,
                status='draft',
            )

            for (node_id, node_type, label, role, order, desc) in tdata['nodes']:
                _node(tpl, node_id, node_type, label, role, order, desc)

            for (edge_id, source, target, handle, elabel) in tdata['edges']:
                _edge(tpl, edge_id, source, target, handle, elabel)

            _publish(tpl)
            self.stdout.write(self.style.SUCCESS(f'  Criado: {name}'))
            created += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nConcluído: {created} criado(s), {skipped} ignorado(s).'
        ))
