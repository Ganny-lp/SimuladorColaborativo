from __future__ import annotations

from dataclasses import dataclass, field

from backend.domain.constants import NodeNames
from backend.domain.entities.causal_system import CausalSystem
from backend.domain.entities.cycle_record import CycleRecord


@dataclass
class Simulation:
    """Execução em andamento: modelo + linha de base (para reiniciar) + histórico de ciclos."""

    system: CausalSystem
    baseline: dict[str, float]
    cycle: int = 0
    history: list[CycleRecord] = field(default_factory=list)

    completed_values: dict[str, float] = field(default_factory=dict)

    @classmethod
    def begin(cls, system: CausalSystem) -> "Simulation":
        return cls(system=system, baseline=system.values())

    def set_input(self, name: str, value: float) -> None:
        """Altera uma decisão de entrada e a torna o novo ponto de partida do 'Reiniciar'."""
        from backend.domain.services.input_validation import validate_input
        value = validate_input(self.system.node(name), value)
        self.system.set_value(name, value)
        self.baseline[name] = float(value)

    def register_cycle(self, profit: float, accumulated_profitability: float) -> CycleRecord:
        self.completed_values = self.system.values()
        self.cycle += 1
        record = CycleRecord(
            self.cycle, profit, accumulated_profitability,
            price=self.completed_values.get(NodeNames.PRECO),
            served_quantity=self.completed_values.get(NodeNames.QUANTIDADE),
            net_revenue=self.completed_values.get(NodeNames.RECEITA_LIQUIDA),
            costs=self.completed_values.get(NodeNames.CUSTOS),
            cash_flow=self.completed_values.get("Fluxo_Caixa"),
            inflation=self.completed_values.get("Inflacao"),
        )
        self.history.append(record)
        return record

    def restore_baseline(self) -> None:
        self.system.apply_values(self.baseline.items())

    def clear_progress(self) -> None:
        self.cycle = 0
        self.history = []
        self.completed_values = {}
