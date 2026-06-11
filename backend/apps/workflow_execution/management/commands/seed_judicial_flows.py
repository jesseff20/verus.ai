"""
Management command para criar templates de fluxo judicial pré-definidos.

Uso: python manage.py seed_judicial_flows
     python manage.py seed_judicial_flows --organ <slug>  (para órgão específico)

Cria 10 templates publicados para contexto de Procuradoria:
  1. Processo Judicial — 1º Grau (Cível/Criminal)
  2. Processo Judicial — 2º Grau (Recursal)
  3. Processo Administrativo
  4. Avocação de Processo
  5. Elaboração de Parecer Jurídico
  6. Controle de Prazos com Alerta
  7. Execução Fiscal (Cobrança da Dívida Ativa)
  8. Defesa em Mandado de Segurança (Poder Público no polo passivo)
  9. Ação Civil Pública
 10. Processo Administrativo Disciplinar (PAD)
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
    # ── 7. Execução Fiscal — Cobrança da Dívida Ativa ────────────
    {
        'name': 'Execução Fiscal — Cobrança da Dívida Ativa',
        'description': (
            'Fluxo para propositura e acompanhamento de execução fiscal de crédito tributário '
            'ou não-tributário inscrito em dívida ativa (Lei 6.830/1980).'
        ),
        'category': 'judicial_1',
        'nodes': [
            ('start', 'start_event', 'Inscrição em Dívida Ativa', '', 0,
             'Crédito inscrito em dívida ativa pela unidade de controle financeiro/tributário.'),
            ('t_verificar_cda', 'user_task', 'Verificar CDA e Documentação', 'procurador', 1,
             'Procurador confere a Certidão de Dívida Ativa (CDA): dados do devedor, valor, correção, multa e juros.'),
            ('gw_viavel', 'exclusive_gateway', 'Execução Viável?', '', 2,
             'Verifica se há patrimônio localizável e se a dívida não está prescrita.'),
            ('t_extinguir_adm', 'user_task', 'Promover Extinção Administrativa', 'procurador', 3,
             'Solicitar cancelamento ou remissão conforme lei específica; arquivar.'),
            ('t_distribuir', 'user_task', 'Distribuir Petição Inicial', 'servidor', 4,
             'Preparar e distribuir a petição inicial de execução fiscal na vara competente.'),
            ('t_citar', 'user_task', 'Acompanhar Citação do Executado', 'servidor', 5,
             'Monitorar a citação do executado e o prazo de três dias para pagamento ou nomeação de bens.'),
            ('gw_pagamento', 'exclusive_gateway', 'Pagamento / Parcelamento?', '', 6, ''),
            ('t_penhora', 'user_task', 'Requerer Penhora / SISBAJUD', 'procurador', 7,
             'Requerer penhora eletrônica via SISBAJUD ou penhora de bens indicados pelo exequente.'),
            ('t_embargos', 'user_task', 'Analisar Embargos à Execução', 'procurador', 8,
             'Impugnar ou responder embargos à execução fiscal interpostos pelo executado (Lei 6.830/1980, Art. 16).'),
            ('t_leilao', 'user_task', 'Acompanhar Hasta Pública / Leilão', 'servidor', 9,
             'Acompanhar a hasta pública dos bens penhorados e verificar satisfação do crédito.'),
            ('t_extinguir', 'user_task', 'Promover Extinção da Execução', 'procurador', 10,
             'Requerer extinção após satisfação integral do crédito ou ocorrência de causa extintiva.'),
            ('end', 'end_event', 'Execução Encerrada', '', 11, ''),
        ],
        'edges': [
            ('e1', 'start', 't_verificar_cda', '', ''),
            ('e2', 't_verificar_cda', 'gw_viavel', '', ''),
            ('e3', 'gw_viavel', 't_distribuir', 'yes', 'Viável'),
            ('e4', 'gw_viavel', 't_extinguir_adm', 'no', 'Inviável'),
            ('e5', 't_extinguir_adm', 'end', '', ''),
            ('e6', 't_distribuir', 't_citar', '', ''),
            ('e7', 't_citar', 'gw_pagamento', '', ''),
            ('e8', 'gw_pagamento', 't_extinguir', 'yes', 'Pago/Parcelado'),
            ('e9', 'gw_pagamento', 't_penhora', 'no', 'Sem pagamento'),
            ('e10', 't_penhora', 't_embargos', '', ''),
            ('e11', 't_embargos', 't_leilao', '', ''),
            ('e12', 't_leilao', 't_extinguir', '', ''),
            ('e13', 't_extinguir', 'end', '', ''),
        ],
    },
    # ── 8. Defesa em Mandado de Segurança (Poder Público) ────────
    {
        'name': 'Defesa em Mandado de Segurança',
        'description': (
            'Fluxo para atuação da Procuradoria na defesa do ente público quando o poder '
            'público figura como autoridade coatora em mandado de segurança (Lei 12.016/2009).'
        ),
        'category': 'judicial_1',
        'nodes': [
            ('start', 'start_event', 'Recebimento da Notificação', '', 0,
             'Procuradoria é notificada da impetração do mandado de segurança.'),
            ('t_analisar_ms', 'user_task', 'Analisar o Writ e Ato Impugnado', 'procurador', 1,
             'Procurador analisa o ato administrativo impugnado, os fundamentos do writ e o pedido de liminar.'),
            ('gw_liminar', 'exclusive_gateway', 'Liminar Concedida?', '', 2, ''),
            ('t_contestar_liminar', 'user_task', 'Interpor Agravo / Suspensão de Liminar', 'procurador', 3,
             'Avaliar cabimento de agravo regimental ou pedido de suspensão de liminar (SS/STJ/STF).'),
            ('t_prestar_informacoes', 'user_task', 'Prestar Informações à Autoridade Coatora', 'procurador', 4,
             'Elaborar as informações a serem prestadas pela autoridade coatora ao juízo no prazo de 10 dias.'),
            ('t_revisar_info', 'user_task', 'Revisar e Assinar Informações', 'procurador_geral', 5,
             'PG ou Subprocurador revisa as informações e autoriza o protocolo.'),
            ('t_protocolar', 'user_task', 'Protocolar Informações', 'servidor', 6,
             'Servidor protocola as informações no sistema judicial (PJe/EPROC) dentro do prazo.'),
            ('t_acompanhar', 'user_task', 'Acompanhar Julgamento', 'procurador', 7,
             'Monitorar publicações, agendar sustentação oral se cabível e acompanhar o julgamento.'),
            ('gw_resultado', 'exclusive_gateway', 'MS Concedido?', '', 8, ''),
            ('t_recurso', 'user_task', 'Interpor Recurso (Apelação / RO)', 'procurador', 9,
             'Interpor apelação ou recurso ordinário contra concessão do MS em favor do impetrante.'),
            ('t_cumprir_decisao', 'user_task', 'Orientar Cumprimento da Decisão', 'procurador', 10,
             'Orientar a autoridade coatora quanto ao cumprimento da decisão e comunicar à área técnica.'),
            ('end', 'end_event', 'Processo Encerrado', '', 11, ''),
        ],
        'edges': [
            ('e1', 'start', 't_analisar_ms', '', ''),
            ('e2', 't_analisar_ms', 'gw_liminar', '', ''),
            ('e3', 'gw_liminar', 't_contestar_liminar', 'yes', 'Liminar concedida'),
            ('e4', 'gw_liminar', 't_prestar_informacoes', 'no', 'Sem liminar'),
            ('e5', 't_contestar_liminar', 't_prestar_informacoes', '', ''),
            ('e6', 't_prestar_informacoes', 't_revisar_info', '', ''),
            ('e7', 't_revisar_info', 't_protocolar', '', ''),
            ('e8', 't_protocolar', 't_acompanhar', '', ''),
            ('e9', 't_acompanhar', 'gw_resultado', '', ''),
            ('e10', 'gw_resultado', 't_recurso', 'yes', 'MS concedido'),
            ('e11', 'gw_resultado', 'end', 'no', 'MS denegado'),
            ('e12', 't_recurso', 't_cumprir_decisao', '', ''),
            ('e13', 't_cumprir_decisao', 'end', '', ''),
        ],
    },
    # ── 9. Ação Civil Pública ─────────────────────────────────────
    {
        'name': 'Ação Civil Pública',
        'description': (
            'Fluxo para propositura e acompanhamento de Ação Civil Pública pela Procuradoria '
            'na tutela de interesses difusos, coletivos ou individuais homogêneos (Lei 7.347/1985).'
        ),
        'category': 'judicial_1',
        'nodes': [
            ('start', 'start_event', 'Identificação do Dano/Ameaça', '', 0,
             'Identificação de dano ou ameaça a interesse difuso ou coletivo que justifique a ACP.'),
            ('t_investigar', 'user_task', 'Investigar e Reunir Provas', 'procurador', 1,
             'Levantamento de provas, laudos periciais, documentos e depoimentos.'),
            ('t_ic', 'user_task', 'Instaurar Inquérito Civil (se necessário)', 'procurador', 2,
             'Instaurar IC para coleta de provas antes de ajuizar a ACP, se necessário.'),
            ('gw_ajuizamento', 'exclusive_gateway', 'Ajuizamento Necessário?', '', 3,
             'Avaliar se o TAC (Termo de Ajustamento de Conduta) é suficiente ou se é necessário ajuizar.'),
            ('t_tac', 'user_task', 'Celebrar TAC', 'procurador', 4,
             'Negociar e assinar Termo de Ajustamento de Conduta com o responsável pelo dano.'),
            ('t_elaborar_inicial', 'user_task', 'Elaborar Petição Inicial da ACP', 'procurador', 5,
             'Redigir petição inicial com pedido de tutela de urgência se cabível.'),
            ('t_revisar', 'user_task', 'Revisão e Autorização', 'procurador_geral', 6,
             'PG ou Subprocurador revisa e autoriza o ajuizamento.'),
            ('t_distribuir', 'user_task', 'Distribuir e Protocolar', 'servidor', 7,
             'Protocolar a ação no sistema eletrônico competente.'),
            ('t_acompanhar', 'user_task', 'Acompanhar Instrução e Julgamento', 'procurador', 8,
             'Acompanhar citações, audiências, produção de provas, memoriais e julgamento.'),
            ('t_execucao', 'user_task', 'Executar Sentença / Monitorar TAC', 'procurador', 9,
             'Fiscalizar o cumprimento da sentença ou do TAC celebrado.'),
            ('end', 'end_event', 'ACP Encerrada', '', 10, ''),
        ],
        'edges': [
            ('e1', 'start', 't_investigar', '', ''),
            ('e2', 't_investigar', 't_ic', '', ''),
            ('e3', 't_ic', 'gw_ajuizamento', '', ''),
            ('e4', 'gw_ajuizamento', 't_elaborar_inicial', 'yes', 'Ajuizar'),
            ('e5', 'gw_ajuizamento', 't_tac', 'no', 'TAC'),
            ('e6', 't_tac', 't_execucao', '', ''),
            ('e7', 't_elaborar_inicial', 't_revisar', '', ''),
            ('e8', 't_revisar', 't_distribuir', '', ''),
            ('e9', 't_distribuir', 't_acompanhar', '', ''),
            ('e10', 't_acompanhar', 't_execucao', '', ''),
            ('e11', 't_execucao', 'end', '', ''),
        ],
    },
    # ── 10. Processo Administrativo Disciplinar (PAD) ─────────────
    {
        'name': 'Processo Administrativo Disciplinar (PAD)',
        'description': (
            'Fluxo para condução do Processo Administrativo Disciplinar visando à apuração '
            'de infração funcional de agente público (Lei 8.112/1990 e equivalentes estaduais/municipais).'
        ),
        'category': 'administrative',
        'nodes': [
            ('start', 'start_event', 'Conhecimento do Fato', '', 0,
             'Autoridade toma conhecimento de possível infração disciplinar.'),
            ('t_sindicancia', 'user_task', 'Sindicância Investigativa', 'procurador', 1,
             'Instaurar sindicância para apuração sumária dos fatos e identificação dos envolvidos.'),
            ('gw_pad', 'exclusive_gateway', 'PAD Necessário?', '', 2,
             'Avaliar gravidade: se a infração comportar demissão, suspensão >30 dias ou cassação, instaurar PAD.'),
            ('t_arquivar_sin', 'user_task', 'Arquivar / Penalidade Leve', 'procurador', 3,
             'Arquivar por insuficiência de provas ou aplicar penalidade leve (advertência/suspensão ≤30 dias).'),
            ('t_instaurar_pad', 'user_task', 'Instaurar PAD e Nomear Comissão', 'procurador_geral', 4,
             'Autoridade competente instaura o PAD por portaria, nomeando comissão processante.'),
            ('t_instrucao', 'user_task', 'Instrução Processual', 'procurador', 5,
             'Comissão notifica o indiciado, colhe depoimentos, realiza diligências e produz relatório.'),
            ('t_defesa', 'user_task', 'Defesa Escrita do Indiciado', 'procurador', 6,
             'Aguardar e analisar a defesa escrita do servidor indiciado no prazo legal.'),
            ('t_relatorio', 'user_task', 'Elaborar Relatório Final', 'procurador', 7,
             'Comissão elabora relatório conclusivo com indicação de penalidade ou absolvição.'),
            ('t_julgamento', 'user_task', 'Julgamento pela Autoridade Competente', 'procurador_geral', 8,
             'Autoridade julgadora aplica penalidade ou absolve, com base no relatório da comissão.'),
            ('gw_recurso', 'exclusive_gateway', 'Recurso Interposto?', '', 9, ''),
            ('t_analisar_recurso', 'user_task', 'Analisar Recurso Administrativo', 'procurador', 10,
             'Comissão revisora ou autoridade superior analisa o recurso do servidor punido.'),
            ('t_encerrar', 'user_task', 'Registrar e Arquivar PAD', 'servidor', 11,
             'Registrar a decisão no assentamento funcional e arquivar o processo.'),
            ('end', 'end_event', 'PAD Encerrado', '', 12, ''),
        ],
        'edges': [
            ('e1', 'start', 't_sindicancia', '', ''),
            ('e2', 't_sindicancia', 'gw_pad', '', ''),
            ('e3', 'gw_pad', 't_instaurar_pad', 'yes', 'PAD necessário'),
            ('e4', 'gw_pad', 't_arquivar_sin', 'no', 'Encerrar'),
            ('e5', 't_arquivar_sin', 'end', '', ''),
            ('e6', 't_instaurar_pad', 't_instrucao', '', ''),
            ('e7', 't_instrucao', 't_defesa', '', ''),
            ('e8', 't_defesa', 't_relatorio', '', ''),
            ('e9', 't_relatorio', 't_julgamento', '', ''),
            ('e10', 't_julgamento', 'gw_recurso', '', ''),
            ('e11', 'gw_recurso', 't_analisar_recurso', 'yes', 'Com recurso'),
            ('e12', 'gw_recurso', 't_encerrar', 'no', 'Sem recurso'),
            ('e13', 't_analisar_recurso', 't_encerrar', '', ''),
            ('e14', 't_encerrar', 'end', '', ''),
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
