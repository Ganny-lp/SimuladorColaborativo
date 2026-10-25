from __future__ import annotations

import streamlit as st

from backend.application.dto import PriceScaleDTO
from frontend.assets.asset_template import AssetTemplate
from frontend.compat import render_html_frame

_HIDE_SYNC_INPUT_CSS = """
<style>
div[data-testid="stNumberInput"]:has(input[aria-label="__KEY__"]) {
    position:absolute !important;
    width:1px !important; height:1px !important;
    padding:0 !important; margin:-1px !important;
    overflow:hidden !important; clip:rect(0,0,0,0) !important;
    white-space:nowrap !important; border:0 !important;
}
</style>
"""


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
    """Legenda estática (chip de cor + valor) abaixo da régua."""

    def render(self, scale: PriceScaleDTO) -> None:
        chips = "".join(
            f'<span><i style="background:{s.color}"></i>R$ {s.value:.0f} · {s.label}</span>'
            for s in sorted(scale.stops, key=lambda s: s.value)
        )
        st.markdown(f'<div class="price-legend">{chips}</div>', unsafe_allow_html=True)


class PriceSlider:
    """
    Régua de preço vermelho→verde.

    Composta por (1) um ``st.number_input`` nativo e oculto, que é a ponte Python↔JS, e
    (2) um ``<input type="range">`` em iframe que escreve nele. Retorna o valor vigente
    do number_input; o chamador decide o que fazer quando ele muda.
    """

    _IFRAME_HEIGHT = 84

    def __init__(self, sync_key: str, ruler_key: str) -> None:
        self._sync_key = sync_key
        self._ruler_key = ruler_key
        self._template = AssetTemplate("price_ruler.html")
        self._tokens = AssetTemplate("brand_tokens.css")
        self._bridge = AssetTemplate("theme_bridge.js")
        self._legend = PriceScaleLegend()

    def render(self, scale: PriceScaleDTO, current_value: float) -> float:
        st.markdown(_HIDE_SYNC_INPUT_CSS.replace("__KEY__", self._sync_key), unsafe_allow_html=True)
        synced_value = st.number_input(
            self._sync_key,
            min_value=float(scale.minimum),
            max_value=float(scale.maximum),
            value=float(current_value),
            step=1.0,
            key=self._sync_key,
            label_visibility="collapsed",
        )
        st.markdown("**Preço de Venda (Pt)** · arraste na régua colorida")
        render_html_frame(self._ruler_html(scale, current_value), height=self._IFRAME_HEIGHT)
        self._legend.render(scale)
        return float(synced_value)

    def _ruler_html(self, scale: PriceScaleDTO, value: float) -> str:
        return self._template.render(
            uid=self._ruler_key,
            tokens=self._tokens.read(),
            theme_bridge=self._bridge.read(),
            sync_key=self._sync_key,
            gradient=PriceGradient.css(scale),
            vmin=float(scale.minimum),
            vmax=float(scale.maximum),
            value=float(value),
            vmin_label=f"{scale.minimum:.0f}",
            vmax_label=f"{scale.maximum:.0f}",
            value_label=f"{value:.0f}",
        )
