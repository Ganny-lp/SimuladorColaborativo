import math
import pytest
from backend.domain.entities.node import Node, NodeCategory
from backend.domain.entities.causal_system import CausalSystem
from backend.domain.exceptions import ExpressionEvaluationError, InvalidModelError
from backend.domain.services.reference_finder import ReferenceFinder


def test_negative_substitution_preserves_exponent_precedence(evaluator):
    assert evaluator.evaluate('X^2', {'X': -3}) == 9
    assert evaluator.evaluate('-X^2', {'X': -3}) == -9

@pytest.mark.parametrize('expression',['(-1)^0.5','EXP(10000)','1/0','__import__("os")'])
def test_invalid_expression_is_a_domain_error(evaluator,expression):
    with pytest.raises(ExpressionEvaluationError): evaluator.evaluate(expression,{})


def test_longest_names_only_are_dependencies():
    names=['Custos','Custos Abertura','Pró-Labore','B']
    assert ReferenceFinder().find('Custos Abertura + Pró-Labore',names) == {'Custos Abertura','Pró-Labore'}


def test_derived_failure_is_atomic(engine):
    s=CausalSystem(nodes={
        'A':Node('A',NodeCategory.EQUATION,value=99,expression='1'),
        'B':Node('B',NodeCategory.EQUATION,value=88,expression='A/0'),
        'Stock':Node('Stock',NodeCategory.STATE,value=10,expression='A'),
    })
    before=s.values()
    with pytest.raises(ExpressionEvaluationError): engine.advance_cycle(s)
    assert s.values() == before

@pytest.mark.parametrize('name,value',[('Pt',-1),('Numero_Tecnicos',1.5),('Carga_Tributaria',1.1),('Prazo',0),('Inflacao',math.nan),('Pt',math.inf),('Qt',10)])
def test_invalid_inputs_do_not_mutate_simulation(migrated_system,name,value):
    from backend.domain.entities.simulation import Simulation
    s=Simulation.begin(migrated_system);before=s.system.values()
    with pytest.raises(InvalidModelError): s.set_input(name,value)
    assert s.system.values() == before


def test_all_initial_financial_inputs_reapply_on_restart(migrated_system,engine):
    from backend.domain.entities.simulation import Simulation
    from backend.application.use_cases.restart_simulation import RestartSimulationUseCase
    from tests.application.fakes import InMemorySimulationStore
    store=InMemorySimulationStore();s=Simulation.begin(migrated_system);store.put(s)
    engine.advance_cycle(s.system);s.set_input('Infra_Reforma',18000);s.set_input('Estoque_Inicial',42)
    RestartSimulationUseCase(store,engine).execute()
    assert s.system.value_of('Estoque_Pecas') == 42
    assert s.system.value_of('Rentabilidade') == -(52500+10000-108*20)


def test_input_change_recomputes_without_advancing_state(migrated_system,engine):
    from backend.domain.entities.simulation import Simulation
    from backend.application.use_cases.change_input import ChangeInputUseCase
    from backend.application.services.model_publisher import ModelPublisher
    from backend.domain.services.initial_state_calculator import InitialStateCalculator
    from tests.application.fakes import InMemorySimulationStore,FakeRepository
    store=InMemorySimulationStore();s=Simulation.begin(migrated_system);store.put(s)
    baseline=s.system.value_of('St')
    use=ChangeInputUseCase(store,ModelPublisher(FakeRepository(),InitialStateCalculator(engine._evaluator)),engine)
    use.execute('Pt',100)
    assert store.get().system.value_of('St') > baseline
    assert store.get().cycle == 0
    assert store.get().system.value_of('Backlog_Servicos') == 0


def test_legacy_upgrade_removes_price_and_preserves_custom_nodes(migrator,default_system):
    old=default_system.clone();old.extras.pop('schema_version');old.nodes['Pm']=Node('Pm',NodeCategory.ENVIRONMENT,140)
    old.nodes['Custom']=Node('Custom',NodeCategory.INPUT,7)
    old.set_value('Pt',123)
    upgraded=migrator.migrate(old)
    assert upgraded.value_of('Pt') == 123 and upgraded.value_of('Custom') == 7
    assert not upgraded.has_node('Pm')
    assert upgraded.value_of('Salarios_Beneficios')*upgraded.value_of('Numero_Tecnicos') == old.value_of('Salarios_Beneficios')
