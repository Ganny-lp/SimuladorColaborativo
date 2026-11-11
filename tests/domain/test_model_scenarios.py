import math
import pytest
from backend.domain.services.reference_finder import ReferenceFinder

def test_every_formula_is_executable(migrated_system, evaluator):
    for node in migrated_system.nodes.values():
        if node.has_expression:
            assert math.isfinite(evaluator.evaluate(node.expression,migrated_system.values()))

def test_inflation_changes_required_drivers(migrated_system, engine):
    high = migrated_system.clone(); high.set_value('Inflacao',0.2)
    engine.advance_cycle(migrated_system); engine.advance_cycle(high)
    for name in ('Cp_Corrigido','Tx_Juros_Emprestimo','Preco_Novo_Corrigido'):
        assert high.value_of(name) > migrated_system.value_of(name)
    assert high.value_of('Satisfacao_Cliente') < migrated_system.value_of('Satisfacao_Cliente')

def test_overload_reduces_satisfaction(migrated_system,engine):
    high=migrated_system.clone(); high.set_value('B',50000)
    for _ in range(4): engine.advance_cycle(migrated_system);engine.advance_cycle(high)
    assert high.value_of('Backlog_Servicos') > migrated_system.value_of('Backlog_Servicos')
    assert high.value_of('Satisfacao_Cliente') < migrated_system.value_of('Satisfacao_Cliente')

def test_supplier_and_inventory_affect_service(migrated_system,engine):
    low=migrated_system.clone();low.set_value('Estoque_Pecas',1);low.set_value('Prazo_Fornecedor',60)
    engine.advance_cycle(migrated_system);engine.advance_cycle(low)
    assert low.value_of('Qt') < migrated_system.value_of('Qt')
    assert low.value_of('Tempo_Atendimento') > migrated_system.value_of('Tempo_Atendimento')

def test_more_technicians_increase_capacity_and_payroll(migrated_system,engine):
    high=migrated_system.clone();high.set_value('Numero_Tecnicos',6)
    engine.recompute_derived(high)
    assert high.value_of('Capacidade_Operacional') > migrated_system.value_of('Capacidade_Operacional')
    assert high.value_of('Custo_Fixo') > migrated_system.value_of('Custo_Fixo')

def test_finance_zero_interest_and_term(migrated_system,engine):
    migrated_system.set_value('Juros_Base',0);migrated_system.set_value('Inflacao',0)
    for i in range(14):
        engine.advance_cycle(migrated_system)
        expected=10000/12 if i<12 else 0
        assert migrated_system.value_of('Emprestimos_Mensal') == pytest.approx(expected)

def test_no_removed_price_dependency(migrated_system):
    assert not migrated_system.has_node('Pm')
    for node in migrated_system.nodes.values():
        assert not ReferenceFinder().find(node.expression,['Pm'])

def test_state_updates_are_independent_of_insertion_order(migrated_system,engine):
    reverse=migrated_system.clone();reverse.nodes=dict(reversed(list(reverse.nodes.items())))
    for _ in range(8):
        engine.advance_cycle(migrated_system);engine.advance_cycle(reverse)
    assert reverse.values() == pytest.approx(migrated_system.values())


def test_positive_result_funds_next_cycle_training(migrated_system,engine):
    for k,v in {'Pt':500,'Salarios_Beneficios':100,'Pró-Labore':100,'Despesas':100,
                'Servicos_Terceiros_Consultoria':100,'Manutencao':100,'Prazo_Fornecedor':1,
                'Estoque_Pecas':500,'Estoque_Alvo':500,'Inflacao':0,'Numero_Tecnicos':6}.items():
        migrated_system.set_value(k,v)
    no_reinvestment=migrated_system.clone();no_reinvestment.set_value('Taxa_Reinvestimento',0)
    for _ in range(3):
        engine.advance_cycle(migrated_system);engine.advance_cycle(no_reinvestment)
    assert migrated_system.value_of('Reinvestimento_Disponivel') > 0
    assert migrated_system.value_of('Nivel_Qualificacao_Tecnica') > no_reinvestment.value_of('Nivel_Qualificacao_Tecnica')
