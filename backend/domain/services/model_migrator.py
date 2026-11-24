from __future__ import annotations

from backend.domain.entities.causal_system import CausalSystem
from backend.domain.services.simulation_engine import SimulationEngine

# Compatibility fixes for independently authored models.
EXPRESSION_FIXES = {
    "Margem_Lucro": ("Rentabilidade/MAX(1,Receita Líquida)", "Resultado_Mensal/MAX(1,Receita Líquida)"),
}

_PREVIOUS_TEAM_EXPRESSIONS = {
    "Nivel_Qualificacao_Tecnica": "MAX(0.3,MIN(1,Nivel_Qualificacao_Tecnica+(budget_training+Reinvestimento_Disponivel/3)/500000-0.01))-Nivel_Qualificacao_Tecnica",
    "Experiencia_Acumulada": "MAX(0.1,MIN(10,Experiencia_Acumulada+0.05-Rotatividade_Tecnicos*Experiencia_Acumulada))-Experiencia_Acumulada",
}


class ModelMigrator:
    def __init__(self, engine: SimulationEngine, template: CausalSystem | None = None) -> None:
        self._engine = engine
        self._template = template

    def migrate(self, system: CausalSystem) -> CausalSystem:
        # Upgrade the shipped legacy simulator and supplied extended payload together.
        # Keep user decisions and positions; replace the obsolete built-in equations.
        if self._template is not None and all(system.has_node(n) for n in ("Pt", "Qt", "St", "Cp", "budget_training")) and system.extras.get("schema_version") != 2:
            canonical = self._template.clone()
            for name, node in canonical.nodes.items():
                old = system.nodes.get(name)
                if old is not None:
                    node.x, node.y = old.x, old.y
                    if not node.has_expression and not node.is_state:
                        node.value = old.value
            if system.has_node("Salarios_Beneficios"):
                canonical.node("Salarios_Beneficios").value = system.value_of("Salarios_Beneficios") / max(1, system.value_of("Numero_Tecnicos", 1))
            # Preserve custom nodes unless they use the removed price parameter.
            from backend.domain.exceptions import InvalidModelError
            from backend.domain.services.reference_finder import ReferenceFinder
            for name, node in system.nodes.items():
                if name not in canonical.nodes and name != "Pm":
                    if "Pm" in ReferenceFinder().find(node.expression, ["Pm"]):
                        raise InvalidModelError(f"Reformule a equação de {name}: parâmetro de preço removido.")
                    canonical.nodes[name] = node
            for link in system.links:
                if link.source in canonical.nodes and link.target in canonical.nodes and (link.source not in self._template.nodes or link.target not in self._template.nodes):
                    canonical.links.append(link)
            canonical.initial_state.update({k:v for k,v in system.initial_state.items() if k not in self._template.nodes and k in canonical.nodes})
            canonical.extras.update({k:v for k,v in system.extras.items() if k != "schema_version"})
            system = canonical
        from backend.domain.exceptions import InvalidModelError
        from backend.domain.services.reference_finder import ReferenceFinder
        if system.has_node("Pm") or any(ReferenceFinder().find(node.expression,["Pm"]) for node in system.nodes.values()):
            raise InvalidModelError("O modelo contém parâmetro de preço removido; reformule-o antes de simular.")
        if self._template and self._template.has_node("Simular_Abertura") and not system.has_node("Simular_Abertura"):
            system.nodes["Simular_Abertura"] = self._template.clone().node("Simular_Abertura")
            if system.has_node("Emprestimos_Mensal"):
                system.node("Emprestimos_Mensal").expression = "Simular_Abertura*(" + system.node("Emprestimos_Mensal").expression + ")"
        if self._template is not None and system.extras.get("schema_version") == 2:
            for name, previous in _PREVIOUS_TEAM_EXPRESSIONS.items():
                node = system.nodes.get(name)
                updated = self._template.nodes.get(name)
                if node and updated and node.is_state and node.expression == previous:
                    node.expression = updated.expression
                    node.description = updated.description
        self._engine.reset_state(system)
        self._engine.recompute_derived(system)
        return system
