"""Identidade visual LUMINA · PUB USP: paleta (espelho de assets/brand_tokens.css) e ativos de marca."""
from __future__ import annotations

import base64
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

_BRAND_DIR = Path(__file__).parent / "assets" / "brand"


@dataclass(frozen=True)
class Palette:
    """Cores usadas no lado Python (gráficos). São as da marca, iguais nos temas claro e escuro.

    Fonte: ``:root`` em brand_tokens.css. As cores de superfície/texto, que mudam com o tema,
    ficam só no CSS.
    """

    slate: str = "#6f8391"
    slate_light: str = "#b0c6d4"
    usp_blue: str = "#1094ab"        # azul primário USP
    usp_blue_light: str = "#64c4d2"  # azul secundário USP
    usp_yellow: str = "#fcb421"      # amarelo USP
    positive: str = "#2fa56b"
    negative: str = "#e0584d"


PALETTE = Palette()


class BrandAssets:
    """Símbolo e favicon da marca. O símbolo tem uma variante para cada tema."""

    @staticmethod
    @lru_cache(maxsize=None)
    def mark_data_uri(variant: str = "dark") -> str:
        """Símbolo como data URI (serve ao CSS da página e ao iframe do diagrama).

        ``dark``: traços claros, para fundo escuro. ``light``: traços escuros, para fundo claro.
        """
        filename = "lumina_mark_light.png" if variant == "light" else "lumina_mark.png"
        data = (_BRAND_DIR / filename).read_bytes()
        return "data:image/png;base64," + base64.b64encode(data).decode("ascii")

    @staticmethod
    def favicon_path() -> str:
        return str(_BRAND_DIR / "favicon.png")
