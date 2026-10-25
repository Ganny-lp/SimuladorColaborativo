import streamlit as st

from backend.application.dto import SimulationSnapshot
from backend.application.use_cases.start_simulation import StartSimulationUseCase
from frontend.compat import STRETCH
from frontend.components.cld_diagram import CldDiagram
from frontend.views.tab import Tab

_SYNC_EXPLANATION = (
    "Persistência ativa. As edições feitas no diagrama só chegam à aba Simulação depois de clicar em "
    "**Salvar** (no diagrama) e em **Recarregar modelo da nuvem** (aqui ao lado). São dois estados "
    "diferentes (JS do diagrama e Python da simulação), sincronizados via nuvem."
)


class DiagramTab(Tab):
    title = ":material/hub: Diagrama CLD"

    def __init__(self, diagram: CldDiagram, start_simulation: StartSimulationUseCase) -> None:
        self._diagram = diagram
        self._start_simulation = start_simulation

    def render(self, snapshot: SimulationSnapshot) -> None:
        with st.container(key="lumina-diagram"):  # a chave dá ao CSS um alvo para a altura responsiva
            self._diagram.render(snapshot.model_payload)
        with st.container(key="lumina-diagram-foot"):
            reload_col, info_col = st.columns(2)
            with reload_col:
                if st.button("Recarregar modelo da nuvem", icon=":material/cloud_sync:", **STRETCH):
                    self._start_simulation.execute(force_reload=True)
                    st.rerun()
            with info_col:
                if snapshot.cloud_enabled:
                    st.caption(_SYNC_EXPLANATION)
                else:
                    st.caption("Configure [jsonbin] nas Secrets para ativar a persistência.")
