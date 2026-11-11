from datetime import date
import streamlit as st
from backend.application.source_calculators import estimate,tax_annex_iii,count_cnpj,TAX_SOURCE
from backend.application.dto import PersistenceOutcome

SCHEMAS={
'Alfa':'failures,device_months',
'Beta_1':'captured_share,competitors,repair_price,new_price',
'Preco_Equipamento_Novo':'specification,condition,price_brl',
'Influencia_Avaliacoes_Online':'reputation_before,reputation_after,satisfaction,marketing_brl',
'Inovacao_Fabricantes':'stock,captured_demand,parts_availability',
}

def render_source_tools(snapshot,calibration):
    if not calibration or snapshot.cycle:return False
    with st.expander('Calcular a partir de fontes e amostras'):
        st.caption('Não aplicamos dados de demonstração. Informe o recorte real; os resultados são calculados antes de serem vinculados ao cenário.')
        kind=st.selectbox('Fonte / cálculo',['Carga_Tributaria','Nc']+list(SCHEMAS),key='source-kind')
        reference=st.date_input('Referência da base',max_value=date.today(),key='source-date')
        result=None;source='';method='Estimativa empírica declarada'
        try:
            if kind=='Carga_Tributaria':
                method='Cálculo normativo condicionado'
                st.markdown(f'[Resolução CGSN 140, arts. 21–22 e Anexo III]({TAX_SOURCE})')
                st.caption('Cenário de serviços enquadrados no Anexo III, em 2026, sem MEI, comércio, retenções ou ISS fora do DAS. Não é apuração fiscal completa. Início de atividade exige RBT12 proporcional conforme art. 22.')
                revenue=st.number_input('RBT12 para enquadramento (R$)',min_value=0.0,max_value=3600000.0,value=180000.0,step=1000.0)
                confirmed=st.checkbox('Confirmo enquadramento no Anexo III e ausência das exceções descritas')
                if confirmed:
                    result=tax_annex_iii(revenue,reference.isoformat());source=f'{TAX_SOURCE}; Anexo III; RBT12={revenue}; regra conferida para 2026'
            elif kind=='Nc':
                method='Contagem cadastral declarada'
                st.markdown('[Layout oficial dos dados CNPJ](https://www.gov.br/receitafederal/dados/cnpj-metadados.pdf)')
                st.caption('Envie recorte completo do arquivo Estabelecimentos: sem cabeçalho, 30 campos, ;, Latin-1. Não use apenas um dos fragmentos nacionais como se fosse o município inteiro. Município usa código Receita, não IBGE. CNAE principal; não cobre informalidade.')
                uf=st.text_input('UF',value='SP',max_chars=2)
                municipality=st.text_input('Código do município na Receita')
                cnae=st.text_input('CNAE principal (7 dígitos)',value='9511800')
                own=st.text_input('CNPJ da própria empresa a excluir (opcional)')
                file=st.file_uploader('Recorte de estabelecimentos',type=['csv','txt'],key='cnpj-file')
                complete=st.checkbox('Confirmo que o arquivo cobre todo o recorte regional na data informada')
                if file and complete:result,source=count_cnpj(file.getvalue(),uf,municipality,cnae,own)
            else:
                st.caption('Fonte necessária: registros da operação ou cotações datadas comparáveis. Valores ajustados não são uma série oficial. Para inovação, o cálculo é apenas proxy de obsolescência de peças.')
                st.code(SCHEMAS[kind],language=None)
                st.download_button('Baixar cabeçalho CSV',SCHEMAS[kind]+'\n',file_name=kind+'.csv',mime='text/csv')
                source_label=st.text_input('Documento/URL, produto, região, período e método da coleta',key='sample-source')
                file=st.file_uploader('Amostra real (UTF-8, vírgulas, decimal com ponto)',type=['csv'],key='sample-file')
                if file:
                    result,summary=estimate(kind,file.getvalue());source=f'{source_label}; {summary}'
                    if len(source_label.strip())<8:st.info('Informe a origem da amostra antes de aplicar.');result=None
            if result is not None:
                st.metric('Valor calculado (fração para taxas)',f'{result:.6g}')
                st.caption(source)
                if st.button('Aplicar valor calculado com fonte'):
                    status=calibration.execute(kind,result,source,reference.isoformat(),method)
                    if status is PersistenceOutcome.FAILED:st.warning('Aplicado localmente; falhou a persistência remota.')
                    return True
        except (ValueError,UnicodeError,OverflowError) as exc:st.error(str(exc))
    return False
