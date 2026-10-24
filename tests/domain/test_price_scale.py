import pytest

from backend.domain.entities.price_scale import PriceScale, PriceStop
from backend.domain.exceptions import InvalidModelError


def test_requires_two_stops():
    with pytest.raises(InvalidModelError):
        PriceScale(0, 100, (PriceStop(0, "#000", "a"),))


def test_derives_scale_from_market_price():
    scale = PriceScale.derive(market_price=140, variable_cost=30)
    assert scale.minimum == 0 and scale.maximum == 310
    assert [s.value for s in scale.sorted_stops][0] == 0


def test_system_without_scale_falls_back_to_derived(default_system):
    default_system.price_scale = None
    assert default_system.effective_price_scale().maximum > 0
