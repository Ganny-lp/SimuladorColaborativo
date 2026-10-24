from __future__ import annotations

from backend.application.dto import (
    CycleRecordDTO,
    KpiDTO,
    PriceScaleDTO,
    PriceStopDTO,
    SimulationSnapshot,
    VariableDTO,
)
from backend.application.mappers.model_mapper import ModelMapper
from backend.domain.constants import NodeNames
from backend.domain.entities.simulation import Simulation


class SnapshotAssembler:
    """Monta o DTO de leitura a partir da entidade Simulation."""

    def __init__(self, model_mapper: ModelMapper) -> None:
        self._model_mapper = model_mapper

    def assemble(self, simulation: Simulation, cloud_enabled: bool) -> SimulationSnapshot:
        system = simulation.system
        scale = system.effective_price_scale()
        return SimulationSnapshot(
            cycle=simulation.cycle,
            kpis=KpiDTO(
                accumulated_profitability=system.value_of(NodeNames.RENTABILIDADE),
                net_revenue=system.value_of(NodeNames.RECEITA_LIQUIDA),
                served_quantity=system.value_of(NodeNames.QUANTIDADE),
                market_share=system.value_of(NodeNames.MARKET_SHARE),
            ),
            variables=tuple(
                VariableDTO(n.name, n.category.value, n.value, n.expression, n.description)
                for n in system.nodes.values()
            ),
            price_scale=PriceScaleDTO(
                minimum=scale.minimum,
                maximum=scale.maximum,
                stops=tuple(PriceStopDTO(s.value, s.color, s.label) for s in scale.stops),
            ),
            history=tuple(
                CycleRecordDTO(r.cycle, r.profit, r.accumulated_profitability)
                for r in simulation.history
            ),
            model_payload=self._model_mapper.to_dict(system),
            cloud_enabled=cloud_enabled,
        )
