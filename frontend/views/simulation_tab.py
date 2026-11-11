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
from frontend.config import PRICE_VARIABLE
from frontend.components.decision_control import DecisionControl, group_for
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
        self._decision_control = DecisionControl()

    def render(self, snapshot: SimulationSnapshot) -> None:
        self._section.render("KPIs do ciclo atual", chip=f"Ciclo {snapshot.cycle}")
        self._kpi_cards.render(snapshot.kpis)

        self._section.render("Decisões", hint="Ajuste as variáveis de decisão e avance o ciclo para ver o efeito.")
        self._render_decision_context(snapshot)
        changed = self._render_price_decision(snapshot)
        changed = self._render_other_decisions(snapshot) or changed
        if changed:
            # o snapshot foi tirado antes de aplicar a decisão: recarrega para os KPIs não ficarem defasados
            st.rerun()
        self._render_controls()
        self._section.render("Evolução", hint="Histórico dos ciclos já simulados.")
        self._charts.render(snapshot.history)

    def _render_decision_context(self, snapshot: SimulationSnapshot) -> None:
        def value(name):
            variable = snapshot.variable(name)
            return variable.value if variable else 0
        cols = st.columns(3)
        cols[0].metric("Preço sugerido por custos", f"R$ {value('Preco_Sugerido'):,.2f}")
        cols[1].metric("Fila de serviços", f"{value('Backlog_Servicos'):,.0f}")
        cols[2].metric("Caixa operacional", f"R$ {value('Caixa_Disponivel'):,.2f}")
        st.caption("Indicadores do último ciclo calculado. Use-os para ajustar decisões; coeficientes comportamentais são hipóteses didáticas.")

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
        for group in ("Operação e equipe", "Investimentos e estratégia", "Mercado e ambiente", "Abertura e financiamento"):
            members = [v for v in variables if group_for(v.name) == group]
            with st.expander(group, expanded=group == "Investimentos e estratégia"):
                if group == "Abertura e financiamento":
                    st.caption("Valores iniciais: reinicie a simulação para aplicar mudanças após o primeiro ciclo.")
                for start in range(0, len(members), 2):
                    for column, variable in zip(st.columns(2), members[start:start + 2]):
                        with column:
                            new_value = self._decision_control.render(variable)
                        changed = self._apply_input(variable.name, new_value) or changed
        budgets = [v for v in variables if v.name.startswith("budget_")]
        total = sum(v.value for v in budgets)
        if total > 0:
            st.caption(f"Distribuição do orçamento mensal · R$ {total:,.2f}")
            for variable in budgets:
                st.progress(min(1.0,max(0.0,variable.value/total)), text=f"{variable.name.replace('budget_','')} · {variable.value/total:.0%}")
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
