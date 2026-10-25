from __future__ import annotations

from html import escape

import streamlit as st

from backend.application.dto import KpiDTO
from frontend import formatters


class KpiCards:
    """Indicadores do ciclo. Grid CSS próprio: 4 → 2 → 1 coluna conforme a largura disponível."""

    def cards(self, kpis: KpiDTO) -> tuple[tuple[str, str, str, str], ...]:
        """(rótulo, valor, dica, tom) de cada cartão. O tom colore só o que tem sinal."""
        profit = kpis.accumulated_profitability
        tone = "neg" if profit < 0 else "pos" if profit > 0 else "neutral"
        return (
            ("Rentabilidade acumulada", formatters.thousands_currency(profit), "soma dos ciclos até agora", tone),
            ("Receita do ciclo", formatters.currency(kpis.net_revenue), "receita líquida no ciclo atual", "neutral"),
            ("Quantidade atendida", formatters.integer(kpis.served_quantity), "unidades vendidas no ciclo", "neutral"),
            ("Market share", formatters.percent(kpis.market_share), "fatia do mercado capturada", "neutral"),
        )

    def html(self, kpis: KpiDTO) -> str:
        items = "".join(
            f'<div class="kpi" data-tone="{tone}"><span class="kpi-label">{escape(label)}</span>'
            f'<span class="kpi-value">{escape(value)}</span><span class="kpi-hint">{escape(hint)}</span></div>'
            for label, value, hint, tone in self.cards(kpis)
        )
        return f'<div class="kpi-grid">{items}</div>'

    def render(self, kpis: KpiDTO) -> None:
        st.markdown(self.html(kpis), unsafe_allow_html=True)
