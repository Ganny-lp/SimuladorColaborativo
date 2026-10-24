from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from backend.domain.exceptions import InvalidModelError


class LinkSign(str, Enum):
    POSITIVE = "+"
    NEGATIVE = "-"

    @classmethod
    def parse(cls, symbol: str) -> "LinkSign":
        try:
            return cls(symbol)
        except ValueError as exc:
            raise InvalidModelError(f"Sinal de ligação inválido: '{symbol}'.") from exc


@dataclass(frozen=True)
class Link:
    """Relação causal dirigida entre duas variáveis."""

    source: str
    target: str
    sign: LinkSign
    description: str = ""
