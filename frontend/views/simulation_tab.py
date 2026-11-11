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
from backend.application.use_cases._base import SimulationError


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
        market_data=None,
    ) -> None:
        self._kpi_cards = kpi_cards
        self._price_slider = price_slider
        self._charts = charts
        self._change_input = change_input
        self._advance_cycle = advance_cycle
        self._restart = restart
        self._market_data = market_data
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
        enabled = snapshot.variable("Simular_Abertura")
        if enabled:
            if snapshot.cycle == 0:
                opening = st.toggle("Simular abertura da empresa?", value=bool(enabled.value))
                changed = self._apply_input("Simular_Abertura", float(opening)) or changed
            else:
                opening = bool(enabled.value)
                st.caption("Configuração inicial encerrada. Reinicie para simular outra abertura.")
        else:
            opening = False
        primary = {"Numero_Tecnicos", "Estoque_Alvo", "budget_training", "budget_update", "budget_infra", "budget_promo"}
        def render_members(members):
            nonlocal changed
            for start in range(0,len(members),2):
                for column,variable in zip(st.columns(2),members[start:start+2]):
                    with column:
                        chosen = self._decision_control.render(variable)
                    changed = self._apply_input(variable.name,chosen) or changed
        render_members([v for v in variables if v.name in primary])
        if opening and snapshot.cycle == 0:
            with st.expander("Preparar abertura e financiamento",expanded=True):
                st.caption("Desembolso inicial e crédito ocorrem uma única vez no primeiro ciclo. As parcelas do empréstimo continuam até o prazo contratado.")
                render_members([v for v in variables if group_for(v.name)=="Abertura e financiamento" and v.name!="Simular_Abertura"])
        with st.expander("Ajustes operacionais avançados"):
            render_members([v for v in variables if v.name not in primary and group_for(v.name) not in {"Mercado e ambiente","Abertura e financiamento"}])
        from frontend.components.market_context import render_market_context
        changed = render_market_context(snapshot,self._apply_input,self._market_data) or changed
        from frontend.components.budget_summary import render_budget_summary
        render_budget_summary(variables)
        return changed

    def _apply_input(self, name: str, value: float) -> bool:
        try:
            result = self._change_input.execute(name, value)
        except (SimulationError, ValueError) as exc:
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
                try:
                    self._advance_cycle.execute()
                except (SimulationError, ValueError) as exc:
                    st.error(f"O ciclo não foi aplicado: {exc}")
                else:
                    st.rerun()
        with restart_col:
            if st.button("Reiniciar", icon=":material/restart_alt:", **STRETCH):
                self._restart.execute()
                st.rerun()
