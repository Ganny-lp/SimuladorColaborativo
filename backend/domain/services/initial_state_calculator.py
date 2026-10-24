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
        initial = {**DEFAULT_INITIAL_STATE, **overrides}
        if NodeNames.RENTABILIDADE not in overrides:
            investment = self._opening_investment(system)
            initial[NodeNames.RENTABILIDADE] = -investment if investment else 0.0  # evita -0.0
        return {name: float(v) for name, v in initial.items() if system.has_node(name)}

    def _opening_investment(self, system: CausalSystem) -> float:
        node = system.nodes.get(NodeNames.CUSTOS_ABERTURA)
        if node is None or not node.has_expression:
            return 0.0
        try:
            return self._evaluator.evaluate(node.expression, system.values())
        except ExpressionEvaluationError:
            return 0.0
