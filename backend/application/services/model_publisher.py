from __future__ import annotations

import logging

from backend.application.dto import PersistenceOutcome
from backend.application.ports.model_repository import ModelRepository, RepositoryError
from backend.domain.entities.causal_system import CausalSystem
from backend.domain.services.initial_state_calculator import InitialStateCalculator

logger = logging.getLogger(__name__)


class ModelPublisher:
    """
    Publica só o MODELO na nuvem. Os nós de estado são gravados com o valor INICIAL
    para que o armazenamento nunca acumule ciclos de simulação. A sessão local não é tocada.
    """

    def __init__(self, repository: ModelRepository, initial_state: InitialStateCalculator) -> None:
        self._repository = repository
        self._initial_state = initial_state

    def publish(self, system: CausalSystem) -> PersistenceOutcome:
        if not self._repository.is_persistent:
            return PersistenceOutcome.SKIPPED
        payload = system.clone()
        payload.apply_values(self._initial_state.calculate(payload).items())
        try:
            self._repository.save(payload)
        except RepositoryError as exc:
            logger.warning("Falha ao publicar o modelo: %s", exc)
            return PersistenceOutcome.FAILED
        return PersistenceOutcome.SAVED
