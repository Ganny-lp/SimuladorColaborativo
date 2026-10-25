from __future__ import annotations

from html import escape

import streamlit as st

from backend.application.dto import PriceScaleDTO
from frontend.assets.asset_template import AssetTemplate, js_literal
from frontend.compat import render_html_frame
from frontend.config import FONTS_URL
from frontend.formatters import currency

# O input numérico nativo é a ponte Python↔JS. Fica no DOM (precisa receber foco/eventos),
# mas invisível e fora do fluxo: sem isso ele abriria um espaço vazio entre os elementos.
_HIDE_SYNC_INPUT_CSS = """
<style>
[data-testid="stElementContainer"]:has(input[aria-label="__KEY__"]),
div[data-testid="stNumberInput"]:has(input[aria-label="__KEY__"]){
    position:absolute !important; width:1px !important; height:1px !important;
    padding:0 !important; margin:-1px !important; overflow:hidden !important;
    clip:rect(0,0,0,0) !important; white-space:nowrap !important; border:0 !important;
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
    """
    Régua de preço vermelho→verde.

    Composta por (1) um ``st.number_input`` nativo e oculto, que é a ponte Python↔JS, e
    (2) um ``<input type="range">`` em iframe que escreve nele. O HTML do iframe não contém o
    valor atual (a régua o lê do input oculto), então não muda entre execuções: o Streamlit não
    recria o iframe, e arraste e foco de teclado sobrevivem ao rerun.
    Retorna o valor vigente do number_input; o chamador decide o que fazer quando ele muda.
    """

    _IFRAME_HEIGHT = 88

    def __init__(self, sync_key: str, ruler_key: str) -> None:
        self._sync_key = sync_key
        self._ruler_key = ruler_key
        self._template = AssetTemplate("price_ruler.html")
        self._tokens = AssetTemplate("brand_tokens.css")
        self._theme_sync = AssetTemplate("theme_sync.js")
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
        st.markdown(
            '<div class="price-head"><p class="card-title">Preço de venda <code>Pt</code></p>'
            '<p class="card-hint">Arraste a régua ou use as setas do teclado</p></div>',
            unsafe_allow_html=True,
        )
        render_html_frame(self._ruler_html(scale), height=self._IFRAME_HEIGHT)
        self._legend.render(scale)
        return float(synced_value)

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
