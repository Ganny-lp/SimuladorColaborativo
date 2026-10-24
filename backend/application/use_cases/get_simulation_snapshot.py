from backend.application.dto import SimulationSnapshot
from backend.application.mappers.snapshot_assembler import SnapshotAssembler
from backend.application.ports.model_repository import ModelRepository
from backend.application.ports.simulation_store import SimulationStore
from backend.application.use_cases._base import require_simulation


class GetSimulationSnapshotUseCase:
    def __init__(
        self, store: SimulationStore, repository: ModelRepository, assembler: SnapshotAssembler
    ) -> None:
        self._store = store
        self._repository = repository
        self._assembler = assembler

    def execute(self) -> SimulationSnapshot:
        simulation = require_simulation(self._store)
        return self._assembler.assemble(simulation, cloud_enabled=self._repository.is_persistent)
