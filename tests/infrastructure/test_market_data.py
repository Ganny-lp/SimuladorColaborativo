import pytest
from backend.infrastructure.market_data import fetch_ipca

class Response:
    def raise_for_status(self): pass
    def json(self):return [{'data':'01/10/2026','valor':'-0,32'}]

def test_ipca_units_date_and_deflation(monkeypatch):
    monkeypatch.setattr('backend.infrastructure.market_data.requests.get',lambda *a,**k:Response())
    obs=fetch_ipca()
    assert obs['value']==pytest.approx(-.0032)
    assert obs['reference']=='2026-10-01'
    assert '433' in obs['source']
