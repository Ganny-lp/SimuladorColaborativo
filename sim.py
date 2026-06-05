import streamlit as st
import streamlit.components.v1 as components
import json
import copy
import math
import re
import requests
import pandas as pd
import plotly.graph_objects as go

# ============================================================
# CONFIGURAÇÃO DA PÁGINA
# ============================================================
st.set_page_config(
    page_title="LUMINA · Simulador de Laços Causais",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}
.stApp {
    background-color: #0d0f1a;
    color: #d8ddf0;
}

/* ── Header ── */
.lumina-header {
    display: flex;
    align-items: baseline;
    gap: 12px;
    padding: 0 0 4px;
    border-bottom: 1px solid rgba(120,130,200,0.12);
    margin-bottom: 12px;
    flex-wrap: wrap;
}
.main-header {
    font-family: 'DM Serif Display', serif;
    font-size: clamp(1.2rem, 4vw, 1.8rem);
    color: #e8a94a;
    letter-spacing: 0.5px;
    line-height: 1;
}
.sub-header {
    font-family: 'DM Mono', monospace;
    font-size: clamp(0.55rem, 2vw, 0.72rem);
    color: #5a6290;
    letter-spacing: 1px;
}

/* ── Cards / KPI ── */
.card {
    background: #1e2340;
    border: 1px solid rgba(120,130,200,0.15);
    border-radius: 12px;
    padding: clamp(0.6rem, 2vw, 1rem);
    margin-bottom: 0.7rem;
}
.kpi-value {
    font-family: 'DM Mono', monospace;
    font-size: clamp(1.1rem, 3vw, 1.5rem);
    color: #e8a94a;
    font-weight: 600;
    white-space: nowrap;
}
.kpi-label {
    font-size: clamp(0.6rem, 1.5vw, 0.7rem);
    color: #5a6290;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* ── Buttons ── */
.stButton > button {
    background: #4a6aee;
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 500;
    min-height: 42px;
    font-size: clamp(0.75rem, 2vw, 0.9rem);
    width: 100%;
}
.stButton > button:hover {
    background: #6c8fff;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    flex-wrap: nowrap;
    overflow-x: auto;
    scrollbar-width: none;
}
.stTabs [data-baseweb="tab-list"]::-webkit-scrollbar { display: none; }
.stTabs [data-baseweb="tab"] {
    font-size: clamp(0.7rem, 2vw, 0.85rem);
    padding: 8px 12px;
    white-space: nowrap;
}

/* ── Streamlit input adjustments for dark theme ── */
.stNumberInput input, .stSelectbox select, .stTextInput input {
    font-size: clamp(0.75rem, 2vw, 0.9rem);
}

/* ── Dataframe mobile ── */
[data-testid="stDataFrame"] {
    width: 100% !important;
    overflow-x: auto;
}

/* ── Mobile: collapse columns on very small screens ── */
@media (max-width: 600px) {
    [data-testid="column"] {
        min-width: 120px;
    }
    .kpi-value { font-size: 1rem; }
    .card { padding: 0.5rem; }
}

/* ── Streamlit dark overrides ── */
div[data-testid="stMarkdownContainer"] p { color: #8892be; }
.stCaption { color: #5a6290 !important; }
hr { border-color: rgba(120,130,200,0.12) !important; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# CONFIG JSONBIN
# ============================================================
def _get_cfg():
    try:
        return st.secrets["jsonbin"]["api_key"], st.secrets["jsonbin"]["bin_id"]
    except Exception:
        return None, None


def load_system():
    api_key, bin_id = _get_cfg()
    if api_key and bin_id:
        try:
            r = requests.get(
                f"https://api.jsonbin.io/v3/b/{bin_id}/latest",
                headers={"X-Master-Key": api_key},
                timeout=8,
            )
            if r.status_code == 200:
                data = r.json().get("record", {})
                if "nodes" in data and "links" in data:
                    return data
        except Exception:
            pass
    return copy.deepcopy(DEFAULT_SYSTEM)


def save_system(system):
    api_key, bin_id = _get_cfg()
    if api_key and bin_id:
        try:
            requests.put(
                f"https://api.jsonbin.io/v3/b/{bin_id}",
                headers={"Content-Type": "application/json", "X-Master-Key": api_key},
                json=system,
                timeout=8,
            )
        except Exception:
            pass
    st.session_state.system = system


# ============================================================
# MODELO PADRÃO
# ============================================================
DEFAULT_SYSTEM = {
    "nodes": {
        "Rentabilidade": {"cat": "Estado",    "val": 0,      "expr": "Receita - Custos",                                           "desc": "Acumulado de receitas menos custos.",    "x": 760, "y": 300},
        "Receita":        {"cat": "Equação",   "val": 0,      "expr": "(Pt*Qt)*(1-Carga_Tributaria)",                               "desc": "Receita líquida.",                       "x": 560, "y": 200},
        "Custos":         {"cat": "Equação",   "val": 0,      "expr": "Custo_Fixo+Custo_Variavel_t+Emprestimos_Mensal",             "desc": "Custo total.",                           "x": 560, "y": 400},
        "Pt":             {"cat": "Input",     "val": 150,    "expr": "",                                                           "desc": "Preço de venda.",                        "x": 360, "y": 130},
        "Qt":             {"cat": "Equação",   "val": 0,      "expr": "MIN(Dpt*St, Cap)",                                           "desc": "Demanda capturada.",                     "x": 360, "y": 270},
        "Carga_Tributaria":{"cat":"Parâmetro", "val": 0.15,   "expr": "",                                                           "desc": "Percentual de impostos.",               "x": 560, "y": 100},
        "Custo_Fixo":     {"cat": "Equação",   "val": 500,    "expr": "500+budget_update+budget_training+budget_infra+budget_promo","desc": "Custos fixos.",                          "x": 360, "y": 430},
        "Custo_Variavel_t":{"cat":"Equação",   "val": 0,      "expr": "CVt*(1+Inflacao)",                                          "desc": "Custo variável ajustado.",              "x": 360, "y": 520},
        "Emprestimos_Mensal":{"cat":"Equação", "val": 0,      "expr": "Emprestimo/a_ni",                                           "desc": "Parcela mensal.",                        "x": 560, "y": 520},
        "Dpt":            {"cat": "Equação",   "val": 0,      "expr": "B*Alfa*Teta_1",                                             "desc": "Demanda Potencial.",                     "x": 160, "y": 270},
        "St":             {"cat": "Equação",   "val": 0,      "expr": "EXP(-Beta_1*(Pt-Pm))/(1+Nc)",                               "desc": "Market share.",                          "x": 360, "y": 200},
        "B":              {"cat": "Ambiente",  "val": 10000,  "expr": "",                                                           "desc": "Base instalada.",                        "x": 80,  "y": 180},
        "Alfa":           {"cat": "Ambiente",  "val": 1,      "expr": "",                                                           "desc": "Taxa de falha.",                         "x": 80,  "y": 350},
        "Teta_1":         {"cat": "Ambiente",  "val": 0.10,   "expr": "",                                                           "desc": "Confiança.",                             "x": 160, "y": 430},
        "Pm":             {"cat": "Ambiente",  "val": 140,    "expr": "",                                                           "desc": "Preço concorrência.",                    "x": 200, "y": 130},
        "Beta_1":         {"cat": "Parâmetro", "val": 0.5,    "expr": "",                                                           "desc": "Sensibilidade.",                         "x": 200, "y": 200},
        "Nc":             {"cat": "Ambiente",  "val": 4,      "expr": "",                                                           "desc": "Nº concorrentes.",                       "x": 200, "y": 310},
        "Cap":            {"cat": "Parâmetro", "val": 300,    "expr": "",                                                           "desc": "Capacidade máx.",                        "x": 460, "y": 310},
        "CVt":            {"cat": "Equação",   "val": 0,      "expr": "Qt*(Cp+C_Mao_Obra)",                                        "desc": "Custo variável base.",                   "x": 160, "y": 560},
        "Cp":             {"cat": "Ambiente",  "val": 20,     "expr": "",                                                           "desc": "Custo peças.",                           "x": 80,  "y": 520},
        "C_Mao_Obra":     {"cat": "Parâmetro", "val": 10,     "expr": "",                                                           "desc": "Mão de obra.",                           "x": 280, "y": 580},
        "Inflacao":       {"cat": "Ambiente",  "val": 0.035,  "expr": "",                                                           "desc": "Inflação.",                              "x": 460, "y": 520},
        "Emprestimo":     {"cat": "Parâmetro", "val": 10000,  "expr": "",                                                           "desc": "Valor empréstimo.",                      "x": 660, "y": 580},
        "a_ni":           {"cat": "Equação",   "val": 0,      "expr": "((1+Tx_Juros_Emprestimo)^Prazo-1)/((1+Tx_Juros_Emprestimo)^Prazo*Tx_Juros_Emprestimo)", "desc": "Fator anuidade.", "x": 760, "y": 520},
        "Tx_Juros_Emprestimo":{"cat":"Parâmetro","val":0.016, "expr": "",                                                           "desc": "Juros mensais.",                         "x": 860, "y": 580},
        "Prazo":          {"cat": "Parâmetro", "val": 12,     "expr": "",                                                           "desc": "Prazo.",                                 "x": 960, "y": 520},
        "budget_update":  {"cat": "Input",     "val": 5000,   "expr": "",                                                           "desc": "P&D.",                                   "x": 560, "y": 380},
        "budget_training":{"cat": "Input",     "val": 5000,   "expr": "",                                                           "desc": "Treinamento.",                           "x": 660, "y": 430},
        "budget_infra":   {"cat": "Input",     "val": 5000,   "expr": "",                                                           "desc": "Infraestrutura.",                        "x": 760, "y": 430},
        "budget_promo":   {"cat": "Input",     "val": 10000,  "expr": "",                                                           "desc": "Marketing.",                             "x": 860, "y": 380},
    },
    "links": [
        {"from": "Receita",            "to": "Rentabilidade",    "sign": "+", "desc": "Receita → Rentabilidade"},
        {"from": "Custos",             "to": "Rentabilidade",    "sign": "-", "desc": "Custos → Rentabilidade"},
        {"from": "Pt",                 "to": "Receita",          "sign": "+", "desc": "Preço → Receita"},
        {"from": "Qt",                 "to": "Receita",          "sign": "+", "desc": "Qt → Receita"},
        {"from": "Carga_Tributaria",   "to": "Receita",          "sign": "-", "desc": "Imposto → Receita"},
        {"from": "Custo_Fixo",         "to": "Custos",           "sign": "+", "desc": "Fixo → Custos"},
        {"from": "Custo_Variavel_t",   "to": "Custos",           "sign": "+", "desc": "Variável → Custos"},
        {"from": "Emprestimos_Mensal", "to": "Custos",           "sign": "+", "desc": "Parcela → Custos"},
        {"from": "Dpt",                "to": "Qt",               "sign": "+", "desc": "Demanda → Qt"},
        {"from": "St",                 "to": "Qt",               "sign": "+", "desc": "Share → Qt"},
        {"from": "Cap",                "to": "Qt",               "sign": "-", "desc": "Capacidade → Qt"},
        {"from": "B",                  "to": "Dpt",              "sign": "+", "desc": "Base → Dpt"},
        {"from": "Alfa",               "to": "Dpt",              "sign": "+", "desc": "Falha → Dpt"},
        {"from": "Teta_1",             "to": "Dpt",              "sign": "+", "desc": "Confiança → Dpt"},
        {"from": "Pm",                 "to": "St",               "sign": "+", "desc": "Preço médio → St"},
        {"from": "Pt",                 "to": "St",               "sign": "-", "desc": "Preço → St"},
        {"from": "Beta_1",             "to": "St",               "sign": "-", "desc": "Sensibilidade → St"},
        {"from": "Nc",                 "to": "St",               "sign": "-", "desc": "Concorrentes → St"},
        {"from": "Qt",                 "to": "CVt",              "sign": "+", "desc": "Qt → CVt"},
        {"from": "Cp",                 "to": "CVt",              "sign": "+", "desc": "Peças → CVt"},
        {"from": "C_Mao_Obra",         "to": "CVt",              "sign": "+", "desc": "Mão de obra → CVt"},
        {"from": "CVt",                "to": "Custo_Variavel_t", "sign": "+", "desc": "CVt → Custo Var"},
        {"from": "Inflacao",           "to": "Custo_Variavel_t", "sign": "+", "desc": "Inflação → Custo Var"},
        {"from": "Emprestimo",         "to": "Emprestimos_Mensal","sign":"+", "desc": "Empréstimo → Parcela"},
        {"from": "a_ni",               "to": "Emprestimos_Mensal","sign":"-", "desc": "Anuidade → Parcela"},
        {"from": "Tx_Juros_Emprestimo","to": "a_ni",             "sign": "+", "desc": "Juros → a_ni"},
        {"from": "Prazo",              "to": "a_ni",             "sign": "+", "desc": "Prazo → a_ni"},
        {"from": "budget_update",      "to": "Custo_Fixo",       "sign": "+", "desc": "P&D → Fixo"},
        {"from": "budget_training",    "to": "Custo_Fixo",       "sign": "+", "desc": "Treinamento → Fixo"},
        {"from": "budget_infra",       "to": "Custo_Fixo",       "sign": "+", "desc": "Infra → Fixo"},
        {"from": "budget_promo",       "to": "Custo_Fixo",       "sign": "+", "desc": "Marketing → Fixo"},
    ]
}

# ============================================================
# AVALIADOR DE EXPRESSÕES
# ============================================================
def safe_eval(expr: str, nodes: dict, snapshot: dict = None):
    if not expr or expr.strip() == "":
        return 0.0
    sanitized = expr
    var_names = sorted(nodes.keys(), key=len, reverse=True)
    for name in var_names:
        val = snapshot[name] if (snapshot and name in snapshot) else nodes[name]["val"]
        sanitized = re.sub(r'\b' + re.escape(name) + r'\b', str(val), sanitized)
    func_map = {
        'EXP': 'math.exp', 'MIN': 'min', 'MAX': 'max', 'ABS': 'abs',
        'SQRT': 'math.sqrt', 'LOG': 'math.log10', 'LN': 'math.log',
        'SIN': 'math.sin', 'COS': 'math.cos', 'TAN': 'math.tan',
    }
    for fn, py_fn in func_map.items():
        sanitized = re.sub(r'\b' + fn + r'\b', py_fn, sanitized, flags=re.IGNORECASE)
    sanitized = sanitized.replace('^', '**')
    try:
        result = eval(sanitized, {"math": math, "__builtins__": {}}, {})
        if math.isnan(result) or not math.isfinite(result):
            return 0.0
        return float(result)
    except Exception:
        return 0.0


# ============================================================
# INICIALIZAÇÃO DO SESSION STATE
# ============================================================
if "system" not in st.session_state:
    st.session_state.system = load_system()
    st.session_state.initial_vals = {k: v["val"] for k, v in st.session_state.system["nodes"].items()}
    st.session_state.sim_cycle = 0
    st.session_state.sim_history = []
    st.session_state.selected_node = None

SYSTEM = st.session_state.system
api_key, bin_id = _get_cfg()


# ============================================================
# HTML DO SIMULADOR — VERSÃO TOTALMENTE RESPONSIVA
# ============================================================
def get_simulator_html(model_json: str, js_api_key, js_bin_id) -> str:
    ak = json.dumps(js_api_key)
    bi = json.dumps(js_bin_id)

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
<style>
/* ═══════════════════════════════════════════════
   DESIGN TOKENS
═══════════════════════════════════════════════ */
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500;600&display=swap');

:root {{
  --bg:     #0d0f1a;
  --bg2:    #13162a;
  --bg3:    #1a1e35;
  --surface:#1e2340;
  --surf2:  #252b4a;
  --border: rgba(120,130,200,0.15);
  --border2:rgba(120,130,200,0.28);
  --text:   #d8ddf0;
  --text2:  #8892be;
  --text3:  #5a6290;
  --accent: #6c8fff;
  --accent2:#4a6aee;
  --gold:   #e8a94a;
  --teal:   #3ecfb0;
  --coral:  #e06060;
  --green:  #52c97a;
  --mono:   'DM Mono', monospace;
  --serif:  'DM Serif Display', serif;
  --sans:   'DM Sans', sans-serif;

  /* Layout breakpoint flags via CSS custom properties */
  --panel-w: 300px;
  --toolbar-h: 56px;
  --header-h: 40px;
}}

/* ═══════════════════════════════════════════════
   RESET & BASE
═══════════════════════════════════════════════ */
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

body {{
  background: var(--bg);
  color: var(--text);
  font-family: var(--sans);
  font-size: 14px;
  height: 100dvh;           /* dynamic viewport height — safe on mobile */
  overflow: hidden;
  display: flex;
  flex-direction: column;
}}

/* ═══════════════════════════════════════════════
   LAYOUT SHELL
═══════════════════════════════════════════════ */
#app-shell {{
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}}

/* ─── Top toolbar ─── */
#top-bar {{
  height: var(--header-h);
  flex-shrink: 0;
  background: var(--bg2);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  padding: 0 12px;
  gap: 6px;
  z-index: 30;
  overflow: hidden;
}}
#top-bar-title {{
  font-family: var(--serif);
  font-size: 15px;
  color: var(--gold);
  white-space: nowrap;
  margin-right: 6px;
}}
#save-indicator {{
  font-size: 11px;
  font-family: var(--mono);
  color: var(--text3);
  background: var(--bg3);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 3px 10px;
  transition: all 0.25s;
  white-space: nowrap;
  margin-left: auto;
  flex-shrink: 0;
}}
#save-indicator.saving {{ color: var(--gold);  border-color: var(--gold);  }}
#save-indicator.saved  {{ color: var(--green); border-color: var(--green); }}
#save-indicator.error  {{ color: var(--coral); border-color: var(--coral); }}

/* ─── Main content area ─── */
#main-area {{
  display: flex;
  flex: 1;
  overflow: hidden;
  position: relative;
}}

/* ─── Canvas wrapper ─── */
#canvas-wrap {{
  flex: 1;
  position: relative;
  overflow: hidden;
  background: var(--bg);
  background-image: radial-gradient(circle at 50% 50%, rgba(108,143,255,0.03) 0%, transparent 70%);
}}
#canvas-wrap::before {{
  content: '';
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(120,130,200,0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(120,130,200,0.04) 1px, transparent 1px);
  background-size: 36px 36px;
  pointer-events: none;
}}
#cld-canvas {{
  position: absolute;
  inset: 0;
  transform-origin: 0 0;
  will-change: transform;
}}
#cld-svg {{
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  overflow: visible;
}}

/* ─── Bottom toolbar (canvas controls) ─── */
#canvas-toolbar {{
  position: absolute;
  bottom: 12px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(19, 22, 42, 0.92);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  border: 1px solid var(--border2);
  border-radius: 40px;
  padding: 5px 10px;
  display: flex;
  gap: 3px;
  align-items: center;
  z-index: 20;
  box-shadow: 0 4px 24px rgba(0,0,0,0.4);
  max-width: calc(100% - 24px);
  overflow-x: auto;
  scrollbar-width: none;
}}
#canvas-toolbar::-webkit-scrollbar {{ display: none; }}

.tool-btn {{
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  padding: 7px 11px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--text2);
  font-size: 12px;
  font-family: var(--sans);
  cursor: pointer;
  border-radius: 24px;
  transition: all 0.15s;
  white-space: nowrap;
  min-height: 36px;
  /* Touch target */
  min-width: 36px;
}}
.tool-btn:hover  {{ background: var(--surface); color: var(--text); }}
.tool-btn.active {{ background: var(--surf2); border-color: var(--accent); color: var(--accent); }}
.tool-btn.danger:hover {{ background: rgba(224,96,96,0.12); color: var(--coral); border-color: var(--coral); }}
.tool-sep {{ width: 1px; height: 18px; background: var(--border); flex-shrink: 0; }}

/* ─── Zoom hint chip ─── */
#zoom-chip {{
  position: absolute;
  top: 10px;
  left: 10px;
  font-size: 11px;
  font-family: var(--mono);
  color: var(--text3);
  background: rgba(19,22,42,0.7);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 3px 9px;
  pointer-events: none;
  z-index: 10;
  transition: opacity 0.3s;
}}

/* ═══════════════════════════════════════════════
   NODES
═══════════════════════════════════════════════ */
.cld-node {{
  position: absolute;
  cursor: grab;
  user-select: none;
  transform: translate(-50%, -50%);
  z-index: 5;
  touch-action: none;
}}
.cld-node:active {{ cursor: grabbing; }}

.node-box {{
  padding: 7px 13px;
  border-radius: 10px;
  border: 1.5px solid;
  font-size: 11.5px;
  font-family: var(--sans);
  font-weight: 500;
  white-space: nowrap;
  transition: transform 0.12s, box-shadow 0.12s;
  text-align: center;
  min-width: 80px;
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}}
.cld-node:hover  .node-box {{ transform: scale(1.05); }}
.cld-node.selected .node-box {{
  box-shadow: 0 0 0 3px rgba(108,143,255,0.5), 0 0 20px rgba(108,143,255,0.2);
}}
.cld-node.linking-source .node-box {{
  box-shadow: 0 0 0 3px rgba(232,169,74,0.6), 0 0 20px rgba(232,169,74,0.2);
  animation: pulse-gold 0.9s ease-in-out infinite;
}}
@keyframes pulse-gold {{
  0%, 100% {{ box-shadow: 0 0 0 3px rgba(232,169,74,0.6), 0 0 20px rgba(232,169,74,0.15); }}
  50%       {{ box-shadow: 0 0 0 6px rgba(232,169,74,0.3), 0 0 30px rgba(232,169,74,0.08); }}
}}

/* Category colours */
.cat-estado    {{ background: rgba(14,26,80,0.88);   border-color: #4a6aee; color: #a0b4ff; }}
.cat-equacao   {{ background: rgba(80,14,14,0.88);   border-color: #c04040; color: #ffb0b0; }}
.cat-parametro {{ background: rgba(20,14,60,0.88);   border-color: #6040c0; color: #c0a8ff; }}
.cat-ambiente  {{ background: rgba(14,50,40,0.88);   border-color: #208060; color: #80ffcc; }}
.cat-input     {{ background: rgba(70,30,8,0.88);    border-color: #c06020; color: #ffc080; }}

/* ═══════════════════════════════════════════════
   RIGHT DETAIL PANEL
═══════════════════════════════════════════════ */
#right-panel {{
  width: var(--panel-w);
  flex-shrink: 0;
  background: var(--bg2);
  border-left: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: width 0.3s cubic-bezier(.4,0,.2,1);
}}
#right-panel.collapsed {{
  width: 0;
  border-left: none;
}}

.panel-header {{
  padding: 12px 14px 10px;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  flex-shrink: 0;
}}
.panel-title {{
  font-family: var(--serif);
  font-size: 15px;
  color: var(--gold);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}}
#panel-mode-badge {{
  font-size: 10px;
  font-family: var(--mono);
  letter-spacing: 1px;
  color: var(--text3);
  white-space: nowrap;
}}
.panel-close-btn {{
  background: transparent;
  border: none;
  color: var(--text3);
  cursor: pointer;
  font-size: 16px;
  line-height: 1;
  padding: 4px;
  border-radius: 6px;
  flex-shrink: 0;
  min-width: 28px;
  min-height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
}}
.panel-close-btn:hover {{ background: var(--surface); color: var(--text); }}

.panel-body {{
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 14px;
  scrollbar-width: thin;
  scrollbar-color: var(--border2) transparent;
}}
.panel-body::-webkit-scrollbar {{ width: 4px; }}
.panel-body::-webkit-scrollbar-thumb {{ background: var(--border2); border-radius: 2px; }}

.panel-legend {{
  padding: 10px 14px;
  border-top: 1px solid var(--border);
  flex-shrink: 0;
}}
.legend-title {{
  font-size: 10px;
  color: var(--text3);
  text-transform: uppercase;
  letter-spacing: 1px;
  font-family: var(--mono);
  margin-bottom: 7px;
}}
.legend-grid {{
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 5px;
}}
.legend-item {{
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  color: var(--text2);
}}
.legend-dot {{
  width: 9px;
  height: 9px;
  border-radius: 3px;
  border: 1.5px solid;
  flex-shrink: 0;
}}

/* Detail panel internals */
.node-detail-name {{
  font-family: var(--serif);
  font-size: 17px;
  color: var(--text);
  margin-bottom: 3px;
  line-height: 1.2;
  word-break: break-word;
}}
.node-detail-cat {{
  font-size: 10px;
  font-family: var(--mono);
  letter-spacing: 1.2px;
  text-transform: uppercase;
  margin-bottom: 12px;
}}
.detail-label {{
  font-size: 10px;
  color: var(--text3);
  text-transform: uppercase;
  letter-spacing: 0.8px;
  margin: 12px 0 4px;
  font-family: var(--mono);
}}
.detail-val {{
  font-family: var(--mono);
  font-size: 13px;
  color: var(--gold);
}}
.detail-desc {{
  font-size: 12.5px;
  color: var(--text2);
  line-height: 1.6;
}}
.detail-eq {{
  font-family: var(--mono);
  font-size: 11.5px;
  color: var(--teal);
  background: var(--bg3);
  padding: 8px 10px;
  border-radius: 6px;
  border-left: 2px solid var(--teal);
  word-break: break-all;
  line-height: 1.6;
}}
.relation-item {{
  background: var(--bg3);
  border-radius: 7px;
  padding: 7px 10px;
  margin-bottom: 5px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}}
.rel-sign {{
  font-weight: 700;
  font-size: 13px;
  padding: 1px 6px;
  border-radius: 4px;
  flex-shrink: 0;
}}
.rel-pos {{ color: var(--green); background: rgba(82,201,122,0.12); }}
.rel-neg {{ color: var(--coral); background: rgba(224,96,96,0.12);  }}
.detail-actions {{
  margin-top: 16px;
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}}

.placeholder-msg {{
  color: var(--text3);
  font-size: 13px;
  line-height: 1.7;
  text-align: center;
  padding: 40px 12px 20px;
}}
.placeholder-msg .ico {{ font-size: 30px; margin-bottom: 10px; }}

/* ═══════════════════════════════════════════════
   MOBILE PANEL TOGGLE BUTTON (FAB)
═══════════════════════════════════════════════ */
#panel-fab {{
  display: none;
  position: absolute;
  bottom: 80px;
  right: 14px;
  z-index: 25;
  background: var(--accent2);
  color: #fff;
  border: none;
  border-radius: 50%;
  width: 50px;
  height: 50px;
  font-size: 20px;
  cursor: pointer;
  box-shadow: 0 4px 16px rgba(0,0,0,0.4);
  align-items: center;
  justify-content: center;
  transition: transform 0.15s, background 0.15s;
}}
#panel-fab:hover {{ background: var(--accent); transform: scale(1.08); }}
#panel-fab.has-node {{ background: var(--gold); color: #000; }}

/* Mobile drawer overlay */
#drawer-backdrop {{
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(5,7,20,0.7);
  z-index: 99;
  backdrop-filter: blur(2px);
  -webkit-backdrop-filter: blur(2px);
}}

/* ═══════════════════════════════════════════════
   MODALS
═══════════════════════════════════════════════ */
.modal-overlay {{
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(5,7,20,0.82);
  z-index: 200;
  align-items: flex-end;           /* sheet-style on mobile */
  justify-content: center;
  backdrop-filter: blur(5px);
  -webkit-backdrop-filter: blur(5px);
}}
.modal-overlay.open {{ display: flex; }}

.modal {{
  background: var(--bg2);
  border: 1px solid var(--border2);
  width: 100%;
  max-width: 500px;
  max-height: 85dvh;
  overflow-y: auto;
  padding: 22px 20px 28px;
  border-radius: 18px 18px 0 0;
  animation: slide-up 0.22s cubic-bezier(.4,0,.2,1);
}}
@keyframes slide-up {{
  from {{ transform: translateY(40px); opacity: 0; }}
  to   {{ transform: translateY(0);    opacity: 1; }}
}}
/* On larger screens: centered dialog */
@media (min-width: 600px) {{
  .modal-overlay {{ align-items: center; }}
  .modal {{
    border-radius: 14px;
    padding: 24px;
    max-width: 480px;
    width: 90%;
    animation: fade-scale 0.2s cubic-bezier(.4,0,.2,1);
  }}
  @keyframes fade-scale {{
    from {{ transform: scale(0.96); opacity: 0; }}
    to   {{ transform: scale(1);    opacity: 1; }}
  }}
}}

/* Modal drag handle */
.modal::before {{
  content: '';
  display: block;
  width: 36px;
  height: 4px;
  background: var(--border2);
  border-radius: 2px;
  margin: 0 auto 18px;
}}
@media (min-width: 600px) {{ .modal::before {{ display: none; }} }}

.modal-title {{
  font-family: var(--serif);
  font-size: 20px;
  color: var(--gold);
  margin-bottom: 3px;
}}
.modal-sub {{
  font-size: 12px;
  color: var(--text3);
  margin-bottom: 18px;
}}

.form-row {{ margin-bottom: 13px; }}
.form-label {{
  display: block;
  font-size: 10px;
  color: var(--text3);
  text-transform: uppercase;
  letter-spacing: 0.8px;
  font-family: var(--mono);
  margin-bottom: 5px;
}}
.form-input,
.form-select,
.form-textarea {{
  width: 100%;
  background: var(--bg3);
  border: 1px solid var(--border2);
  border-radius: 8px;
  color: var(--text);
  font-family: var(--sans);
  font-size: 14px;
  padding: 9px 11px;
  outline: none;
  transition: border 0.15s;
  -webkit-appearance: none;
  appearance: none;
}}
.form-input:focus,
.form-select:focus,
.form-textarea:focus {{ border-color: var(--accent); }}
.form-textarea {{
  resize: vertical;
  min-height: 64px;
  font-family: var(--mono);
  font-size: 13px;
}}
.modal-actions {{
  display: flex;
  gap: 9px;
  justify-content: flex-end;
  margin-top: 20px;
  flex-wrap: wrap;
}}
.btn-cancel {{
  flex: 0 0 auto;
  padding: 10px 16px;
  border: 1px solid var(--border2);
  background: transparent;
  color: var(--text2);
  font-family: var(--sans);
  font-size: 13px;
  cursor: pointer;
  border-radius: 8px;
  min-height: 44px;
  transition: all 0.15s;
}}
.btn-cancel:hover {{ background: var(--surface); color: var(--text); }}
.btn-primary {{
  flex: 1 1 auto;
  padding: 10px 18px;
  border: none;
  background: var(--accent2);
  color: #fff;
  font-family: var(--sans);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  border-radius: 8px;
  min-height: 44px;
  transition: background 0.15s;
}}
.btn-primary:hover {{ background: var(--accent); }}
.btn-icon-sm {{
  padding: 8px 12px;
  border: 1px solid var(--border2);
  background: var(--bg3);
  color: var(--text2);
  font-family: var(--sans);
  font-size: 12px;
  cursor: pointer;
  border-radius: 7px;
  min-height: 36px;
  transition: all 0.15s;
  white-space: nowrap;
}}
.btn-icon-sm:hover {{ background: var(--surf2); color: var(--text); }}
.btn-danger-sm {{
  padding: 8px 12px;
  border: 1px solid rgba(224,96,96,0.25);
  background: rgba(224,96,96,0.06);
  color: var(--coral);
  font-family: var(--sans);
  font-size: 12px;
  cursor: pointer;
  border-radius: 7px;
  min-height: 36px;
  transition: all 0.15s;
  white-space: nowrap;
}}
.btn-danger-sm:hover {{ background: rgba(224,96,96,0.15); border-color: var(--coral); }}

.link-hint {{
  background: rgba(232,169,74,0.08);
  border: 1px solid rgba(232,169,74,0.25);
  border-radius: 8px;
  padding: 9px 13px;
  font-size: 12px;
  color: var(--gold);
  margin-bottom: 14px;
  line-height: 1.6;
}}

/* Scrollbar */
::-webkit-scrollbar {{ width: 5px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{ background: var(--border2); border-radius: 3px; }}


/* ═══════════════════════════════════════════════
   RESPONSIVE OVERRIDES
═══════════════════════════════════════════════ */

/* Medium screens: narrower panel */
@media (max-width: 900px) and (min-width: 601px) {{
  :root {{ --panel-w: 260px; }}
  .node-box {{ font-size: 11px; padding: 6px 10px; min-width: 70px; }}
}}

/* Mobile: panel becomes a bottom drawer */
@media (max-width: 600px) {{
  :root {{ --panel-w: 0px; --toolbar-h: 52px; }}

  #right-panel {{
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    width: 100% !important;
    height: 60dvh;
    border-left: none;
    border-top: 1px solid var(--border2);
    border-radius: 18px 18px 0 0;
    z-index: 100;
    transform: translateY(100%);
    transition: transform 0.32s cubic-bezier(.4,0,.2,1);
    box-shadow: 0 -8px 32px rgba(0,0,0,0.5);
  }}
  #right-panel.open {{
    transform: translateY(0);
  }}

  #panel-fab {{ display: flex; }}
  #drawer-backdrop.open {{ display: block; }}

  /* Handle bar for the drawer */
  #right-panel .panel-header::before {{
    content: '';
    display: block;
    width: 36px;
    height: 4px;
    background: var(--border2);
    border-radius: 2px;
    position: absolute;
    top: 8px;
    left: 50%;
    transform: translateX(-50%);
  }}
  #right-panel .panel-header {{
    position: relative;
    padding-top: 20px;
  }}

  #canvas-toolbar {{
    bottom: 10px;
    border-radius: 28px;
    padding: 4px 8px;
    gap: 2px;
  }}
  .tool-btn {{
    font-size: 11px;
    padding: 6px 9px;
    min-height: 34px;
    min-width: 34px;
  }}
  .node-box {{
    font-size: 10.5px;
    padding: 6px 10px;
    min-width: 72px;
    border-radius: 8px;
  }}
  #top-bar-title {{ font-size: 13px; }}
  #zoom-chip {{ font-size: 10px; padding: 2px 7px; }}
}}
</style>
</head>
<body>
<div id="app-shell">

  <!-- ══ TOP BAR ══ -->
  <div id="top-bar">
    <span id="top-bar-title">⬡ LUMINA</span>
    <span class="tool-sep" style="margin:0 4px;"></span>
    <button class="tool-btn active" id="tool-select" onclick="setTool('select')" title="Selecionar (S)">⬚</button>
    <button class="tool-btn" onclick="openAddNodeModal()" title="Novo Nó (N)">＋ Nó</button>
    <button class="tool-btn" id="tool-link" onclick="setTool('link')" title="Criar Ligação (L)">→ Link</button>
    <span class="tool-sep" style="margin:0 4px;"></span>
    <button class="tool-btn" onclick="zoomReset()" title="Centralizar (R)">◎</button>
    <button class="tool-btn danger" onclick="deleteSelected()" title="Excluir selecionado (Del)">✕</button>
    <div id="save-indicator">pronto</div>
  </div>

  <!-- ══ MAIN AREA ══ -->
  <div id="main-area">

    <!-- Canvas -->
    <div id="canvas-wrap">
      <div id="zoom-chip" id="zoom-info">75%</div>
      <div id="cld-canvas"></div>
      <svg id="cld-svg"></svg>

      <!-- Bottom toolbar -->
      <div id="canvas-toolbar">
        <button class="tool-btn" onclick="zoomIn()" title="Zoom +">＋</button>
        <button class="tool-btn" onclick="zoomOut()" title="Zoom −">－</button>
        <div class="tool-sep"></div>
        <button class="tool-btn" onclick="zoomReset()">◎ Centralizar</button>
        <div class="tool-sep"></div>
        <button class="tool-btn" onclick="togglePanel()" id="toggle-panel-btn">◧ Painel</button>
      </div>

      <!-- Mobile FAB -->
      <button id="panel-fab" onclick="openDrawer()" title="Detalhes">📋</button>
    </div>

    <!-- Detail panel -->
    <div id="right-panel">
      <div class="panel-header">
        <span class="panel-title">Detalhes</span>
        <span id="panel-mode-badge">SELECIONAR</span>
        <button class="panel-close-btn" onclick="closeDrawer()" title="Fechar painel">✕</button>
      </div>
      <div class="panel-body" id="detail-content">
        <div class="placeholder-msg">
          <div class="ico">⬡</div>
          <p>Clique em um nó para ver seus detalhes, relações e equação.</p>
        </div>
      </div>
      <div class="panel-legend">
        <div class="legend-title">Categorias</div>
        <div class="legend-grid">
          <div class="legend-item"><div class="legend-dot" style="background:rgba(14,26,80,0.9);border-color:#4a6aee"></div>Estado</div>
          <div class="legend-item"><div class="legend-dot" style="background:rgba(80,14,14,0.9);border-color:#c04040"></div>Equação</div>
          <div class="legend-item"><div class="legend-dot" style="background:rgba(20,14,60,0.9);border-color:#6040c0"></div>Parâmetro</div>
          <div class="legend-item"><div class="legend-dot" style="background:rgba(14,50,40,0.9);border-color:#208060"></div>Ambiente</div>
          <div class="legend-item"><div class="legend-dot" style="background:rgba(70,30,8,0.9);border-color:#c06020"></div>Input</div>
        </div>
      </div>
    </div>
  </div>
</div>

<!-- Drawer backdrop (mobile) -->
<div id="drawer-backdrop" onclick="closeDrawer()"></div>

<!-- ══ MODALS ══ -->

<!-- Add Node -->
<div class="modal-overlay" id="modal-add-node">
  <div class="modal">
    <div class="modal-title">Novo Nó</div>
    <div class="modal-sub">Crie uma nova variável no sistema</div>
    <div class="form-row"><label class="form-label">Nome *</label><input class="form-input" id="new-node-name" placeholder="ex: Taxa_Adocao"></div>
    <div class="form-row"><label class="form-label">Categoria</label>
      <select class="form-select" id="new-node-cat">
        <option value="Estado">Estado</option>
        <option value="Equação">Equação</option>
        <option value="Parâmetro">Parâmetro</option>
        <option value="Ambiente">Ambiente</option>
        <option value="Input">Input</option>
      </select>
    </div>
    <div class="form-row"><label class="form-label">Valor Inicial</label><input class="form-input" id="new-node-val" type="number" value="0" step="any"></div>
    <div class="form-row"><label class="form-label">Equação (opcional)</label><textarea class="form-textarea" id="new-node-eq" placeholder="ex: A * B + C"></textarea></div>
    <div class="form-row"><label class="form-label">Descrição</label><textarea class="form-textarea" id="new-node-desc" placeholder="Descreva o papel desta variável..."></textarea></div>
    <div class="modal-actions">
      <button class="btn-cancel" onclick="closeModal('modal-add-node')">Cancelar</button>
      <button class="btn-primary" onclick="addNode()">Criar Nó</button>
    </div>
  </div>
</div>

<!-- Edit Node -->
<div class="modal-overlay" id="modal-edit-node">
  <div class="modal">
    <div class="modal-title">Editar Variável</div>
    <div class="modal-sub">Altere os atributos da variável selecionada</div>
    <input type="hidden" id="edit-node-id">
    <div class="form-row"><label class="form-label">Nome</label><input class="form-input" id="edit-node-name"></div>
    <div class="form-row"><label class="form-label">Categoria</label>
      <select class="form-select" id="edit-node-cat">
        <option value="Estado">Estado</option>
        <option value="Equação">Equação</option>
        <option value="Parâmetro">Parâmetro</option>
        <option value="Ambiente">Ambiente</option>
        <option value="Input">Input</option>
      </select>
    </div>
    <div class="form-row"><label class="form-label">Valor Atual</label><input class="form-input" id="edit-node-val" type="number" step="any"></div>
    <div class="form-row"><label class="form-label">Equação</label><textarea class="form-textarea" id="edit-node-eq"></textarea></div>
    <div class="form-row"><label class="form-label">Descrição</label><textarea class="form-textarea" id="edit-node-desc"></textarea></div>
    <div class="modal-actions">
      <button class="btn-cancel" onclick="closeModal('modal-edit-node')">Cancelar</button>
      <button class="btn-primary" onclick="saveEditNode()">Salvar</button>
    </div>
  </div>
</div>

<!-- Add Link -->
<div class="modal-overlay" id="modal-add-link">
  <div class="modal">
    <div class="modal-title">Nova Ligação</div>
    <div class="modal-sub">Defina a relação causal entre variáveis</div>
    <div class="link-hint" id="link-hint-text">Selecione a origem e o destino da ligação.</div>
    <div class="form-row"><label class="form-label">De (Origem)</label><input class="form-input" id="link-from" readonly></div>
    <div class="form-row"><label class="form-label">Para (Destino)</label><select class="form-select" id="link-to"></select></div>
    <div class="form-row"><label class="form-label">Sinal da Relação</label>
      <select class="form-select" id="link-sign">
        <option value="+">＋ Positiva — A aumenta, B aumenta</option>
        <option value="-">－ Negativa — A aumenta, B diminui</option>
      </select>
    </div>
    <div class="form-row"><label class="form-label">Descrição (opcional)</label><textarea class="form-textarea" id="link-desc" placeholder="ex: Maior preço reduz o volume vendido"></textarea></div>
    <div class="modal-actions">
      <button class="btn-cancel" onclick="closeModal('modal-add-link')">Cancelar</button>
      <button class="btn-primary" onclick="confirmLink()">Criar Ligação</button>
    </div>
  </div>
</div>

<!-- ══ JAVASCRIPT ══ -->
<script>
/* ─── Config ─── */
const JSONBIN_API_KEY = {ak};
const JSONBIN_BIN_ID  = {bi};
let SYSTEM = {model_json};

/* ─── State ─── */
let selectedNode = null;
let linkSource   = null;
let currentTool  = 'select';
let isDragging   = false;
let dragNode     = null;
let dragOffX     = 0, dragOffY = 0;
let panX = 60, panY = 60, scale = 0.75;
let isPanning   = false;
let panStartX   = 0, panStartY = 0;
let saveTimer   = null;
let panelOpen   = true;  // desktop: open by default
let isMobile    = false;

const catClass = {{
  Estado:'cat-estado', Equação:'cat-equacao',
  Parâmetro:'cat-parametro', Ambiente:'cat-ambiente', Input:'cat-input'
}};
const catColor = {{
  Estado:'#6a8aff', Equação:'#ff9090',
  Parâmetro:'#c090ff', Ambiente:'#60ffa0', Input:'#ffb060'
}};

/* ─── Responsive detection ─── */
function detectMobile() {{
  isMobile = window.innerWidth <= 600;
  // On mobile, panel starts closed
  if (isMobile) {{
    panelOpen = false;
    document.getElementById('right-panel').classList.remove('open');
    document.getElementById('panel-fab').style.display = 'flex';
    document.getElementById('toggle-panel-btn').style.display = 'none';
  }} else {{
    panelOpen = true;
    document.getElementById('right-panel').classList.remove('open');
    document.getElementById('right-panel').classList.remove('collapsed');
    document.getElementById('panel-fab').style.display = 'none';
    document.getElementById('toggle-panel-btn').style.display = '';
    if (!panelOpen) document.getElementById('right-panel').classList.add('collapsed');
  }}
  renderAll();
}}

/* ─── Panel / Drawer ─── */
function openDrawer() {{
  document.getElementById('right-panel').classList.add('open');
  document.getElementById('drawer-backdrop').classList.add('open');
  panelOpen = true;
}}
function closeDrawer() {{
  if (isMobile) {{
    document.getElementById('right-panel').classList.remove('open');
    document.getElementById('drawer-backdrop').classList.remove('open');
    panelOpen = false;
  }} else {{
    collapsePanel();
  }}
}}
function togglePanel() {{
  if (isMobile) {{
    panelOpen ? closeDrawer() : openDrawer();
  }} else {{
    panelOpen ? collapsePanel() : expandPanel();
  }}
}}
function expandPanel() {{
  document.getElementById('right-panel').classList.remove('collapsed');
  document.getElementById('toggle-panel-btn').textContent = '◨ Painel';
  panelOpen = true;
}}
function collapsePanel() {{
  document.getElementById('right-panel').classList.add('collapsed');
  document.getElementById('toggle-panel-btn').textContent = '◧ Painel';
  panelOpen = false;
}}

/* ─── Persist ─── */
function setIndicator(cls, msg) {{
  const el = document.getElementById('save-indicator');
  el.className = cls; el.textContent = msg;
}}
async function persistToCloud() {{
  if (!JSONBIN_API_KEY || !JSONBIN_BIN_ID) {{ setIndicator('', 'sem credenciais'); return; }}
  setIndicator('saving', '⏳ salvando…');
  try {{
    const r = await fetch(`https://api.jsonbin.io/v3/b/${{JSONBIN_BIN_ID}}`, {{
      method: 'PUT',
      headers: {{'Content-Type':'application/json','X-Master-Key':JSONBIN_API_KEY}},
      body: JSON.stringify(SYSTEM)
    }});
    if (r.ok) {{
      setIndicator('saved', '✓ salvo');
      setTimeout(() => setIndicator('', 'pronto'), 2500);
    }} else {{
      setIndicator('error', '✗ erro ' + r.status);
    }}
  }} catch(e) {{
    setIndicator('error', '✗ sem conexão');
  }}
}}
function scheduleSave() {{
  clearTimeout(saveTimer);
  saveTimer = setTimeout(persistToCloud, 700);
}}

/* ─── Zoom ─── */
function updateZoomChip() {{
  document.getElementById('zoom-chip').textContent = Math.round(scale * 100) + '%';
}}
function applyTransform() {{
  document.getElementById('cld-canvas').style.transform = `translate(${{panX}}px,${{panY}}px) scale(${{scale}})`;
  updateZoomChip();
  renderEdges();
}}
function zoomIn()   {{ setScale(Math.min(2.5, scale * 1.15)); }}
function zoomOut()  {{ setScale(Math.max(0.25, scale * 0.87)); }}
function setScale(ns, cx, cy) {{
  const wrap = document.getElementById('canvas-wrap');
  const mx = cx ?? wrap.clientWidth  / 2;
  const my = cy ?? wrap.clientHeight / 2;
  panX = mx - (mx - panX) * (ns / scale);
  panY = my - (my - panY) * (ns / scale);
  scale = ns;
  applyTransform();
}}
function zoomReset() {{
  scale = 0.75; panX = 60; panY = 60;
  applyTransform();
  renderAll();
}}

/* ─── Render ─── */
function renderAll() {{
  const canvas = document.getElementById('cld-canvas');
  canvas.innerHTML = '';
  canvas.style.transformOrigin = '0 0';
  canvas.style.transform = `translate(${{panX}}px,${{panY}}px) scale(${{scale}})`;
  for (const [id, node] of Object.entries(SYSTEM.nodes)) {{
    const el = document.createElement('div');
    el.className = 'cld-node';
    el.id = 'node-' + id;
    el.style.left = node.x + 'px';
    el.style.top  = node.y + 'px';
    el.innerHTML  = `<div class="node-box ${{catClass[node.cat] || 'cat-estado'}}">${{id}}</div>`;
    if (selectedNode === id) el.classList.add('selected');
    if (linkSource   === id) el.classList.add('linking-source');
    el.addEventListener('mousedown',  e => onNodePointerDown(e, id, false));
    el.addEventListener('touchstart', e => {{ e.preventDefault(); onNodePointerDown(e, id, true); }}, {{passive: false}});
    el.addEventListener('click',      e => onNodeClick(e, id));
    el.addEventListener('touchend',   e => {{ e.preventDefault(); onNodeClick(e, id); }});
    canvas.appendChild(el);
  }}
  renderEdges();
  updateZoomChip();
}}

function renderEdges() {{
  const svg  = document.getElementById('cld-svg');
  const wrap = document.getElementById('canvas-wrap');
  const W    = wrap.clientWidth;
  const H    = wrap.clientHeight;
  svg.setAttribute('viewBox', `0 0 ${{W}} ${{H}}`);
  svg.setAttribute('width',  W);
  svg.setAttribute('height', H);
  svg.innerHTML = `<defs>
    <marker id="arr-pos" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M1 2L9 5L1 8" fill="none" stroke="#52c97a" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
    </marker>
    <marker id="arr-neg" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M1 2L9 5L1 8" fill="none" stroke="#e06060" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
    </marker>
  </defs>`;

  for (const link of SYSTEM.links) {{
    const fn = SYSTEM.nodes[link.from];
    const tn = SYSTEM.nodes[link.to];
    if (!fn || !tn) continue;
    const fEl = document.getElementById('node-' + link.from);
    const tEl = document.getElementById('node-' + link.to);
    if (!fEl || !tEl) continue;

    const fw = fEl.offsetWidth  || 90;
    const fh = fEl.offsetHeight || 30;
    const tw = tEl.offsetWidth  || 90;
    const th = tEl.offsetHeight || 30;

    const fx = fn.x * scale + panX;
    const fy = fn.y * scale + panY;
    const tx = tn.x * scale + panX;
    const ty = tn.y * scale + panY;

    const dx   = tx - fx;
    const dy   = ty - fy;
    const dist = Math.sqrt(dx*dx + dy*dy) || 1;
    const ux   = dx / dist;
    const uy   = dy / dist;

    const x1 = fx + ux * (fw * scale / 2 + 2);
    const y1 = fy + uy * (fh * scale / 2 + 2);
    const x2 = tx - ux * (tw * scale / 2 + 6);
    const y2 = ty - uy * (th * scale / 2 + 6);

    const cx = (x1 + x2) / 2 - uy * 20;
    const cy = (y1 + y2) / 2 + ux * 20;

    const color = link.sign === '+' ? '#52c97a' : '#e06060';
    const markId = link.sign === '+' ? 'arr-pos' : 'arr-neg';

    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', `M${{x1}},${{y1}} Q${{cx}},${{cy}} ${{x2}},${{y2}}`);
    path.setAttribute('fill',          'none');
    path.setAttribute('stroke',        color);
    path.setAttribute('stroke-width',  '1.5');
    path.setAttribute('stroke-opacity','0.65');
    path.setAttribute('marker-end',    `url(#${{markId}})`);

    const lbl = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    lbl.setAttribute('x',            cx);
    lbl.setAttribute('y',            cy - 5);
    lbl.setAttribute('text-anchor',  'middle');
    lbl.setAttribute('font-size',    '11');
    lbl.setAttribute('font-family',  'DM Mono, monospace');
    lbl.setAttribute('font-weight',  '700');
    lbl.setAttribute('fill',         color);
    lbl.setAttribute('opacity',      '0.9');
    lbl.textContent = link.sign;

    svg.appendChild(path);
    svg.appendChild(lbl);
  }}
}}

/* ─── Pointer interactions ─── */
function getPointerXY(e) {{
  if (e.touches && e.touches.length > 0) return [e.touches[0].clientX, e.touches[0].clientY];
  if (e.changedTouches && e.changedTouches.length > 0) return [e.changedTouches[0].clientX, e.changedTouches[0].clientY];
  return [e.clientX, e.clientY];
}}

function onNodePointerDown(e, id, isTouch) {{
  if (currentTool !== 'select') return;
  e.stopPropagation();
  isDragging = false;
  dragNode   = id;
  const [cx, cy] = getPointerXY(e);
  const rect = document.getElementById('canvas-wrap').getBoundingClientRect();
  dragOffX = (cx - rect.left - panX) / scale - SYSTEM.nodes[id].x;
  dragOffY = (cy - rect.top  - panY) / scale - SYSTEM.nodes[id].y;
}}

function onNodeClick(e, id) {{
  if (isDragging) return;
  e.stopPropagation();
  if (currentTool === 'link') {{
    if (!linkSource) {{
      // first click: set source
      linkSource = id;
      document.getElementById('node-' + id)?.classList.add('linking-source');
      document.getElementById('link-hint-text').textContent = `Origem: "${{id}}" — agora selecione o destino ou use o formulário abaixo.`;
      document.getElementById('link-from').value = id;
      populateLinkToSelect(id);
      openModal('modal-add-link');
    }} else if (linkSource !== id) {{
      // second click: set target and confirm
      document.getElementById('link-to').value = id;
      confirmLink();
    }}
    return;
  }}
  selectNode(id);
}}

function selectNode(id) {{
  document.querySelectorAll('.cld-node').forEach(el => el.classList.remove('selected'));
  selectedNode = id;
  document.getElementById('node-' + id)?.classList.add('selected');
  renderDetailPanel(id);
  // Update FAB style
  const fab = document.getElementById('panel-fab');
  fab.classList.add('has-node');
  if (isMobile) openDrawer();
}}

function deselectAll() {{
  document.querySelectorAll('.cld-node').forEach(el => el.classList.remove('selected'));
  selectedNode = null;
  document.getElementById('detail-content').innerHTML =
    '<div class="placeholder-msg"><div class="ico">⬡</div><p>Clique em um nó para ver seus detalhes.</p></div>';
  document.getElementById('panel-fab').classList.remove('has-node');
}}

function populateLinkToSelect(excludeId) {{
  document.getElementById('link-to').innerHTML =
    Object.keys(SYSTEM.nodes)
      .filter(n => n !== excludeId)
      .map(n => `<option value="${{n}}">${{n}}</option>`)
      .join('');
}}

/* ─── Detail panel ─── */
function renderDetailPanel(id) {{
  const node = SYSTEM.nodes[id];
  if (!node) return;
  const out = SYSTEM.links.filter(l => l.from === id);
  const inc = SYSTEM.links.filter(l => l.to   === id);
  const col = catColor[node.cat] || '#aaa';

  let h = `
    <div class="node-detail-name">${{id}}</div>
    <div class="node-detail-cat" style="color:${{col}}">${{node.cat}}</div>
    <div class="detail-label">Descrição</div>
    <div class="detail-desc">${{node.desc || '—'}}</div>
    <div class="detail-label">Valor Atual</div>
    <div class="detail-val">${{typeof node.val === 'number' ? node.val.toPrecision(6).replace(/\.?0+$/, '') : node.val}}</div>
  `;
  if (node.expr) h += `<div class="detail-label">Equação</div><div class="detail-eq">${{node.expr}}</div>`;

  if (inc.length) {{
    h += `<div class="detail-label">Causas (${{inc.length}})</div>`;
    inc.forEach(l => h += `
      <div class="relation-item">
        <span class="rel-sign ${{l.sign === '+' ? 'rel-pos' : 'rel-neg'}}">${{l.sign}}</span>
        <span style="color:var(--text2)">${{l.from}}</span>
      </div>`);
  }}
  if (out.length) {{
    h += `<div class="detail-label">Efeitos (${{out.length}})</div>`;
    out.forEach(l => h += `
      <div class="relation-item">
        <span class="rel-sign ${{l.sign === '+' ? 'rel-pos' : 'rel-neg'}}">${{l.sign}}</span>
        <span style="color:var(--text2)">${{l.to}}</span>
      </div>`);
  }}

  h += `
    <div class="detail-actions">
      <button class="btn-icon-sm" onclick="openEditNodeModal('${{id}}')">✎ Editar</button>
      <button class="btn-icon-sm" onclick="openLinkFromSelected()">+ Ligação</button>
      <button class="btn-danger-sm" onclick="deleteNode('${{id}}')">✕ Excluir</button>
    </div>`;

  document.getElementById('detail-content').innerHTML = h;
}}

/* ─── Pan & drag ─── */
const wrap = document.getElementById('canvas-wrap');

function onCanvasPointerDown(e) {{
  const target = e.target;
  if (target === wrap || target.id === 'cld-svg' || target.closest('#cld-svg') === document.getElementById('cld-svg')) {{
    isPanning = true;
    const [cx, cy] = getPointerXY(e);
    panStartX = cx - panX;
    panStartY = cy - panY;
    deselectAll();
    if (isMobile) closeDrawer();
  }}
}}

wrap.addEventListener('mousedown',  onCanvasPointerDown);
wrap.addEventListener('touchstart', e => {{ e.preventDefault(); onCanvasPointerDown(e); }}, {{passive: false}});

function onGlobalMove(e) {{
  const [cx, cy] = getPointerXY(e);
  if (dragNode) {{
    const rect = wrap.getBoundingClientRect();
    SYSTEM.nodes[dragNode].x = (cx - rect.left - panX) / scale - dragOffX;
    SYSTEM.nodes[dragNode].y = (cy - rect.top  - panY) / scale - dragOffY;
    isDragging = true;
    renderAll();
  }} else if (isPanning) {{
    panX = cx - panStartX;
    panY = cy - panStartY;
    document.getElementById('cld-canvas').style.transform = `translate(${{panX}}px,${{panY}}px) scale(${{scale}})`;
    renderEdges();
  }}
}}

function onGlobalUp() {{
  if (dragNode) scheduleSave();
  dragNode   = null;
  isPanning  = false;
  setTimeout(() => {{ isDragging = false; }}, 50);
}}

document.addEventListener('mousemove', onGlobalMove);
document.addEventListener('mouseup',   onGlobalUp);
document.addEventListener('touchmove', e => {{ e.preventDefault(); onGlobalMove(e); }}, {{passive: false}});
document.addEventListener('touchend',  onGlobalUp);

/* Pinch-to-zoom */
let lastPinchDist = null;
wrap.addEventListener('touchstart', e => {{
  if (e.touches.length === 2) lastPinchDist = null;
}}, {{passive: true}});
wrap.addEventListener('touchmove', e => {{
  if (e.touches.length === 2) {{
    e.preventDefault();
    const d = Math.hypot(
      e.touches[0].clientX - e.touches[1].clientX,
      e.touches[0].clientY - e.touches[1].clientY
    );
    if (lastPinchDist !== null) {{
      const rect = wrap.getBoundingClientRect();
      const cx = (e.touches[0].clientX + e.touches[1].clientX) / 2 - rect.left;
      const cy = (e.touches[0].clientY + e.touches[1].clientY) / 2 - rect.top;
      setScale(Math.max(0.25, Math.min(2.5, scale * (d / lastPinchDist))), cx, cy);
    }}
    lastPinchDist = d;
  }}
}}, {{passive: false}});

/* Mouse wheel zoom */
wrap.addEventListener('wheel', e => {{
  e.preventDefault();
  const rect = wrap.getBoundingClientRect();
  const mx   = e.clientX - rect.left;
  const my   = e.clientY - rect.top;
  const ns   = Math.max(0.25, Math.min(2.5, scale * (e.deltaY > 0 ? 0.9 : 1.1)));
  setScale(ns, mx, my);
}}, {{passive: false}});

/* ─── Tools ─── */
function setTool(t) {{
  currentTool = t;
  linkSource  = null;
  document.querySelectorAll('.cld-node').forEach(el => el.classList.remove('linking-source'));
  document.querySelectorAll('.tool-btn[id^="tool-"]').forEach(b => b.classList.remove('active'));
  document.getElementById('tool-' + t)?.classList.add('active');
  document.getElementById('panel-mode-badge').textContent = t === 'select' ? 'SELECIONAR' : 'CRIAR LIGAÇÃO';
  if (t === 'link') {{
    document.getElementById('link-from').value = '';
    populateLinkToSelect('');
    openModal('modal-add-link');
  }}
}}

function deleteSelected() {{
  if (selectedNode) deleteNode(selectedNode);
}}

function deleteNode(id) {{
  delete SYSTEM.nodes[id];
  SYSTEM.links = SYSTEM.links.filter(l => l.from !== id && l.to !== id);
  selectedNode = null;
  document.getElementById('detail-content').innerHTML =
    '<div class="placeholder-msg"><div class="ico">⬡</div><p>Nó excluído com sucesso.</p></div>';
  document.getElementById('panel-fab').classList.remove('has-node');
  scheduleSave();
  renderAll();
  if (isMobile) closeDrawer();
}}

function openLinkFromSelected() {{
  if (!selectedNode) return;
  linkSource = selectedNode;
  document.getElementById('link-from').value = selectedNode;
  document.getElementById('link-hint-text').textContent = `Origem: "${{selectedNode}}" — selecione o destino.`;
  populateLinkToSelect(selectedNode);
  openModal('modal-add-link');
}}

/* ─── Modals ─── */
function openModal(id) {{
  document.getElementById(id).classList.add('open');
}}
function closeModal(id) {{
  document.getElementById(id).classList.remove('open');
  if (id === 'modal-add-link') {{
    linkSource = null;
    document.querySelectorAll('.cld-node').forEach(el => el.classList.remove('linking-source'));
    if (currentTool === 'link') setTool('select');
  }}
}}
document.querySelectorAll('.modal-overlay').forEach(overlay => {{
  overlay.addEventListener('click', e => {{ if (e.target === overlay) closeModal(overlay.id); }});
}});

/* Keyboard shortcuts */
document.addEventListener('keydown', e => {{
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') return;
  if (e.key === 's' || e.key === 'S') setTool('select');
  if (e.key === 'l' || e.key === 'L') setTool('link');
  if (e.key === 'n' || e.key === 'N') openAddNodeModal();
  if (e.key === 'r' || e.key === 'R') zoomReset();
  if (e.key === 'Delete' || e.key === 'Backspace') deleteSelected();
  if (e.key === 'Escape') {{
    document.querySelectorAll('.modal-overlay.open').forEach(m => closeModal(m.id));
    closeDrawer();
  }}
}});

function openAddNodeModal() {{
  openModal('modal-add-node');
}}

function addNode() {{
  const name = document.getElementById('new-node-name').value.trim();
  if (!name)             return alert('Nome é obrigatório.');
  if (SYSTEM.nodes[name]) return alert(`Variável "${{name}}" já existe.`);
  SYSTEM.nodes[name] = {{
    cat:  document.getElementById('new-node-cat').value,
    val:  parseFloat(document.getElementById('new-node-val').value) || 0,
    expr: document.getElementById('new-node-eq').value.trim(),
    desc: document.getElementById('new-node-desc').value.trim() || 'Sem descrição.',
    x: 400 + Math.random() * 200,
    y: 280 + Math.random() * 120,
  }};
  closeModal('modal-add-node');
  ['new-node-name','new-node-eq','new-node-desc'].forEach(id => document.getElementById(id).value = '');
  document.getElementById('new-node-val').value = '0';
  scheduleSave();
  renderAll();
  selectNode(name);
}}

function openEditNodeModal(id) {{
  const node = SYSTEM.nodes[id];
  document.getElementById('edit-node-id').value   = id;
  document.getElementById('edit-node-name').value = id;
  document.getElementById('edit-node-cat').value  = node.cat;
  document.getElementById('edit-node-val').value  = node.val;
  document.getElementById('edit-node-eq').value   = node.expr || '';
  document.getElementById('edit-node-desc').value = node.desc || '';
  openModal('modal-edit-node');
}}

function saveEditNode() {{
  const oldId   = document.getElementById('edit-node-id').value;
  const newName = document.getElementById('edit-node-name').value.trim();
  if (!newName)                         return alert('Nome é obrigatório.');
  if (newName !== oldId && SYSTEM.nodes[newName]) return alert('Nome já existe.');
  const node = SYSTEM.nodes[oldId];
  node.cat  = document.getElementById('edit-node-cat').value;
  node.val  = parseFloat(document.getElementById('edit-node-val').value) || 0;
  node.expr = document.getElementById('edit-node-eq').value.trim();
  node.desc = document.getElementById('edit-node-desc').value.trim() || 'Sem descrição.';
  if (newName !== oldId) {{
    SYSTEM.nodes[newName] = node;
    delete SYSTEM.nodes[oldId];
    SYSTEM.links.forEach(l => {{
      if (l.from === oldId) l.from = newName;
      if (l.to   === oldId) l.to   = newName;
    }});
    selectedNode = newName;
  }}
  closeModal('modal-edit-node');
  scheduleSave();
  renderAll();
  if (selectedNode) renderDetailPanel(selectedNode);
}}

function confirmLink() {{
  const from = document.getElementById('link-from').value || linkSource;
  const to   = document.getElementById('link-to').value;
  const sign = document.getElementById('link-sign').value;
  const desc = document.getElementById('link-desc').value.trim()
    || `${{from}} ${{sign === '+' ? 'reforça' : 'reduz'}} ${{to}}`;
  if (!from || !to || from === to) return alert('Selecione origem e destino diferentes.');
  const existing = SYSTEM.links.find(l => l.from === from && l.to === to);
  if (existing) {{
    existing.sign = sign;
    existing.desc = desc;
  }} else {{
    SYSTEM.links.push({{from, to, sign, desc}});
  }}
  document.getElementById('link-desc').value = '';
  closeModal('modal-add-link');
  linkSource = null;
  setTool('select');
  scheduleSave();
  renderAll();
}}

/* ─── Init ─── */
window.addEventListener('resize', () => {{
  detectMobile();
  renderEdges();
}});

detectMobile();
renderAll();
</script>
</body>
</html>"""


# ============================================================
# LAYOUT STREAMLIT
# ============================================================
st.markdown("""
<div class="lumina-header">
  <span class="main-header">⬡ LUMINA</span>
  <span class="sub-header">SIMULADOR DE LAÇOS CAUSAIS · COLABORATIVO</span>
</div>
""", unsafe_allow_html=True)

tab_cld, tab_sim, tab_vars = st.tabs(["⬡ Diagrama CLD", "▶ Simulação", "≋ Variáveis"])

# ── Tab 1: Diagrama ──────────────────────────────────────────
with tab_cld:
    components.html(
        get_simulator_html(
            model_json=json.dumps(SYSTEM),
            js_api_key=api_key,
            js_bin_id=bin_id,
        ),
        height=640,
        scrolling=False,
    )
    col1, col2 = st.columns([3, 2])
    with col1:
        if st.button("🔄 Recarregar modelo da nuvem", use_container_width=True):
            fresh = load_system()
            st.session_state.system = fresh
            st.session_state.initial_vals = {k: v["val"] for k, v in fresh["nodes"].items()}
            st.rerun()
    with col2:
        if api_key and bin_id:
            st.caption("✅ Persistência ativa — salvo automaticamente via JS")
        else:
            st.caption("⚠️ Configure [jsonbin] nas Secrets do Streamlit para persistência")

# ── Tab 2: Simulação ─────────────────────────────────────────
with tab_sim:
    st.markdown("### KPIs do Ciclo Atual")

    rent    = SYSTEM["nodes"].get("Rentabilidade", {}).get("val", 0)
    receita = SYSTEM["nodes"].get("Receita",       {}).get("val", 0)
    qt      = SYSTEM["nodes"].get("Qt",            {}).get("val", 0)
    st_mk   = SYSTEM["nodes"].get("St",            {}).get("val", 0)

    kpi_cols = st.columns(4)
    kpi_data = [
        ("Rentabilidade",  f"R$ {rent/1000:.1f}k"),
        ("Receita Ciclo",  f"R$ {receita:,.0f}"),
        ("Qt Atendida",    f"{qt:.0f}"),
        ("Market Share",   f"{st_mk*100:.2f}%"),
    ]
    for col, (label, val) in zip(kpi_cols, kpi_data):
        with col:
            st.markdown(
                f'<div class="card">'
                f'<div class="kpi-label">{label}</div>'
                f'<div class="kpi-value">{val}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

    st.markdown("### Decisões de Input")
    input_keys = ['Pt', 'budget_update', 'budget_training', 'budget_infra', 'budget_promo', 'Nc']
    input_cols = st.columns(len(input_keys))
    for i, key in enumerate(input_keys):
        if key in SYSTEM["nodes"]:
            node = SYSTEM["nodes"][key]
            label_map = {
                'Pt': 'Preço (Pt)',
                'budget_update': 'P&D',
                'budget_training': 'Treinamento',
                'budget_infra': 'Infraestrutura',
                'budget_promo': 'Marketing',
                'Nc': 'Concorrentes',
            }
            step = 100.0 if node["val"] > 10 else 0.01
            new_val = input_cols[i].number_input(
                label_map.get(key, key),
                value=float(node["val"]),
                step=step,
                format="%.4g",
            )
            if new_val != node["val"]:
                node["val"] = float(new_val)
                st.session_state.initial_vals[key] = float(new_val)
                save_system(SYSTEM)

    st.markdown(f"**Ciclo atual:** {st.session_state.sim_cycle}")
    adv_col, res_col = st.columns([3, 1])
    with adv_col:
        if st.button("▶ Avançar Ciclo", use_container_width=True):
            snapshot = {k: v["val"] for k, v in SYSTEM["nodes"].items()}
            new_vals = {}
            for nid, node in SYSTEM["nodes"].items():
                if node.get("expr"):
                    result = safe_eval(node["expr"], SYSTEM["nodes"], snapshot)
                    new_vals[nid] = snapshot[nid] + result if node["cat"] == "Estado" else result
                else:
                    new_vals[nid] = snapshot[nid]
            for nid, val in new_vals.items():
                SYSTEM["nodes"][nid]["val"] = val
            st.session_state.sim_cycle += 1
            profit = (SYSTEM["nodes"].get("Receita", {}).get("val", 0)
                      - SYSTEM["nodes"].get("Custos", {}).get("val", 0))
            st.session_state.sim_history.append({
                "cycle": st.session_state.sim_cycle,
                "profit": profit,
                "rentabilidade": SYSTEM["nodes"].get("Rentabilidade", {}).get("val", 0),
            })
            save_system(SYSTEM)
            st.rerun()
    with res_col:
        if st.button("↺ Reiniciar", use_container_width=True):
            for k, v in st.session_state.initial_vals.items():
                if k in SYSTEM["nodes"]:
                    SYSTEM["nodes"][k]["val"] = v
            st.session_state.sim_cycle   = 0
            st.session_state.sim_history = []
            save_system(SYSTEM)
            st.rerun()

    if st.session_state.sim_history:
        hist        = st.session_state.sim_history
        cycles      = [h["cycle"]        for h in hist]
        rent_vals   = [h["rentabilidade"] for h in hist]
        profit_vals = [h["profit"]        for h in hist]

        chart_cols = st.columns(2)
        with chart_cols[0]:
            fig1 = go.Figure()
            fig1.add_trace(go.Bar(
                x=cycles, y=rent_vals,
                marker_color=['#4a6aee' if v >= 0 else '#e06060' for v in rent_vals],
                name="Rentabilidade",
            ))
            fig1.update_layout(
                title="Rentabilidade Acumulada",
                template="plotly_dark",
                height=260,
                margin=dict(l=10, r=10, t=40, b=20),
                font=dict(family="DM Sans"),
            )
            st.plotly_chart(fig1, use_container_width=True)
        with chart_cols[1]:
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(
                x=cycles, y=profit_vals,
                marker_color=['#52c97a' if v >= 0 else '#e06060' for v in profit_vals],
                name="Lucro",
            ))
            fig2.update_layout(
                title="Lucro Líquido por Ciclo",
                template="plotly_dark",
                height=260,
                margin=dict(l=10, r=10, t=40, b=20),
                font=dict(family="DM Sans"),
            )
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("▶ Avance alguns ciclos para visualizar os gráficos de evolução.")

# ── Tab 3: Variáveis ─────────────────────────────────────────
with tab_vars:
    st.markdown("### Variáveis do Sistema")

    search = st.text_input("🔍 Filtrar variáveis", placeholder="Digite para filtrar por nome ou categoria…")

    data = []
    for nid, node in SYSTEM["nodes"].items():
        val_display = node["val"]
        if isinstance(val_display, float):
            val_display = round(val_display, 6)
        data.append({
            "Variável":    nid,
            "Categoria":   node["cat"],
            "Valor Atual": val_display,
            "Equação":     node.get("expr", "—") or "—",
            "Descrição":   (node.get("desc", "") or "")[:90],
        })

    df = pd.DataFrame(data)
    if search:
        mask = (
            df["Variável"].str.contains(search, case=False, na=False) |
            df["Categoria"].str.contains(search, case=False, na=False)
        )
        df = df[mask]

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Variável":    st.column_config.TextColumn("Variável",    width="medium"),
            "Categoria":   st.column_config.TextColumn("Categoria",   width="small"),
            "Valor Atual": st.column_config.NumberColumn("Valor Atual", format="%.5g"),
            "Equação":     st.column_config.TextColumn("Equação",     width="large"),
            "Descrição":   st.column_config.TextColumn("Descrição",   width="large"),
        }
    )

    st.markdown(f"**{len(df)} de {len(SYSTEM['nodes'])} variáveis exibidas**")

    selected_var = st.selectbox(
        "Ir para variável no diagrama:",
        options=[""] + sorted(SYSTEM["nodes"].keys()),
    )
    if selected_var:
        st.session_state.selected_node = selected_var
        st.info(f"Variável **{selected_var}** selecionada. Volte à aba Diagrama para editá-la.")

st.markdown("---")
st.caption("⬡ LUMINA · Simulador de Laços Causais · Streamlit Colaborativo")
