from backend.application.ports.simulation_store import SimulationStore
from backend.application.use_cases._base import require_simulation
from backend.domain.constants import NodeNames
from backend.domain.services.simulation_engine import SimulationEngine


class AdvanceCycleUseCase:
    def __init__(self, store: SimulationStore, engine: SimulationEngine) -> None:
        self._store = store
        self._engine = engine

    def execute(self) -> None:
        simulation = require_simulation(self._store)
        system = simulation.system
        self._engine.advance_cycle(system)
        profit = system.value_of(NodeNames.RECEITA_LIQUIDA) - system.value_of(NodeNames.CUSTOS)
        simulation.register_cycle(profit, system.value_of(NodeNames.RENTABILIDADE))
        self._store.put(simulation)
