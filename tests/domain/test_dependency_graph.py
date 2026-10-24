from backend.domain.entities.causal_system import CausalSystem
from backend.domain.entities.node import Node, NodeCategory
from backend.domain.services.dependency_graph import DependencyGraph


def _system(**exprs) -> CausalSystem:
    return CausalSystem(
        nodes={n: Node(n, NodeCategory.EQUATION, expression=e) for n, e in exprs.items()}
    )


def test_dependencies_are_computed_before_dependents():
    system = _system(C="B + 1", A="", B="A * 2")  # declarados fora de ordem
    order = DependencyGraph(system).topological_order()
    assert order.index("B") < order.index("C")


def test_default_model_order_respects_every_equation(default_system):
    order = DependencyGraph(default_system).topological_order()
    position = {name: i for i, name in enumerate(order)}
    assert sorted(order) == sorted(default_system.nodes)
    assert position["Qt"] < position["Receita Líquida"] < position["Rentabilidade"]
    assert position["St"] < position["Qt"] < position["CVt"] < position["Custo_Variavel_t"]


def test_feedback_cycle_does_not_hang():
    system = _system(A="B + 1", B="A + 1")
    assert sorted(DependencyGraph(system).topological_order()) == ["A", "B"]


def test_state_nodes_are_category_state_or_self_referencing():
    system = _system(Acc="Acc + 1", Plain="1")
    system.nodes["Rent"] = Node("Rent", NodeCategory.STATE, expression="Plain")
    assert DependencyGraph(system).state_nodes() == {"Acc", "Rent"}
