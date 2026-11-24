import requests
import streamlit as st
from backend.application.dto import PersistenceOutcome
from backend.application.use_cases.calibrate_input import OFFICIAL_SERIES_METHOD
from frontend.components.decision_control import scaled_number
from frontend.compat import keyed_container
from frontend.formatters import percent


def _render_inflation(snapshot, apply_input, query, calibration) -> bool:
    inflation = snapshot.variable("Inflacao")
    if inflation is None:
        return False
    hint = "Taxa mensal usada no próximo ciclo. Informe um valor negativo para simular deflação."
    chosen = scaled_number(
        "Inflação do próximo ciclo (%)", inflation.value * 100, "decision_Inflacao",
        minimum=-99.0, maximum=100.0, step=0.01, hint=hint, suffix="%",
        show_scale=False, number_format="%.2f",
    )
    st.caption(hint)
    if chosen != inflation.value * 100:
        return apply_input("Inflacao", chosen / 100)

    if query and st.button("Consultar IPCA oficial"):
        try:
            st.session_state["market_ipca"] = query.execute()
        except (requests.RequestException, ValueError, KeyError, TypeError):
            st.warning("Fonte indisponível. A inflação do cenário foi mantida. Tente novamente.")
    observation = st.session_state.get("market_ipca")
    persisted = snapshot.model_payload.get("calibration", {}).get("Inflacao", {})
    if not observation and persisted.get("method") == OFFICIAL_SERIES_METHOD:
        observation = {**persisted, "retrieved_at": persisted.get("registered_at", "")}
    if not observation:
        st.caption("Consulte o IPCA para ver o último mês publicado pelo IBGE.")
        return False

    reference = observation["reference"]
    st.metric(f"IPCA oficial · {reference[5:7]}/{reference[:4]}", percent(observation["value"]))
    st.caption(f"IBGE / Banco Central · SGS 433 · consulta em {observation['retrieved_at'][:10]}")
    if st.button("Usar IPCA no próximo ciclo", disabled=observation["value"] == inflation.value):
        if not calibration:
            return apply_input("Inflacao", observation["value"])
        try:
            outcome = calibration.execute(
                "Inflacao", observation["value"], observation["source"], reference, OFFICIAL_SERIES_METHOD,
            )
        except ValueError as exc:
            st.error(str(exc))
            return False
        if outcome is PersistenceOutcome.FAILED:
            st.toast("IPCA aplicado nesta sessão. Não foi possível salvar na nuvem.", icon=":material/warning:")
        return True
    return False


def render_market_context(snapshot,apply_input,query,calibration=None):
    changed=False
    with keyed_container("market-context"):
        st.markdown("### Contexto de mercado")
        st.caption("Referências externas e premissas do cenário — separadas das decisões do empreendedor")
        changed = _render_inflation(snapshot, apply_input, query, calibration)
        st.markdown("[Fonte: IPCA mensal no SGS/BCB](https://www3.bcb.gov.br/sgspub/consultarValoresSeries.do?method=consultarSeries&series=433)")
        st.caption("O IPCA é referência macroeconômica, não índice exclusivo de assistências técnicas. Preço de equipamento, concorrentes e coeficientes de demanda continuam premissas até calibração local; não são estimativas oficiais.")
        from frontend.components.source_tools import render_source_tools
        changed = render_source_tools(snapshot,calibration) or changed
        with st.expander("Premissas e fontes para calibração"):
            names={"Nc","Beta_1","Alfa","Preco_Equipamento_Novo","Carga_Tributaria","Inovacao_Fabricantes","Influencia_Avaliacoes_Online"}
            evidence=snapshot.model_payload.get("calibration",{})
            paths={
                "Carga_Tributaria":"Resolução CGSN 140 / Anexo III; calculadora condicionada ao regime e RBT12",
                "Nc":"RFB / Estabelecimentos: importar recorte completo por município e CNAE",
                "Alfa":"Histórico de falhas e exposição equipamento-mês: importar CSV",
                "Beta_1":"Histórico de captação, preços e concorrentes: importar CSV",
                "Preco_Equipamento_Novo":"Cotações comparáveis datadas de equipamentos novos: importar CSV",
                "Influencia_Avaliacoes_Online":"Série local de reputação, satisfação e marketing: importar CSV",
                "Inovacao_Fabricantes":"Estoque, demanda e disponibilidade: proxy de obsolescência, não inovação observada",
                "Inflacao":"BCB / SGS 433: consulta oficial",
            }
            rows=[]
            for v in snapshot.variables:
                if v.name not in names | {"Inflacao"}: continue
                item=evidence.get(v.name,{})
                valid=bool(item) and item.get("value")==v.value
                rows.append({"Parâmetro":v.name.replace("_"," "),"Valor":v.value,"Origem":item.get("method") if valid else "Hipótese sem evidência vinculada","Referência":item.get("reference","") if valid else "Aguardando evidência","Fonte":item.get("source","") if valid else paths[v.name]})
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
                        try:
                            status=calibration.execute(name,value,source,reference.isoformat(),method)
                            changed=True
                            if status is PersistenceOutcome.FAILED: st.warning("Aplicado nesta sessão; não foi possível salvar na nuvem.")
                        except ValueError as exc: st.error(str(exc))
            st.markdown("Concorrentes locais: [Dados públicos do CNPJ / Receita Federal](https://www.gov.br/receitafederal/pt-br/assuntos/orientacao-tributaria/cadastros/cnpj), com recorte por município, CNAE e situação ativa. A base municipal ainda não está integrada; a contagem exibida é uma hipótese.")
    return changed
