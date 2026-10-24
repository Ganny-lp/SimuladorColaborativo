import pytest
import requests

from backend.application.ports.model_repository import RepositoryError
from backend.infrastructure.config.settings import JsonBinSettings
from backend.infrastructure.persistence import jsonbin_model_repository as module
from backend.infrastructure.persistence.jsonbin_model_repository import JsonBinModelRepository
from backend.infrastructure.persistence.null_model_repository import NullModelRepository


class FakeResponse:
    def __init__(self, status=200, payload=None):
        self.status_code, self._payload = status, payload or {}

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


@pytest.fixture
def repo(mapper):
    return JsonBinModelRepository(JsonBinSettings("KEY", "BIN"), mapper)


def test_settings_from_secrets():
    assert JsonBinSettings.from_secrets({"jsonbin": {"api_key": "k", "bin_id": "b"}}).is_configured
    assert not JsonBinSettings.from_secrets({}).is_configured

    class Missing:  # st.secrets sem secrets.toml levanta FileNotFoundError
        def __getitem__(self, key):
            raise FileNotFoundError

    assert not JsonBinSettings.from_secrets(Missing()).is_configured


def test_load_returns_entity(monkeypatch, repo, mapper, default_system):
    calls = {}

    def fake_get(url, headers, timeout):
        calls.update(url=url, headers=headers)
        return FakeResponse(200, {"record": mapper.to_dict(default_system)})

    monkeypatch.setattr(module.requests, "get", fake_get)
    loaded = repo.load()
    assert loaded is not None and len(loaded.nodes) == 30
    assert calls["url"].endswith("/BIN/latest") and calls["headers"]["X-Master-Key"] == "KEY"


@pytest.mark.parametrize(
    "response",
    [FakeResponse(500), FakeResponse(200, {"record": {"foo": 1}}), requests.ConnectionError("down")],
)
def test_load_never_raises(monkeypatch, repo, response):
    def fake_get(*args, **kwargs):
        if isinstance(response, Exception):
            raise response
        return response

    monkeypatch.setattr(module.requests, "get", fake_get)
    assert repo.load() is None


def test_save_puts_serialized_model(monkeypatch, repo, default_system):
    sent = {}

    def fake_put(url, headers, json, timeout):
        sent.update(url=url, body=json)
        return FakeResponse(200)

    monkeypatch.setattr(module.requests, "put", fake_put)
    repo.save(default_system)
    assert sent["url"].endswith("/BIN") and "nodes" in sent["body"]


def test_save_wraps_http_errors(monkeypatch, repo, default_system):
    monkeypatch.setattr(module.requests, "put", lambda *a, **k: FakeResponse(401))
    with pytest.raises(RepositoryError):
        repo.save(default_system)


def test_null_repository(default_system):
    null = NullModelRepository()
    assert not null.is_persistent and null.load() is None
    null.save(default_system)  # não faz nada, não levanta
