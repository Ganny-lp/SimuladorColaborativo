from __future__ import annotations

from dataclasses import dataclass
import math
import re

from backend.domain.exceptions import InvalidModelError


@dataclass(frozen=True)
class PriceStop:
    """Ponto de referência da régua de preço (valor, cor e rótulo)."""

    value: float
    color: str
    label: str


@dataclass(frozen=True)
class PriceScale:
    """Régua de preço parametrizável (gradiente vermelho → verde)."""

    minimum: float
    maximum: float
    stops: tuple[PriceStop, ...]

    def __post_init__(self) -> None:
        if not math.isfinite(self.minimum) or not math.isfinite(self.maximum) or self.minimum >= self.maximum:
            raise InvalidModelError("Limites da régua inválidos.")
        for stop in self.stops:
            if not math.isfinite(stop.value) or not self.minimum <= stop.value <= self.maximum:
                raise InvalidModelError("Ponto da régua fora dos limites.")
            if not isinstance(stop.color, str) or not re.fullmatch(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})",stop.color):
                raise InvalidModelError("Cor inválida na régua.")
        if len(self.stops) < 2:
            raise InvalidModelError("A régua de preço precisa de ao menos 2 pontos.")

    @property
    def sorted_stops(self) -> tuple[PriceStop, ...]:
        return tuple(sorted(self.stops, key=lambda s: s.value))

    @classmethod
    def derive(cls, reference_price: float, variable_cost: float) -> "PriceScale":
        """Régua padrão derivada do preço sugerido por custos e do custo variável unitário."""
        upper = max(reference_price * 2.2, variable_cost * 3, 100)
        return cls(
            minimum=0,
            maximum=math.ceil(upper / 10) * 10,
            stops=(
                PriceStop(0, "#e06060", "Prejuízo"),
                PriceStop(variable_cost, "#e8825a", "Custo variável"),
                PriceStop(reference_price * 0.6, "#e8a94a", "Abaixo do preço sugerido"),
                PriceStop(reference_price, "#52c97a", "Preço sugerido por custos"),
                PriceStop(reference_price * 1.4, "#e8a94a", "Acima do preço sugerido"),
                PriceStop(upper, "#e06060", "Preço muito alto"),
            ),
        )
