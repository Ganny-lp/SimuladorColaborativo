import streamlit as st

from backend.application.dto import SimulationSnapshot
from frontend.compat import STRETCH
from frontend.components.section import SectionHeader
from frontend.components.variables_table import VariablesTable
from frontend.session.ui_state import UiState
from frontend.views.tab import Tab


class VariablesTab(Tab):
    title = ":material/table_rows: Variáveis"

    def __init__(self, table: VariablesTable, ui_state: UiState) -> None:
        self._table = table
        self._ui_state = ui_state
        self._section = SectionHeader()

    def render(self, snapshot: SimulationSnapshot) -> None:
        self._section.render("Variáveis do sistema", hint="Valores do ciclo atual, com a equação de cada uma.")
        search_col, category_col = st.columns([2, 3], vertical_alignment="bottom")
        search = search_col.text_input("Filtrar", placeholder="Nome ou categoria…")
        categories = category_col.multiselect(
            "Categorias", options=sorted({v.category for v in snapshot.variables}), placeholder="Todas as categorias"
        )
        frame = self._table.build_dataframe(snapshot.variables, search, categories)
        self._table.render(frame)
        st.caption(f"{len(frame)} de {len(snapshot.variables)} variáveis")

        names = sorted(v.name for v in snapshot.variables)
        st.selectbox(
            "Localizar no diagrama",
            options=names, index=None, placeholder="Escolha uma variável…",
            key=UiState.PICKER_KEY, on_change=self._ui_state.request_focus,
        )
        selected = self._ui_state.selected_variable
        if selected:
            in_diagram = selected in (snapshot.model_payload or {}).get("nodes", {})
            if in_diagram:
                info_col, again_col = st.columns([4, 1], vertical_alignment="center")
                info_col.info(
                    f"**{selected}** será destacada ao abrir a aba Diagrama CLD.", icon=":material/hub:"
                )
                again_col.button(
                    "Destacar de novo", icon=":material/center_focus_strong:", key="lumina.refocus",
                    on_click=self._ui_state.request_focus,
                    help="Útil se você já abriu o diagrama e selecionou outro nó nele.", **STRETCH,
                )
            else:
                st.warning(
                    f"**{selected}** não é um nó do diagrama (é uma variável calculada ou auxiliar), "
                    "então não há o que destacar.",
                    icon=":material/info:",
                )
