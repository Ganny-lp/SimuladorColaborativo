from html import escape
import streamlit as st
from frontend.compat import keyed_container
from frontend.components.decision_control import LABELS
from frontend.formatters import currency


def render_budget_summary(variables):
    budgets=[v for v in variables if v.name.startswith("budget_")]
    total=sum(max(0,v.value) for v in budgets)
    colors=["#1094ab","#6c70bc","#d79835","#4b936e"]
    with keyed_container("budget-summary"):
        st.markdown("### Plano de investimento mensal")
        st.caption("Como o orçamento está distribuído entre as áreas da empresa")
        st.metric("Total por mês",currency(total))
        if total == 0:
            st.info("Defina um orçamento para visualizar a distribuição.")
            return
        segments="".join(f'<span style="width:{max(0,v.value)/total*100:.4f}%;background:{c}" title="{escape(LABELS.get(v.name,v.name))}"></span>' for v,c in zip(budgets,colors))
        st.markdown(f'<div class="budget-track" role="img" aria-label="Distribuição do orçamento">{segments}</div>',unsafe_allow_html=True)
        for col,v,c in zip(st.columns(4),budgets,colors):
            col.metric(LABELS.get(v.name,v.name),currency(v.value))
            col.caption(f"{v.value/total:.1%} do orçamento")
