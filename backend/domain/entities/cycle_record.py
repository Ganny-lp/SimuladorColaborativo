from dataclasses import dataclass


@dataclass(frozen=True)
class CycleRecord:
    """Resultado de um ciclo simulado."""

    cycle: int
    profit: float
    accumulated_profitability: float
