import streamlit as st

from backend.application.dto import SimulationSnapshot
from backend.application.use_cases.start_simulation import StartSimulationUseCase
from frontend.compat import STRETCH
from frontend.components.cld_diagram import CldDiagram
from frontend.session.ui_state import UiState
from frontend.views.tab import Tab

_SYNC_EXPLANATION = (
    "Edições do diagrama só chegam à simulação depois de **Salvar** (no diagrama) e de "
    "**Recarregar modelo** (aqui). São dois estados diferentes, sincronizados pela nuvem."
)


class DiagramTab(Tab):
    title = ":material/hub: Diagrama CLD"

    def __init__(
        self, diagram: CldDiagram, start_simulation: StartSimulationUseCase, ui_state: UiState | None = None
    ) -> None:
        self._diagram = diagram
        self._start_simulation = start_simulation
        self._ui_state = ui_state

    def render(self, snapshot: SimulationSnapshot) -> None:
        ui = self._ui_state
        self._diagram.render(
            snapshot.model_payload,
            focus=ui.focus_request if ui else None,
            epoch=ui.diagram_epoch if ui else 0,
        )
        info_col, reload_col = st.columns([3, 1], vertical_alignment="center")
        with info_col:
            if snapshot.cloud_enabled:
                st.caption(_SYNC_EXPLANATION)
            else:
                st.caption(":material/cloud_off: Persistência desativada. Configure `[jsonbin]` nas Secrets para salvar o diagrama.")
        with reload_col:
            if st.button("Recarregar modelo", icon=":material/cloud_sync:", help="Traz o modelo salvo na nuvem para a simulação", **STRETCH):
                self._start_simulation.execute(force_reload=True)
                if ui:
                    ui.bump_diagram_epoch()
                st.rerun()
