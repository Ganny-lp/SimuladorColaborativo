from __future__ import annotations

import json
from pathlib import Path

from backend.application.mappers.model_mapper import ModelMapper
from backend.application.ports.default_model_provider import DefaultModelProvider
from backend.domain.entities.causal_system import CausalSystem

_DEFAULT_MODEL_FILE = Path(__file__).with_name("default_model.json")


class JsonDefaultModelProvider(DefaultModelProvider):
    """Modelo de fábrica versionado em ``default_model.json``."""

    def __init__(self, mapper: ModelMapper, path: Path = _DEFAULT_MODEL_FILE) -> None:
        self._mapper = mapper
        self._path = path

    def provide(self) -> CausalSystem:
        data = json.loads(self._path.read_text(encoding="utf-8"))
        return self._mapper.to_entity(data)
