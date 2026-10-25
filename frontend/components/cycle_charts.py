from __future__ import annotations

from typing import Sequence

import plotly.graph_objects as go
import streamlit as st

from backend.application.dto import CycleRecordDTO
from frontend.branding import PALETTE
from frontend.compat import STRETCH, keyed_container

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
            st.info("Avance alguns ciclos para ver a evolução aqui.", icon=":material/insights:")
            return
        cycles = [r.cycle for r in history]
        left, right = st.columns(2)
        with left, keyed_container("lumina-card-chart-acc"):
            st.markdown(
                '<p class="chart-title">Rentabilidade acumulada</p>'
                '<p class="chart-hint">Soma dos lucros até cada ciclo</p>',
                unsafe_allow_html=True,
            )
            st.plotly_chart(self.accumulated_chart(cycles, [r.accumulated_profitability for r in history]), **STRETCH)
        with right, keyed_container("lumina-card-chart-profit"):
            st.markdown(
                '<p class="chart-title">Lucro líquido por ciclo</p>'
                '<p class="chart-hint">Resultado de cada ciclo isoladamente</p>',
                unsafe_allow_html=True,
            )
            st.plotly_chart(self.profit_chart(cycles, [r.profit for r in history]), **STRETCH)

    # ── figuras ────────────────────────────────────────────────────────────
    @classmethod
    def accumulated_chart(cls, x: list[int], y: list[float]) -> go.Figure:
        figure = go.Figure(
            go.Scatter(
                x=x, y=y, mode="lines+markers", name="Rentabilidade",
                line=dict(color=PALETTE.usp_blue, width=3, shape="spline", smoothing=.4),
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
