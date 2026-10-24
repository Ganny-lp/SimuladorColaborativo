from __future__ import annotations

from abc import ABC, abstractmethod

from backend.domain.entities.causal_system import CausalSystem


class RepositoryError(Exception):
    """Falha ao gravar o modelo no armazenamento externo."""


class ModelRepository(ABC):
    """Porta de persistência do MODELO (equações, inputs e layout)."""

    @property
    @abstractmethod
    def is_persistent(self) -> bool:
        """False para a implementação nula (sem credenciais configuradas)."""

    @abstractmethod
    def load(self) -> CausalSystem | None:
        """Retorna o modelo salvo ou None se indisponível/inválido (nunca lança)."""

    @abstractmethod
    def save(self, system: CausalSystem) -> None:
        """Grava o modelo. Lança RepositoryError em caso de falha."""
