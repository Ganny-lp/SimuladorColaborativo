"""Evidence calculators. No synthetic sample is applied as real calibration."""
import csv
import io
import math
import statistics
import hashlib
from datetime import date

TAX_SOURCE='https://normas.receita.fazenda.gov.br/sijut2consulta/link.action?idAto=92278'
CNPJ_SOURCE='https://www.gov.br/receitafederal/dados/cnpj-metadados.pdf'

def number(value):
    result=float(value)
    if not math.isfinite(result): raise ValueError('A amostra contém número não finito.')
    return result

def positive(value):
    result=number(value)
    if result<=0: raise ValueError('Denominadores e preços devem ser positivos.')
    return result

def fraction(value):
    result=number(value)
    if not 0<=result<=1: raise ValueError('Proporções devem estar entre 0 e 1.')
    return result

def tax_annex_iii(revenue,reference):
    if date.fromisoformat(reference).year!=2026: raise ValueError('Tabela conferida para 2026. Revise a legislação para outro ano.')
    revenue=number(revenue)
    if not 0<=revenue<=3600000: raise ValueError('Calculadora limitada a RBT12 de 0 a R$ 3,6 milhões; sublimites/ISS fora do escopo.')
    for limit,rate,deduction in [(180000,.06,0),(360000,.112,9360),(720000,.135,17640),(1800000,.16,35640),(3600000,.21,125640)]:
        if revenue<=limit:return (max(1,revenue)*rate-deduction)/max(1,revenue)

def estimate(name,content):
    """UTF-8 CSV, comma delimiter, decimal point. Returns value + auditable summary."""
    if len(content)>5_000_000: raise ValueError('Amostra limitada a 5 MB.')
    rows=list(csv.DictReader(io.StringIO(content.decode('utf-8-sig'))))
    if not rows:raise ValueError('CSV sem observações.')
    try:
        if name=='Preco_Equipamento_Novo':
            if len({r['specification'] for r in rows})!=1:raise ValueError('Separe equipamentos com especificações distintas.')
            value=statistics.median(positive(r['price_brl']) for r in rows)
            method='Mediana de cotações comparáveis; inclui apenas equipamentos novos'
            if any(r['condition'].lower()!='new' for r in rows):raise ValueError('A amostra deve conter somente equipamentos novos (condition=new).')
        elif name=='Alfa':
            events=sum(number(r['failures']) for r in rows)
            exposure=sum(positive(r['device_months']) for r in rows)
            if any(number(r['failures'])<0 for r in rows):raise ValueError('Falhas negativas.')
            value=fraction(events/exposure);method='Falhas / exposição em equipamento-mês; não taxa de sucesso de reparos'
        elif name=='Beta_1':
            if len(rows)<3:raise ValueError('Beta requer pelo menos 3 observações com preços distintos.')
            x=[];y=[]
            for r in rows:
                share=positive(r['captured_share']);nc=number(r['competitors'])
                if share>1 or nc<0 or not nc.is_integer():raise ValueError('Participação/concorrentes inválidos.')
                x.append(positive(r['repair_price'])/positive(r['new_price']))
                y.append(1/(share*(1+nc))-1)
            if max(x)-min(x)<1e-6:raise ValueError('Sem variação de preços: Beta não é identificável.')
            value=sum(a*b for a,b in zip(x,y))/sum(a*a for a in x)
            if value<0:raise ValueError('Amostra incompatível com a sensibilidade não negativa do modelo.')
            method='Mínimos quadrados sem intercepto: 1/(share*(1+Nc))-1 = Beta*(Pt/Pnovo); associação, não efeito causal'
        elif name=='Influencia_Avaliacoes_Online':
            x=[];y=[]
            if len(rows)<3:raise ValueError('Coeficiente requer pelo menos 3 meses não saturados.')
            for r in rows:
                previous=fraction(r['reputation_before']);after=fraction(r['reputation_after']);satisfaction=positive(r['satisfaction'])
                marketing=number(r['marketing_brl'])
                target=previous+(after-previous)/.2
                if satisfaction>1 or marketing<0 or not 0<target<1:raise ValueError('Escala inválida ou reputação saturada; exclua essa observação.')
                x.append(satisfaction);y.append(target-marketing/100000)
            value=sum(a*b for a,b in zip(x,y))/sum(a*a for a in x)
            if value<0:raise ValueError('Coeficiente negativo incompatível com o modelo.')
            method='Ajuste da equação de reputação com inércia 0,2 e marketing controlado; não efeito causal de estrelas públicas'
        elif name=='Inovacao_Fabricantes':
            estimates=[]
            for r in rows:
                base=min(1,number(r['stock'])/positive(r['captured_demand']))
                availability=fraction(r['parts_availability'])
                if base<=0 or availability>base:raise ValueError('Disponibilidade incompatível com estoque/demanda.')
                estimates.append(2*(1-availability/base))
            value=fraction(statistics.mean(estimates));method='Proxy ajustada de obsolescência de peças na equação atual; não mede lançamentos dos fabricantes'
        else:raise ValueError('Calculadora não disponível.')
    except (KeyError,TypeError,UnicodeError) as exc:
        raise ValueError(f'CSV fora do esquema: {exc}') from exc
    return value,f'{method}; n={len(rows)}; sha256={hashlib.sha256(content).hexdigest()}'

def count_cnpj(content,uf,municipality,cnae,own=''):
    if len(content)>50_000_000:raise ValueError('Use um recorte regional completo até 50 MB.')
    if len(uf)!=2 or not municipality.isdigit() or len(cnae)!=7 or not cnae.isdigit():raise ValueError('Informe UF, município Receita e CNAE de 7 dígitos.')
    own=''.join(c for c in own if c.isdigit())
    if own and len(own)!=14:raise ValueError('CNPJ próprio precisa de 14 dígitos.')
    seen=set();total=0
    for row in csv.reader(io.StringIO(content.decode('latin-1')),delimiter=';'):
        if len(row)!=30:raise ValueError('Esperado arquivo Estabelecimentos oficial sem cabeçalho, com 30 campos separados por ;.')
        identifier=''.join(row[:3])
        if len(identifier)!=14 or not identifier.isdigit():raise ValueError('CNPJ inválido no recorte.')
        total+=1
        if row[5].lstrip('0')=='2' and row[19].upper()==uf.upper() and row[20].lstrip('0')==municipality.lstrip('0') and row[11]==cnae and identifier!=own:
            seen.add(identifier)
    if not total:raise ValueError('Arquivo vazio não comprova ausência de concorrentes.')
    return len(seen),f'{CNPJ_SOURCE}; UF={uf.upper()}; município Receita={municipality}; CNAE principal={cnae}; ativos; CNPJ próprio excluído={bool(own)}; linhas={total}; sha256={hashlib.sha256(content).hexdigest()}'
