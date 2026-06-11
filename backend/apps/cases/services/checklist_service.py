"""
Serviço de Checklist por Tipo de Ação — Verus.AI.

Fornece checklists pré-definidos de tarefas por especialidade jurídica,
permitindo criação em massa de CaseTask ao iniciar ou organizar um caso.
"""
from typing import List


# ─────────────────────────────────────────────────────────────────────────────
# CHECKLISTS POR ESPECIALIDADE
# ─────────────────────────────────────────────────────────────────────────────

CHECKLISTS = {
    'trabalhista': [
        {'titulo': 'Reunir documentos do cliente (CTPS, contracheques, contrato)', 'descricao': 'Solicitar ao cliente todos os documentos trabalhistas: CTPS, contracheques, contrato de trabalho, TRCT, extrato FGTS.', 'prioridade': 'alta'},
        {'titulo': 'Analisar verbas rescisórias', 'descricao': 'Verificar cálculo de saldo de salário, férias proporcionais, 13º proporcional, aviso prévio, multa FGTS.', 'prioridade': 'alta'},
        {'titulo': 'Elaborar petição inicial', 'descricao': 'Redigir a petição inicial com pedidos, causa de pedir e valor da causa.', 'prioridade': 'urgente'},
        {'titulo': 'Calcular valor da causa e pedidos', 'descricao': 'Elaborar planilha de cálculos com todos os pedidos e seus valores.', 'prioridade': 'alta'},
        {'titulo': 'Verificar prescrição bienal e quinquenal', 'descricao': 'Conferir se os pedidos estão dentro do prazo prescricional (CLT art. 11).', 'prioridade': 'urgente'},
        {'titulo': 'Juntar procuração e declaração de hipossuficiência', 'descricao': 'Preparar procuração ad judicia e declaração de hipossuficiência para justiça gratuita.', 'prioridade': 'media'},
        {'titulo': 'Pesquisar jurisprudência aplicável', 'descricao': 'Buscar decisões do TRT e TST sobre os temas discutidos no caso.', 'prioridade': 'media'},
        {'titulo': 'Preparar rol de testemunhas', 'descricao': 'Identificar e qualificar testemunhas que possam ser arroladas.', 'prioridade': 'media'},
    ],
    'civel': [
        {'titulo': 'Analisar documentação do cliente', 'descricao': 'Reunir e analisar todos os documentos relevantes para a causa cível.', 'prioridade': 'alta'},
        {'titulo': 'Verificar competência e foro adequado', 'descricao': 'Determinar a competência territorial e material (CPC arts. 42-66).', 'prioridade': 'alta'},
        {'titulo': 'Elaborar petição inicial', 'descricao': 'Redigir petição inicial com qualificação das partes, causa de pedir, pedidos e requerimentos.', 'prioridade': 'urgente'},
        {'titulo': 'Calcular valor da causa', 'descricao': 'Definir o valor da causa conforme CPC art. 291-293.', 'prioridade': 'alta'},
        {'titulo': 'Preparar procuração e documentos obrigatórios', 'descricao': 'Providenciar procuração, documentos pessoais do cliente e comprovante de residência.', 'prioridade': 'alta'},
        {'titulo': 'Pesquisar jurisprudência e doutrina', 'descricao': 'Buscar precedentes nos tribunais superiores e doutrina aplicável.', 'prioridade': 'media'},
        {'titulo': 'Verificar possibilidade de tutela provisória', 'descricao': 'Avaliar cabimento de tutela de urgência ou evidência (CPC arts. 294-311).', 'prioridade': 'media'},
        {'titulo': 'Recolher custas iniciais', 'descricao': 'Emitir e recolher guia de custas judiciais ou requerer justiça gratuita.', 'prioridade': 'media'},
    ],
    'criminal': [
        {'titulo': 'Analisar inquérito policial ou denúncia', 'descricao': 'Examinar detalhadamente o IP ou denúncia para identificar teses defensivas.', 'prioridade': 'urgente'},
        {'titulo': 'Verificar prescrição penal', 'descricao': 'Calcular prazos prescricionais conforme a pena cominada (CP arts. 109-119).', 'prioridade': 'urgente'},
        {'titulo': 'Avaliar possibilidade de habeas corpus', 'descricao': 'Verificar se há constrangimento ilegal que justifique HC.', 'prioridade': 'alta'},
        {'titulo': 'Preparar defesa prévia / resposta à acusação', 'descricao': 'Elaborar resposta à acusação (CPP art. 396-A) com preliminares e mérito.', 'prioridade': 'alta'},
        {'titulo': 'Arrolar testemunhas de defesa', 'descricao': 'Identificar e qualificar testemunhas (limite de 8 no rito ordinário).', 'prioridade': 'alta'},
        {'titulo': 'Analisar provas e laudos periciais', 'descricao': 'Examinar provas documentais, periciais e testemunhais da acusação.', 'prioridade': 'media'},
        {'titulo': 'Verificar nulidades processuais', 'descricao': 'Identificar possíveis nulidades absolutas e relativas no processo.', 'prioridade': 'media'},
        {'titulo': 'Pesquisar jurisprudência penal aplicável', 'descricao': 'Buscar decisões do STF e STJ sobre os temas penais do caso.', 'prioridade': 'media'},
    ],
    'tributario': [
        {'titulo': 'Analisar auto de infração ou cobrança', 'descricao': 'Examinar detalhadamente o auto de infração, CDA ou notificação fiscal.', 'prioridade': 'urgente'},
        {'titulo': 'Verificar prescrição e decadência tributária', 'descricao': 'Conferir prazos prescricionais e decadenciais (CTN arts. 150, 173, 174).', 'prioridade': 'urgente'},
        {'titulo': 'Analisar legalidade da exação', 'descricao': 'Verificar legalidade, base de cálculo, alíquota e fato gerador do tributo.', 'prioridade': 'alta'},
        {'titulo': 'Avaliar via administrativa ou judicial', 'descricao': 'Decidir entre impugnação administrativa ou ação judicial (mandado de segurança, anulatória, etc).', 'prioridade': 'alta'},
        {'titulo': 'Reunir documentação fiscal', 'descricao': 'Solicitar ao cliente notas fiscais, guias de recolhimento, DCTF, etc.', 'prioridade': 'alta'},
        {'titulo': 'Pesquisar jurisprudência tributária', 'descricao': 'Buscar decisões do CARF, STJ e STF sobre a matéria tributária.', 'prioridade': 'media'},
    ],
    'familia': [
        {'titulo': 'Coletar informações familiares e patrimoniais', 'descricao': 'Reunir dados sobre cônjuge, filhos, regime de bens e patrimônio do casal.', 'prioridade': 'alta'},
        {'titulo': 'Analisar regime de bens e partilha', 'descricao': 'Verificar regime de bens e listar bens a serem partilhados.', 'prioridade': 'alta'},
        {'titulo': 'Elaborar petição (divórcio/guarda/alimentos)', 'descricao': 'Redigir petição conforme o tipo de ação familiar.', 'prioridade': 'urgente'},
        {'titulo': 'Avaliar guarda e direito de visitas', 'descricao': 'Definir pretensão quanto à guarda (compartilhada/unilateral) e regime de visitas.', 'prioridade': 'alta'},
        {'titulo': 'Calcular alimentos (Lei 5.478/68)', 'descricao': 'Analisar necessidade do alimentando e possibilidade do alimentante.', 'prioridade': 'alta'},
        {'titulo': 'Verificar possibilidade de acordo extrajudicial', 'descricao': 'Avaliar viabilidade de divórcio ou acordo consensual em cartório.', 'prioridade': 'media'},
    ],
    'consumidor': [
        {'titulo': 'Analisar relação de consumo', 'descricao': 'Verificar enquadramento como relação de consumo (CDC arts. 2-3).', 'prioridade': 'alta'},
        {'titulo': 'Reunir provas do dano', 'descricao': 'Coletar notas fiscais, contratos, prints, protocolos de reclamação e provas do dano.', 'prioridade': 'alta'},
        {'titulo': 'Verificar reclamação prévia (SAC/Procon)', 'descricao': 'Documentar tentativas de resolução administrativa.', 'prioridade': 'media'},
        {'titulo': 'Elaborar petição inicial', 'descricao': 'Redigir petição com fundamentação no CDC e quantificação de danos.', 'prioridade': 'urgente'},
        {'titulo': 'Calcular danos materiais e morais', 'descricao': 'Quantificar perdas materiais e arbitrar valor de danos morais.', 'prioridade': 'alta'},
        {'titulo': 'Avaliar competência (JEC x Vara Cível)', 'descricao': 'Verificar se o valor permite ajuizamento no Juizado Especial.', 'prioridade': 'media'},
    ],
    'previdenciario': [
        {'titulo': 'Analisar CNIS e extrato previdenciário', 'descricao': 'Verificar vínculos, contribuições e tempo de contribuição no CNIS.', 'prioridade': 'urgente'},
        {'titulo': 'Verificar requerimento administrativo (INSS)', 'descricao': 'Conferir se houve requerimento no INSS e o motivo do indeferimento.', 'prioridade': 'alta'},
        {'titulo': 'Calcular tempo de contribuição', 'descricao': 'Elaborar contagem de tempo com conversão de atividades especiais.', 'prioridade': 'alta'},
        {'titulo': 'Reunir documentação médica (se incapacidade)', 'descricao': 'Coletar laudos médicos, exames e atestados para pedidos de auxílio-doença/aposentadoria por invalidez.', 'prioridade': 'alta'},
        {'titulo': 'Elaborar petição inicial', 'descricao': 'Redigir petição para a ação previdenciária (concessão, revisão, restabelecimento).', 'prioridade': 'urgente'},
        {'titulo': 'Pesquisar jurisprudência previdenciária', 'descricao': 'Buscar decisões das Turmas Recursais e TRFs sobre o tema.', 'prioridade': 'media'},
    ],
    'empresarial': [
        {'titulo': 'Analisar contrato social e documentos societários', 'descricao': 'Examinar contrato social, alterações, atas de assembleia e acordos de sócios.', 'prioridade': 'alta'},
        {'titulo': 'Verificar situação cadastral (Junta Comercial/CNPJ)', 'descricao': 'Consultar situação da empresa na Junta Comercial e Receita Federal.', 'prioridade': 'alta'},
        {'titulo': 'Elaborar petição ou notificação empresarial', 'descricao': 'Redigir peça processual conforme a matéria empresarial.', 'prioridade': 'urgente'},
        {'titulo': 'Analisar balanço patrimonial e demonstrações financeiras', 'descricao': 'Examinar demonstrações contábeis relevantes para o litígio.', 'prioridade': 'media'},
        {'titulo': 'Verificar possibilidade de mediação/arbitragem', 'descricao': 'Avaliar cláusula compromissória ou possibilidade de mediação.', 'prioridade': 'media'},
    ],
    'administrativo': [
        {'titulo': 'Analisar ato administrativo impugnado', 'descricao': 'Examinar o ato administrativo, portaria, edital ou decisão a ser contestada.', 'prioridade': 'urgente'},
        {'titulo': 'Verificar prazos para recurso administrativo', 'descricao': 'Conferir prazos na Lei 9.784/99 ou norma específica.', 'prioridade': 'urgente'},
        {'titulo': 'Avaliar via administrativa ou judicial', 'descricao': 'Decidir entre recurso administrativo, mandado de segurança ou ação ordinária.', 'prioridade': 'alta'},
        {'titulo': 'Reunir documentação administrativa', 'descricao': 'Coletar documentos, pareceres, editais e notificações recebidas.', 'prioridade': 'alta'},
        {'titulo': 'Elaborar petição ou recurso', 'descricao': 'Redigir a peça adequada (recurso hierárquico, MS, ação anulatória).', 'prioridade': 'urgente'},
        {'titulo': 'Pesquisar jurisprudência de direito administrativo', 'descricao': 'Buscar decisões dos Tribunais sobre a matéria administrativa.', 'prioridade': 'media'},
    ],
    'imobiliario': [
        {'titulo': 'Analisar matrícula do imóvel e certidões', 'descricao': 'Solicitar e examinar matrícula atualizada, certidões negativas e IPTU.', 'prioridade': 'alta'},
        {'titulo': 'Verificar contrato (compra/venda/locação)', 'descricao': 'Analisar o contrato imobiliário e identificar cláusulas relevantes.', 'prioridade': 'alta'},
        {'titulo': 'Elaborar petição inicial', 'descricao': 'Redigir petição para ação imobiliária (despejo, reintegração, usucapião, etc).', 'prioridade': 'urgente'},
        {'titulo': 'Avaliar necessidade de perícia/vistoria', 'descricao': 'Verificar se há necessidade de laudo de vistoria ou avaliação do imóvel.', 'prioridade': 'media'},
        {'titulo': 'Verificar notificação premonitória', 'descricao': 'Conferir se foi enviada notificação prévia quando exigida por lei.', 'prioridade': 'alta'},
    ],
    'ambiental': [
        {'titulo': 'Analisar auto de infração ambiental', 'descricao': 'Examinar auto de infração do IBAMA, órgão estadual ou municipal.', 'prioridade': 'urgente'},
        {'titulo': 'Verificar licenciamento ambiental', 'descricao': 'Conferir se a atividade possui licenças ambientais válidas.', 'prioridade': 'alta'},
        {'titulo': 'Reunir documentação ambiental', 'descricao': 'Coletar EIA/RIMA, licenças, pareceres técnicos e documentos correlatos.', 'prioridade': 'alta'},
        {'titulo': 'Avaliar possibilidade de TAC', 'descricao': 'Verificar viabilidade de Termo de Ajustamento de Conduta.', 'prioridade': 'media'},
        {'titulo': 'Elaborar defesa ou petição', 'descricao': 'Redigir impugnação administrativa ou petição judicial.', 'prioridade': 'urgente'},
    ],
}

# Alias para especialidades que não possuem checklist específico
CHECKLISTS['outros'] = CHECKLISTS['civel']


class ChecklistService:
    """Serviço de criação de checklists por tipo de ação."""

    @staticmethod
    def get_checklist_for_especialidade(especialidade: str) -> List[dict]:
        """
        Retorna o checklist para a especialidade informada.
        Se não houver checklist específico, retorna o cível como padrão.
        """
        return CHECKLISTS.get(especialidade, CHECKLISTS['civel'])

    @staticmethod
    def get_available_especialidades() -> List[dict]:
        """Retorna as especialidades que possuem checklist."""
        return [
            {'key': key, 'total_tasks': len(tasks)}
            for key, tasks in CHECKLISTS.items()
            if key != 'outros'
        ]

    @staticmethod
    def create_checklist_for_case(case, user=None) -> list:
        """
        Cria tarefas (CaseTask) a partir do checklist da especialidade do caso.

        Args:
            case: instância de LegalCase
            user: usuário que está criando

        Returns:
            lista de CaseTask criados
        """
        from apps.cases.models import CaseTask

        checklist = ChecklistService.get_checklist_for_especialidade(case.especialidade)
        created_tasks = []

        for item in checklist:
            task = CaseTask.objects.create(
                caso=case,
                titulo=item['titulo'],
                descricao=item['descricao'],
                prioridade=item['prioridade'],
                status='pendente',
                created_by=user,
            )
            created_tasks.append(task)

        return created_tasks

    @staticmethod
    def preview_checklist(especialidade: str) -> List[dict]:
        """
        Retorna preview do checklist (sem criar) para exibição no frontend.
        """
        return ChecklistService.get_checklist_for_especialidade(especialidade)
