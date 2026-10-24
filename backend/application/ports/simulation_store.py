from abc import ABC, abstractmethod

from backend.domain.entities.simulation import Simulation


class SimulationStore(ABC):
    """Porta de guarda da simulação em andamento (ex.: sessão do usuário)."""

    @abstractmethod
    def get(self) -> Simulation | None: ...

    @abstractmethod
    def put(self, simulation: Simulation) -> None: ...
