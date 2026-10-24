from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any, Iterable

from backend.domain.constants import NodeNames
from backend.domain.entities.link import Link
from backend.domain.entities.node import Node
from backend.domain.entities.price_scale import PriceScale
from backend.domain.exceptions import NodeNotFoundError


@dataclass
class CausalSystem:
    """Agregado raiz: o modelo de laços causais (variáveis + ligações + metadados)."""

    nodes: dict[str, Node]
    links: list[Link] = field(default_factory=list)
    price_scale: PriceScale | None = None
    initial_state: dict[str, float] = field(default_factory=dict)
    extras: dict[str, Any] = field(default_factory=dict)  # chaves desconhecidas preservadas

    # ── consulta ────────────────────────────────────────────────────────────
    def has_node(self, name: str) -> bool:
        return name in self.nodes

    def node(self, name: str) -> Node:
        try:
            return self.nodes[name]
        except KeyError:
            raise NodeNotFoundError(name) from None

    def value_of(self, name: str, default: float = 0.0) -> float:
        found = self.nodes.get(name)
        return found.value if found else default

    def values(self) -> dict[str, float]:
        return {name: node.value for name, node in self.nodes.items()}

    # ── comando ─────────────────────────────────────────────────────────────
    def set_value(self, name: str, value: float) -> None:
        self.node(name).value = float(value)

    def apply_values(self, values: Iterable[tuple[str, float]]) -> None:
        for name, value in values:
            if name in self.nodes:
                self.nodes[name].value = float(value)

    def clone(self) -> "CausalSystem":
        return copy.deepcopy(self)

    # ── régua de preço ──────────────────────────────────────────────────────
    def effective_price_scale(self) -> PriceScale:
        """Régua configurada no modelo ou, na ausência dela, uma derivada de Pm e do custo variável."""
        if self.price_scale is not None:
            return self.price_scale
        market_price = self.value_of(NodeNames.PRECO_MERCADO, 140) or 140
        variable_cost = (self.value_of(NodeNames.CUSTO_PECAS, 20) or 0) + (
            self.value_of(NodeNames.CUSTO_MAO_DE_OBRA, 10) or 0
        )
        return PriceScale.derive(market_price, variable_cost)
