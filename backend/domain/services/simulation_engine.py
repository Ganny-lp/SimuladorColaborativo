from __future__ import annotations

import logging

from backend.domain.entities.causal_system import CausalSystem
from backend.domain.exceptions import ExpressionEvaluationError
from backend.domain.services.dependency_graph import DependencyGraph
from backend.domain.services.expression_evaluator import ExpressionEvaluator
from backend.domain.services.initial_state_calculator import InitialStateCalculator

logger = logging.getLogger(__name__)


class SimulationEngine:
    """Executa a dinâmica do modelo respeitando a cadeia causal completa."""

    _DERIVED_PASSES = 2

    def __init__(
        self, evaluator: ExpressionEvaluator, initial_state: InitialStateCalculator
    ) -> None:
        self._evaluator = evaluator
        self._initial_state = initial_state

    def advance_cycle(self, system: CausalSystem) -> None:
        """
        Avança um ciclo. Nós são calculados em ordem topológica, cada um lendo o
        valor JÁ ATUALIZADO das suas causas. Nós 'Estado' acumulam (anterior + equação).
        """
        # All rates read the same opening-of-month state. Commit stocks together.
        self.recompute_derived(system)
        values = system.values()
        updates = {}
        for name, node in system.nodes.items():
            if node.is_state and node.has_expression:
                updates[name] = values[name] + self._evaluate(node.expression, values)
        system.apply_values(updates.items())

    def recompute_derived(self, system: CausalSystem) -> None:
        """Recalcula as variáveis derivadas a partir do estado atual, SEM avançar os estados."""
        graph = DependencyGraph(system)
        states = graph.state_nodes()
        values = system.values()
        for _ in range(self._DERIVED_PASSES):
            for name in graph.topological_order():
                node = system.node(name)
                if name in states or not node.has_expression:
                    continue
                node.value = self._evaluate(node.expression, values)
                values[name] = node.value

    def reset_state(self, system: CausalSystem) -> None:
        """Devolve os nós com memória aos seus valores iniciais."""
        system.apply_values(self._initial_state.calculate(system).items())

    def _evaluate(self, expression: str, values: dict[str, float]) -> float:
        try:
            return self._evaluator.evaluate(expression, values)
        except ExpressionEvaluationError as exc:
            logger.debug("Equação ignorada (valor 0): %s", exc)
            return 0.0
