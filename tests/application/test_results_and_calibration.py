import pytest
from backend.application.mappers.snapshot_assembler import SnapshotAssembler
from backend.domain.entities.simulation import Simulation
from backend.application.use_cases.calibrate_input import CalibrateInputUseCase
from backend.application.services.model_publisher import ModelPublisher
from backend.domain.services.initial_state_calculator import InitialStateCalculator
from tests.application.fakes import InMemorySimulationStore,FakeRepository


def test_preparation_is_not_realized_revenue(migrated_system,mapper):
    snapshot=SnapshotAssembler(mapper).assemble(Simulation.begin(migrated_system),False)
    assert snapshot.kpis.net_revenue==0
    assert snapshot.kpis.served_quantity==0
    assert snapshot.kpis.market_share==0
    assert snapshot.variable('Qt').value>0  # explicitly still a projection


def test_completed_results_do_not_change_with_new_decisions(migrated_system,engine,mapper):
    s=Simulation.begin(migrated_system)
    engine.advance_cycle(s.system);s.register_cycle(1,s.system.value_of('Rentabilidade'))
    assembler=SnapshotAssembler(mapper);before=assembler.assemble(s,False).kpis
    s.set_input('Pt',300);engine.recompute_derived(s.system)
    assert assembler.assemble(s,False).kpis==before
    s.clear_progress()
    assert assembler.assemble(s,False).kpis.net_revenue==0


def setup_calibration(system,engine):
    store=InMemorySimulationStore();store.put(Simulation.begin(system));repo=FakeRepository()
    use=CalibrateInputUseCase(store,ModelPublisher(repo,InitialStateCalculator(engine._evaluator)),engine)
    return store,repo,use


def test_calibration_persists_source_and_value(migrated_system,engine,mapper):
    store,repo,use=setup_calibration(migrated_system,engine)
    use.execute('Nc',12,'Relatório CNPJ; município X, CNAE Y, estabelecimentos ativos','2026-01-01','Observação local declarada')
    evidence=repo.saved[-1].extras['calibration']['Nc']
    assert evidence['value']==12 and evidence['reference']=='2026-01-01'
    assert mapper.to_entity(mapper.to_dict(repo.saved[-1])).extras['calibration']['Nc']==evidence
    assert store.get().cycle==0

@pytest.mark.parametrize('source,reference,value',[('','2026-01-01',12),('Documento válido','2099-01-01',12),('Documento válido','2026-01-01',-1)])
def test_calibration_rejects_invalid_evidence_atomically(migrated_system,engine,source,reference,value):
    store,repo,use=setup_calibration(migrated_system,engine)
    before=store.get().system.values()
    with pytest.raises(ValueError):use.execute('Nc',value,source,reference,'Observação local declarada')
    assert store.get().system.values()==before and not repo.saved
