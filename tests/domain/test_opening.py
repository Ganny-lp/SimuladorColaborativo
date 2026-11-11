import pytest

def test_opening_is_charged_exactly_once(migrated_system,engine):
    s=migrated_system;s.set_value('Simular_Abertura',1)
    engine.reset_state(s)
    assert s.value_of('Rentabilidade')==0
    before_cash=s.value_of('Caixa_Disponivel')
    engine.advance_cycle(s)
    assert s.value_of('Rentabilidade')==pytest.approx(s.value_of('Fluxo_Caixa')-s.value_of('Custos Abertura'))
    assert s.value_of('Caixa_Disponivel')==pytest.approx(before_cash+s.value_of('Fluxo_Caixa')+s.value_of('Emprestimo'))
    previous=s.value_of('Rentabilidade');before_cash=s.value_of('Caixa_Disponivel')
    engine.advance_cycle(s)
    assert s.value_of('Rentabilidade')==pytest.approx(previous+s.value_of('Fluxo_Caixa'))
    assert s.value_of('Caixa_Disponivel')==pytest.approx(before_cash+s.value_of('Fluxo_Caixa'))

def test_existing_company_has_no_opening_or_new_loan(migrated_system,engine):
    s=migrated_system;engine.advance_cycle(s)
    assert s.value_of('Rentabilidade')==pytest.approx(s.value_of('Fluxo_Caixa'))
    assert s.value_of('Emprestimos_Mensal')==0
