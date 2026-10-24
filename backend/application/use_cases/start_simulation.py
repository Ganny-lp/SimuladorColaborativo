from __future__ import annotations

import logging

from backend.application.ports.default_model_provider import DefaultModelProvider
from backend.application.ports.model_repository import ModelRepository
from backend.application.ports.simulation_store import SimulationStore
from backend.domain.entities.simulation import Simulation
from backend.domain.services.model_migrator import ModelMigrator

logger = logging.getLogger(__name__)


class StartSimulationUseCase:
    """
    Carrega o modelo (nuvem → fallback para o padrão), migra e cria uma simulação limpa.
    Com ``force_reload=False`` é idempotente: não faz nada se já houver simulação.
    """

    def __init__(
        self,
        store: SimulationStore,
        repository: ModelRepository,
        defaults: DefaultModelProvider,
        migrator: ModelMigrator,
    ) -> None:
        self._store = store
        self._repository = repository
        self._defaults = defaults
        self._migrator = migrator

    def execute(self, force_reload: bool = False) -> None:
        if not force_reload and self._store.get() is not None:
            return
        system = self._repository.load()
        if system is None:
            logger.info("Modelo remoto indisponível; usando o modelo padrão.")
            system = self._defaults.provide()
        self._store.put(Simulation.begin(self._migrator.migrate(system)))
