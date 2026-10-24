from __future__ import annotations

from backend.application.ports.default_model_provider import DefaultModelProvider
from backend.application.ports.model_repository import ModelRepository, RepositoryError
from backend.application.ports.simulation_store import SimulationStore
from backend.domain.entities.causal_system import CausalSystem
from backend.domain.entities.simulation import Simulation


class InMemorySimulationStore(SimulationStore):
    def __init__(self) -> None:
        self.simulation: Simulation | None = None

    def get(self):
        return self.simulation

    def put(self, simulation) -> None:
        self.simulation = simulation


class FakeRepository(ModelRepository):
    def __init__(self, remote: CausalSystem | None = None, persistent=True, fail_on_save=False):
        self.remote, self.persistent, self.fail_on_save = remote, persistent, fail_on_save
        self.saved: list[CausalSystem] = []

    @property
    def is_persistent(self) -> bool:
        return self.persistent

    def load(self):
        return self.remote

    def save(self, system) -> None:
        if self.fail_on_save:
            raise RepositoryError("boom")
        self.saved.append(system)


class FakeDefaults(DefaultModelProvider):
    def __init__(self, factory) -> None:
        self._factory = factory

    def provide(self) -> CausalSystem:
        return self._factory()
