from backend.application.ports.simulation_store import SimulationStore
from backend.application.use_cases._base import require_simulation
from backend.domain.services.simulation_engine import SimulationEngine


class RestartSimulationUseCase:
    """Volta ao ponto de partida (valores-base + decisões já tomadas), zerando o histórico."""

    def __init__(self, store: SimulationStore, engine: SimulationEngine) -> None:
        self._store = store
        self._engine = engine

    def execute(self) -> None:
        simulation = require_simulation(self._store)
        simulation.restore_baseline()
        self._engine.recompute_derived(simulation.system)
        simulation.clear_progress()
        self._store.put(simulation)
