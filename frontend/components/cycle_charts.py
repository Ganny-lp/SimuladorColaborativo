from __future__ import annotations

from typing import Sequence

import plotly.graph_objects as go
import streamlit as st

from backend.application.dto import CycleRecordDTO
from frontend.branding import PALETTE
from frontend.compat import STRETCH

_BLUE, _GREEN, _RED = PALETTE.usp_blue_light, PALETTE.positive, PALETTE.negative
_GRID = "rgba(143,170,188,.14)"


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
            title=dict(text=title, font=dict(family="Montserrat, Open Sans, sans-serif", size=14, color=PALETTE.text)),
            template="plotly_dark", height=260,
            margin=dict(l=10, r=10, t=40, b=20),
            font=dict(family="Open Sans, sans-serif", color=PALETTE.text_muted),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        )
        figure.update_xaxes(gridcolor=_GRID, zerolinecolor=_GRID, title_text="Ciclo")
        figure.update_yaxes(gridcolor=_GRID, zerolinecolor=PALETTE.slate)
        return figure
