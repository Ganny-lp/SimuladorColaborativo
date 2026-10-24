import json

import pytest

from backend.domain.exceptions import InvalidModelError
from backend.infrastructure.persistence import json_default_model_provider as provider


def _raw():
    return json.loads(provider._DEFAULT_MODEL_FILE.read_text(encoding="utf-8"))


def test_round_trip_is_lossless(mapper):
    raw = _raw()
    assert mapper.to_dict(mapper.to_entity(raw)) == raw


def test_unknown_top_level_keys_are_preserved(mapper):
    raw = {**_raw(), "custom_section": {"a": 1}}
    assert mapper.to_dict(mapper.to_entity(raw))["custom_section"] == {"a": 1}


@pytest.mark.parametrize("broken", [{}, {"nodes": {}}, {"links": []}, [], None])
def test_rejects_missing_sections(mapper, broken):
    with pytest.raises(InvalidModelError):
        mapper.to_entity(broken)


def test_rejects_invalid_category_or_sign(mapper):
    bad_cat = {"nodes": {"A": {"cat": "Banana"}}, "links": []}
    bad_sign = {"nodes": {}, "links": [{"from": "A", "to": "B", "sign": "*"}]}
    for payload in (bad_cat, bad_sign):
        with pytest.raises(InvalidModelError):
            mapper.to_entity(payload)


def test_incomplete_price_scale_is_ignored(mapper):
    raw = _raw()
    raw["price_scale"] = {"min": 0, "max": 10, "stops": [{"value": 1, "color": "#fff"}]}
    assert mapper.to_entity(raw).price_scale is None
