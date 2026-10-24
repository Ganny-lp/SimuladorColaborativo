from backend.application.dto import InputChangeResult, PersistenceOutcome
from backend.application.ports.simulation_store import SimulationStore
from backend.application.services.model_publisher import ModelPublisher
from backend.application.use_cases._base import require_simulation


class ChangeInputUseCase:
    """Altera uma decisão de entrada (preço, orçamentos...) e publica o modelo."""

    def __init__(self, store: SimulationStore, publisher: ModelPublisher) -> None:
        self._store = store
        self._publisher = publisher

    def execute(self, name: str, value: float) -> InputChangeResult:
        simulation = require_simulation(self._store)
        if simulation.system.node(name).value == float(value):
            return InputChangeResult(changed=False, persistence=PersistenceOutcome.SKIPPED)
        simulation.set_input(name, value)
        self._store.put(simulation)
        return InputChangeResult(True, self._publisher.publish(simulation.system))
