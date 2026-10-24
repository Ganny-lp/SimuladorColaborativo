import streamlit as st

from backend.application.dto import SimulationSnapshot
from frontend.components.variables_table import VariablesTable
from frontend.session.ui_state import UiState
from frontend.views.tab import Tab


class VariablesTab(Tab):
    title = "≋ Variáveis"

    def __init__(self, table: VariablesTable, ui_state: UiState) -> None:
        self._table = table
        self._ui_state = ui_state

    def render(self, snapshot: SimulationSnapshot) -> None:
        st.markdown("### Variáveis do Sistema")
        search = st.text_input("🔍 Filtrar", placeholder="Nome ou categoria…")
        frame = self._table.build_dataframe(snapshot.variables, search)
        self._table.render(frame)
        st.markdown(f"**{len(frame)} de {len(snapshot.variables)} variáveis**")

        names = sorted(v.name for v in snapshot.variables)
        selected = st.selectbox("Ir para variável:", options=[""] + names)
        if selected:
            self._ui_state.selected_variable = selected
            st.info(f"Variável **{selected}** selecionada. Volte à aba Diagrama para editá-la.")
