import pytest

from backend.domain.entities.node import Node, NodeCategory
from backend.domain.entities.causal_system import CausalSystem
from backend.domain.entities.simulation import Simulation


def test_migration_starts_clean(migrated_system):
    assert migrated_system.value_of("Rentabilidade") == -52500
    assert migrated_system.value_of("B") == 10000
    assert 0 < migrated_system.value_of("St") < 1


def test_first_cycle_cash_and_stock_conservation(migrated_system, engine):
    before = migrated_system.values()
    engine.advance_cycle(migrated_system)
    now = migrated_system.values()
    assert now["Backlog_Servicos"] == pytest.approx(before["Backlog_Servicos"] + now["Demanda_Captada"] - now["Qt"])
    assert now["Estoque_Pecas"] == pytest.approx(before["Estoque_Pecas"] + now["Reposicao_Pecas"] - now["Qt"])
    assert now["Rentabilidade"] == pytest.approx(before["Rentabilidade"] + now["Fluxo_Caixa"])
    assert now["Caixa_Disponivel"] == pytest.approx(before["Caixa_Disponivel"] + now["Fluxo_Caixa"])


def test_state_accumulates_across_cycles(migrated_system, engine):
    total = migrated_system.value_of("Rentabilidade")
    for _ in range(24):
        engine.advance_cycle(migrated_system)
        total += migrated_system.value_of("Fluxo_Caixa")
        assert migrated_system.value_of("Rentabilidade") == pytest.approx(total)
        assert migrated_system.value_of("Estoque_Pecas") >= -1e-9
        assert migrated_system.value_of("Backlog_Servicos") >= -1e-9


def test_capacity_caps_served_quantity(migrated_system, engine):
    migrated_system.set_value("Pt", 0)       # preço baixíssimo → demanda enorme
    migrated_system.set_value("Cap", 50)
    engine.advance_cycle(migrated_system)
    assert migrated_system.value_of("Qt") == 50.0


def test_broken_equation_is_reported_without_mutating_cycle(engine):
    system = CausalSystem(nodes={"X": Node("X", NodeCategory.EQUATION, value=5, expression="1/0")})
    from backend.domain.exceptions import ExpressionEvaluationError
    with pytest.raises(ExpressionEvaluationError):
        engine.advance_cycle(system)
    assert system.value_of("X") == 5.0


def test_recompute_derived_does_not_touch_state(migrated_system, engine):
    engine.advance_cycle(migrated_system)
    rent = migrated_system.value_of("Rentabilidade")
    migrated_system.set_value("Pt", 100)
    engine.recompute_derived(migrated_system)
    assert migrated_system.value_of("Rentabilidade") == rent
    assert migrated_system.value_of("St") > 0.0016816540258471277  # preço menor → mais share


def test_simulation_restart_restores_baseline_and_keeps_decisions(migrated_system, engine):
    simulation = Simulation.begin(migrated_system)
    simulation.set_input("budget_promo", 20000)
    engine.advance_cycle(migrated_system)
    simulation.register_cycle(profit=-1.0, accumulated_profitability=-2.0)

    simulation.restore_baseline()
    engine.recompute_derived(migrated_system)
    simulation.clear_progress()

    assert simulation.cycle == 0 and simulation.history == []
    assert migrated_system.value_of("Rentabilidade") == -52500
    assert migrated_system.value_of("budget_promo") == 20000
