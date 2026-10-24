from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

_ASSETS_DIR = Path(__file__).parent
_TOKEN = re.compile(r"__([A-Z][A-Z0-9_]*)__")


@lru_cache(maxsize=None)
def _read(filename: str) -> str:
    return (_ASSETS_DIR / filename).read_text(encoding="utf-8")


class AssetTemplate:
    """
    Template de arquivo estático (HTML/CSS/JS) com marcadores ``__NOME__``.

    A substituição é feita em uma única passagem: o texto injetado nunca é
    re-interpretado, então valores do usuário não conseguem acionar outros marcadores.
    """

    def __init__(self, filename: str) -> None:
        self._filename = filename

    def read(self) -> str:
        return _read(self._filename)

    def render(self, **tokens: object) -> str:
        values = {key.upper(): str(value) for key, value in tokens.items()}
        return _TOKEN.sub(lambda m: values.get(m.group(1), m.group(0)), self.read())
