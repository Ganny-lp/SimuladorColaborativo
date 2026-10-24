import pytest

from backend.domain.entities.node import Node, NodeCategory
from backend.domain.entities.causal_system import CausalSystem
from backend.domain.entities.simulation import Simulation


def test_migration_starts_clean(migrated_system):
    assert migrated_system.value_of("Rentabilidade") == 0.0
    assert str(migrated_system.value_of("Rentabilidade")) == "0.0"  # sem '-0.0'
    assert migrated_system.value_of("B") == 10000.0
    assert migrated_system.value_of("Dpt") == pytest.approx(1000.0)
    assert migrated_system.value_of("St") == pytest.approx(0.0016816540258471277)


def test_first_cycle_golden_values(migrated_system, engine):
    """Valores de referência validados contra o sim.py original (com o bug do MIN corrigido)."""
    engine.advance_cycle(migrated_system)
    assert migrated_system.value_of("Qt") == pytest.approx(1.6816540258471278)
    assert migrated_system.value_of("Receita Líquida") == pytest.approx(214.41088829550878)
    assert migrated_system.value_of("Custos") == pytest.approx(26474.735921904525)
    assert migrated_system.value_of("Rentabilidade") == pytest.approx(-26260.325033609017)


def test_state_accumulates_across_cycles(migrated_system, engine):
    engine.advance_cycle(migrated_system)
    first = migrated_system.value_of("Rentabilidade")
    engine.advance_cycle(migrated_system)
    assert migrated_system.value_of("Rentabilidade") == pytest.approx(2 * first, rel=1e-6)


def test_capacity_caps_served_quantity(migrated_system, engine):
    migrated_system.set_value("Pt", 0)       # preço baixíssimo → demanda enorme
    migrated_system.set_value("Cap", 50)
    engine.advance_cycle(migrated_system)
    assert migrated_system.value_of("Qt") == 50.0


def test_broken_equation_evaluates_to_zero_instead_of_crashing(engine):
    system = CausalSystem(nodes={"X": Node("X", NodeCategory.EQUATION, value=5, expression="1/0")})
    engine.advance_cycle(system)
    assert system.value_of("X") == 0.0


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
    assert migrated_system.value_of("Rentabilidade") == 0.0
    assert migrated_system.value_of("budget_promo") == 20000
