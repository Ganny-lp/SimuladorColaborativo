from __future__ import annotations

import re
from typing import Iterable


class ReferenceFinder:
    """Descobre quais variáveis uma equação referencia (como palavra inteira)."""

    def find(self, expression: str, names: Iterable[str]) -> set[str]:
        if not expression:
            return set()
        names = sorted(names, key=len, reverse=True)
        if not names:
            return set()
        pattern = re.compile(r"(?<!\w)(?:" + "|".join(re.escape(n) for n in names) + r")(?!\w)")
        return set(pattern.findall(expression))
