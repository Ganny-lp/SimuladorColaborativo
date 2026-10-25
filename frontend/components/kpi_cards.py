import streamlit as st

from backend.application.dto import KpiDTO
from frontend import formatters


class KpiCards:
    """Cartões de KPI numa grade CSS: reorganiza sozinha de 4 colunas até 1, conforme a largura."""

    def render(self, kpis: KpiDTO) -> None:
        cards = (
            ("Rentabilidade", formatters.thousands_currency(kpis.accumulated_profitability)),
            ("Receita Ciclo", formatters.currency(kpis.net_revenue)),
            ("Qt Atendida", formatters.integer(kpis.served_quantity)),
            ("Market Share", formatters.percent(kpis.market_share)),
        )
        html = "".join(
            f'<div class="card"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div></div>'
            for label, value in cards
        )
        st.markdown(f'<div class="kpi-grid">{html}</div>', unsafe_allow_html=True)
