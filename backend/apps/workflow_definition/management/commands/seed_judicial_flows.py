"""
Seed dos fluxos judiciais da Procuradoria.
Carrega os templates de sistema pré-definidos baseados no XPDL 2.2
do arquivo "Fluxograma Gerência Judicial - Processo Eletrônicos - 1º Grau.bpm".

Swim lanes (papéis):
  1. Distribuidor(a)
  2. Procurador(a)
  3. Gerente
  4. Assessor(a) Gerencial
  5. Procurador(a)-Geral / Subprocurador(a)-Geral
  6. Assessor(a) de Gabinete
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.workflow_definition.models import FlowTemplate, FlowNode, FlowEdge


# ── Layout constants ───────────────────────────────────────────
LANE_WIDTH = 900
LANE_HEIGHT = 160
LANE_X = 0
NODE_W = 160
NODE_H = 60
GW_SIZE = 50
EVT_SIZE = 40


def lane_y(index: int) -> int:
    """Y de uma swim lane pelo seu índice (0-based)."""
    return 80 + index * (LANE_HEIGHT + 8)


def node_pos(lane_index: int, col: int):
    """Posição de um nó dentro de uma swim lane."""
    return {
        'x': 60 + col * (NODE_W + 40),
        'y': lane_y(lane_index) + (LANE_HEIGHT - NODE_H) // 2,
    }


def gw_pos(lane_index: int, col: int):
    """Posição de um gateway."""
    return {
        'x': 60 + col * (NODE_W + 40) + (NODE_W - GW_SIZE) // 2,
        'y': lane_y(lane_index) + (LANE_HEIGHT - GW_SIZE) // 2,
    }


def evt_pos(lane_index: int, col: int):
    """Posição de um evento."""
    return {
        'x': 60 + col * (NODE_W + 40) + (NODE_W - EVT_SIZE) // 2,
        'y': lane_y(lane_index) + (LANE_HEIGHT - EVT_SIZE) // 2,
    }


# ── Definição do fluxo judicial 1º Grau ───────────────────────

JUDICIAL_1_SWIMLANES = [
    {'id': 'lane-distribuidor', 'label': 'Distribuidor(a)', 'role': 'distribuidor', 'index': 0},
    {'id': 'lane-procurador', 'label': 'Procurador(a)', 'role': 'procurador', 'index': 1},
    {'id': 'lane-gerente', 'label': 'Gerente', 'role': 'gerente', 'index': 2},
    {'id': 'lane-assessor-gerencial', 'label': 'Assessor(a) Gerencial', 'role': 'assessor_gerencial', 'index': 3},
    {'id': 'lane-pg', 'label': 'Procurador(a)-Geral / Subprocurador(a)-Geral', 'role': 'procurador_geral', 'index': 4},
    {'id': 'lane-assessor-gabinete', 'label': 'Assessor(a) de Gabinete', 'role': 'assessor_gabinete', 'index': 5},
]

JUDICIAL_1_NODES = [
    # Início
    {'id': 'start-1', 'type': 'start_event', 'label': 'Processo Recebido', 'role': 'distribuidor', 'lane': 0, 'col': 0, 'pos_fn': evt_pos},

    # Distribuidor
    {'id': 'task-distribuir', 'type': 'user_task', 'label': 'Distribuir Processo', 'role': 'distribuidor', 'lane': 0, 'col': 1, 'pos_fn': node_pos,
     'desc': 'Distribuidor analisa o processo e o atribui a um procurador da gerência.'},
    {'id': 'gw-redistribuicao', 'type': 'exclusive_gateway', 'label': 'Solicitar Redistribuição?', 'role': 'distribuidor', 'lane': 0, 'col': 2, 'pos_fn': gw_pos},
    {'id': 'task-solicitar-redistribuicao', 'type': 'user_task', 'label': 'Solicitar Redistribuição', 'role': 'distribuidor', 'lane': 0, 'col': 3, 'pos_fn': node_pos,
     'desc': 'Procurador ou distribuidor solicita redistribuição do processo.'},

    # Gerente — aprovação de redistribuição
    {'id': 'task-aprovar-redistribuicao', 'type': 'user_task', 'label': 'Aprovar Redistribuição', 'role': 'gerente', 'lane': 2, 'col': 3, 'pos_fn': node_pos,
     'desc': 'Gerente avalia e aprova ou rejeita a solicitação de redistribuição.'},
    {'id': 'gw-redistribuicao-aceita', 'type': 'exclusive_gateway', 'label': 'Redistribuição Aceita?', 'role': 'gerente', 'lane': 2, 'col': 4, 'pos_fn': gw_pos},

    # Fim redistribuição rejeitada
    {'id': 'end-redistribuicao-rejeitada', 'type': 'end_event', 'label': 'Processo Mantido', 'role': 'distribuidor', 'lane': 0, 'col': 5, 'pos_fn': evt_pos},

    # Procurador — elaboração
    {'id': 'task-analisar', 'type': 'user_task', 'label': 'Analisar Processo', 'role': 'procurador', 'lane': 1, 'col': 1, 'pos_fn': node_pos,
     'desc': 'Procurador analisa o mérito do processo e determina a providência cabível.'},
    {'id': 'gw-peticionar', 'type': 'exclusive_gateway', 'label': 'Processo será\nPeticionado?', 'role': 'procurador', 'lane': 1, 'col': 2, 'pos_fn': gw_pos},
    {'id': 'task-elaborar-peca', 'type': 'user_task', 'label': 'Elaborar Peça Processual', 'role': 'procurador', 'lane': 1, 'col': 3, 'pos_fn': node_pos,
     'desc': 'Procurador elabora a peça processual (petição, contestação, recurso, etc.).'},
    {'id': 'gw-tipo-doc', 'type': 'exclusive_gateway', 'label': 'Tipo de\nDocumento?', 'role': 'procurador', 'lane': 1, 'col': 4, 'pos_fn': gw_pos},

    # Avocação
    {'id': 'task-avocar', 'type': 'user_task', 'label': 'Avocar Processo', 'role': 'procurador_geral', 'lane': 4, 'col': 2, 'pos_fn': node_pos,
     'desc': 'PG/Subprocurador avoca formalmente o processo, assumindo responsabilidade.'},

    # Assessor Gerencial — minuta
    {'id': 'task-elaborar-minuta', 'type': 'user_task', 'label': 'Elaborar Minuta', 'role': 'assessor_gerencial', 'lane': 3, 'col': 4, 'pos_fn': node_pos,
     'desc': 'Assessor Gerencial elabora minuta de despacho ou decisão para revisão do gerente.'},
    {'id': 'task-corrigir-minuta', 'type': 'user_task', 'label': 'Corrigir Documento', 'role': 'assessor_gerencial', 'lane': 3, 'col': 5, 'pos_fn': node_pos,
     'desc': 'Assessor corrige o documento conforme orientações do gerente.'},

    # Gerente — despacho
    {'id': 'task-despacho-gerente', 'type': 'user_task', 'label': 'Revisar e Encaminhar\nDespacho', 'role': 'gerente', 'lane': 2, 'col': 4, 'pos_fn': node_pos,
     'desc': 'Gerente revisa o despacho ou minuta e encaminha para assinatura.'},
    {'id': 'gw-despacho', 'type': 'exclusive_gateway', 'label': 'Deferido?', 'role': 'gerente', 'lane': 2, 'col': 5, 'pos_fn': gw_pos},

    # PG — assinatura
    {'id': 'task-assinar-despacho', 'type': 'user_task', 'label': 'Assinar Despacho', 'role': 'procurador_geral', 'lane': 4, 'col': 4, 'pos_fn': node_pos,
     'desc': 'PG/Subprocurador assina o despacho ou petição com assinatura digital.'},

    # Assessor Gabinete — peticionamento
    {'id': 'task-peticionar-pje', 'type': 'user_task', 'label': 'Realizar Peticionamento\n(PJe/EPROC)', 'role': 'assessor_gabinete', 'lane': 5, 'col': 4, 'pos_fn': node_pos,
     'desc': 'Assessor de Gabinete realiza o peticionamento eletrônico no sistema judicial (PJe ou EPROC).'},
    {'id': 'gw-peticao-ok', 'type': 'exclusive_gateway', 'label': 'Peticionamento\nBem-sucedido?', 'role': 'assessor_gabinete', 'lane': 5, 'col': 5, 'pos_fn': gw_pos},

    # Fins
    {'id': 'end-indeferido', 'type': 'end_event', 'label': 'Processo Arquivado\n(Indeferido)', 'role': 'gerente', 'lane': 2, 'col': 6, 'pos_fn': evt_pos},
    {'id': 'end-peticionado', 'type': 'end_event', 'label': 'Processo Arquivado\n(Peticionado)', 'role': 'assessor_gabinete', 'lane': 5, 'col': 6, 'pos_fn': evt_pos},
    {'id': 'end-erro-peticao', 'type': 'end_event', 'label': 'Processo Arquivado\n(Erro Peticionamento)', 'role': 'assessor_gabinete', 'lane': 5, 'col': 7, 'pos_fn': evt_pos},
    {'id': 'end-sem-peticao', 'type': 'end_event', 'label': 'Processo Arquivado\n(Sem Peticionamento)', 'role': 'procurador', 'lane': 1, 'col': 5, 'pos_fn': evt_pos},
    {'id': 'end-avocado', 'type': 'end_event', 'label': 'Processo Avocado\ne Arquivado', 'role': 'procurador_geral', 'lane': 4, 'col': 3, 'pos_fn': evt_pos},
]

JUDICIAL_1_EDGES = [
    # Início → Distribuir
    ('e-start-dist', 'start-1', 'task-distribuir', '', '', ''),
    # Distribuir → Gateway redistribuição
    ('e-dist-gw', 'task-distribuir', 'gw-redistribuicao', '', '', ''),
    # Gateway → Solicitar redistribuição (Sim)
    ('e-gw-solicitar', 'gw-redistribuicao', 'task-solicitar-redistribuicao', 'yes', '', 'Sim'),
    # Gateway → Analisar (Não)
    ('e-gw-analisar', 'gw-redistribuicao', 'task-analisar', 'no', '', 'Não'),
    # Solicitar redistribuição → Aprovar redistribuição
    ('e-solicitar-aprovar', 'task-solicitar-redistribuicao', 'task-aprovar-redistribuicao', '', '', ''),
    # Aprovar redistribuição → Gateway aceita
    ('e-aprovar-gw', 'task-aprovar-redistribuicao', 'gw-redistribuicao-aceita', '', '', ''),
    # Aceita? Sim → Distribuir (redistribuir)
    ('e-aceita-dist', 'gw-redistribuicao-aceita', 'task-distribuir', 'yes', '', 'Sim'),
    # Aceita? Não → Fim mantido
    ('e-aceita-nao', 'gw-redistribuicao-aceita', 'end-redistribuicao-rejeitada', 'no', '', 'Não'),
    # Analisar → Gateway peticionar
    ('e-analisar-gw', 'task-analisar', 'gw-peticionar', '', '', ''),
    # Peticionar? Não → Fim sem petição
    ('e-nao-peticionar', 'gw-peticionar', 'end-sem-peticao', 'no', '', 'Não'),
    # Peticionar? Sim → Elaborar peça
    ('e-sim-elaborar', 'gw-peticionar', 'task-elaborar-peca', 'yes', '', 'Sim'),
    # Elaborar peça → Gateway tipo doc
    ('e-peca-gw-tipo', 'task-elaborar-peca', 'gw-tipo-doc', '', '', ''),
    # Tipo? Minuta de peça → Elaborar minuta (assessor gerencial)
    ('e-tipo-minuta', 'gw-tipo-doc', 'task-elaborar-minuta', 'minuta', '', 'Minuta de Peça'),
    # Tipo? Mero expediente → Despacho gerente
    ('e-tipo-despacho', 'gw-tipo-doc', 'task-despacho-gerente', 'expediente', '', 'Mero Expediente'),
    # Elaborar minuta → Despacho gerente
    ('e-minuta-despacho', 'task-elaborar-minuta', 'task-despacho-gerente', '', '', ''),
    # Corrigir → Despacho gerente
    ('e-corrigir-despacho', 'task-corrigir-minuta', 'task-despacho-gerente', '', '', ''),
    # Despacho gerente → Gateway deferido
    ('e-despacho-gw', 'task-despacho-gerente', 'gw-despacho', '', '', ''),
    # Deferido? Não → Fim indeferido
    ('e-indeferido', 'gw-despacho', 'end-indeferido', 'no', '', 'Não'),
    # Deferido? Corrigir → Corrigir minuta
    ('e-corrigir', 'gw-despacho', 'task-corrigir-minuta', 'corrigir', '', 'Corrigir'),
    # Deferido? Sim → Assinar despacho
    ('e-assinar', 'gw-despacho', 'task-assinar-despacho', 'yes', '', 'Sim'),
    # Assinar → Peticionar PJe
    ('e-assinar-pje', 'task-assinar-despacho', 'task-peticionar-pje', '', '', ''),
    # Peticionar PJe → Gateway sucesso
    ('e-pje-gw', 'task-peticionar-pje', 'gw-peticao-ok', '', '', ''),
    # Petição OK? Sim → Fim peticionado
    ('e-pje-ok', 'gw-peticao-ok', 'end-peticionado', 'yes', '', 'Sim'),
    # Petição OK? Não → Fim erro
    ('e-pje-erro', 'gw-peticao-ok', 'end-erro-peticao', 'no', '', 'Não'),
    # Avocar
    ('e-avocar-fim', 'task-avocar', 'end-avocado', '', '', ''),
]


class Command(BaseCommand):
    help = 'Carrega os templates de fluxo judicial (sistema) para a plataforma Verus.AI'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Recria os templates mesmo que já existam',
        )

    def handle(self, *args, **options):
        force = options['force']

        with transaction.atomic():
            self._seed_judicial_1(force)

        self.stdout.write(self.style.SUCCESS(
            '✓ Templates de fluxo judicial carregados com sucesso.'
        ))

    def _seed_judicial_1(self, force: bool):
        name = 'Fluxo Judicial — Processos Eletrônicos (1º Grau)'

        if FlowTemplate.objects.filter(name=name, is_system_template=True).exists():
            if not force:
                self.stdout.write(f'  → Template "{name}" já existe. Use --force para recriar.')
                return
            FlowTemplate.objects.filter(name=name, is_system_template=True).delete()
            self.stdout.write(f'  → Template "{name}" removido para recriação.')

        template = FlowTemplate.objects.create(
            name=name,
            description=(
                'Fluxo de gestão de processos judiciais eletrônicos (1º grau) da Procuradoria. '
                'Baseado no Fluxograma da Gerência Judicial — Serra/ES (XPDL 2.2). '
                'Cobre: distribuição, análise, elaboração de peças, minutas, '
                'assinatura, peticionamento (PJe/EPROC), redistribuição e avocação.'
            ),
            category='judicial_1',
            status='published',
            version=1,
            is_system_template=True,
            organ=None,  # disponível para todos os órgãos
        )

        # Criar swim lanes
        for lane in JUDICIAL_1_SWIMLANES:
            FlowNode.objects.create(
                template=template,
                node_id=lane['id'],
                node_type='swimlane',
                label=lane['label'],
                role=lane['role'],
                parent_node_id='',
                position={
                    'x': LANE_X,
                    'y': lane_y(lane['index']),
                    'width': LANE_WIDTH,
                    'height': LANE_HEIGHT,
                },
                data={'laneIndex': lane['index']},
                order=lane['index'],
            )

        # Criar nós
        for i, node in enumerate(JUDICIAL_1_NODES):
            pos_fn = node['pos_fn']
            pos = pos_fn(node['lane'], node['col'])

            # Determinar lane pai
            parent_id = JUDICIAL_1_SWIMLANES[node['lane']]['id']

            FlowNode.objects.create(
                template=template,
                node_id=node['id'],
                node_type=node['type'],
                label=node['label'],
                description=node.get('desc', ''),
                role=node['role'],
                parent_node_id=parent_id,
                position=pos,
                data={},
                order=i,
            )

        # Criar edges
        for edge_data in JUDICIAL_1_EDGES:
            edge_id, src, tgt, src_handle, tgt_handle, label = edge_data
            FlowEdge.objects.create(
                template=template,
                edge_id=edge_id,
                source_node_id=src,
                target_node_id=tgt,
                source_handle=src_handle,
                target_handle=tgt_handle,
                label=label,
                condition=src_handle,
            )

        self.stdout.write(
            f'  ✓ "{name}" criado: '
            f'{len(JUDICIAL_1_SWIMLANES)} swim lanes, '
            f'{len(JUDICIAL_1_NODES)} nós, '
            f'{len(JUDICIAL_1_EDGES)} edges.'
        )
