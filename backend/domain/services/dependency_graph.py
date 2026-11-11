from __future__ import annotations

from backend.domain.entities.causal_system import CausalSystem
from backend.domain.services.reference_finder import ReferenceFinder
from backend.domain.exceptions import InvalidModelError


class DependencyGraph:
    """Grafo de dependências entre equações: define a ordem de cálculo e os nós com memória."""

    def __init__(self, system: CausalSystem, finder: ReferenceFinder | None = None) -> None:
        finder = finder or ReferenceFinder()
        names = list(system.nodes)
        references = {
            name: finder.find(system.nodes[name].expression, names) for name in names
        }
        self._system = system
        self._self_referencing = {name for name, refs in references.items() if name in refs}
        self._dependencies = {name: refs - {name} for name, refs in references.items()}

    def topological_order(self) -> list[str]:
        """
        Toda variável da qual um nó depende (e que possui equação) vem ANTES dele.
        Estados quebram a dependência temporal. Ciclos algébricos são rejeitados.
        """
        if any(not self._system.node(n).is_state for n in self._self_referencing):
            raise InvalidModelError("Equação autorreferente: use um nó Estado com taxa de variação.")
        order: list[str] = []
        visiting: set[str] = set()
        done: set[str] = set()

        def visit(name: str) -> None:
            if name in visiting:
                raise InvalidModelError(f"Ciclo algébrico em {name}: introduza um nó Estado para representar o atraso.")
            if name in done:
                return
            visiting.add(name)
            for dependency in sorted(self._dependencies[name]):
                if self._system.nodes[dependency].has_expression and not self._system.nodes[dependency].is_state:
                    visit(dependency)
            visiting.discard(name)
            done.add(name)
            order.append(name)

        for name in self._system.nodes:
            if not self._system.nodes[name].is_state:
                visit(name)
        order.extend(name for name, node in self._system.nodes.items() if node.is_state)
        return order

    def state_nodes(self) -> set[str]:
        """Nós com memória: categoria 'Estado' ou equação que referencia a si mesma."""
        return {
            name
            for name, node in self._system.nodes.items()
            if node.is_state or name in self._self_referencing
        }
