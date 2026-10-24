from __future__ import annotations

import streamlit as st

from backend.application.dto import PersistenceOutcome, SimulationSnapshot
from backend.application.use_cases.advance_cycle import AdvanceCycleUseCase
from backend.application.use_cases.change_input import ChangeInputUseCase
from backend.application.use_cases.restart_simulation import RestartSimulationUseCase
from frontend.compat import STRETCH
from frontend.components.cycle_charts import CycleCharts
from frontend.components.kpi_cards import KpiCards
from frontend.components.price_slider import PriceSlider
from frontend.config import DECISION_INPUTS, PRICE_VARIABLE
from frontend.views.tab import Tab


class SimulationTab(Tab):
    title = "▶ Simulação"

    def __init__(
        self,
        kpi_cards: KpiCards,
        price_slider: PriceSlider,
        charts: CycleCharts,
        change_input: ChangeInputUseCase,
        advance_cycle: AdvanceCycleUseCase,
        restart: RestartSimulationUseCase,
    ) -> None:
        self._kpi_cards = kpi_cards
        self._price_slider = price_slider
        self._charts = charts
        self._change_input = change_input
        self._advance_cycle = advance_cycle
        self._restart = restart

    def render(self, snapshot: SimulationSnapshot) -> None:
        st.markdown("### KPIs do Ciclo Atual")
        self._kpi_cards.render(snapshot.kpis)

        st.markdown("### Decisões de Input")
        self._render_price_decision(snapshot)
        self._render_other_decisions(snapshot)
        self._render_controls(snapshot)
        self._charts.render(snapshot.history)

    # ── decisões ────────────────────────────────────────────────────────────
    def _render_price_decision(self, snapshot: SimulationSnapshot) -> None:
        price = snapshot.variable(PRICE_VARIABLE)
        if price is None:
            return
        chosen = self._price_slider.render(snapshot.price_scale, price.value)
        self._apply_input(PRICE_VARIABLE, chosen)

    def _render_other_decisions(self, snapshot: SimulationSnapshot) -> None:
        columns = st.columns(len(DECISION_INPUTS))
        for column, decision in zip(columns, DECISION_INPUTS):
            variable = snapshot.variable(decision.variable)
            if variable is None:
                continue
            step = 100.0 if variable.value > 10 else 0.01
            new_value = column.number_input(
                decision.label, value=float(variable.value), step=step, format="%.4g"
            )
            self._apply_input(decision.variable, new_value)

    def _apply_input(self, name: str, value: float) -> None:
        result = self._change_input.execute(name, value)
        if result.changed and result.persistence is PersistenceOutcome.FAILED:
            st.toast("⚠️ Não foi possível salvar o modelo na nuvem.")

    # ── ciclo ───────────────────────────────────────────────────────────────
    def _render_controls(self, snapshot: SimulationSnapshot) -> None:
        st.markdown(f"**Ciclo atual:** {snapshot.cycle}")
        advance_col, restart_col = st.columns([3, 1])
        with advance_col:
            if st.button("▶ Avançar Ciclo", **STRETCH):
                self._advance_cycle.execute()
                st.rerun()
        with restart_col:
            if st.button("↺ Reiniciar", **STRETCH):
                self._restart.execute()
                st.rerun()
