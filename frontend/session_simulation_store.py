from __future__ import annotations

from typing import MutableMapping, TYPE_CHECKING

from backend.application.ports.simulation_store import SimulationStore

if TYPE_CHECKING:  # o adaptador só guarda o objeto; não conhece o seu conteúdo
    from backend.domain.entities.simulation import Simulation


class SessionStateSimulationStore(SimulationStore):
    """Adaptador da porta SimulationStore sobre ``st.session_state``."""

    _SIMULATION_KEY = "lumina.simulation"
    _VERSION_KEY = "lumina.app_version"

    def __init__(self, session_state: MutableMapping, app_version: str) -> None:
        self._state = session_state
        self._app_version = app_version

    def get(self) -> "Simulation | None":
        if self._state.get(self._VERSION_KEY) != self._app_version:
            return None  # sessão criada por uma versão antiga da app: descarta
        return self._state.get(self._SIMULATION_KEY)

    def put(self, simulation: "Simulation") -> None:
        self._state[self._SIMULATION_KEY] = simulation
        self._state[self._VERSION_KEY] = self._app_version
