from __future__ import annotations

from html import escape

import streamlit as st

from backend.application.dto import PriceScaleDTO
from frontend.assets.asset_template import AssetTemplate, js_literal
from frontend.compat import render_html_frame
from frontend.config import FONTS_URL
from frontend.formatters import currency

class PriceGradient:
    """Converte os pontos da régua num ``linear-gradient`` CSS."""

    @staticmethod
    def css(scale: PriceScaleDTO) -> str:
        span = (scale.maximum - scale.minimum) or 1.0

        def percent(value: float) -> float:
            return max(0.0, min(100.0, (value - scale.minimum) / span * 100.0))

        stops = sorted(scale.stops, key=lambda s: s.value)
        return "linear-gradient(to right, " + ", ".join(
            f"{s.color} {percent(s.value):.2f}%" for s in stops
        ) + ")"


class PriceScaleLegend:
    """Legenda dos pontos de referência: grid responsivo (cor + preço + rótulo)."""

    def html(self, scale: PriceScaleDTO) -> str:
        items = "".join(
            f'<li><i style="background:{escape(s.color)}"></i>'
            f"<span><b>{currency(s.value)}</b> · {escape(s.label)}</span></li>"
            for s in sorted(scale.stops, key=lambda s: s.value)
        )
        return f'<ul class="price-legend">{items}</ul>'

    def render(self, scale: PriceScaleDTO) -> None:
        st.markdown(self.html(scale), unsafe_allow_html=True)


class PriceSlider:
    """Escala nativa de preço com digitação exata e legenda de custos."""

    _IFRAME_HEIGHT = 88

    def __init__(self, sync_key: str, ruler_key: str) -> None:
        self._sync_key = sync_key
        self._ruler_key = ruler_key
        self._template = AssetTemplate("price_ruler.html")
        self._tokens = AssetTemplate("brand_tokens.css")
        self._theme_sync = AssetTemplate("theme_sync.js")
        self._legend = PriceScaleLegend()

    def render(self, scale: PriceScaleDTO, current_value: float) -> float:
        from frontend.components.decision_control import scaled_number
        st.markdown('<div class="decision-eyebrow">SUA DECISÃO · R$/SERVIÇO</div>',unsafe_allow_html=True)
        chosen = scaled_number("Preço praticado", current_value, self._sync_key,
                               maximum=max(scale.maximum,current_value), step=1.0,
                               hint="Arraste a escala ou digite o valor exato. A sugestão usa os custos da sua operação.")
        self._legend.render(scale)
        return chosen

    def _ruler_html(self, scale: PriceScaleDTO) -> str:
        ordered = sorted(scale.stops, key=lambda s: s.value)
        stops = [{"v": s.value, "c": s.color, "l": s.label} for s in ordered]
        return self._template.render(
            fonts_url=FONTS_URL,
            tokens=self._tokens.read(),
            theme_sync=self._theme_sync.read(),
            uid=self._ruler_key,
            sync_key=self._sync_key,
            gradient=PriceGradient.css(scale),
            vmin=f"{float(scale.minimum):g}",
            vmax=f"{float(scale.maximum):g}",
            vmin_label=f"{scale.minimum:.0f}",
            vmax_label=f"{scale.maximum:.0f}",
            stops_json=js_literal(stops),
        )
