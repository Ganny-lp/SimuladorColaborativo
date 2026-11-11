import requests
import streamlit as st
from frontend.compat import keyed_container
from frontend.formatters import percent


def render_market_context(snapshot,apply_input,query):
    changed=False
    with keyed_container("market-context"):
        st.markdown("### Contexto de mercado")
        st.caption("Referências externas e premissas do cenário — separadas das decisões do empreendedor")
        ipca=snapshot.variable("Inflacao")
        if ipca: st.metric("Inflação mensal usada",percent(ipca.value))
        if query and st.button("Consultar IPCA oficial",disabled=snapshot.cycle>0):
            try:
                observation=query.execute()
                changed=apply_input("Inflacao",observation["value"])
                st.session_state["market_ipca"]=observation
            except (requests.RequestException,ValueError,KeyError,TypeError) as exc:
                st.warning("Fonte indisponível. O valor do cenário foi mantido; tente novamente.")
        observation=st.session_state.get("market_ipca")
        if observation and ipca and abs(observation["value"]-ipca.value)<1e-10:
            st.caption(f"IBGE / Banco Central · SGS 433 · referência {observation['reference']} · consulta {observation['retrieved_at'][:10]}")
        else:
            st.caption("Inflação ainda não consultada nesta sessão: premissa do cenário, não dado atualizado.")
        st.markdown("[Fonte: IPCA mensal no SGS/BCB](https://www3.bcb.gov.br/sgspub/consultarValoresSeries.do?method=consultarSeries&series=433)")
        st.caption("O IPCA é referência macroeconômica, não índice exclusivo de assistências técnicas. Preço de equipamento, concorrentes e coeficientes de demanda continuam premissas até calibração local; não são estimativas oficiais.")
        with st.expander("Premissas e fontes para calibração"):
            names={"Nc","Beta_1","Alfa","Preco_Equipamento_Novo","Carga_Tributaria","Inovacao_Fabricantes","Influencia_Avaliacoes_Online"}
            st.dataframe([{"Parâmetro":v.name.replace("_"," "),"Valor do cenário":v.value,"Origem":"Premissa não calibrada"} for v in snapshot.variables if v.name in names],hide_index=True)
            st.markdown("Concorrentes locais: [Dados públicos do CNPJ / Receita Federal](https://www.gov.br/receitafederal/pt-br/assuntos/orientacao-tributaria/cadastros/cnpj), com recorte por município, CNAE e situação ativa. A base municipal ainda não está integrada; a contagem exibida é uma hipótese.")
    return changed
