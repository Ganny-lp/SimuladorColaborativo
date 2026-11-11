import copy
from backend.domain.services.input_validation import validate_input
from backend.domain.services.simulation_engine import SimulationEngine

from backend.application.dto import InputChangeResult, PersistenceOutcome
from backend.application.ports.simulation_store import SimulationStore
from backend.application.services.model_publisher import ModelPublisher
from backend.application.use_cases._base import require_simulation


class ChangeInputUseCase:
    """Altera uma decisão de entrada (preço, orçamentos...) e publica o modelo."""

    def __init__(self, store: SimulationStore, publisher: ModelPublisher, engine: SimulationEngine | None = None) -> None:
        self._store = store
        self._publisher = publisher
        self._engine = engine

    def execute(self, name: str, value: float) -> InputChangeResult:
        simulation = require_simulation(self._store)
        value = validate_input(simulation.system.node(name), value)
        if simulation.system.node(name).value == value:
            return InputChangeResult(changed=False, persistence=PersistenceOutcome.SKIPPED)
        from backend.domain.services.opening import OPENING_INPUTS
        from backend.domain.exceptions import InvalidModelError
        if simulation.cycle > 0 and name in OPENING_INPUTS:
            raise InvalidModelError("Reinicie antes de alterar a configuração inicial.")
        simulation = copy.deepcopy(simulation)
        simulation.set_input(name, value)
        if self._engine is not None:
            if simulation.cycle == 0:
                self._engine.reset_state(simulation.system)
            self._engine.recompute_derived(simulation.system)
            if simulation.cycle == 0:
                simulation.baseline = simulation.system.values()
        self._store.put(simulation)
        return InputChangeResult(True, self._publisher.publish(simulation.system))
