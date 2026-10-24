from __future__ import annotations

import re
from typing import Iterable


class ReferenceFinder:
    """Descobre quais variáveis uma equação referencia (como palavra inteira)."""

    def find(self, expression: str, names: Iterable[str]) -> set[str]:
        if not expression:
            return set()
        return {
            name
            for name in names
            if re.search(r"\b" + re.escape(name) + r"\b", expression)
        }
