from __future__ import annotations

import logging
from typing import Any

import requests

from backend.application.mappers.model_mapper import ModelMapper
from backend.application.ports.model_repository import ModelRepository, RepositoryError
from backend.domain.entities.causal_system import CausalSystem
from backend.domain.exceptions import InvalidModelError
from backend.infrastructure.config.settings import JsonBinSettings

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.jsonbin.io/v3/b"
_TIMEOUT_SECONDS = 8


class JsonBinModelRepository(ModelRepository):
    """Persiste o modelo em um bin do JSONBin.io."""

    def __init__(self, settings: JsonBinSettings, mapper: ModelMapper) -> None:
        self._settings = settings
        self._mapper = mapper

    @property
    def is_persistent(self) -> bool:
        return self._settings.is_configured

    def load(self) -> CausalSystem | None:
        if not self.is_persistent:
            return None
        try:
            response = requests.get(
                f"{_BASE_URL}/{self._settings.bin_id}/latest",
                headers={"X-Master-Key": self._settings.api_key},
                timeout=_TIMEOUT_SECONDS,
            )
            if response.status_code != 200:
                logger.warning("JSONBin respondeu HTTP %s ao carregar.", response.status_code)
                return None
            record: Any = response.json().get("record", {})
            return self._mapper.to_entity(record)
        except (requests.RequestException, ValueError, InvalidModelError) as exc:
            logger.warning("Não foi possível carregar o modelo do JSONBin: %s", exc)
            return None

    def save(self, system: CausalSystem) -> None:
        if not self.is_persistent:
            return
        try:
            response = requests.put(
                f"{_BASE_URL}/{self._settings.bin_id}",
                headers={
                    "Content-Type": "application/json",
                    "X-Master-Key": self._settings.api_key,
                },
                json=self._mapper.to_dict(system),
                timeout=_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise RepositoryError(str(exc)) from exc
