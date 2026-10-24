"""Executa o app.py real com o runtime de testes do Streamlit."""
import warnings
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[2] / "app.py")


@pytest.fixture
def app():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return AppTest.from_file(APP, default_timeout=30).run()


def _button(app, text):
    return next(b for b in app.button if text in b.label)


def test_renders_without_errors(app):
    assert not app.exception
    assert [t.label for t in app.tabs] == ["⬡ Diagrama CLD", "▶ Simulação", "≋ Variáveis"]
    assert len(app.dataframe) == 1


def test_advance_and_restart_flow(app):
    for _ in range(2):
        _button(app, "Avançar").click()
        app.run()
    assert not app.exception
    assert any("Ciclo atual:** 2" in m.value for m in app.markdown)

    _button(app, "Reiniciar").click()
    app.run()
    assert any("Ciclo atual:** 0" in m.value for m in app.markdown)


def test_changing_a_decision_input_persists_in_session(app):
    next(n for n in app.number_input if n.label == "Marketing").set_value(20000.0).run()
    _button(app, "Avançar").click()
    app.run()
    assert next(n for n in app.number_input if n.label == "Marketing").value == 20000.0
    assert not app.exception
