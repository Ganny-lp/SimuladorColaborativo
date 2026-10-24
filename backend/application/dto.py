"""Contratos de dados entre backend e frontend (imutáveis, sem lógica de negócio)."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class PersistenceOutcome(str, Enum):
    SAVED = "saved"
    SKIPPED = "skipped"  # persistência não configurada
    FAILED = "failed"


@dataclass(frozen=True)
class VariableDTO:
    name: str
    category: str
    value: float
    expression: str
    description: str


@dataclass(frozen=True)
class PriceStopDTO:
    value: float
    color: str
    label: str


@dataclass(frozen=True)
class PriceScaleDTO:
    minimum: float
    maximum: float
    stops: tuple[PriceStopDTO, ...]


@dataclass(frozen=True)
class CycleRecordDTO:
    cycle: int
    profit: float
    accumulated_profitability: float


@dataclass(frozen=True)
class KpiDTO:
    accumulated_profitability: float
    net_revenue: float
    served_quantity: float
    market_share: float


@dataclass(frozen=True)
class InputChangeResult:
    changed: bool
    persistence: PersistenceOutcome


@dataclass(frozen=True)
class SimulationSnapshot:
    """Visão somente-leitura da simulação, pronta para a camada de apresentação."""

    cycle: int
    kpis: KpiDTO
    variables: tuple[VariableDTO, ...]
    price_scale: PriceScaleDTO
    history: tuple[CycleRecordDTO, ...]
    model_payload: dict[str, Any]
    cloud_enabled: bool

    def variable(self, name: str) -> VariableDTO | None:
        return next((v for v in self.variables if v.name == name), None)
