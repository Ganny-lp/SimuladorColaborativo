"""Identidade visual LUMINA · PUB USP: constantes de marca (espelho de assets/brand_tokens.css) e ativos."""
from __future__ import annotations

import base64
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

_BRAND_DIR = Path(__file__).parent / "assets" / "brand"


@dataclass(frozen=True)
class Palette:
    """Cores de marca que o Python precisa conhecer (gráficos). Fonte: brand_tokens.css."""

    slate: str = "#6f8391"            # cinza-azulado da logo
    usp_blue: str = "#1094ab"         # azul primário USP
    usp_blue_light: str = "#64c4d2"   # azul secundário USP
    usp_yellow: str = "#fcb421"       # amarelo USP


PALETTE = Palette()

# Cores de dados nos gráficos: legíveis sobre fundo claro e escuro (o tema do Streamlit cuida do resto).
CHART_PRIMARY = PALETTE.usp_blue
CHART_POSITIVE = "#2fa866"
CHART_NEGATIVE = "#e0594e"


class BrandAssets:
    """Símbolo (máscara PNG, sem cor própria) e favicon da marca."""

    @staticmethod
    @lru_cache(maxsize=None)
    def mark_data_uri() -> str:
        """Máscara do símbolo como data URI, usada em CSS (`--mark-url`) na página e nos iframes."""
        data = (_BRAND_DIR / "lumina_mark.png").read_bytes()
        return "data:image/png;base64," + base64.b64encode(data).decode("ascii")

    @staticmethod
    def favicon_path() -> str:
        return str(_BRAND_DIR / "favicon.png")

    @staticmethod
    def mark_css_variable() -> str:
        return f':root{{--mark-url:url("{BrandAssets.mark_data_uri()}");}}'
