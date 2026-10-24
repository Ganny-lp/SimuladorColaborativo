from abc import ABC, abstractmethod

from backend.domain.entities.causal_system import CausalSystem


class DefaultModelProvider(ABC):
    """Porta para o modelo de fábrica, usado quando não há modelo salvo."""

    @abstractmethod
    def provide(self) -> CausalSystem:
        """Retorna sempre uma nova instância independente."""
