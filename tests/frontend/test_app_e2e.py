"""Executa o app.py real com o runtime de testes do Streamlit."""
import warnings
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest
from frontend.components.lab_experience import HYPOTHESIS_PRESETS

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
    assert [t.label for t in app.tabs] == [":material/hub: Diagrama CLD", ":material/monitoring: Simulação", ":material/table_rows: Variáveis"]
    assert len(app.dataframe) == 2


def test_advance_and_restart_flow(app):
    for _ in range(2):
        _button(app, "Avançar").click()
        app.run()
    assert not app.exception
    assert any("Ciclo 2" in m.value for m in app.markdown)

    _button(app, "Reiniciar").click()
    app.run()
    assert any("Ciclo 0" in m.value for m in app.markdown)


def test_changing_a_decision_input_persists_in_session(app):
    next(n for n in app.number_input if n.label == "Marketing").set_value(20000.0).run()
    _button(app, "Avançar").click()
    app.run()
    assert next(n for n in app.number_input if n.label == "Marketing").value == 20000.0
    assert not app.exception


def test_fraction_scale_and_exact_entry_are_synchronized(app):
    number = next(n for n in app.number_input if n.label == "Taxa Reinvestimento")
    number.set_value(20.0).run()
    assert not app.exception
    slider = next(s for s in app.slider if s.label == "Escala · Taxa Reinvestimento")
    assert slider.value == 20
    slider.set_value(10.0).run()
    assert next(n for n in app.number_input if n.label == "Taxa Reinvestimento").value == 10


def test_opening_fields_are_opt_in_and_disappear_after_first_cycle(app):
    assert not any(n.label == "Emprestimo" for n in app.number_input)
    app.toggle[0].set_value(True).run()
    assert any(n.label == "Emprestimo" for n in app.number_input)
    _button(app,"Avançar").click().run()
    assert not app.exception
    assert not any(n.label == "Emprestimo" for n in app.number_input)


def test_price_change_updates_model_and_restart_keeps_decision(app):
    next(n for n in app.number_input if n.label == 'Preço praticado').set_value(200).run()
    assert not app.exception
    assert app.session_state['lumina.simulation'].system.value_of('Pt') == 200
    _button(app,'Avançar').click().run()
    _button(app,'Reiniciar').click().run()
    assert next(n for n in app.number_input if n.label == 'Preço praticado').value == 200


def test_price_scale_keeps_exact_value_when_next_cycle_changes_bounds(app):
    key = "pt_hidden_sync_scale"
    app.number_input(key="pt_hidden_sync_number").set_value(500.25).run()
    _button(app, "Avançar").click().run()
    original_maximum = app.slider(key=key).proto.max
    _button(app, "Avançar").click().run()
    assert not app.exception
    assert app.slider(key=key).proto.max != original_maximum
    assert app.slider(key=key).value == 500.25
    app.slider(key=key).set_value(600.0).run()
    assert app.number_input(key="pt_hidden_sync_number").value == 600.0


def test_ipca_reference_and_cycle_inflation_are_independent(app, monkeypatch):
    observation = {
        "value": 0.0082, "reference": "2025-09-01", "retrieved_at": "2025-10-10",
        "source": "https://api.bcb.gov.br/serie/433",
    }
    monkeypatch.setattr("backend.infrastructure.market_data.fetch_ipca", lambda: observation)
    app.number_input(key="decision_Inflacao_number").set_value(-0.2).run()
    app.multiselect(key="lab.presets").select(HYPOTHESIS_PRESETS[3]).run()
    _button(app, "Avançar").click().run()
    first = app.session_state["lumina.simulation"].history[0]
    assert first.inflation == pytest.approx(-0.002)
    assert first.profit == pytest.approx(first.net_revenue - first.costs)
    assert app.session_state["lab.completed_notes"]["1"]["hypothesis"] == HYPOTHESIS_PRESETS[3]

    _button(app, "Consultar IPCA oficial").click().run()
    assert app.number_input(key="decision_Inflacao_number").value == -0.2
    assert any(m.label == "IPCA oficial · 09/2025" for m in app.metric)
    _button(app, "Usar IPCA").click().run()
    assert app.number_input(key="decision_Inflacao_number").value == pytest.approx(0.82)
    _button(app, "Avançar").click().run()
    simulation = app.session_state["lumina.simulation"]
    assert not app.exception
    assert simulation.system.value_of("Mes_Operacao") == 2
    assert [r.inflation for r in simulation.history] == pytest.approx([-0.002, 0.0082])
    table = next(df.value for df in app.dataframe if "Reparos (Qt)" in df.value)
    assert table.iloc[1]["Receita bruta"] == pytest.approx(first.price * first.served_quantity)
    assert table.iloc[1]["Fluxo de caixa"] == pytest.approx(first.cash_flow)


def test_locate_variable_connects_focus_to_diagram(app):
    app.selectbox(key='lumina.variable_picker').select('Pt').run()
    assert not app.exception
    assert app.session_state['lumina.focus_request']['name'] == 'Pt'
    # The same UI state is injected in both tabs, so a focus nonce reaches the iframe.
    assert any('"name": "Pt"' in frame.proto.srcdoc for frame in app.get('iframe'))


def test_tax_calculator_applies_value_and_normative_provenance(app):
    app.selectbox(key='source-kind').select('Carga_Tributaria').run()
    next(c for c in app.checkbox if c.label.startswith('Confirmo enquadramento')).set_value(True).run()
    next(b for b in app.button if b.label=='Aplicar valor calculado com fonte').click().run()
    assert not app.exception
    system=app.session_state['lumina.simulation'].system
    assert system.value_of('Carga_Tributaria')==.06
    assert system.extras['calibration']['Carga_Tributaria']['method']=='Cálculo normativo condicionado'


def test_experiment_notebook_records_completed_cycle_and_clears_on_restart(app):
    app.text_area(key='lab.hypothesis').set_value('Observar a fila após mudar o preço').run()
    _button(app,'Avançar').click().run()
    assert not app.exception
    assert app.session_state['lab.completed_notes']['1']['hypothesis']=='Observar a fila após mudar o preço'
    app.text_area(key='lab.hypothesis').set_value('Segunda hipótese').run()
    assert app.session_state['lab.completed_notes']['1']['hypothesis']=='Observar a fila após mudar o preço'
    _button(app,'Reiniciar').click().run()
    assert not app.exception
    assert 'lab.completed_notes' not in app.session_state
