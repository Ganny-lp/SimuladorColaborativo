from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from backend.domain.exceptions import InvalidModelError


class NodeCategory(str, Enum):
    """Categorias de variáveis do diagrama de laços causais."""

    STATE = "Estado"
    EQUATION = "Equação"
    PARAMETER = "Parâmetro"
    ENVIRONMENT = "Ambiente"
    INPUT = "Input"

    @classmethod
    def parse(cls, label: str) -> "NodeCategory":
        try:
            return cls(label)
        except ValueError as exc:
            valid = ", ".join(c.value for c in cls)
            raise InvalidModelError(f"Categoria inválida '{label}'. Válidas: {valid}.") from exc


@dataclass
class Node:
    """Variável do sistema (nó do CLD) com valor corrente e, opcionalmente, uma equação."""

    name: str
    category: NodeCategory
    value: float = 0.0
    expression: str = ""
    description: str = ""
    x: float = 0.0
    y: float = 0.0

    @property
    def has_expression(self) -> bool:
        return bool(self.expression and self.expression.strip())

    @property
    def is_state(self) -> bool:
        """Nós de categoria 'Estado' acumulam: valor_novo = valor_anterior + equação."""
        return self.category is NodeCategory.STATE
