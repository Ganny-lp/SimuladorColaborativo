import streamlit as st

from backend.application.dto import KpiDTO
from frontend import formatters


class KpiCards:
    def render(self, kpis: KpiDTO) -> None:
        cards = (
            ("Rentabilidade", formatters.thousands_currency(kpis.accumulated_profitability)),
            ("Receita Ciclo", formatters.currency(kpis.net_revenue)),
            ("Qt Atendida", formatters.integer(kpis.served_quantity)),
            ("Market Share", formatters.percent(kpis.market_share)),
        )
        for column, (label, value) in zip(st.columns(len(cards)), cards):
            with column:
                st.markdown(
                    f'<div class="card"><div class="kpi-label">{label}</div>'
                    f'<div class="kpi-value">{value}</div></div>',
                    unsafe_allow_html=True,
                )
