from backend.domain.entities.causal_system import CausalSystem
from backend.domain.entities.node import Node, NodeCategory
from backend.domain.services.model_migrator import _PREVIOUS_TEAM_EXPRESSIONS


def _legacy_system(expression: str) -> CausalSystem:
    return CausalSystem(nodes={"St": Node("St", NodeCategory.EQUATION, expression=expression)})


def test_user_edited_equation_is_preserved(migrator):
    assert migrator.migrate(_legacy_system("0.5")).nodes["St"].expression == "0.5"


def test_migration_is_idempotent(migrator, default_system):
    first = migrator.migrate(default_system).values()
    assert migrator.migrate(default_system).values() == first


def test_current_schema_updates_shipped_team_formula_but_keeps_custom_edits(migrator, default_system):
    system = default_system.clone()
    experience = "Experiencia_Acumulada"
    qualification = "Nivel_Qualificacao_Tecnica"
    system.node(experience).expression = _PREVIOUS_TEAM_EXPRESSIONS[experience]
    system.node(qualification).expression = "0.02"
    system.set_value("Pt", 3000)
    updated = migrator.migrate(system)
    assert updated.node(experience).expression == default_system.node(experience).expression
    assert updated.node(qualification).expression == "0.02"
    assert updated.value_of("Pt") == 3000
