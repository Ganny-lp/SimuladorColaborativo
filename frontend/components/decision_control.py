"""Native accessible controls with synchronized exact entry and visual scales."""
from __future__ import annotations
from html import escape
import streamlit as st
from backend.application.dto import VariableDTO
from frontend.compat import keyed_container

LABELS = {
    'budget_training':'Treinamento', 'budget_update':'Tecnologia e P&D',
    'budget_infra':'Infraestrutura mensal', 'budget_promo':'Marketing',
    'Nc':'Concorrentes na região', 'Cp':'Custo por peça', 'Cap':'Limite de serviços/mês',
    'Pt':'Preço praticado', 'Alfa':'Taxa de falha', 'Beta_1':'Sensibilidade ao preço',
    'C_Mao_Obra':'Mão de obra por serviço', 'Inflacao':'Inflação do período',
}
FRACTIONS = {'Carga_Tributaria','Margem_Alvo','Taxa_Reinvestimento','Alfa','Inovacao_Fabricantes','Inflacao','Juros_Base'}
COUNTS = {'Numero_Tecnicos','Nc','Prazo','Estoque_Alvo','Estoque_Inicial','Base_Instalada_Inicial'}
OPENING = {'Simular_Abertura','Estoque_Inicial','Base_Instalada_Inicial','Custos_Legalizacao','Maquinas_Equipamentos','Recursos_Tecnologicos','Infra_Reforma','Marketing_Abertura','Mobiliario','Caixa_Reserva','Emprestimo','Prazo','Juros_Base'}
MARKET = {'Inflacao','Preco_Equipamento_Novo','Nc','Alfa','Beta_1','Carga_Tributaria','Inovacao_Fabricantes','Influencia_Avaliacoes_Online'}

def group_for(name: str) -> str:
    if name in OPENING: return 'Abertura e financiamento'
    if name in MARKET: return 'Mercado e ambiente'
    if name.startswith('budget_') or name in {'Taxa_Reinvestimento','Margem_Alvo'}: return 'Investimentos e estratégia'
    return 'Operação e equipe'


def scaled_number(label: str, value: float, key: str, *, minimum: float | None = 0.0,
                  maximum: float | None = None, step: float = 1.0,
                  hint: str = '', suffix: str = '') -> float:
    """Two native widgets share a value through callbacks, including keyboard edits."""
    number_key, slider_key = f'{key}_number', f'{key}_scale'
    model_key = f'{key}_model'
    if model_key not in st.session_state or st.session_state[model_key] != float(value):
        st.session_state[number_key] = float(value)
        st.session_state[slider_key] = float(value)
        st.session_state[model_key] = float(value)
    if maximum is not None:
        maximum = max(float(maximum), float(st.session_state[number_key]), minimum + step)
    def from_number():
        st.session_state[slider_key] = st.session_state[number_key]
    def from_slider():
        st.session_state[number_key] = st.session_state[slider_key]
    # Exact entry has no artificial upper limit for amounts; percentages have natural limits.
    chosen = st.number_input(label, min_value=minimum, max_value=maximum if suffix == '%' else None,
                             step=step, key=number_key, help=hint or None, on_change=from_number)
    if maximum is not None and minimum is not None:
        st.slider(f'Escala · {label}', min_value=float(minimum), max_value=float(maximum),
                  step=step, key=slider_key, on_change=from_slider, label_visibility='collapsed')
        st.caption(f'{minimum:g}{suffix}  →  {maximum:g}{suffix}')
    return float(chosen)


class DecisionControl:
    def render(self, variable: VariableDTO) -> float:
        label = LABELS.get(variable.name, variable.name.replace('_',' '))
        with keyed_container(f'decision-card-{variable.name}'):
            st.markdown(f'<div class="decision-eyebrow">{escape(variable.name)}</div>',unsafe_allow_html=True)
            if variable.name in FRACTIONS:
                return scaled_number(label,variable.value*100,f'decision_{variable.name}',
                                     maximum=100,step=0.1,hint=variable.description,suffix='%')/100
            if variable.name in COUNTS:
                return scaled_number(label,variable.value,f'decision_{variable.name}',
                                     minimum=1.0 if variable.name in {'Prazo','Base_Instalada_Inicial'} else 0.0,
                                     maximum=max(20,variable.value*2),step=1.0,hint=variable.description)
            return scaled_number(label,variable.value,f'decision_{variable.name}',minimum=None,
                                 step=1.0 if variable.value>10 else 0.01,hint=variable.description)
