import pytest
from backend.application.source_calculators import estimate,count_cnpj,tax_annex_iii

@pytest.mark.parametrize('revenue,expected',[(0,.06),(180000,.06),(360000,.086),(720000,.1105),(1800000,.1402),(3600000,.1751)])
def test_tax_official_table(revenue,expected):assert tax_annex_iii(revenue,'2026-11-01')==pytest.approx(expected)

@pytest.mark.parametrize('revenue,reference',[(4000000,'2026-01-01'),(-1,'2026-01-01'),(180000,'2027-01-01')])
def test_tax_rejects_unsupported_case(revenue,reference):
    with pytest.raises(ValueError):tax_annex_iii(revenue,reference)


def test_median_and_failures_are_different_measures():
    v,_=estimate('Preco_Equipamento_Novo',b'specification,condition,price_brl\nLaptop X,new,1000\nLaptop X,new,2000\nLaptop X,new,9000\n')
    assert v==2000
    v,summary=estimate('Alfa',b'failures,device_months\n5,500\n2,200\n')
    assert v==pytest.approx(.01) and 'n=2' in summary and 'sha256=' in summary


def test_beta_reconstructs_model_coefficient():
    content='captured_share,competitors,repair_price,new_price\n'
    for ratio in [.1,.2,.4]:content+=f'{1/(5*(1+2*ratio))},4,{ratio*1000},1000\n'
    assert estimate('Beta_1',content.encode())[0]==pytest.approx(2)


def test_online_reconstructs_non_saturated_reputation_fit():
    content='reputation_before,reputation_after,satisfaction,marketing_brl\n'
    for s in [.3,.4,.5]:
        after=.5+(.8*s+.01-.5)*.2
        content+=f'.5,{after},{s},1000\n'
    assert estimate('Influencia_Avaliacoes_Online',content.encode())[0]==pytest.approx(.8)


def test_obsolescence_proxy_reconstructs_parts_equation():
    assert estimate('Inovacao_Fabricantes',b'stock,captured_demand,parts_availability\n100,200,.45\n')[0]==pytest.approx(.2)

@pytest.mark.parametrize('name,content',[
('Alfa',b'failures,device_months\n1,0\n'),
('Alfa',b'failures,device_months\n-1,10\n'),
('Preco_Equipamento_Novo',b'specification,condition,price_brl\nA,used,100\n'),
('Preco_Equipamento_Novo',b'specification,condition,price_brl\nA,new,100\nB,new,200\n'),
('Beta_1',b'captured_share,competitors,repair_price,new_price\n.1,4,100,1000\n'),
('Inovacao_Fabricantes',b'stock,captured_demand,parts_availability\n0,100,.5\n'),
('Alfa',b'failures,device_months\nnan,10\n'),
('Alfa',b'wrong\n5\n'),
])
def test_incompatible_samples_rejected(name,content):
    with pytest.raises(ValueError):estimate(name,content)


def test_cnpj_filter_dedup_and_exclusion():
    def row(cnpj,status='02',city='7107',cnae='9511800'):
        r=['']*30;r[:3]=[cnpj[:8],cnpj[8:12],cnpj[12:]];r[5]=status;r[19]='SP';r[20]=city;r[11]=cnae
        return ';'.join(r)+'\n'
    content=(row('12345678000100')*2+row('99999999000100')+row('88888888000100','08')+row('77777777000100',city='1')).encode()
    value,source=count_cnpj(content,'SP','7107','9511800','99999999000100')
    assert value==1 and 'sha256=' in source


def test_empty_cnpj_cannot_prove_zero_competitors():
    with pytest.raises(ValueError):count_cnpj(b'','SP','7107','9511800')
