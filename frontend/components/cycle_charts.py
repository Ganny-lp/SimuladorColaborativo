from __future__ import annotations

from typing import Sequence

import plotly.graph_objects as go
import streamlit as st

from backend.application.dto import CycleRecordDTO
from frontend.branding import PALETTE
from frontend.compat import STRETCH, keyed_container
from frontend.formatters import currency, decimal_number

_MARGIN = dict(l=8, r=8, t=8, b=8)
_HOVER_FONT = dict(family="Open Sans, sans-serif", size=13)


class CycleCharts:
    """
    Gráficos da evolução por ciclo.

    Sem ``template`` fixo: o Streamlit aplica o tema claro/escuro vigente (textos, grade, fundo).
    Só as cores de dados vêm da marca (azul USP para positivo, coral para negativo).
    """

    def render(self, history: Sequence[CycleRecordDTO]) -> None:
        if not history:
            st.markdown('<div class="lab-empty"><span>AINDA É O COMEÇO</span><h3>Uma decisão inicia uma trajetória.</h3><p>Avance o primeiro ciclo para acompanhar o resultado mensal e o fluxo acumulado.</p></div>',unsafe_allow_html=True)
            return
        cycles = [r.cycle for r in history]
        left, right = st.columns(2)
        with left, keyed_container("lumina-card-chart-acc"):
            st.markdown(
                '<p class="chart-title">Rentabilidade acumulada</p>'
                '<p class="chart-hint">Desembolso inicial + fluxos de caixa até cada ciclo</p>',
                unsafe_allow_html=True,
            )
            st.plotly_chart(self.accumulated_chart(cycles, [r.accumulated_profitability for r in history]), **STRETCH)
        with right, keyed_container("lumina-card-chart-profit"):
            st.markdown(
                '<p class="chart-title">Resultado líquido por ciclo</p>'
                '<p class="chart-hint">Resultado de cada ciclo isoladamente</p>',
                unsafe_allow_html=True,
            )
            st.plotly_chart(self.profit_chart(cycles, [r.profit for r in history]), **STRETCH)
        self._render_cycle_details(history)

    @staticmethod
    def _render_cycle_details(history: Sequence[CycleRecordDTO]) -> None:
        with st.expander("Reparos, receitas e fluxo de caixa por ciclo", expanded=True):
            st.caption(
                "Receita bruta = preço praticado × reparos concluídos (Qt). "
                "A receita líquida desconta os tributos. Compras e consumo de peças ajustam "
                "o resultado líquido para chegar ao fluxo de caixa."
            )
            if len(history) > 1:
                previous, current = history[-2:]
                if all(v is not None for v in (previous.net_revenue, current.net_revenue, previous.costs, current.costs)):
                    delta_revenue = current.net_revenue - previous.net_revenue
                    delta_costs = current.costs - previous.costs
                    volumes = ""
                    if previous.served_quantity is not None and current.served_quantity is not None:
                        volumes = (
                            f" Reparos concluídos de {decimal_number(previous.served_quantity)} "
                            f"para {decimal_number(current.served_quantity)}."
                        )
                    st.caption(
                        f"Do ciclo {previous.cycle} ao {current.cycle}, a receita líquida variou "
                        f"{currency(delta_revenue)} e os custos variaram {currency(delta_costs)}."
                        f"{volumes}"
                    )
            money = ("Preço praticado", "Receita bruta", "Receita líquida", "Custos", "Resultado líquido", "Fluxo de caixa")
            st.dataframe(
                [
                    {
                        "Ciclo": r.cycle,
                        "Reparos (Qt)": r.served_quantity,
                        "Preço praticado": r.price,
                        "Receita bruta": r.gross_revenue,
                        "Receita líquida": r.net_revenue,
                        "Custos": r.costs,
                        "Resultado líquido": r.profit,
                        "Fluxo de caixa": r.cash_flow,
                        "Inflação (%)": r.inflation * 100 if r.inflation is not None else None,
                    }
                    for r in reversed(history)
                ],
                column_config={
                    **{name: st.column_config.NumberColumn(format="R$ %.2f") for name in money},
                    "Reparos (Qt)": st.column_config.NumberColumn(format="%.2f"),
                    "Inflação (%)": st.column_config.NumberColumn(format="%.2f%%"),
                },
                hide_index=True, **STRETCH,
            )

    # ── figuras ────────────────────────────────────────────────────────────
    @classmethod
    def accumulated_chart(cls, x: list[int], y: list[float]) -> go.Figure:
        figure = go.Figure(
            go.Scatter(
                x=x, y=y, mode="lines+markers", name="Rentabilidade",
                line=dict(color=PALETTE.usp_blue, width=3, shape="linear"),
                marker=dict(size=8, color=PALETTE.usp_blue, line=dict(width=2, color="rgba(255,255,255,.85)")),
                fill="tozeroy", fillcolor="rgba(16,148,171,.12)",
                hovertemplate="Ciclo %{x}<br><b>R$ %{y:,.0f}</b><extra></extra>",
            )
        )
        return cls._style(figure, x)

    @classmethod
    def profit_chart(cls, x: list[int], y: list[float]) -> go.Figure:
        figure = go.Figure(
            go.Bar(
                x=x, y=y, name="Lucro",
                marker_color=[PALETTE.usp_blue_light if v >= 0 else PALETTE.negative for v in y],
                hovertemplate="Ciclo %{x}<br><b>R$ %{y:,.0f}</b><extra></extra>",
            )
        )
        figure.update_layout(bargap=.35)
        return cls._style(figure, x)

    @staticmethod
    def _style(figure: go.Figure, x: list[int]) -> go.Figure:
        figure.update_layout(
            height=280, margin=_MARGIN, showlegend=False, hoverlabel=dict(font=_HOVER_FONT),
            separators=",.",   # pt-BR: vírgula decimal, ponto de milhar
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Open Sans, sans-serif", size=12),
        )
        figure.update_xaxes(
            title_text="Ciclo", showgrid=False, zeroline=False,
            tickmode="linear" if len(x) <= 15 else "auto", dtick=1 if len(x) <= 15 else None,
        )
        figure.update_yaxes(tickprefix="R$ ", tickformat=",.0f", zeroline=True, gridcolor="rgba(128,150,165,.18)",
                            zerolinecolor="rgba(128,150,165,.45)", title_text=None)
        return figure
