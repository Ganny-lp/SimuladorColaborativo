"""Identidade visual LUMINA · PUB USP: paleta (espelho de assets/brand_tokens.css) e ativos de marca."""
from __future__ import annotations

import base64
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

_BRAND_DIR = Path(__file__).parent / "assets" / "brand"


@dataclass(frozen=True)
class Palette:
    """Cores usadas no lado Python (gráficos, chips). Fonte: brand_tokens.css."""

    slate: str = "#6f8391"            # cinza-azulado da logo
    slate_light: str = "#b0c6d4"
    usp_blue: str = "#1094ab"         # azul primário USP
    usp_blue_light: str = "#64c4d2"   # azul secundário USP
    usp_yellow: str = "#fcb421"       # amarelo USP
    bg: str = "#0b1218"
    surface: str = "#192832"
    text: str = "#dbe6ec"
    text_muted: str = "#9db1be"
    text_faint: str = "#7a8f9d"
    positive: str = "#52c97a"
    negative: str = "#e8685d"


PALETTE = Palette()


class BrandAssets:
    """Símbolo e favicon da marca (PNGs transparentes derivados da logo, para fundo escuro)."""

    @staticmethod
    @lru_cache(maxsize=None)
    def mark_data_uri() -> str:
        """Símbolo como data URI: serve para <img> no Streamlit e para o iframe do diagrama."""
        data = (_BRAND_DIR / "lumina_mark.png").read_bytes()
        return "data:image/png;base64," + base64.b64encode(data).decode("ascii")

    @staticmethod
    def favicon_path() -> str:
        return str(_BRAND_DIR / "favicon.png")
