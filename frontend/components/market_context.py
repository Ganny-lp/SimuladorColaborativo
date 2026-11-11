import requests
import streamlit as st
from frontend.compat import keyed_container
from frontend.formatters import percent


def render_market_context(snapshot,apply_input,query,calibration=None):
    changed=False
    with keyed_container("market-context"):
        st.markdown("### Contexto de mercado")
        st.caption("Referências externas e premissas do cenário — separadas das decisões do empreendedor")
        ipca=snapshot.variable("Inflacao")
        if ipca: st.metric("Inflação mensal usada",percent(ipca.value))
        if query and st.button("Consultar IPCA oficial",disabled=snapshot.cycle>0):
            try:
                observation=query.execute()
                if calibration:
                    calibration.execute("Inflacao",observation["value"],observation["source"],observation["reference"],"Série oficial consultada")
                    changed=True
                else:
                    changed=apply_input("Inflacao",observation["value"])
                st.session_state["market_ipca"]=observation
            except (requests.RequestException,ValueError,KeyError,TypeError) as exc:
                st.warning("Fonte indisponível. O valor do cenário foi mantido; tente novamente.")
        observation=st.session_state.get("market_ipca")
        persisted=snapshot.model_payload.get("calibration",{}).get("Inflacao",{})
        if not observation and persisted.get("method")=="Série oficial consultada":
            observation={**persisted,"retrieved_at":persisted.get("registered_at","")}
        if observation and ipca and abs(observation["value"]-ipca.value)<1e-10:
            st.caption(f"IBGE / Banco Central · SGS 433 · referência {observation['reference']} · consulta {observation['retrieved_at'][:10]}")
        else:
            st.caption("Inflação ainda não consultada nesta sessão: premissa do cenário, não dado atualizado.")
        st.markdown("[Fonte: IPCA mensal no SGS/BCB](https://www3.bcb.gov.br/sgspub/consultarValoresSeries.do?method=consultarSeries&series=433)")
        st.caption("O IPCA é referência macroeconômica, não índice exclusivo de assistências técnicas. Preço de equipamento, concorrentes e coeficientes de demanda continuam premissas até calibração local; não são estimativas oficiais.")
        with st.expander("Premissas e fontes para calibração"):
            names={"Nc","Beta_1","Alfa","Preco_Equipamento_Novo","Carga_Tributaria","Inovacao_Fabricantes","Influencia_Avaliacoes_Online"}
            evidence=snapshot.model_payload.get("calibration",{})
            rows=[]
            for v in snapshot.variables:
                if v.name not in names | {"Inflacao"}: continue
                item=evidence.get(v.name,{})
                valid=bool(item) and item.get("value")==v.value
                rows.append({"Parâmetro":v.name.replace("_"," "),"Valor":v.value,"Origem":item.get("method") if valid else "Hipótese sem evidência vinculada","Referência":item.get("reference","") if valid else "","Fonte":item.get("source","") if valid else ""})
            st.dataframe(rows,hide_index=True)
            if calibration and snapshot.cycle==0:
                from datetime import date
                with st.form("calibration-form"):
                    st.markdown("#### Registrar evidência do cenário")
                    st.caption("Dados declarados pelo responsável. Fonte e data ficam vinculadas ao valor; o aplicativo não verifica documentos locais nem valida todo o modelo por esse registro.")
                    name=st.selectbox("Parâmetro a calibrar",sorted(names))
                    value=st.number_input("Valor observado/estimado (fração para taxas)",value=0.0,step=0.01)
                    source=st.text_input("Fonte e recorte",placeholder="URL ou relatório, município/CNAE, período, amostra e método")
                    reference=st.date_input("Data de referência",value=date.today(),max_value=date.today())
                    method=st.selectbox("Método da evidência",["Observação local declarada","Estimativa empírica declarada"])
                    if st.form_submit_button("Aplicar evidência ao cenário"):
                        from backend.application.dto import PersistenceOutcome
                        try:
                            status=calibration.execute(name,value,source,reference.isoformat(),method)
                            changed=True
                            if status is PersistenceOutcome.FAILED: st.warning("Aplicado nesta sessão; não foi possível salvar na nuvem.")
                        except ValueError as exc: st.error(str(exc))
            st.markdown("Concorrentes locais: [Dados públicos do CNPJ / Receita Federal](https://www.gov.br/receitafederal/pt-br/assuntos/orientacao-tributaria/cadastros/cnpj), com recorte por município, CNAE e situação ativa. A base municipal ainda não está integrada; a contagem exibida é uma hipótese.")
    return changed
