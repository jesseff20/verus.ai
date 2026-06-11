"""
Validação de templates de fluxo antes da publicação.
Regras:
  1. Deve ter pelo menos 1 start_event
  2. Deve ter pelo menos 1 end_event
  3. Todos os nós (exceto swimlanes) devem ter pelo menos 1 edge de entrada ou saída
  4. Gateways exclusivos devem ter pelo menos 2 edges de saída
  5. Deve ter pelo menos 1 swimlane
"""
from dataclasses import dataclass, field
from typing import List


@dataclass
class ValidationResult:
    valid: bool = True
    errors: List[str] = field(default_factory=list)

    def add_error(self, msg: str):
        self.valid = False
        self.errors.append(msg)


def validate_flow_for_publish(template) -> ValidationResult:
    result = ValidationResult()

    nodes = list(template.nodes.all())
    edges = list(template.edges.all())

    if not nodes:
        result.add_error('O fluxo não tem nenhum nó.')
        return result

    node_ids = {n.node_id for n in nodes}
    node_by_id = {n.node_id: n for n in nodes}

    # Edges referenciando nós inexistentes
    for edge in edges:
        if edge.source_node_id not in node_ids:
            result.add_error(
                f'Edge "{edge.edge_id}" referencia nó de origem inexistente: {edge.source_node_id}'
            )
        if edge.target_node_id not in node_ids:
            result.add_error(
                f'Edge "{edge.edge_id}" referencia nó de destino inexistente: {edge.target_node_id}'
            )

    # Regra 1 — start event
    start_nodes = [n for n in nodes if n.node_type == 'start_event']
    if not start_nodes:
        result.add_error('O fluxo deve ter pelo menos um Evento de Início (start_event).')

    # Regra 2 — end event
    end_nodes = [n for n in nodes if n.node_type == 'end_event']
    if not end_nodes:
        result.add_error('O fluxo deve ter pelo menos um Evento de Fim (end_event).')

    # Regra 3 — swim lanes
    swimlanes = [n for n in nodes if n.node_type == 'swimlane']
    if not swimlanes:
        result.add_error('O fluxo deve ter pelo menos uma Swim Lane.')

    # Regra 4 — conectividade básica (não-swimlanes devem ter edge)
    sources = {e.source_node_id for e in edges}
    targets = {e.target_node_id for e in edges}

    for node in nodes:
        if node.node_type == 'swimlane':
            continue
        if node.node_type == 'end_event':
            if node.node_id not in targets:
                result.add_error(
                    f'Evento de Fim "{node.label}" não tem nenhuma conexão de entrada.'
                )
            continue
        if node.node_type == 'start_event':
            if node.node_id not in sources:
                result.add_error(
                    f'Evento de Início "{node.label}" não tem nenhuma conexão de saída.'
                )
            continue
        if node.node_id not in sources and node.node_id not in targets:
            result.add_error(
                f'Nó "{node.label}" ({node.node_type}) está desconectado do fluxo.'
            )

    # Regra 5 — gateways exclusivos com pelo menos 2 saídas
    for node in nodes:
        if node.node_type == 'exclusive_gateway':
            outgoing = [e for e in edges if e.source_node_id == node.node_id]
            if len(outgoing) < 2:
                result.add_error(
                    f'Gateway "{node.label}" deve ter pelo menos 2 saídas (tem {len(outgoing)}).'
                )

    return result
