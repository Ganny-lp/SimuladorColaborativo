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
DECISION_HELP = {
    "Alfa": "Fração da base de equipamentos que apresenta falhas no mês. Quanto maior, maior a demanda potencial.",
    "Beta_1": "Quanto a captação reage ao preço do reparo em relação ao de um equipamento novo.",
    "Cap": "Teto mensal de reparos, mesmo quando há equipe, peças e pedidos para atender mais.",
    "Carga_Tributaria": "Percentual da receita bruta descontado como tributos no ciclo.",
    "Cp": "Custo base por peça em reais, antes da correção pela inflação do ciclo.",
    "C_Mao_Obra": "Custo variável de mão de obra em reais por reparo concluído.",
    "Complexidade_Reparo": "Nível médio de dificuldade dos reparos. Uma complexidade maior aumenta o tempo de serviço e reduz a capacidade mensal.",
    "Emprestimo": "Valor do crédito em reais que entra no caixa no primeiro ciclo quando a abertura está ativada.",
    "Prazo": "Número de parcelas mensais do financiamento contratado na abertura.",
    "budget_update": "Gasto mensal em reais com tecnologia e pesquisa. Melhora as condições de diagnóstico.",
    "budget_training": "Gasto mensal em reais com treinamento. Afeta a qualificação e a motivação dos técnicos.",
    "budget_infra": "Gasto mensal em reais com infraestrutura de operação e diagnóstico.",
    "budget_promo": "Gasto mensal em reais com divulgação. Contribui para a reputação da assistência.",
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
                  hint: str = '', suffix: str = '', show_scale: bool = True,
                  number_format: str | None = None) -> float:
    """Two native widgets share a value through callbacks, including keyboard edits."""
    number_key, slider_key = f'{key}_number', f'{key}_scale'
    model_key = f'{key}_model'
    if st.session_state.get(model_key) != float(value) or number_key not in st.session_state:
        st.session_state[number_key] = float(value)
        st.session_state[model_key] = float(value)

    def from_slider():
        st.session_state[number_key] = st.session_state[slider_key]

    chosen = st.number_input(label, min_value=minimum, max_value=maximum if suffix == '%' else None,
                             step=step, format=number_format, key=number_key, help=hint or None)
    if show_scale and maximum is not None and minimum is not None:
        maximum = max(float(maximum), float(chosen), minimum + step)
        # Reapply the selection when derived bounds change the slider's widget identity.
        st.session_state[slider_key] = float(chosen)
        st.slider(f'Escala · {label}', min_value=float(minimum), max_value=float(maximum),
                  step=step, key=slider_key, on_change=from_slider, label_visibility='collapsed')
        st.caption(f'{minimum:g}{suffix}  →  {maximum:g}{suffix}')
    return float(chosen)


class DecisionControl:
    def render(self, variable: VariableDTO) -> float:
        label = LABELS.get(variable.name, variable.name.replace('_',' '))
        hint = DECISION_HELP.get(variable.name, variable.description)
        category = 'Investimento mensal' if variable.name.startswith('budget_') else ('Equipe e capacidade' if variable.name == 'Numero_Tecnicos' else 'Decisão operacional')
        with keyed_container(f'decision-card-{variable.name}'):
            st.markdown(f'<div class="decision-eyebrow">{escape(category)}</div>',unsafe_allow_html=True)
            if variable.name in FRACTIONS:
                chosen = scaled_number(label,variable.value*100,f'decision_{variable.name}',
                                       maximum=100.0,step=0.1,hint=hint,suffix='%')/100
            elif variable.name in COUNTS:
                chosen = scaled_number(label,variable.value,f'decision_{variable.name}',
                                       minimum=1.0 if variable.name in {'Prazo','Base_Instalada_Inicial'} else 0.0,
                                       maximum=max(20,variable.value*2),step=1.0,hint=hint)
            else:
                chosen = scaled_number(label,variable.value,f'decision_{variable.name}',minimum=None,
                                       step=1.0 if variable.value>10 else 0.01,hint=hint)
            if hint:
                st.caption(hint)
            return chosen
