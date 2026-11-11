from __future__ import annotations

from typing import Any, Mapping
import math
import re

from backend.domain.entities.causal_system import CausalSystem
from backend.domain.entities.link import Link, LinkSign
from backend.domain.entities.node import Node, NodeCategory
from backend.domain.entities.price_scale import PriceScale, PriceStop
from backend.domain.exceptions import InvalidModelError

_KNOWN_KEYS = {"nodes", "links", "price_scale", "initial_state"}


class ModelMapper:
    """Converte entre o contrato JSON do modelo (JSONBin / diagrama JS) e o domínio."""

    # ── dict → domínio ──────────────────────────────────────────────────────
    def to_entity(self, data: Mapping[str, Any]) -> CausalSystem:
        if not isinstance(data, Mapping) or "nodes" not in data or "links" not in data:
            raise InvalidModelError("O modelo precisa conter 'nodes' e 'links'.")
        try:
            nodes = {name: self._node(name, raw) for name, raw in data["nodes"].items()}
            links = [self._link(raw) for raw in data["links"]]
            initial_state = {k: self._finite(v) for k, v in (data.get("initial_state") or {}).items()}
            if any(l.source not in nodes or l.target not in nodes for l in links):
                raise InvalidModelError("Ligação referencia uma variável inexistente.")
            if any(k not in nodes for k in initial_state):
                raise InvalidModelError("Estado inicial referencia variável inexistente.")
        except (AttributeError, KeyError, TypeError, ValueError) as exc:
            raise InvalidModelError(f"Modelo malformado: {exc}") from exc
        try:
            scale = self._price_scale(data.get("price_scale"))
        except (AttributeError, KeyError, TypeError, ValueError) as exc:
            raise InvalidModelError(f"Régua inválida: {exc}") from exc
        return CausalSystem(
            nodes=nodes,
            links=links,
            price_scale=scale,
            initial_state=initial_state,
            extras={k: v for k, v in data.items() if k not in _KNOWN_KEYS},
        )

    @staticmethod
    def _finite(value: Any) -> float:
        if isinstance(value, bool):
            raise InvalidModelError("Valores booleanos não são números do modelo.")
        result = float(value)
        if not math.isfinite(result):
            raise InvalidModelError("Valores e coordenadas devem ser finitos.")
        return result

    @staticmethod
    def _node(name: str, raw: Mapping[str, Any]) -> Node:
        if not isinstance(name, str) or not name.strip():
            raise InvalidModelError("Nome de variável vazio ou inválido.")
        if not isinstance(raw.get("expr", ""), str) or not isinstance(raw.get("desc", ""), str):
            raise InvalidModelError("Equação e descrição devem ser texto.")
        if raw["cat"] == "Input" and raw.get("expr", "").strip():
            raise InvalidModelError("Uma entrada não pode ter equação.")
        return Node(
            name=name,
            category=NodeCategory.parse(raw["cat"]),
            value=ModelMapper._finite(raw.get("val", 0)),
            expression=raw.get("expr") or "",
            description=raw.get("desc") or "",
            x=ModelMapper._finite(raw.get("x", 0)),
            y=ModelMapper._finite(raw.get("y", 0)),
        )

    @staticmethod
    def _link(raw: Mapping[str, Any]) -> Link:
        return Link(
            source=raw["from"],
            target=raw["to"],
            sign=LinkSign.parse(raw["sign"]),
            description=raw.get("desc") or "",
        )

    @staticmethod
    def _price_scale(raw: Mapping[str, Any] | None) -> PriceScale | None:
        """Régua ausente ou incompleta (< 2 pontos) vira None → o domínio deriva uma padrão."""
        if not raw or not isinstance(raw.get("stops"), list) or len(raw["stops"]) < 2:
            return None
        stops = tuple(
            PriceStop(ModelMapper._finite(s["value"]), s["color"], s.get("label", "")) for s in raw["stops"]
        )
        return PriceScale(ModelMapper._finite(raw["min"]), ModelMapper._finite(raw["max"]), stops)

    # ── domínio → dict ──────────────────────────────────────────────────────
    def to_dict(self, system: CausalSystem) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "nodes": {
                name: {
                    "cat": node.category.value,
                    "val": node.value,
                    "expr": node.expression,
                    "desc": node.description,
                    "x": node.x,
                    "y": node.y,
                }
                for name, node in system.nodes.items()
            },
            "links": [
                {"from": l.source, "to": l.target, "sign": l.sign.value, "desc": l.description}
                for l in system.links
            ],
        }
        if system.price_scale is not None:
            scale = system.price_scale
            payload["price_scale"] = {
                "min": scale.minimum,
                "max": scale.maximum,
                "stops": [
                    {"value": s.value, "color": s.color, "label": s.label} for s in scale.stops
                ],
            }
        if system.initial_state:
            payload["initial_state"] = dict(system.initial_state)
        payload.update(system.extras)
        return payload
