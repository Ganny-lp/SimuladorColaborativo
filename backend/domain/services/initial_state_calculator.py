from __future__ import annotations

from backend.domain.constants import NodeNames
from backend.domain.entities.causal_system import CausalSystem
from backend.domain.exceptions import ExpressionEvaluationError
from backend.domain.services.expression_evaluator import ExpressionEvaluator

DEFAULT_INITIAL_STATE: dict[str, float] = {
    "B": 10000.0,
    "Satisfacao_Cliente": 0.5,
    "Reputacao_Empresa": 0.5,
    "Nivel_Qualificacao_Tecnica": 0.6,
    "Experiencia_Acumulada": 1.0,
    "Backlog_Servicos": 0.0,
    "Motivacao": 0.7,
}


class InitialStateCalculator:
    """
    Valores iniciais dos nós com memória. Podem ser sobrescritos pela chave
    ``initial_state`` do modelo. A Rentabilidade inicial é ``-Custos Abertura``.
    """

    def __init__(self, evaluator: ExpressionEvaluator) -> None:
        self._evaluator = evaluator

    def calculate(self, system: CausalSystem) -> dict[str, float]:
        overrides = system.initial_state
        initial = {name: node.value for name, node in system.nodes.items() if node.is_state}
        initial.update(DEFAULT_INITIAL_STATE)
        initial.update(overrides)
        if system.extras.get("schema_version") == 2:
            initial.update(B=system.value_of("Base_Instalada_Inicial", 10000),
                           Estoque_Pecas=system.value_of("Estoque_Inicial", 150),
                           Caixa_Disponivel=system.value_of("Caixa_Reserva") + system.value_of("Emprestimo"),
                           Reinvestimento_Disponivel=0, Mes_Operacao=0)
        if NodeNames.RENTABILIDADE not in overrides:
            investment = self._opening_investment(system)
            initial[NodeNames.RENTABILIDADE] = -investment if investment else 0.0  # evita -0.0
        return {name: float(v) for name, v in initial.items() if system.has_node(name)}

    def _opening_investment(self, system: CausalSystem) -> float:
        node = system.nodes.get(NodeNames.CUSTOS_ABERTURA)
        if node is None:
            return 0.0
        if not node.has_expression:
            return node.value
        return self._evaluator.evaluate(node.expression, system.values())
