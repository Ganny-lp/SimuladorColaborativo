from backend.domain.entities.causal_system import CausalSystem
from backend.domain.entities.node import Node, NodeCategory
from backend.domain.services.model_migrator import EXPRESSION_FIXES


def _legacy_system(expression: str) -> CausalSystem:
    return CausalSystem(nodes={"St": Node("St", NodeCategory.EQUATION, expression=expression)})


def test_old_equation_is_fixed(migrator):
    old, new = EXPRESSION_FIXES["St"]
    assert migrator.migrate(_legacy_system(old)).nodes["St"].expression == new


def test_user_edited_equation_is_preserved(migrator):
    assert migrator.migrate(_legacy_system("0.5")).nodes["St"].expression == "0.5"


def test_migration_is_idempotent(migrator, default_system):
    first = migrator.migrate(default_system).values()
    assert migrator.migrate(default_system).values() == first
