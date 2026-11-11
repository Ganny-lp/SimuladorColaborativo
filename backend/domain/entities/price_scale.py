from __future__ import annotations

from dataclasses import dataclass

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
            maximum=round(upper, -1) or 300,
            stops=(
                PriceStop(0, "#e06060", "Prejuízo"),
                PriceStop(variable_cost, "#e8825a", "Custo variável"),
                PriceStop(reference_price * 0.6, "#e8a94a", "Abaixo do preço sugerido"),
                PriceStop(reference_price, "#52c97a", "Preço sugerido por custos"),
                PriceStop(reference_price * 1.4, "#e8a94a", "Acima do preço sugerido"),
                PriceStop(upper, "#e06060", "Preço muito alto"),
            ),
        )
