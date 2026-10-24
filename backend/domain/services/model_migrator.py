from __future__ import annotations

from backend.domain.entities.causal_system import CausalSystem
from backend.domain.services.simulation_engine import SimulationEngine

# (equação antiga, equação corrigida). Só substitui se a equação ainda for exatamente
# a antiga: idempotente e não sobrescreve edições feitas pelo usuário.
EXPRESSION_FIXES: dict[str, tuple[str, str]] = {
    "St": (
        "EXP(-Beta_1*(Pt-Pm))/(1+Nc)",
        "1/(1+Nc*EXP(Beta_1*(Pt-Pm)))",
    ),
    "Margem_Lucro": (
        "Rentabilidade/((1)+(Receita Líquida)+SQRT(((1)-(Receita Líquida))^2))/2",
        "Rentabilidade/MAX(1,Receita Líquida)",
    ),
    "ROI": (
        "Rentabilidade/((1)+(Custos Abertura)+SQRT(((1)-(Custos Abertura))^2))/2",
        "Rentabilidade/MAX(1,Custos Abertura)",
    ),
}


class ModelMigrator:
    """
    Aplica correções de equação a modelos antigos e prepara o ponto de partida da
    simulação: o estado NUNCA é herdado da nuvem, sempre começa limpo.
    """

    def __init__(self, engine: SimulationEngine) -> None:
        self._engine = engine

    def migrate(self, system: CausalSystem) -> CausalSystem:
        for name, (old, new) in EXPRESSION_FIXES.items():
            node = system.nodes.get(name)
            if node is not None and (node.expression or "").strip() == old:
                node.expression = new
        self._engine.reset_state(system)
        self._engine.recompute_derived(system)
        return system
