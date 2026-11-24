from dataclasses import dataclass


@dataclass(frozen=True)
class CycleRecord:
    """Resultado de um ciclo simulado."""

    cycle: int
    profit: float
    accumulated_profitability: float
    price: float | None = None
    served_quantity: float | None = None
    net_revenue: float | None = None
    costs: float | None = None
    cash_flow: float | None = None
    inflation: float | None = None
