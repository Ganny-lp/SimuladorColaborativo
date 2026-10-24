import json
import re

from backend.application.dto import PriceScaleDTO, PriceStopDTO, VariableDTO
from frontend.assets.asset_template import AssetTemplate
from frontend.components.cld_diagram import CldDiagram
from frontend.components.price_slider import PriceGradient, PriceSlider
from frontend.components.variables_table import VariablesTable
from frontend.config import CloudCredentials


def test_asset_template_is_single_pass(tmp_path, monkeypatch):
    from frontend.assets import asset_template as module

    (tmp_path / "t.txt").write_text("a=__A__ b=__B__ keep=__OTHER__")
    monkeypatch.setattr(module, "_ASSETS_DIR", tmp_path)
    module._read.cache_clear()
    # o valor injetado contém um marcador: NÃO pode ser re-interpretado
    assert AssetTemplate("t.txt").render(a="__B__", b="2") == "a=__B__ b=2 keep=__OTHER__"
    module._read.cache_clear()


def test_diagram_html_has_no_unresolved_tokens_and_valid_payload():
    payload = {"nodes": {"X": {"desc": "</script><b>"}}, "links": []}
    html = CldDiagram(CloudCredentials("KEY", "BIN")).build_html(payload)
    assert not re.search(r"__[A-Z_]+__", html)
    assert "</script><b>" not in html  # texto do usuário não fecha a tag <script>
    literal = re.search(r"let SYS = (.*);\n", html).group(1)
    assert json.loads(literal.replace("<\\/", "</")) == payload
    assert 'const JSONBIN_API_KEY = "KEY";' in html


def test_diagram_without_credentials_uses_null():
    html = CldDiagram(CloudCredentials()).build_html({"nodes": {}, "links": []})
    assert "const JSONBIN_API_KEY = null;" in html and "const JSONBIN_BIN_ID  = null;" in html


def test_price_gradient():
    scale = PriceScaleDTO(0, 200, (PriceStopDTO(200, "#b", "b"), PriceStopDTO(0, "#a", "a"), PriceStopDTO(100, "#m", "m")))
    assert PriceGradient.css(scale) == "linear-gradient(to right, #a 0.00%, #m 50.00%, #b 100.00%)"


def test_price_ruler_html_is_fully_rendered():
    scale = PriceScaleDTO(0, 300, (PriceStopDTO(0, "#e06060", "x"), PriceStopDTO(300, "#52c97a", "y")))
    html = PriceSlider("pt_hidden_sync", "pt_ruler")._ruler_html(scale, 150)
    assert not re.search(r"__[A-Z_]+__", html)
    assert 'aria-label="pt_hidden_sync"' in html and 'value="150.0"' in html


def test_variables_table_filters_and_truncates():
    variables = [
        VariableDTO("Pt", "Input", 150.123456789, "", "Preço"),
        VariableDTO("Qt", "Equação", 1.0, "MIN(a,b)", "x" * 200),
    ]
    table = VariablesTable()
    frame = table.build_dataframe(variables, search="equa")
    assert list(frame["Variável"]) == ["Qt"]
    assert len(frame.iloc[0]["Descrição"]) == 90
    assert table.build_dataframe(variables).iloc[0]["Equação"] == "—"
    assert table.build_dataframe(variables).iloc[0]["Valor Atual"] == 150.123457
