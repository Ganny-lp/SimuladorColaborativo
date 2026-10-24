from abc import ABC, abstractmethod

from backend.application.dto import SimulationSnapshot


class Tab(ABC):
    """Uma aba da página principal."""

    @property
    @abstractmethod
    def title(self) -> str: ...

    @abstractmethod
    def render(self, snapshot: SimulationSnapshot) -> None: ...
