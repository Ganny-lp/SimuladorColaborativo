from __future__ import annotations

from typing import Sequence

import plotly.graph_objects as go
import streamlit as st

from backend.application.dto import CycleRecordDTO
from frontend.branding import CHART_NEGATIVE, CHART_POSITIVE, CHART_PRIMARY
from frontend.compat import STRETCH


class CycleCharts:
    """Gráficos de barras da evolução por ciclo (claro/escuro: o tema do Streamlit cuida de fundo e texto)."""

    def render(self, history: Sequence[CycleRecordDTO]) -> None:
        if not history:
            st.info("Avance alguns ciclos para visualizar os gráficos.", icon=":material/insights:")
            return
        cycles = [r.cycle for r in history]
        with st.container(key="lumina-charts"):
            left, right = st.columns(2)
            with left:
                st.plotly_chart(
                    self._bar_chart(
                        "Rentabilidade Acumulada", "Rentabilidade", cycles,
                        [r.accumulated_profitability for r in history], positive_color=CHART_PRIMARY,
                    ),
                    **STRETCH,
                )
            with right:
                st.plotly_chart(
                    self._bar_chart(
                        "Lucro Líquido por Ciclo", "Lucro", cycles,
                        [r.profit for r in history], positive_color=CHART_POSITIVE,
                    ),
                    **STRETCH,
                )

    @staticmethod
    def _bar_chart(
        title: str, series_name: str, x: list[int], y: list[float], positive_color: str
    ) -> go.Figure:
        figure = go.Figure()
        figure.add_trace(
            go.Bar(x=x, y=y, name=series_name,
                   marker_color=[positive_color if v >= 0 else CHART_NEGATIVE for v in y])
        )
        figure.update_layout(
            title=dict(text=title, font=dict(family="Montserrat, Open Sans, sans-serif", size=15)),
            height=300, margin=dict(l=10, r=10, t=56, b=30), showlegend=False,
            font=dict(family="Open Sans, sans-serif"),
        )
        figure.update_xaxes(title_text="Ciclo", dtick=1)
        return figure
