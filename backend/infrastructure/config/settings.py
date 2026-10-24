from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class JsonBinSettings:
    api_key: str | None = None
    bin_id: str | None = None

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.bin_id)

    @classmethod
    def from_secrets(cls, secrets: Mapping[str, Any]) -> "JsonBinSettings":
        """Lê ``[jsonbin] api_key / bin_id``. Ausência de secrets ⇒ configuração vazia."""
        try:
            section = secrets["jsonbin"]
            return cls(api_key=section["api_key"], bin_id=section["bin_id"])
        except (KeyError, TypeError, FileNotFoundError):
            return cls()
