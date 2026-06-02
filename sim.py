python

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
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp { background-color: #0d0f1a; }
.main-header { font-family: 'DM Serif Display', serif; font-size: 1.8rem; color: #e8a94a; letter-spacing: 0.5px; }
.sub-header { font-family: 'DM Mono', monospace; font-size: 0.75rem; color: #5a6290; letter-spacing: 0.5px; }
.card { background: #1e2340; border: 1px solid rgba(120,130,200,0.15); border-radius: 12px; padding: 1rem; margin-bottom: 0.8rem; }
.kpi-value { font-family: 'DM Mono', monospace; font-size: 1.5rem; color: #e8a94a; font-weight: 600; }
.kpi-label { font-size: 0.7rem; color: #5a6290; text-transform: uppercase; letter-spacing: 0.5px; }
.stButton>button { background: #4a6aee; color: white; border: none; border-radius: 8px; font-weight: 500; }
.stButton>button:hover { background: #6c8fff; }
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
        "Rentabilidade": {"cat": "Estado", "val": 0, "expr": "Receita - Custos", "desc": "Acumulado de receitas menos custos.", "x": 760, "y": 300},
        "Receita": {"cat": "Equação", "val": 0, "expr": "(Pt*Qt)*(1-Carga_Tributaria)", "desc": "Receita líquida.", "x": 560, "y": 200},
        "Custos": {"cat": "Equação", "val": 0, "expr": "Custo_Fixo+Custo_Variavel_t+Emprestimos_Mensal", "desc": "Custo total.", "x": 560, "y": 400},
        "Pt": {"cat": "Input", "val": 150, "expr": "", "desc": "Preço de venda.", "x": 360, "y": 130},
        "Qt": {"cat": "Equação", "val": 0, "expr": "MIN(Dpt*St, Cap)", "desc": "Demanda capturada.", "x": 360, "y": 270},
        "Carga_Tributaria": {"cat": "Parâmetro", "val": 0.15, "expr": "", "desc": "Percentual de impostos.", "x": 560, "y": 100},
        "Custo_Fixo": {"cat": "Equação", "val": 500, "expr": "500+budget_update+budget_training+budget_infra+budget_promo", "desc": "Custos fixos.", "x": 360, "y": 430},
        "Custo_Variavel_t": {"cat": "Equação", "val": 0, "expr": "CVt*(1+Inflacao)", "desc": "Custo variável ajustado.", "x": 360, "y": 520},
        "Emprestimos_Mensal": {"cat": "Equação", "val": 0, "expr": "Emprestimo/a_ni", "desc": "Parcela mensal.", "x": 560, "y": 520},
        "Dpt": {"cat": "Equação", "val": 0, "expr": "B*Alfa*Teta_1", "desc": "Demanda Potencial.", "x": 160, "y": 270},
        "St": {"cat": "Equação", "val": 0, "expr": "EXP(-Beta_1*(Pt-Pm))/(1+Nc)", "desc": "Market share.", "x": 360, "y": 200},
        "B": {"cat": "Ambiente", "val": 10000, "expr": "", "desc": "Base instalada.", "x": 80, "y": 180},
        "Alfa": {"cat": "Ambiente", "val": 1, "expr": "", "desc": "Taxa de falha.", "x": 80, "y": 350},
        "Teta_1": {"cat": "Ambiente", "val": 0.10, "expr": "", "desc": "Confiança.", "x": 160, "y": 430},
        "Pm": {"cat": "Ambiente", "val": 140, "expr": "", "desc": "Preço concorrência.", "x": 200, "y": 130},
        "Beta_1": {"cat": "Parâmetro", "val": 0.5, "expr": "", "desc": "Sensibilidade.", "x": 200, "y": 200},
        "Nc": {"cat": "Ambiente", "val": 4, "expr": "", "desc": "Nº concorrentes.", "x": 200, "y": 310},
        "Cap": {"cat": "Parâmetro", "val": 300, "expr": "", "desc": "Capacidade máx.", "x": 460, "y": 310},
        "CVt": {"cat": "Equação", "val": 0, "expr": "Qt*(Cp+C_Mao_Obra)", "desc": "Custo variável base.", "x": 160, "y": 560},
        "Cp": {"cat": "Ambiente", "val": 20, "expr": "", "desc": "Custo peças.", "x": 80, "y": 520},
        "C_Mao_Obra": {"cat": "Parâmetro", "val": 10, "expr": "", "desc": "Mão de obra.", "x": 280, "y": 580},
        "Inflacao": {"cat": "Ambiente", "val": 0.035, "expr": "", "desc": "Inflação.", "x": 460, "y": 520},
        "Emprestimo": {"cat": "Parâmetro", "val": 10000, "expr": "", "desc": "Valor empréstimo.", "x": 660, "y": 580},
        "a_ni": {"cat": "Equação", "val": 0, "expr": "((1+Tx_Juros_Emprestimo)^Prazo-1)/((1+Tx_Juros_Emprestimo)^Prazo*Tx_Juros_Emprestimo)", "desc": "Fator anuidade.", "x": 760, "y": 520},
        "Tx_Juros_Emprestimo": {"cat": "Parâmetro", "val": 0.016, "expr": "", "desc": "Juros mensais.", "x": 860, "y": 580},
        "Prazo": {"cat": "Parâmetro", "val": 12, "expr": "", "desc": "Prazo.", "x": 960, "y": 520},
        "budget_update": {"cat": "Input", "val": 5000, "expr": "", "desc": "P&D.", "x": 560, "y": 380},
        "budget_training": {"cat": "Input", "val": 5000, "expr": "", "desc": "Treinamento.", "x": 660, "y": 430},
        "budget_infra": {"cat": "Input", "val": 5000, "expr": "", "desc": "Infraestrutura.", "x": 760, "y": 430},
        "budget_promo": {"cat": "Input", "val": 10000, "expr": "", "desc": "Marketing.", "x": 860, "y": 380},
    },
    "links": [
        {"from": "Receita", "to": "Rentabilidade", "sign": "+", "desc": "Receita → Rentabilidade"},
        {"from": "Custos", "to": "Rentabilidade", "sign": "-", "desc": "Custos → Rentabilidade"},
        {"from": "Pt", "to": "Receita", "sign": "+", "desc": "Preço → Receita"},
        {"from": "Qt", "to": "Receita", "sign": "+", "desc": "Qt → Receita"},
        {"from": "Carga_Tributaria", "to": "Receita", "sign": "-", "desc": "Imposto → Receita"},
        {"from": "Custo_Fixo", "to": "Custos", "sign": "+", "desc": "Fixo → Custos"},
        {"from": "Custo_Variavel_t", "to": "Custos", "sign": "+", "desc": "Variável → Custos"},
        {"from": "Emprestimos_Mensal", "to": "Custos", "sign": "+", "desc": "Parcela → Custos"},
        {"from": "Dpt", "to": "Qt", "sign": "+", "desc": "Demanda → Qt"},
        {"from": "St", "to": "Qt", "sign": "+", "desc": "Share → Qt"},
        {"from": "Cap", "to": "Qt", "sign": "-", "desc": "Capacidade → Qt"},
        {"from": "B", "to": "Dpt", "sign": "+", "desc": "Base → Dpt"},
        {"from": "Alfa", "to": "Dpt", "sign": "+", "desc": "Falha → Dpt"},
        {"from": "Teta_1", "to": "Dpt", "sign": "+", "desc": "Confiança → Dpt"},
        {"from": "Pm", "to": "St", "sign": "+", "desc": "Preço médio → St"},
        {"from": "Pt", "to": "St", "sign": "-", "desc": "Preço → St"},
        {"from": "Beta_1", "to": "St", "sign": "-", "desc": "Sensibilidade → St"},
        {"from": "Nc", "to": "St", "sign": "-", "desc": "Concorrentes → St"},
        {"from": "Qt", "to": "CVt", "sign": "+", "desc": "Qt → CVt"},
        {"from": "Cp", "to": "CVt", "sign": "+", "desc": "Peças → CVt"},
        {"from": "C_Mao_Obra", "to": "CVt", "sign": "+", "desc": "Mão de obra → CVt"},
        {"from": "CVt", "to": "Custo_Variavel_t", "sign": "+", "desc": "CVt → Custo Var"},
        {"from": "Inflacao", "to": "Custo_Variavel_t", "sign": "+", "desc": "Inflação → Custo Var"},
        {"from": "Emprestimo", "to": "Emprestimos_Mensal", "sign": "+", "desc": "Empréstimo → Parcela"},
        {"from": "a_ni", "to": "Emprestimos_Mensal", "sign": "-", "desc": "Anuidade → Parcela"},
        {"from": "Tx_Juros_Emprestimo", "to": "a_ni", "sign": "+", "desc": "Juros → a_ni"},
        {"from": "Prazo", "to": "a_ni", "sign": "+", "desc": "Prazo → a_ni"},
        {"from": "budget_update", "to": "Custo_Fixo", "sign": "+", "desc": "P&D → Fixo"},
        {"from": "budget_training", "to": "Custo_Fixo", "sign": "+", "desc": "Treinamento → Fixo"},
        {"from": "budget_infra", "to": "Custo_Fixo", "sign": "+", "desc": "Infra → Fixo"},
        {"from": "budget_promo", "to": "Custo_Fixo", "sign": "+", "desc": "Marketing → Fixo"},
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
# Carrega do JSONBin UMA VEZ por sessão — nunca sobrescreve depois
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
# HTML DO SIMULADOR
# A CHAVE da arquitetura: o JS salva DIRETO no JSONBin via fetch.
# Não depende mais do round-trip Streamlit (setComponentValue).
# Python injeta model_json + credenciais como literais JS.
# ============================================================
def get_simulator_html(model_json: str, js_api_key, js_bin_id) -> str:
    ak = json.dumps(js_api_key)   # None → "null" | str → '"..."'
    bi = json.dumps(js_bin_id)

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500;600&display=swap');
:root {{
  --bg:#0d0f1a;--bg2:#13162a;--bg3:#1a1e35;--surface:#1e2340;--surface2:#252b4a;
  --border:rgba(120,130,200,0.15);--border2:rgba(120,130,200,0.28);
  --text:#d8ddf0;--text2:#8892be;--text3:#5a6290;
  --accent:#6c8fff;--accent2:#4a6aee;--gold:#e8a94a;--teal:#3ecfb0;
  --coral:#e06060;--green:#52c97a;
  --mono:'DM Mono',monospace;--serif:'DM Serif Display',serif;--sans:'DM Sans',sans-serif;
}}
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{background:var(--bg);color:var(--text);font-family:var(--sans);font-size:14px;overflow:hidden;height:100vh;display:flex;flex-direction:column;margin:0;}}
#main{{display:flex;flex:1;overflow:hidden;height:100%;}}
#canvas-wrap{{flex:1;position:relative;overflow:hidden;background:var(--bg);background-image:radial-gradient(circle at 50% 50%,rgba(108,143,255,0.03) 0%,transparent 70%);}}
#canvas-wrap::before{{content:'';position:absolute;inset:0;background-image:linear-gradient(rgba(120,130,200,0.04) 1px,transparent 1px),linear-gradient(90deg,rgba(120,130,200,0.04) 1px,transparent 1px);background-size:40px 40px;pointer-events:none;}}
#cld-canvas{{position:absolute;inset:0;}}
#cld-svg{{position:absolute;inset:0;width:100%;height:100%;pointer-events:none;}}
#canvas-toolbar{{position:absolute;bottom:20px;left:50%;transform:translateX(-50%);background:var(--bg2);border:1px solid var(--border2);border-radius:10px;padding:8px 12px;display:flex;gap:8px;align-items:center;z-index:10;}}
#save-indicator{{position:absolute;top:12px;right:12px;font-size:11px;font-family:var(--mono);color:var(--text3);background:var(--bg2);border:1px solid var(--border);border-radius:6px;padding:4px 10px;z-index:20;transition:all 0.3s;}}
#save-indicator.saving{{color:var(--gold);border-color:var(--gold);}}
#save-indicator.saved{{color:var(--green);border-color:var(--green);}}
#save-indicator.error{{color:var(--coral);border-color:var(--coral);}}
.tool-btn{{padding:6px 10px;border:1px solid transparent;background:transparent;color:var(--text2);font-size:12px;font-family:var(--sans);cursor:pointer;border-radius:6px;transition:all 0.15s;display:flex;align-items:center;gap:5px;}}
.tool-btn:hover{{background:var(--surface);color:var(--text);}}
.tool-btn.active{{background:var(--surface2);border-color:var(--accent);color:var(--accent);}}
.tool-sep{{width:1px;height:18px;background:var(--border);}}
.cld-node{{position:absolute;cursor:grab;user-select:none;transform:translate(-50%,-50%);z-index:5;}}
.cld-node:active{{cursor:grabbing;}}
.node-box{{padding:8px 14px;border-radius:10px;border:1.5px solid;font-size:12px;font-family:var(--sans);font-weight:500;white-space:nowrap;transition:all 0.15s;text-align:center;min-width:90px;backdrop-filter:blur(8px);}}
.cld-node:hover .node-box{{transform:scale(1.04);}}
.cld-node.selected .node-box{{box-shadow:0 0 0 3px rgba(108,143,255,0.45);}}
.cld-node.linking-source .node-box{{box-shadow:0 0 0 3px rgba(232,169,74,0.6);animation:pulse-gold 0.8s ease-in-out infinite;}}
@keyframes pulse-gold{{0%,100%{{box-shadow:0 0 0 3px rgba(232,169,74,0.6)}}50%{{box-shadow:0 0 0 6px rgba(232,169,74,0.3)}}}}
.cat-estado{{background:rgba(14,26,80,0.85);border-color:#4a6aee;color:#a0b4ff;}}
.cat-equacao{{background:rgba(80,14,14,0.85);border-color:#c04040;color:#ffb0b0;}}
.cat-parametro{{background:rgba(20,14,60,0.85);border-color:#6040c0;color:#c0a8ff;}}
.cat-ambiente{{background:rgba(14,50,40,0.85);border-color:#208060;color:#80ffcc;}}
.cat-input{{background:rgba(70,30,8,0.85);border-color:#c06020;color:#ffc080;}}
#right-panel{{width:320px;flex-shrink:0;background:var(--bg2);border-left:1px solid var(--border);display:flex;flex-direction:column;overflow:hidden;}}
.panel-header{{padding:14px 16px 10px;border-bottom:1px solid var(--border);font-family:var(--serif);font-size:16px;color:var(--gold);display:flex;justify-content:space-between;align-items:center;}}
.panel-content{{flex:1;overflow-y:auto;padding:14px 16px;}}
.node-detail-name{{font-family:var(--serif);font-size:18px;color:var(--text);margin-bottom:4px;}}
.node-detail-cat{{font-size:11px;font-family:var(--mono);letter-spacing:1px;text-transform:uppercase;margin-bottom:12px;}}
.detail-label{{font-size:11px;color:var(--text3);text-transform:uppercase;letter-spacing:0.8px;margin:12px 0 4px;font-family:var(--mono);}}
.detail-desc{{font-size:13px;color:var(--text2);line-height:1.6;}}
.detail-eq{{font-family:var(--mono);font-size:12px;color:var(--teal);background:var(--bg3);padding:8px 10px;border-radius:6px;border-left:2px solid var(--teal);word-break:break-all;line-height:1.5;}}
.relation-item{{background:var(--bg3);border-radius:7px;padding:8px 10px;margin-bottom:6px;display:flex;align-items:center;gap:8px;font-size:12px;}}
.rel-sign{{font-weight:600;font-size:13px;padding:1px 5px;border-radius:4px;}}
.rel-pos{{color:var(--green);background:rgba(82,201,122,0.12);}}
.rel-neg{{color:var(--coral);background:rgba(224,96,96,0.12);}}
.placeholder-text{{color:var(--text3);font-size:13px;line-height:1.7;text-align:center;padding-top:40px;}}
.placeholder-text .icon{{font-size:32px;margin-bottom:12px;}}
.legend{{padding:14px 16px;border-top:1px solid var(--border);flex-shrink:0;}}
.legend-title{{font-size:10px;color:var(--text3);text-transform:uppercase;letter-spacing:1px;font-family:var(--mono);margin-bottom:8px;}}
.legend-items{{display:flex;flex-wrap:wrap;gap:6px;}}
.legend-item{{display:flex;align-items:center;gap:5px;font-size:11px;color:var(--text2);}}
.legend-dot{{width:10px;height:10px;border-radius:3px;border:1.5px solid;flex-shrink:0;}}
.modal-overlay{{display:none;position:fixed;inset:0;background:rgba(5,7,20,0.85);z-index:1000;align-items:center;justify-content:center;backdrop-filter:blur(4px);}}
.modal-overlay.open{{display:flex;}}
.modal{{background:var(--bg2);border:1px solid var(--border2);border-radius:14px;width:520px;max-height:85vh;overflow-y:auto;padding:24px;}}
.modal-title{{font-family:var(--serif);font-size:22px;color:var(--gold);margin-bottom:4px;}}
.modal-sub{{font-size:12px;color:var(--text3);margin-bottom:20px;}}
.form-row{{margin-bottom:14px;}}
.form-label{{display:block;font-size:11px;color:var(--text3);text-transform:uppercase;letter-spacing:0.8px;font-family:var(--mono);margin-bottom:5px;}}
.form-input,.form-select,.form-textarea{{width:100%;background:var(--bg3);border:1px solid var(--border2);border-radius:7px;color:var(--text);font-family:var(--sans);font-size:13px;padding:8px 10px;outline:none;transition:border 0.15s;}}
.form-input:focus,.form-select:focus,.form-textarea:focus{{border-color:var(--accent);}}
.form-textarea{{resize:vertical;min-height:60px;font-family:var(--mono);}}
.modal-actions{{display:flex;gap:10px;justify-content:flex-end;margin-top:20px;}}
.btn-cancel{{padding:8px 16px;border:1px solid var(--border2);background:transparent;color:var(--text2);font-family:var(--sans);font-size:13px;cursor:pointer;border-radius:7px;}}
.btn-cancel:hover{{background:var(--surface);}}
.btn-primary{{padding:6px 14px;border:none;background:var(--accent2);color:#fff;font-family:var(--sans);font-size:13px;font-weight:500;cursor:pointer;border-radius:6px;}}
.btn-primary:hover{{background:var(--accent);}}
.btn-icon{{padding:6px 12px;border:1px solid var(--border2);background:var(--bg3);color:var(--text2);font-family:var(--sans);font-size:12px;cursor:pointer;border-radius:6px;}}
.btn-icon:hover{{background:var(--surface2);color:var(--text);}}
.link-hint{{background:rgba(232,169,74,0.08);border:1px solid rgba(232,169,74,0.25);border-radius:8px;padding:10px 14px;font-size:12px;color:var(--gold);margin-bottom:16px;line-height:1.6;}}
::-webkit-scrollbar{{width:6px;}}::-webkit-scrollbar-track{{background:transparent;}}::-webkit-scrollbar-thumb{{background:var(--border2);border-radius:3px;}}
</style>
</head>
<body>

<div id="save-indicator">pronto</div>

<div id="main">
  <div id="canvas-wrap">
    <div id="cld-canvas"></div>
    <svg id="cld-svg"></svg>
    <div id="canvas-toolbar">
      <button class="tool-btn active" id="tool-select" onclick="setTool('select')">⬚ Selecionar</button>
      <button class="tool-btn" onclick="openAddNodeModal()">➕ Novo Nó</button>
      <div class="tool-sep"></div>
      <button class="tool-btn" id="tool-link" onclick="setTool('link')">→ Criar Ligação</button>
      <div class="tool-sep"></div>
      <button class="tool-btn" onclick="zoomReset()">◎ Centralizar</button>
      <button class="tool-btn" onclick="deleteSelected()">✕ Excluir</button>
    </div>
  </div>
  <div id="right-panel">
    <div class="panel-header">
      <span>Detalhes</span>
      <span id="panel-mode-badge" style="font-size:11px;font-family:var(--mono);color:var(--text3)">SELECIONAR</span>
    </div>
    <div class="panel-content" id="detail-content">
      <div class="placeholder-text"><div class="icon">⬡</div><p>Clique em um nó para ver seus detalhes.</p></div>
    </div>
    <div class="legend">
      <div class="legend-title">Categorias</div>
      <div class="legend-items">
        <div class="legend-item"><div class="legend-dot" style="background:rgba(14,26,80,0.9);border-color:#4a6aee"></div>Estado</div>
        <div class="legend-item"><div class="legend-dot" style="background:rgba(80,14,14,0.9);border-color:#c04040"></div>Equação</div>
        <div class="legend-item"><div class="legend-dot" style="background:rgba(20,14,60,0.9);border-color:#6040c0"></div>Parâmetro</div>
        <div class="legend-item"><div class="legend-dot" style="background:rgba(14,50,40,0.9);border-color:#208060"></div>Ambiente</div>
        <div class="legend-item"><div class="legend-dot" style="background:rgba(70,30,8,0.9);border-color:#c06020"></div>Input</div>
      </div>
    </div>
  </div>
</div>

<!-- Modais -->
<div class="modal-overlay" id="modal-add-node">
  <div class="modal">
    <div class="modal-title">Novo Nó</div>
    <div class="modal-sub">Crie uma nova variável no diagrama</div>
    <div class="form-row"><label class="form-label">Nome *</label><input class="form-input" id="new-node-name" placeholder="ex: taxa_crescimento"></div>
    <div class="form-row"><label class="form-label">Categoria *</label><select class="form-select" id="new-node-cat"><option value="Estado">Estado (Estoque)</option><option value="Equação">Equação (Fluxo)</option><option value="Parâmetro">Parâmetro</option><option value="Ambiente">Ambiente (Exógena)</option><option value="Input">Input (Decisão)</option></select></div>
    <div class="form-row"><label class="form-label">Valor Inicial</label><input class="form-input" id="new-node-val" type="number" value="0"></div>
    <div class="form-row"><label class="form-label">Equação (opcional)</label><textarea class="form-textarea" id="new-node-eq"></textarea></div>
    <div class="form-row"><label class="form-label">Descrição</label><textarea class="form-textarea" id="new-node-desc"></textarea></div>
    <div class="modal-actions"><button class="btn-cancel" onclick="closeModal('modal-add-node')">Cancelar</button><button class="btn-primary" onclick="addNode()">Criar Nó</button></div>
  </div>
</div>

<div class="modal-overlay" id="modal-edit-node">
  <div class="modal">
    <div class="modal-title">Editar Variável</div>
    <div class="modal-sub">Altere os atributos e a equação</div>
    <input type="hidden" id="edit-node-id">
    <div class="form-row"><label class="form-label">Nome *</label><input class="form-input" id="edit-node-name"></div>
    <div class="form-row"><label class="form-label">Categoria *</label><select class="form-select" id="edit-node-cat"><option value="Estado">Estado</option><option value="Equação">Equação</option><option value="Parâmetro">Parâmetro</option><option value="Ambiente">Ambiente</option><option value="Input">Input</option></select></div>
    <div class="form-row"><label class="form-label">Valor Atual</label><input class="form-input" id="edit-node-val" type="number" step="any"></div>
    <div class="form-row"><label class="form-label">Equação</label><textarea class="form-textarea" id="edit-node-eq"></textarea></div>
    <div class="form-row"><label class="form-label">Descrição</label><textarea class="form-textarea" id="edit-node-desc"></textarea></div>
    <div class="modal-actions"><button class="btn-cancel" onclick="closeModal('modal-edit-node')">Cancelar</button><button class="btn-primary" onclick="saveEditNode()">Salvar</button></div>
  </div>
</div>

<div class="modal-overlay" id="modal-add-link">
  <div class="modal">
    <div class="modal-title">Nova Ligação Causal</div>
    <div class="modal-sub">Defina como as variáveis se relacionam</div>
    <div class="link-hint" id="link-hint-text">Selecione a variável de destino ou escolha abaixo.</div>
    <div class="form-row"><label class="form-label">De (Origem)</label><input class="form-input" id="link-from" readonly></div>
    <div class="form-row"><label class="form-label">Para (Destino)</label><select class="form-select" id="link-to"></select></div>
    <div class="form-row"><label class="form-label">Tipo de Relação</label><select class="form-select" id="link-sign"><option value="+">+ Positiva</option><option value="-">− Negativa</option></select></div>
    <div class="form-row"><label class="form-label">Descrição</label><textarea class="form-textarea" id="link-desc"></textarea></div>
    <div class="modal-actions"><button class="btn-cancel" onclick="closeModal('modal-add-link')">Cancelar</button><button class="btn-primary" onclick="confirmLink()">Criar Ligação</button></div>
  </div>
</div>

<script>
// ============================================================
// CREDENCIAIS — injetadas pelo Python, nunca expostas em repositório
// ============================================================
const JSONBIN_API_KEY = {ak};
const JSONBIN_BIN_ID  = {bi};

// Modelo inicial injetado pelo Python
let SYSTEM = {model_json};

let selectedNode = null, linkSource = null, currentTool = 'select';
let isDragging = false, dragNode = null, dragOffX = 0, dragOffY = 0;
let panX = 40, panY = 60, isPanning = false, panStartX = 0, panStartY = 0, scale = 0.75;
let saveTimer = null;
const catCC = {{Estado:"cat-estado",Equação:"cat-equacao",Parâmetro:"cat-parametro",Ambiente:"cat-ambiente",Input:"cat-input"}};

// ============================================================
// PERSISTÊNCIA DIRETA JS → JSONBin (elimina o problema de timing)
// ============================================================
function setIndicator(cls, msg) {{
  const el = document.getElementById('save-indicator');
  el.className = cls; el.textContent = msg;
}}

async function persistToCloud() {{
  if (!JSONBIN_API_KEY || !JSONBIN_BIN_ID) {{ setIndicator('', 'sem credenciais'); return; }}
  setIndicator('saving', '⏳ salvando...');
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

// ============================================================
// RENDER
// ============================================================
function renderAll() {{
  const canvas = document.getElementById('cld-canvas');
  canvas.innerHTML = '';
  canvas.style.transform = `translate(${{panX}}px,${{panY}}px) scale(${{scale}})`;
  canvas.style.transformOrigin = '0 0';
  for (const [id, node] of Object.entries(SYSTEM.nodes)) {{
    const el = document.createElement('div');
    el.className = 'cld-node'; el.id = 'node-' + id;
    el.style.left = node.x + 'px'; el.style.top = node.y + 'px';
    el.innerHTML = `<div class="node-box ${{catCC[node.cat]||'cat-estado'}}">${{id}}</div>`;
    el.addEventListener('mousedown', e => onNodeMousedown(e, id));
    el.addEventListener('click', e => onNodeClick(e, id));
    canvas.appendChild(el);
  }}
  renderEdges();
}}

function renderEdges() {{
  const svg = document.getElementById('cld-svg');
  const wrap = document.getElementById('canvas-wrap');
  const W = wrap.clientWidth, H = wrap.clientHeight;
  svg.setAttribute('viewBox', `0 0 ${{W}} ${{H}}`);
  svg.setAttribute('width', W); svg.setAttribute('height', H);
  svg.innerHTML = `<defs>
    <marker id="arr-pos" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M1 1L9 5L1 9" fill="none" stroke="#52c97a" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
    </marker>
    <marker id="arr-neg" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M1 1L9 5L1 9" fill="none" stroke="#e06060" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
    </marker>
  </defs>`;
  for (const link of SYSTEM.links) {{
    const fn=SYSTEM.nodes[link.from], tn=SYSTEM.nodes[link.to];
    if (!fn||!tn) continue;
    const fEl=document.getElementById('node-'+link.from);
    const tEl=document.getElementById('node-'+link.to);
    if (!fEl||!tEl) continue;
    const fx=fn.x*scale+panX, fy=fn.y*scale+panY;
    const tx=tn.x*scale+panX, ty=tn.y*scale+panY;
    const dx=tx-fx, dy=ty-fy, dist=Math.sqrt(dx*dx+dy*dy)||1;
    const ux=dx/dist, uy=dy/dist;
    const x1=fx+ux*(fEl.offsetWidth*scale/2+2), y1=fy+uy*(fEl.offsetHeight*scale/2+2);
    const x2=tx-ux*(tEl.offsetWidth*scale/2+2), y2=ty-uy*(tEl.offsetHeight*scale/2+2);
    const cx=(x1+x2)/2-uy*18, cy=(y1+y2)/2+ux*18;
    const color=link.sign==='+'?'#52c97a':'#e06060';
    const p=document.createElementNS('http://www.w3.org/2000/svg','path');
    p.setAttribute('d',`M${{x1}},${{y1}} Q${{cx}},${{cy}} ${{x2}},${{y2}}`);
    p.setAttribute('fill','none'); p.setAttribute('stroke',color);
    p.setAttribute('stroke-width','1.5'); p.setAttribute('stroke-opacity','0.6');
    p.setAttribute('marker-end',link.sign==='+'?'url(#arr-pos)':'url(#arr-neg)');
    const lbl=document.createElementNS('http://www.w3.org/2000/svg','text');
    lbl.setAttribute('x',cx); lbl.setAttribute('y',cy-4);
    lbl.setAttribute('text-anchor','middle'); lbl.setAttribute('font-size','11');
    lbl.setAttribute('font-family','DM Mono,monospace'); lbl.setAttribute('font-weight','600');
    lbl.setAttribute('fill',color); lbl.setAttribute('opacity','0.9');
    lbl.textContent=link.sign;
    svg.appendChild(p); svg.appendChild(lbl);
  }}
}}

// ============================================================
// NODE INTERACTION
// ============================================================
function onNodeMousedown(e, id) {{
  if (currentTool!=='select') return;
  e.stopPropagation(); isDragging=false; dragNode=id;
  const rect=document.getElementById('canvas-wrap').getBoundingClientRect();
  dragOffX=(e.clientX-rect.left-panX)/scale-SYSTEM.nodes[id].x;
  dragOffY=(e.clientY-rect.top-panY)/scale-SYSTEM.nodes[id].y;
}}

function onNodeClick(e, id) {{
  if (isDragging) return;
  e.stopPropagation();
  if (currentTool==='link') {{
    if (!linkSource) {{
      linkSource=id;
      document.getElementById('node-'+id)?.classList.add('linking-source');
      document.getElementById('link-hint-text').textContent=`Origem: "${{id}}" — clique no destino.`;
      document.getElementById('link-from').value=id;
      document.getElementById('link-to').innerHTML=Object.keys(SYSTEM.nodes).filter(n=>n!==id).map(n=>`<option value="${{n}}">${{n}}</option>`).join('');
      document.getElementById('modal-add-link').classList.add('open');
    }} else if (linkSource!==id) {{
      document.getElementById('link-to').value=id;
      confirmLink();
    }}
    return;
  }}
  selectNode(id);
}}

function selectNode(id) {{
  document.querySelectorAll('.cld-node').forEach(el=>el.classList.remove('selected'));
  selectedNode=id;
  document.getElementById('node-'+id)?.classList.add('selected');
  renderDetailPanel(id);
}}

function renderDetailPanel(id) {{
  const node=SYSTEM.nodes[id];
  const out=SYSTEM.links.filter(l=>l.from===id);
  const inc=SYSTEM.links.filter(l=>l.to===id);
  const catColor={{Estado:'#6a8aff',Equação:'#ff9090',Parâmetro:'#c090ff',Ambiente:'#60ffa0',Input:'#ffb060'}};
  let h=`<div class="node-detail-name">${{id}}</div>`;
  h+=`<div class="node-detail-cat" style="color:${{catColor[node.cat]||'#aaa'}}">${{node.cat}}</div>`;
  h+=`<div class="detail-label">Descrição</div><div class="detail-desc">${{node.desc}}</div>`;
  h+=`<div class="detail-label">Valor Atual</div><div class="detail-desc" style="font-family:var(--mono);color:var(--gold)">${{node.val}}</div>`;
  if (node.expr) h+=`<div class="detail-label">Equação</div><div class="detail-eq">${{node.expr}}</div>`;
  if (inc.length) {{
    h+=`<div class="detail-label">Causas (entrada)</div>`;
    inc.forEach(l=>h+=`<div class="relation-item"><span class="rel-sign ${{l.sign==='+'?'rel-pos':'rel-neg'}}">${{l.sign}}</span><span style="color:var(--text2)">${{l.from}}</span></div>`);
  }}
  if (out.length) {{
    h+=`<div class="detail-label">Efeitos (saída)</div>`;
    out.forEach(l=>h+=`<div class="relation-item"><span class="rel-sign ${{l.sign==='+'?'rel-pos':'rel-neg'}}">${{l.sign}}</span><span style="color:var(--text2)">${{l.to}}</span></div>`);
  }}
  h+=`<div style="margin-top:16px;display:flex;gap:8px">
    <button class="btn-icon" onclick="openEditNodeModal('${{id}}')">✎ Editar</button>
    <button class="btn-icon" onclick="openLinkFromSelected()">+ Ligação</button>
    <button class="btn-icon" style="color:var(--coral)" onclick="deleteNode('${{id}}')">✕ Excluir</button>
  </div>`;
  document.getElementById('detail-content').innerHTML=h;
}}

// ============================================================
// MOUSE / WHEEL
// ============================================================
document.getElementById('canvas-wrap').addEventListener('mousedown', e => {{
  if (e.target===document.getElementById('canvas-wrap')||e.target===document.getElementById('cld-svg')) {{
    isPanning=true; panStartX=e.clientX-panX; panStartY=e.clientY-panY;
    selectedNode=null;
    document.querySelectorAll('.cld-node').forEach(el=>el.classList.remove('selected'));
    document.getElementById('detail-content').innerHTML='<div class="placeholder-text"><div class="icon">⬡</div><p>Clique em um nó para ver seus detalhes.</p></div>';
  }}
}});

document.addEventListener('mousemove', e => {{
  if (dragNode) {{
    const rect=document.getElementById('canvas-wrap').getBoundingClientRect();
    SYSTEM.nodes[dragNode].x=(e.clientX-rect.left-panX)/scale-dragOffX;
    SYSTEM.nodes[dragNode].y=(e.clientY-rect.top-panY)/scale-dragOffY;
    isDragging=true; renderAll();
  }} else if (isPanning) {{
    panX=e.clientX-panStartX; panY=e.clientY-panStartY;
    document.getElementById('cld-canvas').style.transform=`translate(${{panX}}px,${{panY}}px) scale(${{scale}})`;
    renderEdges();
  }}
}});

document.addEventListener('mouseup', () => {{
  if (dragNode) scheduleSave();
  dragNode=null; isPanning=false;
  setTimeout(()=>{{isDragging=false;}},50);
}});

document.getElementById('canvas-wrap').addEventListener('wheel', e => {{
  e.preventDefault();
  const rect=document.getElementById('canvas-wrap').getBoundingClientRect();
  const mx=e.clientX-rect.left, my=e.clientY-rect.top;
  const ns=Math.max(0.3,Math.min(2.5,scale*(e.deltaY>0?0.9:1.1)));
  panX=mx-(mx-panX)*(ns/scale); panY=my-(my-panY)*(ns/scale); scale=ns;
  document.getElementById('cld-canvas').style.transform=`translate(${{panX}}px,${{panY}}px) scale(${{scale}})`;
  renderEdges();
}}, {{passive:false}});

// ============================================================
// TOOLS & MODALS
// ============================================================
function setTool(t) {{
  currentTool=t; linkSource=null;
  document.querySelectorAll('.tool-btn').forEach(b=>b.classList.remove('active'));
  document.getElementById('tool-'+t)?.classList.add('active');
  document.getElementById('panel-mode-badge').textContent=t==='select'?'SELECIONAR':'CRIAR LIGAÇÃO';
  if (t==='link') {{
    document.getElementById('link-from').value='';
    document.getElementById('link-to').innerHTML=Object.keys(SYSTEM.nodes).map(n=>`<option>${{n}}</option>`).join('');
    document.getElementById('modal-add-link').classList.add('open');
  }}
}}

function openLinkFromSelected() {{
  if (!selectedNode) return;
  linkSource=selectedNode;
  document.getElementById('link-from').value=selectedNode;
  document.getElementById('link-to').innerHTML=Object.keys(SYSTEM.nodes).filter(n=>n!==selectedNode).map(n=>`<option value="${{n}}">${{n}}</option>`).join('');
  document.getElementById('modal-add-link').classList.add('open');
}}

function zoomReset() {{ scale=0.75; panX=60; panY=60; renderAll(); }}
function deleteSelected() {{ if (selectedNode) deleteNode(selectedNode); }}

function deleteNode(id) {{
  delete SYSTEM.nodes[id];
  SYSTEM.links=SYSTEM.links.filter(l=>l.from!==id&&l.to!==id);
  selectedNode=null;
  document.getElementById('detail-content').innerHTML='<div class="placeholder-text"><div class="icon">⬡</div><p>Nó excluído.</p></div>';
  scheduleSave(); renderAll();
}}

function openAddNodeModal() {{ document.getElementById('modal-add-node').classList.add('open'); }}
function closeModal(id) {{
  document.getElementById(id).classList.remove('open');
  if (id==='modal-add-link') {{ linkSource=null; setTool('select'); }}
}}
document.querySelectorAll('.modal-overlay').forEach(o => {{
  o.addEventListener('click', e => {{ if(e.target===o) closeModal(o.id); }});
}});

function addNode() {{
  const name=document.getElementById('new-node-name').value.trim();
  if (!name) return alert('Nome obrigatório.');
  if (SYSTEM.nodes[name]) return alert('Já existe.');
  SYSTEM.nodes[name]={{
    cat:document.getElementById('new-node-cat').value,
    val:parseFloat(document.getElementById('new-node-val').value)||0,
    expr:document.getElementById('new-node-eq').value.trim(),
    desc:document.getElementById('new-node-desc').value.trim()||'Sem descrição.',
    x:400+Math.random()*200, y:300+Math.random()*100
  }};
  closeModal('modal-add-node');
  ['new-node-name','new-node-eq','new-node-desc'].forEach(id=>document.getElementById(id).value='');
  document.getElementById('new-node-val').value='0';
  scheduleSave(); renderAll();
}}

function openEditNodeModal(id) {{
  const node=SYSTEM.nodes[id];
  document.getElementById('edit-node-id').value=id;
  document.getElementById('edit-node-name').value=id;
  document.getElementById('edit-node-cat').value=node.cat;
  document.getElementById('edit-node-val').value=node.val;
  document.getElementById('edit-node-eq').value=node.expr||'';
  document.getElementById('edit-node-desc').value=node.desc||'';
  document.getElementById('modal-edit-node').classList.add('open');
}}

function saveEditNode() {{
  const oldId=document.getElementById('edit-node-id').value;
  const newName=document.getElementById('edit-node-name').value.trim();
  if (!newName) return alert('Nome obrigatório.');
  if (newName!==oldId&&SYSTEM.nodes[newName]) return alert('Nome já existe.');
  const node=SYSTEM.nodes[oldId];
  node.cat=document.getElementById('edit-node-cat').value;
  node.val=parseFloat(document.getElementById('edit-node-val').value)||0;
  node.expr=document.getElementById('edit-node-eq').value.trim();
  node.desc=document.getElementById('edit-node-desc').value.trim()||'Sem descrição.';
  if (newName!==oldId) {{
    SYSTEM.nodes[newName]=node; delete SYSTEM.nodes[oldId];
    SYSTEM.links.forEach(l=>{{if(l.from===oldId)l.from=newName;if(l.to===oldId)l.to=newName;}});
    selectedNode=newName;
  }}
  closeModal('modal-edit-node');
  scheduleSave(); renderAll();
  if (selectedNode) renderDetailPanel(selectedNode);
}}

function confirmLink() {{
  const from=document.getElementById('link-from').value||linkSource;
  const to=document.getElementById('link-to').value;
  const sign=document.getElementById('link-sign').value;
  const desc=document.getElementById('link-desc').value.trim()||`${{from}} ${{sign==='+'?'reforça':'reduz'}} ${{to}}`;
  if (!from||!to||from===to) return alert('Selecione origem e destino diferentes.');
  const ex=SYSTEM.links.find(l=>l.from===from&&l.to===to);
  if (ex){{ex.sign=sign;ex.desc=desc;}} else SYSTEM.links.push({{from,to,sign,desc}});
  document.getElementById('link-desc').value='';
  closeModal('modal-add-link'); linkSource=null; setTool('select');
  scheduleSave(); renderAll();
}}

// Init
renderAll();
</script>
</body>
</html>"""


# ============================================================
# CABEÇALHO
# ============================================================
st.markdown('<div class="main-header">⬡ LUMINA</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">SIMULADOR DE LAÇOS CAUSAIS · COLABORATIVO</div>', unsafe_allow_html=True)

# ============================================================
# ABAS
# ============================================================
tab_cld, tab_sim, tab_vars = st.tabs(["⬡ Diagrama CLD", "▶ Simulação", "≋ Variáveis"])

with tab_cld:
    components.html(
        get_simulator_html(
            model_json=json.dumps(SYSTEM),
            js_api_key=api_key,
            js_bin_id=bin_id,
        ),
        height=700,
        scrolling=False,
    )

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🔄 Recarregar modelo da nuvem"):
            fresh = load_system()
            st.session_state.system = fresh
            st.session_state.initial_vals = {k: v["val"] for k, v in fresh["nodes"].items()}
            st.rerun()
    with col2:
        if api_key and bin_id:
            st.caption("✅ Persistência ativa — o diagrama salva direto na nuvem via JS.")
        else:
            st.caption("⚠️ Configure [jsonbin] api_key e bin_id nas Secrets do Streamlit.")

# ============================================================
# ABA 2: SIMULAÇÃO
# ============================================================
with tab_sim:
    st.markdown("## Simulação por Ciclos")

    col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
    rent    = SYSTEM["nodes"].get("Rentabilidade", {}).get("val", 0)
    receita = SYSTEM["nodes"].get("Receita", {}).get("val", 0)
    qt      = SYSTEM["nodes"].get("Qt", {}).get("val", 0)
    st_mk   = SYSTEM["nodes"].get("St", {}).get("val", 0)

    with col_kpi1:
        st.markdown(f'<div class="card"><div class="kpi-label">Rentabilidade</div><div class="kpi-value">R$ {rent/1000:.1f}k</div></div>', unsafe_allow_html=True)
    with col_kpi2:
        st.markdown(f'<div class="card"><div class="kpi-label">Receita Ciclo</div><div class="kpi-value">R$ {receita:.0f}</div></div>', unsafe_allow_html=True)
    with col_kpi3:
        st.markdown(f'<div class="card"><div class="kpi-label">Qt Atendida</div><div class="kpi-value">{qt:.0f}</div></div>', unsafe_allow_html=True)
    with col_kpi4:
        st.markdown(f'<div class="card"><div class="kpi-label">Market Share</div><div class="kpi-value">{st_mk*100:.1f}%</div></div>', unsafe_allow_html=True)

    st.markdown("### Inputs de Decisão")
    input_keys = ['Pt', 'budget_update', 'budget_training', 'budget_infra', 'budget_promo', 'Nc']
    cols = st.columns(6)
    for i, key in enumerate(input_keys):
        if key in SYSTEM["nodes"]:
            node = SYSTEM["nodes"][key]
            new_val = cols[i].number_input(key, value=float(node["val"]), step=100.0 if node["val"] > 1 else 0.01)
            if new_val != node["val"]:
                node["val"] = float(new_val)
                st.session_state.initial_vals[key] = float(new_val)
                save_system(SYSTEM)

    col_adv, col_res = st.columns([2, 1])
    with col_adv:
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
            profit = SYSTEM["nodes"].get("Receita", {}).get("val", 0) - SYSTEM["nodes"].get("Custos", {}).get("val", 0)
            st.session_state.sim_history.append({
                "cycle": st.session_state.sim_cycle,
                "profit": profit,
                "rentabilidade": SYSTEM["nodes"].get("Rentabilidade", {}).get("val", 0)
            })
            save_system(SYSTEM)
            st.rerun()

    with col_res:
        if st.button("↺ Reiniciar", use_container_width=True):
            for k, v in st.session_state.initial_vals.items():
                if k in SYSTEM["nodes"]:
                    SYSTEM["nodes"][k]["val"] = v
            st.session_state.sim_cycle = 0
            st.session_state.sim_history = []
            save_system(SYSTEM)
            st.rerun()

    st.markdown(f"Ciclo atual: **{st.session_state.sim_cycle}**")

    if st.session_state.sim_history:
        hist = st.session_state.sim_history
        cycles = [h["cycle"] for h in hist]
        rent_vals = [h["rentabilidade"] for h in hist]
        profit_vals = [h["profit"] for h in hist]

        fig1 = go.Figure()
        fig1.add_trace(go.Bar(x=cycles, y=rent_vals,
                              marker_color=['#4a6aee' if v >= 0 else '#e06060' for v in rent_vals]))
        fig1.update_layout(title="Rentabilidade Acumulada", template="plotly_dark", height=250,
                           margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig1, use_container_width=True)

        fig2 = go.Figure()
        fig2.add_trace(go.Bar(x=cycles, y=profit_vals,
                              marker_color=['#52c97a' if v >= 0 else '#e06060' for v in profit_vals]))
        fig2.update_layout(title="Lucro Líquido por Ciclo", template="plotly_dark", height=250,
                           margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Avance alguns ciclos para visualizar os gráficos.")

# ============================================================
# ABA 3: VARIÁVEIS
# ============================================================
with tab_vars:
    st.markdown("## Variáveis do Sistema")
    data = []
    for nid, node in SYSTEM["nodes"].items():
        data.append({
            "Variável": nid,
            "Categoria": node["cat"],
            "Valor Atual": node["val"],
            "Equação": node.get("expr", "—"),
            "Descrição": node.get("desc", "")[:80],
        })
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True, hide_index=True,
                 column_config={
                     "Variável": st.column_config.TextColumn("Variável", width="medium"),
                     "Categoria": st.column_config.TextColumn("Categoria", width="small"),
                     "Valor Atual": st.column_config.NumberColumn("Valor Atual", format="%.4g"),
                     "Equação": st.column_config.TextColumn("Equação", width="large"),
                 })
    selected_var = st.selectbox("Ir para variável:", options=[""] + list(SYSTEM["nodes"].keys()))
    if selected_var:
        st.session_state.selected_node = selected_var
        st.info(f"Variável '{selected_var}' selecionada. Volte para a aba Diagrama para editá-la.")

st.markdown("---")
st.caption("LUMINA · Simulador de Laços Causais · Versão Streamlit Colaborativa")
