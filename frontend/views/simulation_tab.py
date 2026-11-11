from __future__ import annotations

import streamlit as st

from backend.application.dto import PersistenceOutcome, SimulationSnapshot
from backend.application.use_cases.advance_cycle import AdvanceCycleUseCase
from backend.application.use_cases.change_input import ChangeInputUseCase
from backend.application.use_cases.restart_simulation import RestartSimulationUseCase
from frontend.compat import STRETCH, keyed_container
from frontend.components.cycle_charts import CycleCharts
from frontend.components.kpi_cards import KpiCards
from frontend.components.price_slider import PriceSlider
from frontend.components.section import SectionHeader
from frontend.config import DECISION_INPUTS, PRICE_VARIABLE
from frontend.views.tab import Tab


class SimulationTab(Tab):
    title = ":material/monitoring: Simulação"

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
        self._section = SectionHeader()

    def render(self, snapshot: SimulationSnapshot) -> None:
        self._section.render("KPIs do ciclo atual", chip=f"Ciclo {snapshot.cycle}")
        self._kpi_cards.render(snapshot.kpis)

        self._section.render("Decisões", hint="Ajuste as variáveis de decisão e avance o ciclo para ver o efeito.")
        changed = self._render_price_decision(snapshot)
        changed = self._render_other_decisions(snapshot) or changed
        if changed:
            # o snapshot foi tirado antes de aplicar a decisão: recarrega para os KPIs não ficarem defasados
            st.rerun()
        self._render_controls()
        self._section.render("Evolução", hint="Histórico dos ciclos já simulados.")
        self._charts.render(snapshot.history)

    # ── decisões ────────────────────────────────────────────────────────────
    def _render_price_decision(self, snapshot: SimulationSnapshot) -> bool:
        price = snapshot.variable(PRICE_VARIABLE)
        if price is None:
            return False
        with keyed_container("lumina-card-price"):
            chosen = self._price_slider.render(snapshot.price_scale, price.value)
        return self._apply_input(PRICE_VARIABLE, chosen)

    def _render_other_decisions(self, snapshot: SimulationSnapshot) -> bool:
        changed = False
        variables = [v for v in snapshot.variables if v.category == "Input" and not v.expression and v.name != PRICE_VARIABLE]
        for start in range(0, len(variables), 3):
            for column, variable in zip(st.columns(3), variables[start:start + 3]):
                new_value = column.number_input(
                    variable.name, value=float(variable.value), step=0.01,
                    key=f"decision_{variable.name}", help=variable.description or None,
                )
                changed = self._apply_input(variable.name, new_value) or changed
        return changed

    def _apply_input(self, name: str, value: float) -> bool:
        try:
            result = self._change_input.execute(name, value)
        except ValueError as exc:
            st.error(str(exc))
            return False
        if result.changed and result.persistence is PersistenceOutcome.FAILED:
            st.toast("Não foi possível salvar o modelo na nuvem.", icon=":material/warning:")
        return result.changed

    # ── ciclo ───────────────────────────────────────────────────────────────
    def _render_controls(self) -> None:
        advance_col, restart_col = st.columns([3, 1], vertical_alignment="center")
        with advance_col:
            if st.button("Avançar ciclo", type="primary", icon=":material/play_arrow:", **STRETCH):
                self._advance_cycle.execute()
                st.rerun()
        with restart_col:
            if st.button("Reiniciar", icon=":material/restart_alt:", **STRETCH):
                self._restart.execute()
                st.rerun()
