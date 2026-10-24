from __future__ import annotations

from typing import Sequence

import plotly.graph_objects as go
import streamlit as st

from backend.application.dto import CycleRecordDTO
from frontend.compat import STRETCH

_BLUE, _GREEN, _RED = "#4a6aee", "#52c97a", "#e06060"


class CycleCharts:
    """Gráficos de barras da evolução por ciclo."""

    def render(self, history: Sequence[CycleRecordDTO]) -> None:
        if not history:
            st.info("▶ Avance alguns ciclos para visualizar os gráficos.")
            return
        cycles = [r.cycle for r in history]
        left, right = st.columns(2)
        with left:
            st.plotly_chart(
                self._bar_chart(
                    "Rentabilidade Acumulada", "Rentabilidade", cycles,
                    [r.accumulated_profitability for r in history], positive_color=_BLUE,
                ),
                **STRETCH,
            )
        with right:
            st.plotly_chart(
                self._bar_chart(
                    "Lucro Líquido por Ciclo", "Lucro", cycles,
                    [r.profit for r in history], positive_color=_GREEN,
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
                   marker_color=[positive_color if v >= 0 else _RED for v in y])
        )
        figure.update_layout(
            title=title, template="plotly_dark", height=260,
            margin=dict(l=10, r=10, t=40, b=20), font=dict(family="DM Sans"),
        )
        return figure
