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
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp { background-color: #0d0f1a; color: #d8ddf0; }
.lumina-header { display:flex; align-items:baseline; gap:12px; padding:0 0 4px; border-bottom:1px solid rgba(120,130,200,0.12); margin-bottom:12px; flex-wrap:wrap; }
.main-header { font-family:'DM Serif Display',serif; font-size:clamp(1.2rem,4vw,1.8rem); color:#e8a94a; letter-spacing:.5px; line-height:1; }
.sub-header { font-family:'DM Mono',monospace; font-size:clamp(.55rem,2vw,.72rem); color:#5a6290; letter-spacing:1px; }
.card { background:#1e2340; border:1px solid rgba(120,130,200,0.15); border-radius:12px; padding:clamp(.6rem,2vw,1rem); margin-bottom:.7rem; }
.kpi-value { font-family:'DM Mono',monospace; font-size:clamp(1rem,3vw,1.5rem); color:#e8a94a; font-weight:600; white-space:nowrap; }
.kpi-label { font-size:clamp(.6rem,1.5vw,.7rem); color:#5a6290; text-transform:uppercase; letter-spacing:.5px; }
.stButton>button { background:#4a6aee; color:white; border:none; border-radius:8px; font-weight:500; min-height:42px; font-size:clamp(.75rem,2vw,.9rem); width:100%; }
.stButton>button:hover { background:#6c8fff; }
.stTabs [data-baseweb="tab-list"] { gap:4px; flex-wrap:nowrap; overflow-x:auto; scrollbar-width:none; }
.stTabs [data-baseweb="tab-list"]::-webkit-scrollbar { display:none; }
.stTabs [data-baseweb="tab"] { font-size:clamp(.7rem,2vw,.85rem); padding:8px 12px; white-space:nowrap; }
[data-testid="stDataFrame"] { width:100% !important; overflow-x:auto; }
div[data-testid="stMarkdownContainer"] p { color:#8892be; }
.stCaption { color:#5a6290 !important; }
hr { border-color:rgba(120,130,200,0.12) !important; }
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
                headers={"X-Master-Key": api_key}, timeout=8,
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
                json=system, timeout=8,
            )
        except Exception:
            pass
    st.session_state.system = system

# ============================================================
# MODELO PADRÃO
# ============================================================
DEFAULT_SYSTEM = {
    "nodes": {
        "Rentabilidade":      {"cat":"Estado",    "val":0,      "expr":"Receita - Custos",                                            "desc":"Acumulado de receitas menos custos.",   "x":760,"y":300},
        "Receita":            {"cat":"Equação",   "val":0,      "expr":"(Pt*Qt)*(1-Carga_Tributaria)",                                "desc":"Receita líquida.",                      "x":560,"y":200},
        "Custos":             {"cat":"Equação",   "val":0,      "expr":"Custo_Fixo+Custo_Variavel_t+Emprestimos_Mensal",              "desc":"Custo total.",                          "x":560,"y":400},
        "Pt":                 {"cat":"Input",     "val":150,    "expr":"",                                                            "desc":"Preço de venda.",                       "x":360,"y":130},
        "Qt":                 {"cat":"Equação",   "val":0,      "expr":"MIN(Dpt*St, Cap)",                                            "desc":"Demanda capturada.",                    "x":360,"y":270},
        "Carga_Tributaria":   {"cat":"Parâmetro", "val":0.15,   "expr":"",                                                            "desc":"Percentual de impostos.",              "x":560,"y":100},
        "Custo_Fixo":         {"cat":"Equação",   "val":500,    "expr":"500+budget_update+budget_training+budget_infra+budget_promo", "desc":"Custos fixos.",                         "x":360,"y":430},
        "Custo_Variavel_t":   {"cat":"Equação",   "val":0,      "expr":"CVt*(1+Inflacao)",                                           "desc":"Custo variável ajustado.",             "x":360,"y":520},
        "Emprestimos_Mensal": {"cat":"Equação",   "val":0,      "expr":"Emprestimo/a_ni",                                            "desc":"Parcela mensal.",                       "x":560,"y":520},
        "Dpt":                {"cat":"Equação",   "val":0,      "expr":"B*Alfa*Teta_1",                                              "desc":"Demanda Potencial.",                    "x":160,"y":270},
        "St":                 {"cat":"Equação",   "val":0,      "expr":"EXP(-Beta_1*(Pt-Pm))/(1+Nc)",                                "desc":"Market share.",                         "x":360,"y":200},
        "B":                  {"cat":"Ambiente",  "val":10000,  "expr":"",                                                            "desc":"Base instalada.",                       "x":80, "y":180},
        "Alfa":               {"cat":"Ambiente",  "val":1,      "expr":"",                                                            "desc":"Taxa de falha.",                        "x":80, "y":350},
        "Teta_1":             {"cat":"Ambiente",  "val":0.10,   "expr":"",                                                            "desc":"Confiança.",                            "x":160,"y":430},
        "Pm":                 {"cat":"Ambiente",  "val":140,    "expr":"",                                                            "desc":"Preço concorrência.",                   "x":200,"y":130},
        "Beta_1":             {"cat":"Parâmetro", "val":0.5,    "expr":"",                                                            "desc":"Sensibilidade.",                        "x":200,"y":200},
        "Nc":                 {"cat":"Ambiente",  "val":4,      "expr":"",                                                            "desc":"Nº concorrentes.",                      "x":200,"y":310},
        "Cap":                {"cat":"Parâmetro", "val":300,    "expr":"",                                                            "desc":"Capacidade máx.",                       "x":460,"y":310},
        "CVt":                {"cat":"Equação",   "val":0,      "expr":"Qt*(Cp+C_Mao_Obra)",                                         "desc":"Custo variável base.",                  "x":160,"y":560},
        "Cp":                 {"cat":"Ambiente",  "val":20,     "expr":"",                                                            "desc":"Custo peças.",                          "x":80, "y":520},
        "C_Mao_Obra":         {"cat":"Parâmetro", "val":10,     "expr":"",                                                            "desc":"Mão de obra.",                          "x":280,"y":580},
        "Inflacao":           {"cat":"Ambiente",  "val":0.035,  "expr":"",                                                            "desc":"Inflação.",                             "x":460,"y":520},
        "Emprestimo":         {"cat":"Parâmetro", "val":10000,  "expr":"",                                                            "desc":"Valor empréstimo.",                     "x":660,"y":580},
        "a_ni":               {"cat":"Equação",   "val":0,      "expr":"((1+Tx_Juros_Emprestimo)^Prazo-1)/((1+Tx_Juros_Emprestimo)^Prazo*Tx_Juros_Emprestimo)", "desc":"Fator anuidade.", "x":760,"y":520},
        "Tx_Juros_Emprestimo":{"cat":"Parâmetro", "val":0.016,  "expr":"",                                                            "desc":"Juros mensais.",                        "x":860,"y":580},
        "Prazo":              {"cat":"Parâmetro", "val":12,     "expr":"",                                                            "desc":"Prazo.",                                "x":960,"y":520},
        "budget_update":      {"cat":"Input",     "val":5000,   "expr":"",                                                            "desc":"P&D.",                                  "x":560,"y":380},
        "budget_training":    {"cat":"Input",     "val":5000,   "expr":"",                                                            "desc":"Treinamento.",                          "x":660,"y":430},
        "budget_infra":       {"cat":"Input",     "val":5000,   "expr":"",                                                            "desc":"Infraestrutura.",                       "x":760,"y":430},
        "budget_promo":       {"cat":"Input",     "val":10000,  "expr":"",                                                            "desc":"Marketing.",                            "x":860,"y":380},
    },
    "links": [
        {"from":"Receita",            "to":"Rentabilidade",    "sign":"+","desc":"Receita → Rentabilidade"},
        {"from":"Custos",             "to":"Rentabilidade",    "sign":"-","desc":"Custos → Rentabilidade"},
        {"from":"Pt",                 "to":"Receita",          "sign":"+","desc":"Preço → Receita"},
        {"from":"Qt",                 "to":"Receita",          "sign":"+","desc":"Qt → Receita"},
        {"from":"Carga_Tributaria",   "to":"Receita",          "sign":"-","desc":"Imposto → Receita"},
        {"from":"Custo_Fixo",         "to":"Custos",           "sign":"+","desc":"Fixo → Custos"},
        {"from":"Custo_Variavel_t",   "to":"Custos",           "sign":"+","desc":"Variável → Custos"},
        {"from":"Emprestimos_Mensal", "to":"Custos",           "sign":"+","desc":"Parcela → Custos"},
        {"from":"Dpt",                "to":"Qt",               "sign":"+","desc":"Demanda → Qt"},
        {"from":"St",                 "to":"Qt",               "sign":"+","desc":"Share → Qt"},
        {"from":"Cap",                "to":"Qt",               "sign":"-","desc":"Capacidade → Qt"},
        {"from":"B",                  "to":"Dpt",              "sign":"+","desc":"Base → Dpt"},
        {"from":"Alfa",               "to":"Dpt",              "sign":"+","desc":"Falha → Dpt"},
        {"from":"Teta_1",             "to":"Dpt",              "sign":"+","desc":"Confiança → Dpt"},
        {"from":"Pm",                 "to":"St",               "sign":"+","desc":"Preço médio → St"},
        {"from":"Pt",                 "to":"St",               "sign":"-","desc":"Preço → St"},
        {"from":"Beta_1",             "to":"St",               "sign":"-","desc":"Sensibilidade → St"},
        {"from":"Nc",                 "to":"St",               "sign":"-","desc":"Concorrentes → St"},
        {"from":"Qt",                 "to":"CVt",              "sign":"+","desc":"Qt → CVt"},
        {"from":"Cp",                 "to":"CVt",              "sign":"+","desc":"Peças → CVt"},
        {"from":"C_Mao_Obra",         "to":"CVt",              "sign":"+","desc":"Mão de obra → CVt"},
        {"from":"CVt",                "to":"Custo_Variavel_t", "sign":"+","desc":"CVt → Custo Var"},
        {"from":"Inflacao",           "to":"Custo_Variavel_t", "sign":"+","desc":"Inflação → Custo Var"},
        {"from":"Emprestimo",         "to":"Emprestimos_Mensal","sign":"+","desc":"Empréstimo → Parcela"},
        {"from":"a_ni",               "to":"Emprestimos_Mensal","sign":"-","desc":"Anuidade → Parcela"},
        {"from":"Tx_Juros_Emprestimo","to":"a_ni",             "sign":"+","desc":"Juros → a_ni"},
        {"from":"Prazo",              "to":"a_ni",             "sign":"+","desc":"Prazo → a_ni"},
        {"from":"budget_update",      "to":"Custo_Fixo",       "sign":"+","desc":"P&D → Fixo"},
        {"from":"budget_training",    "to":"Custo_Fixo",       "sign":"+","desc":"Treinamento → Fixo"},
        {"from":"budget_infra",       "to":"Custo_Fixo",       "sign":"+","desc":"Infra → Fixo"},
        {"from":"budget_promo",       "to":"Custo_Fixo",       "sign":"+","desc":"Marketing → Fixo"},
    ]
}

# ============================================================
# AVALIADOR
# ============================================================
def safe_eval(expr, nodes):
    """
    Avalia 'expr' substituindo cada nome de variável pelo valor ATUAL em
    nodes[name]["val"]. Importante: esta função não tira mais um snapshot
    isolado -- ela lê o dicionário `nodes` ao vivo. Isso só funciona
    corretamente se as variáveis das quais 'expr' depende já tiverem sido
    recalculadas antes, na ordem certa (ver `_topological_order` /
    `advance_cycle` abaixo).
    """
    if not expr or not expr.strip():
        return 0.0
    s = expr
    for name in sorted(nodes.keys(), key=len, reverse=True):
        val = nodes[name]["val"]
        s = re.sub(r'\b' + re.escape(name) + r'\b', repr(float(val)), s)
    for fn, py in [('EXP','math.exp'),('MIN','min'),('MAX','max'),('ABS','abs'),
                   ('SQRT','math.sqrt'),('LOG','math.log10'),('LN','math.log'),
                   ('SIN','math.sin'),('COS','math.cos'),('TAN','math.tan')]:
        s = re.sub(r'\b' + fn + r'\b', py, s, flags=re.IGNORECASE)
    s = s.replace('^', '**')
    try:
        r = eval(s, {"math": math, "__builtins__": {}}, {})
        return 0.0 if (math.isnan(r) or not math.isfinite(r)) else float(r)
    except Exception:
        return 0.0


def _referenced_vars(expr, all_names):
    """Retorna o subconjunto de all_names que aparece (como palavra inteira) em expr."""
    if not expr:
        return set()
    found = set()
    for name in all_names:
        if re.search(r'\b' + re.escape(name) + r'\b', expr):
            found.add(name)
    return found


def _topological_order(nodes):
    """
    Ordena os nós que possuem 'expr' de modo que toda variável da qual um
    nó depende seja calculada ANTES dele, no mesmo ciclo.

    Isso é exatamente o que faltava no código original: lá, todos os nós
    eram recalculados a partir de uma única "foto" (snapshot) tirada no
    início do ciclo. Uma equação como `Qt = MIN(Dpt*St, Cap)` acabava
    usando o Dpt/St do CICLO ANTERIOR, e não o valor recém-calculado no
    mesmo ciclo -- então uma mudança em qualquer variável (ex.: o Preço)
    levava vários cliques em "Avançar Ciclo" para se propagar por toda a
    cadeia causal até `Rentabilidade`, dando a impressão de que o
    diagrama "não influenciava" a simulação.
    """
    names = list(nodes.keys())
    deps = {n: _referenced_vars(nodes[n].get("expr", ""), names) - {n} for n in names}
    order, temp_mark, perm_mark = [], set(), set()

    def visit(n):
        if n in perm_mark:
            return
        if n in temp_mark:
            # Dependência circular (loop algébrico) -- evita recursão
            # infinita. Nesse caso raro o nó mantém o valor do ciclo
            # anterior nesta iteração (não deveria ocorrer no modelo
            # padrão, que é um DAG, mas protege contra loops criados
            # manualmente pelo usuário no editor de diagrama).
            return
        temp_mark.add(n)
        for dep in deps[n]:
            if nodes[dep].get("expr"):
                visit(dep)
        temp_mark.discard(n)
        perm_mark.add(n)
        order.append(n)

    for n in names:
        visit(n)
    return order


def advance_cycle(system):
    """
    Avança um ciclo de simulação respeitando a cadeia causal completa:

    1) Calcula todas as variáveis com 'expr' (Equação e Estado) na ordem
       correta de dependência, sempre lendo o valor MAIS RECENTE (já
       recalculado neste mesmo ciclo) das variáveis das quais dependem.
    2) Para variáveis do tipo Estado (acumuladores/estoques), soma o
       resultado da equação (o "fluxo" do período) ao valor que a
       variável já tinha ANTES deste ciclo.
    3) Variáveis sem 'expr' (Ambiente, Parâmetro, Input) são decisões
       exógenas: só mudam quando o usuário edita manualmente.
    """
    nodes = system["nodes"]
    prev_vals = {nid: nd["val"] for nid, nd in nodes.items()}
    order = _topological_order(nodes)
    for nid in order:
        nd = nodes[nid]
        expr = nd.get("expr")
        if not expr:
            continue
        r = safe_eval(expr, nodes)
        if nd["cat"] == "Estado":
            nd["val"] = prev_vals[nid] + r
        else:
            nd["val"] = r
    return system

# ============================================================
# SESSION STATE
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
# HTML DO SIMULADOR (VERSÃO ORIGINAL, APENAS COM BOTÕES MANUAIS)
# ============================================================
def get_simulator_html(model_json, js_api_key, js_bin_id):
    ak = json.dumps(js_api_key)
    bi = json.dumps(js_bin_id)
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no,viewport-fit=cover">
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500;600&display=swap');
:root{{
  --bg:#0d0f1a;--bg2:#13162a;--bg3:#1a1e35;
  --surface:#1e2340;--surf2:#252b4a;
  --border:rgba(120,130,200,.15);--border2:rgba(120,130,200,.28);
  --text:#d8ddf0;--text2:#8892be;--text3:#5a6290;
  --accent:#6c8fff;--accent2:#4a6aee;
  --gold:#e8a94a;--teal:#3ecfb0;--coral:#e06060;--green:#52c97a;
  --mono:'DM Mono',monospace;--serif:'DM Serif Display',serif;--sans:'DM Sans',sans-serif;
  --panel-w:300px;
  --topbar-h:44px;
  --toolbar-h:52px;
}}
*{{box-sizing:border-box;margin:0;padding:0;}}
html,body{{height:100%;overflow:hidden;background:var(--bg);color:var(--text);font-family:var(--sans);font-size:14px;}}

/* ── Shell ── */
#shell{{display:flex;flex-direction:column;height:100%;}}

/* ── Top bar ── */
#topbar{{
  height:var(--topbar-h);flex-shrink:0;
  background:var(--bg2);border-bottom:1px solid var(--border);
  display:flex;align-items:center;gap:6px;padding:0 10px;
  overflow:hidden;
}}
#tb-title{{font-family:var(--serif);font-size:15px;color:var(--gold);white-space:nowrap;margin-right:4px;}}
#save-ind{{
  margin-left:auto;font-size:11px;font-family:var(--mono);
  color:var(--text3);background:var(--bg3);border:1px solid var(--border);
  border-radius:20px;padding:3px 10px;white-space:nowrap;flex-shrink:0;transition:all .25s;
}}
#save-ind.saving{{color:var(--gold);border-color:var(--gold);}}
#save-ind.saved{{color:var(--green);border-color:var(--green);}}
#save-ind.error{{color:var(--coral);border-color:var(--coral);}}

/* ── Main row ── */
#main{{display:flex;flex:1;overflow:hidden;position:relative;}}

/* ── Canvas area ── */
#canvas-wrap{{
  flex:1;position:relative;overflow:hidden;
  background:var(--bg);
}}
#canvas-wrap::before{{
  content:'';position:absolute;inset:0;pointer-events:none;
  background-image:linear-gradient(rgba(120,130,200,.04) 1px,transparent 1px),
                   linear-gradient(90deg,rgba(120,130,200,.04) 1px,transparent 1px);
  background-size:36px 36px;
}}
#cld-canvas{{position:absolute;inset:0;transform-origin:0 0;will-change:transform;}}
#cld-svg{{position:absolute;inset:0;width:100%;height:100%;pointer-events:none;overflow:visible;}}

/* ── Bottom toolbar ── */
#toolbar{{
  position:absolute;bottom:10px;left:50%;transform:translateX(-50%);
  background:rgba(19,22,42,.94);backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);
  border:1px solid var(--border2);border-radius:40px;
  padding:5px 10px;display:flex;align-items:center;gap:3px;
  z-index:20;box-shadow:0 4px 20px rgba(0,0,0,.4);
  max-width:calc(100% - 24px);overflow-x:auto;scrollbar-width:none;
}}
#toolbar::-webkit-scrollbar{{display:none;}}

/* ── Zoom chip ── */
#zoom-chip{{
  position:absolute;top:8px;left:8px;
  font-size:11px;font-family:var(--mono);color:var(--text3);
  background:rgba(19,22,42,.75);border:1px solid var(--border);
  border-radius:20px;padding:2px 9px;pointer-events:none;z-index:10;
}}

/* ── Tool buttons ── */
.tbtn{{
  display:inline-flex;align-items:center;justify-content:center;gap:4px;
  padding:6px 11px;border:1px solid transparent;background:transparent;
  color:var(--text2);font-size:12px;font-family:var(--sans);
  cursor:pointer;border-radius:20px;transition:all .15s;
  white-space:nowrap;min-height:34px;min-width:34px;
}}
.tbtn:hover{{background:var(--surface);color:var(--text);}}
.tbtn.active{{background:var(--surf2);border-color:var(--accent);color:var(--accent);}}
.tbtn.danger:hover{{background:rgba(224,96,96,.12);color:var(--coral);border-color:var(--coral);}}
.tsep{{width:1px;height:18px;background:var(--border);flex-shrink:0;}}

/* ── RIGHT PANEL (desktop sidebar) ── */
#right-panel{{
  width:var(--panel-w);flex-shrink:0;
  background:var(--bg2);border-left:1px solid var(--border);
  display:flex;flex-direction:column;overflow:hidden;
  transition:width .28s cubic-bezier(.4,0,.2,1);
}}
#right-panel.panel-hidden{{width:0;border-left:none;overflow:hidden;}}

.panel-hdr{{
  padding:11px 13px 9px;border-bottom:1px solid var(--border);
  display:flex;align-items:center;gap:8px;flex-shrink:0;min-height:44px;
}}
.panel-title{{font-family:var(--serif);font-size:15px;color:var(--gold);flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}}
#panel-badge{{font-size:10px;font-family:var(--mono);letter-spacing:1px;color:var(--text3);white-space:nowrap;}}
.panel-x{{background:transparent;border:none;color:var(--text3);cursor:pointer;font-size:17px;line-height:1;padding:4px 5px;border-radius:5px;flex-shrink:0;}}
.panel-x:hover{{background:var(--surface);color:var(--text);}}

.panel-body{{flex:1;overflow-y:auto;overflow-x:hidden;padding:13px;scrollbar-width:thin;scrollbar-color:var(--border2) transparent;}}
.panel-body::-webkit-scrollbar{{width:4px;}}
.panel-body::-webkit-scrollbar-thumb{{background:var(--border2);border-radius:2px;}}

.panel-legend{{padding:9px 13px;border-top:1px solid var(--border);flex-shrink:0;}}
.legend-lbl{{font-size:10px;color:var(--text3);text-transform:uppercase;letter-spacing:1px;font-family:var(--mono);margin-bottom:6px;}}
.legend-grid{{display:grid;grid-template-columns:1fr 1fr;gap:5px;}}
.legend-item{{display:flex;align-items:center;gap:5px;font-size:11px;color:var(--text2);}}
.legend-dot{{width:9px;height:9px;border-radius:3px;border:1.5px solid;flex-shrink:0;}}

/* Detail panel content */
.dn-name{{font-family:var(--serif);font-size:17px;color:var(--text);margin-bottom:3px;word-break:break-word;}}
.dn-cat{{font-size:10px;font-family:var(--mono);letter-spacing:1.2px;text-transform:uppercase;margin-bottom:12px;}}
.dl{{font-size:10px;color:var(--text3);text-transform:uppercase;letter-spacing:.8px;margin:11px 0 4px;font-family:var(--mono);}}
.dv{{font-family:var(--mono);font-size:13px;color:var(--gold);}}
.dd{{font-size:12.5px;color:var(--text2);line-height:1.6;}}
.deq{{font-family:var(--mono);font-size:11.5px;color:var(--teal);background:var(--bg3);padding:8px 10px;border-radius:6px;border-left:2px solid var(--teal);word-break:break-all;line-height:1.6;}}
.rel-row{{background:var(--bg3);border-radius:7px;padding:7px 10px;margin-bottom:5px;display:flex;align-items:center;gap:8px;font-size:12px;}}
.rsgn{{font-weight:700;font-size:13px;padding:1px 6px;border-radius:4px;flex-shrink:0;}}
.rpos{{color:var(--green);background:rgba(82,201,122,.12);}}
.rneg{{color:var(--coral);background:rgba(224,96,96,.12);}}
.dact{{margin-top:16px;display:flex;gap:6px;flex-wrap:wrap;}}
.ph{{color:var(--text3);font-size:13px;line-height:1.7;text-align:center;padding:36px 12px 16px;}}
.ph .ico{{font-size:28px;margin-bottom:8px;}}

/* ── NODES ── */
.cld-node{{position:absolute;cursor:grab;user-select:none;transform:translate(-50%,-50%);z-index:5;touch-action:none;}}
.cld-node:active{{cursor:grabbing;}}
.node-box{{
  padding:7px 13px;border-radius:10px;border:1.5px solid;
  font-size:11.5px;font-family:var(--sans);font-weight:500;white-space:nowrap;
  transition:transform .12s,box-shadow .12s;text-align:center;min-width:80px;
  backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);
}}
.cld-node:hover .node-box{{transform:scale(1.05);}}
.cld-node.selected .node-box{{box-shadow:0 0 0 3px rgba(108,143,255,.5),0 0 20px rgba(108,143,255,.2);}}
.cld-node.lk-src .node-box{{animation:pgold .9s ease-in-out infinite;}}
@keyframes pgold{{
  0%,100%{{box-shadow:0 0 0 3px rgba(232,169,74,.6),0 0 20px rgba(232,169,74,.15);}}
  50%{{box-shadow:0 0 0 6px rgba(232,169,74,.3),0 0 30px rgba(232,169,74,.08);}}
}}
.cat-estado{{background:rgba(14,26,80,.88);border-color:#4a6aee;color:#a0b4ff;}}
.cat-equacao{{background:rgba(80,14,14,.88);border-color:#c04040;color:#ffb0b0;}}
.cat-parametro{{background:rgba(20,14,60,.88);border-color:#6040c0;color:#c0a8ff;}}
.cat-ambiente{{background:rgba(14,50,40,.88);border-color:#208060;color:#80ffcc;}}
.cat-input{{background:rgba(70,30,8,.88);border-color:#c06020;color:#ffc080;}}

/* ── MOBILE BOTTOM SHEET ── */
#mobile-sheet{{
  display:none;
  position:absolute;
  bottom:0;left:0;right:0;
  height:55%;
  background:var(--bg2);
  border-top:1px solid var(--border2);
  border-radius:18px 18px 0 0;
  box-shadow:0 -8px 32px rgba(0,0,0,.5);
  z-index:50;
  flex-direction:column;
  overflow:hidden;
  transform:translateY(100%);
  transition:transform .3s cubic-bezier(.4,0,.2,1);
}}
#mobile-sheet.open{{transform:translateY(0);}}
#sheet-handle{{width:36px;height:4px;background:var(--border2);border-radius:2px;margin:10px auto 0;flex-shrink:0;}}
#sheet-hdr{{padding:8px 13px 9px;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:8px;flex-shrink:0;}}
#sheet-title{{font-family:var(--serif);font-size:14px;color:var(--gold);flex:1;}}
#sheet-x{{background:transparent;border:none;color:var(--text3);cursor:pointer;font-size:17px;padding:4px 5px;border-radius:5px;}}
#sheet-x:hover{{background:var(--surface);color:var(--text);}}
#sheet-body{{flex:1;overflow-y:auto;padding:12px;scrollbar-width:thin;scrollbar-color:var(--border2) transparent;}}
#sheet-body::-webkit-scrollbar{{width:4px;}}
#sheet-body::-webkit-scrollbar-thumb{{background:var(--border2);border-radius:2px;}}
#sheet-legend{{padding:8px 13px;border-top:1px solid var(--border);flex-shrink:0;}}

/* Backdrop for mobile sheet */
#sheet-backdrop{{
  display:none;position:absolute;inset:0;
  background:rgba(5,7,20,.6);z-index:49;
}}
#sheet-backdrop.open{{display:block;}}

/* FAB */
#fab{{
  position:absolute;bottom:70px;right:14px;z-index:30;
  display:none;
  width:50px;height:50px;border-radius:50%;
  background:var(--accent2);color:#fff;border:none;
  font-size:19px;cursor:pointer;
  box-shadow:0 4px 16px rgba(0,0,0,.4);
  align-items:center;justify-content:center;
  transition:transform .15s,background .15s;
}}
#fab.show{{display:flex;}}
#fab:hover{{background:var(--accent);transform:scale(1.08);}}
#fab.node-sel{{background:var(--gold);color:#000;}}

/* ── MODALS ── */
.modal-overlay{{
  display:none;position:absolute;inset:0;
  background:rgba(5,7,20,.82);z-index:100;
  align-items:flex-end;justify-content:center;
  backdrop-filter:blur(5px);-webkit-backdrop-filter:blur(5px);
}}
.modal-overlay.open{{display:flex;}}
.modal{{
  background:var(--bg2);border:1px solid var(--border2);
  width:100%;max-width:480px;max-height:85%;
  overflow-y:auto;padding:20px 18px 26px;
  border-radius:18px 18px 0 0;
  animation:slideup .22s cubic-bezier(.4,0,.2,1);
}}
@keyframes slideup{{from{{transform:translateY(40px);opacity:0;}}to{{transform:translateY(0);opacity:1;}}}}
@media(min-width:560px){{
  .modal-overlay{{align-items:center;}}
  .modal{{border-radius:14px;width:90%;animation:fscale .2s cubic-bezier(.4,0,.2,1);}}
  @keyframes fscale{{from{{transform:scale(.96);opacity:0;}}to{{transform:scale(1);opacity:1;}}}}
}}
.modal::before{{content:'';display:block;width:36px;height:4px;background:var(--border2);border-radius:2px;margin:0 auto 16px;}}
@media(min-width:560px){{.modal::before{{display:none;}}}}
.modal-title{{font-family:var(--serif);font-size:19px;color:var(--gold);margin-bottom:3px;}}
.modal-sub{{font-size:12px;color:var(--text3);margin-bottom:16px;}}
.frow{{margin-bottom:12px;}}
.flabel{{display:block;font-size:10px;color:var(--text3);text-transform:uppercase;letter-spacing:.8px;font-family:var(--mono);margin-bottom:5px;}}
.finput,.fselect,.ftextarea{{
  width:100%;background:var(--bg3);border:1px solid var(--border2);border-radius:8px;
  color:var(--text);font-family:var(--sans);font-size:14px;padding:9px 11px;
  outline:none;transition:border .15s;-webkit-appearance:none;appearance:none;
}}
.finput:focus,.fselect:focus,.ftextarea:focus{{border-color:var(--accent);}}
.ftextarea{{resize:vertical;min-height:62px;font-family:var(--mono);font-size:13px;}}
.mact{{display:flex;gap:8px;justify-content:flex-end;margin-top:18px;flex-wrap:wrap;}}
.btn-cancel{{flex:0 0 auto;padding:10px 16px;border:1px solid var(--border2);background:transparent;color:var(--text2);font-family:var(--sans);font-size:13px;cursor:pointer;border-radius:8px;min-height:44px;transition:all .15s;}}
.btn-cancel:hover{{background:var(--surface);color:var(--text);}}
.btn-ok{{flex:1 1 auto;padding:10px 18px;border:none;background:var(--accent2);color:#fff;font-family:var(--sans);font-size:13px;font-weight:600;cursor:pointer;border-radius:8px;min-height:44px;transition:background .15s;}}
.btn-ok:hover{{background:var(--accent);}}
.bi{{padding:7px 12px;border:1px solid var(--border2);background:var(--bg3);color:var(--text2);font-family:var(--sans);font-size:12px;cursor:pointer;border-radius:7px;min-height:36px;transition:all .15s;white-space:nowrap;}}
.bi:hover{{background:var(--surf2);color:var(--text);}}
.bd{{padding:7px 12px;border:1px solid rgba(224,96,96,.25);background:rgba(224,96,96,.06);color:var(--coral);font-family:var(--sans);font-size:12px;cursor:pointer;border-radius:7px;min-height:36px;transition:all .15s;white-space:nowrap;}}
.bd:hover{{background:rgba(224,96,96,.15);border-color:var(--coral);}}
.lhint{{background:rgba(232,169,74,.08);border:1px solid rgba(232,169,74,.25);border-radius:8px;padding:9px 13px;font-size:12px;color:var(--gold);margin-bottom:13px;line-height:1.6;}}

::-webkit-scrollbar{{width:5px;}}
::-webkit-scrollbar-track{{background:transparent;}}
::-webkit-scrollbar-thumb{{background:var(--border2);border-radius:3px;}}
</style>
</head>
<body>
<div id="shell">

<!-- TOP BAR -->
<div id="topbar">
  <span id="tb-title">⬡ LUMINA</span>
  <div class="tsep" style="margin:0 3px;"></div>
  <button class="tbtn active" id="tool-select" onclick="setTool('select')" title="Selecionar (S)">⬚ Sel</button>
  <button class="tbtn" onclick="openAddModal()" title="Novo Nó (N)">＋ Nó</button>
  <button class="tbtn" id="tool-link" onclick="setTool('link')" title="Criar Link (L)">→ Link</button>
  <div class="tsep" style="margin:0 3px;"></div>
  <button class="tbtn" onclick="zoomReset()" title="Reset zoom (R)">◎</button>
  <button class="tbtn danger" onclick="deleteSelected()" title="Excluir (Del)">✕</button>
  <div class="tsep"></div>
  <button class="tbtn" onclick="manualSave()">💾 Salvar</button>
  <button class="tbtn" onclick="refreshFromCloud()">↻ Recarregar</button>
  <div id="save-ind">pronto</div>
</div>

<!-- MAIN ROW -->
<div id="main">

  <!-- CANVAS -->
  <div id="canvas-wrap">
    <div id="zoom-chip">75%</div>
    <div id="cld-canvas"></div>
    <svg id="cld-svg"></svg>

    <!-- BOTTOM TOOLBAR -->
    <div id="toolbar">
      <button class="tbtn" onclick="zoomIn()">＋</button>
      <button class="tbtn" onclick="zoomOut()">－</button>
      <div class="tsep"></div>
      <button class="tbtn" onclick="zoomReset()">◎ Central.</button>
      <div class="tsep"></div>
      <button class="tbtn" id="toggle-panel-btn" onclick="togglePanel()">◧ Painel</button>
    </div>

    <!-- FAB (mobile only) -->
    <button id="fab" onclick="openSheet()" title="Ver detalhes">📋</button>

    <!-- MOBILE BACKDROP -->
    <div id="sheet-backdrop" onclick="closeSheet()"></div>

    <!-- MOBILE BOTTOM SHEET -->
    <div id="mobile-sheet">
      <div id="sheet-handle"></div>
      <div id="sheet-hdr">
        <span id="sheet-title">Detalhes</span>
        <button id="sheet-x" onclick="closeSheet()">✕</button>
      </div>
      <div id="sheet-body">
        <div class="ph"><div class="ico">⬡</div><p>Clique em um nó para ver detalhes.</p></div>
      </div>
      <div id="sheet-legend">
        <div class="legend-lbl">Categorias</div>
        <div class="legend-grid">
          <div class="legend-item"><div class="legend-dot" style="background:rgba(14,26,80,.9);border-color:#4a6aee"></div>Estado</div>
          <div class="legend-item"><div class="legend-dot" style="background:rgba(80,14,14,.9);border-color:#c04040"></div>Equação</div>
          <div class="legend-item"><div class="legend-dot" style="background:rgba(20,14,60,.9);border-color:#6040c0"></div>Parâmetro</div>
          <div class="legend-item"><div class="legend-dot" style="background:rgba(14,50,40,.9);border-color:#208060"></div>Ambiente</div>
          <div class="legend-item"><div class="legend-dot" style="background:rgba(70,30,8,.9);border-color:#c06020"></div>Input</div>
        </div>
      </div>
    </div>
  </div>

  <!-- DESKTOP RIGHT PANEL -->
  <div id="right-panel">
    <div class="panel-hdr">
      <span class="panel-title">Detalhes</span>
      <span id="panel-badge">SELECIONAR</span>
      <button class="panel-x" onclick="togglePanel()" title="Fechar painel">✕</button>
    </div>
    <div class="panel-body" id="panel-content">
      <div class="ph"><div class="ico">⬡</div><p>Clique em um nó para ver seus detalhes, relações e equação.</p></div>
    </div>
    <div class="panel-legend">
      <div class="legend-lbl">Categorias</div>
      <div class="legend-grid">
        <div class="legend-item"><div class="legend-dot" style="background:rgba(14,26,80,.9);border-color:#4a6aee"></div>Estado</div>
        <div class="legend-item"><div class="legend-dot" style="background:rgba(80,14,14,.9);border-color:#c04040"></div>Equação</div>
        <div class="legend-item"><div class="legend-dot" style="background:rgba(20,14,60,.9);border-color:#6040c0"></div>Parâmetro</div>
        <div class="legend-item"><div class="legend-dot" style="background:rgba(14,50,40,.9);border-color:#208060"></div>Ambiente</div>
        <div class="legend-item"><div class="legend-dot" style="background:rgba(70,30,8,.9);border-color:#c06020"></div>Input</div>
      </div>
    </div>
  </div>
</div><!-- /main -->
</div><!-- /shell -->

<!-- MODALS -->
<div class="modal-overlay" id="modal-add">
  <div class="modal">
    <div class="modal-title">Novo Nó</div>
    <div class="modal-sub">Crie uma nova variável no sistema</div>
    <div class="frow"><label class="flabel">Nome *</label><input class="finput" id="nn-name" placeholder="ex: Taxa_Adocao"></div>
    <div class="frow"><label class="flabel">Categoria</label>
      <select class="fselect" id="nn-cat">
        <option value="Estado">Estado</option><option value="Equação">Equação</option>
        <option value="Parâmetro">Parâmetro</option><option value="Ambiente">Ambiente</option>
        <option value="Input">Input</option>
      </select>
    </div>
    <div class="frow"><label class="flabel">Valor Inicial</label><input class="finput" id="nn-val" type="number" value="0" step="any"></div>
    <div class="frow"><label class="flabel">Equação (opcional)</label><textarea class="ftextarea" id="nn-eq" placeholder="ex: A * B + C"></textarea></div>
    <div class="frow"><label class="flabel">Descrição</label><textarea class="ftextarea" id="nn-desc" placeholder="Descreva o papel desta variável..."></textarea></div>
    <div class="mact">
      <button class="btn-cancel" onclick="closeModal('modal-add')">Cancelar</button>
      <button class="btn-ok" onclick="addNode()">Criar Nó</button>
    </div>
  </div>
</div>

<div class="modal-overlay" id="modal-edit">
  <div class="modal">
    <div class="modal-title">Editar Variável</div>
    <div class="modal-sub">Altere os atributos da variável selecionada</div>
    <input type="hidden" id="en-id">
    <div class="frow"><label class="flabel">Nome</label><input class="finput" id="en-name"></div>
    <div class="frow"><label class="flabel">Categoria</label>
      <select class="fselect" id="en-cat">
        <option value="Estado">Estado</option><option value="Equação">Equação</option>
        <option value="Parâmetro">Parâmetro</option><option value="Ambiente">Ambiente</option>
        <option value="Input">Input</option>
      </select>
    </div>
    <div class="frow"><label class="flabel">Valor Atual</label><input class="finput" id="en-val" type="number" step="any"></div>
    <div class="frow"><label class="flabel">Equação</label><textarea class="ftextarea" id="en-eq"></textarea></div>
    <div class="frow"><label class="flabel">Descrição</label><textarea class="ftextarea" id="en-desc"></textarea></div>
    <div class="mact">
      <button class="btn-cancel" onclick="closeModal('modal-edit')">Cancelar</button>
      <button class="btn-ok" onclick="saveEdit()">Salvar</button>
    </div>
  </div>
</div>

<div class="modal-overlay" id="modal-link">
  <div class="modal">
    <div class="modal-title">Nova Ligação</div>
    <div class="modal-sub">Defina a relação causal entre variáveis</div>
    <div class="lhint" id="link-hint">Selecione a origem e o destino da ligação.</div>
    <div class="frow"><label class="flabel">De (Origem)</label><input class="finput" id="lk-from" readonly></div>
    <div class="frow"><label class="flabel">Para (Destino)</label><select class="fselect" id="lk-to"></select></div>
    <div class="frow"><label class="flabel">Sinal da Relação</label>
      <select class="fselect" id="lk-sign">
        <option value="+">＋ Positiva — A aumenta → B aumenta</option>
        <option value="-">－ Negativa — A aumenta → B diminui</option>
      </select>
    </div>
    <div class="frow"><label class="flabel">Descrição (opcional)</label><textarea class="ftextarea" id="lk-desc" placeholder="ex: Maior preço reduz o volume vendido"></textarea></div>
    <div class="mact">
      <button class="btn-cancel" onclick="closeModal('modal-link')">Cancelar</button>
      <button class="btn-ok" onclick="confirmLink()">Criar Ligação</button>
    </div>
  </div>
</div>

<script>
const JSONBIN_API_KEY = {ak};
const JSONBIN_BIN_ID  = {bi};
let SYS = {model_json};

// ── State ──
let selNode=null, lkSrc=null, curTool='select';
let isDrag=false, dragNode=null, dragOX=0, dragOY=0;
let panX=60,panY=60,scale=.75,isPan=false,panSX=0,panSY=0;
let saveTimer=null, isMobile=false;

const CAT_CLS={{Estado:'cat-estado',Equação:'cat-equacao',Parâmetro:'cat-parametro',Ambiente:'cat-ambiente',Input:'cat-input'}};
const CAT_COL={{Estado:'#6a8aff',Equação:'#ff9090',Parâmetro:'#c090ff',Ambiente:'#60ffa0',Input:'#ffb060'}};

// ── Save / Load manual ──
function setInd(cls,msg){{const e=document.getElementById('save-ind');e.className=cls;e.textContent=msg;}}

async function manualSave(){{
  if(!JSONBIN_API_KEY||!JSONBIN_BIN_ID){{setInd('error','sem credenciais');return;}}
  setInd('saving','⏳ salvando…');
  try{{
    const r=await fetch(`https://api.jsonbin.io/v3/b/${{JSONBIN_BIN_ID}}`,{{method:'PUT',headers:{{'Content-Type':'application/json','X-Master-Key':JSONBIN_API_KEY}},body:JSON.stringify(SYS)}});
    if(r.ok){{setInd('saved','✓ salvo');setTimeout(()=>setInd('','pronto'),2500);}}
    else setInd('error','✗ erro '+r.status);
  }}catch{{setInd('error','✗ sem conexão');}}
}}

async function refreshFromCloud(){{
  if(!JSONBIN_API_KEY||!JSONBIN_BIN_ID){{alert('Credenciais não configuradas.');return;}}
  setInd('saving','⏳ carregando…');
  try{{
    const r=await fetch(`https://api.jsonbin.io/v3/b/${{JSONBIN_BIN_ID}}/latest`,{{headers:{{'X-Master-Key':JSONBIN_API_KEY}}}});
    if(r.ok){{
      const data=await r.json();
      if(data.record && data.record.nodes){{
        SYS = data.record;
        selNode=null; lkSrc=null;
        renderAll();
        setInd('saved','✓ recarregado');
        setTimeout(()=>setInd('','pronto'),2500);
      }} else throw new Error();
    }} else throw new Error();
  }}catch{{setInd('error','✗ falha');}}
}}

// ── Zoom ──
function upZoom(){{document.getElementById('zoom-chip').textContent=Math.round(scale*100)+'%';}}
function applyXform(){{document.getElementById('cld-canvas').style.transform=`translate(${{panX}}px,${{panY}}px) scale(${{scale}})`; upZoom(); requestAnimationFrame(renderEdges);}}
function setScale(ns,cx,cy){{
  const w=document.getElementById('canvas-wrap');
  const mx=cx??w.clientWidth/2, my=cy??w.clientHeight/2;
  panX=mx-(mx-panX)*(ns/scale); panY=my-(my-panY)*(ns/scale); scale=ns;
  applyXform();
}}
function zoomIn(){{setScale(Math.min(2.5,scale*1.15));}}
function zoomOut(){{setScale(Math.max(.25,scale*.87));}}
function zoomReset(){{scale=.75;panX=60;panY=60;applyXform();renderAll();}}

// ── Render nodes ──
function renderAll(){{
  const cv=document.getElementById('cld-canvas');
  cv.innerHTML='';
  cv.style.transformOrigin='0 0';
  cv.style.transform=`translate(${{panX}}px,${{panY}}px) scale(${{scale}})`;
  for(const[id,nd] of Object.entries(SYS.nodes)){{
    const el=document.createElement('div');
    el.className='cld-node';
    el.id='node-'+id;
    el.style.left=nd.x+'px';
    el.style.top=nd.y+'px';
    el.innerHTML=`<div class="node-box ${{CAT_CLS[nd.cat]||'cat-estado'}}">${{id}}</div>`;
    if(selNode===id) el.classList.add('selected');
    if(lkSrc===id)  el.classList.add('lk-src');
    el.addEventListener('mousedown', e=>onNDown(e,id));
    el.addEventListener('touchstart',e=>{{e.preventDefault();onNDown(e,id);}},{{passive:false}});
    el.addEventListener('click',     e=>onNClick(e,id));
    el.addEventListener('touchend',  e=>{{e.preventDefault();onNClick(e,id);}});
    cv.appendChild(el);
  }}
  requestAnimationFrame(renderEdges);
  upZoom();
}}

// ── Render edges ──
function renderEdges(){{
  const svg=document.getElementById('cld-svg');
  const wrap=document.getElementById('canvas-wrap');
  const W=wrap.clientWidth, H=wrap.clientHeight;
  if(W===0||H===0){{setTimeout(renderEdges,50);return;}}
  svg.setAttribute('viewBox',`0 0 ${{W}} ${{H}}`);
  svg.setAttribute('width',W);
  svg.setAttribute('height',H);
  svg.innerHTML=`<defs>
    <marker id="a+" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M1 2L9 5L1 8" fill="none" stroke="#52c97a" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
    </marker>
    <marker id="a-" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M1 2L9 5L1 8" fill="none" stroke="#e06060" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
    </marker>
  </defs>`;
  for(const lk of SYS.links){{
    const fn=SYS.nodes[lk.from], tn=SYS.nodes[lk.to];
    if(!fn||!tn) continue;
    const fEl=document.getElementById('node-'+lk.from);
    const tEl=document.getElementById('node-'+lk.to);
    if(!fEl||!tEl) continue;
    const fx=fn.x*scale+panX, fy=fn.y*scale+panY;
    const tx=tn.x*scale+panX, ty=tn.y*scale+panY;
    const fw=fEl.offsetWidth*scale, fh=fEl.offsetHeight*scale;
    const tw=tEl.offsetWidth*scale, th=tEl.offsetHeight*scale;
    const dx=tx-fx, dy=ty-fy, dist=Math.hypot(dx,dy)||1;
    const ux=dx/dist, uy=dy/dist;
    const x1=fx+ux*Math.min(fw/2+2,Math.abs(fw/2/ux)||fw/2);
    const y1=fy+uy*Math.min(fh/2+2,Math.abs(fh/2/uy)||fh/2);
    const x2=tx-ux*Math.min(tw/2+6,Math.abs(tw/2/ux)||tw/2);
    const y2=ty-uy*Math.min(th/2+6,Math.abs(th/2/uy)||th/2);
    const cx=(x1+x2)/2-uy*20, cy=(y1+y2)/2+ux*20;
    const col=lk.sign==='+'?'#52c97a':'#e06060';
    const p=document.createElementNS('http://www.w3.org/2000/svg','path');
    p.setAttribute('d',`M${{x1}},${{y1}} Q${{cx}},${{cy}} ${{x2}},${{y2}}`);
    p.setAttribute('fill','none');p.setAttribute('stroke',col);
    p.setAttribute('stroke-width','1.5');p.setAttribute('stroke-opacity','.65');
    p.setAttribute('marker-end',`url(#a${{lk.sign}})`);
    const t=document.createElementNS('http://www.w3.org/2000/svg','text');
    t.setAttribute('x',cx);t.setAttribute('y',cy-5);
    t.setAttribute('text-anchor','middle');t.setAttribute('font-size','11');
    t.setAttribute('font-family','DM Mono,monospace');t.setAttribute('font-weight','700');
    t.setAttribute('fill',col);t.setAttribute('opacity','.9');
    t.textContent=lk.sign;
    svg.appendChild(p);svg.appendChild(t);
  }}
}}

// ── ResizeObserver: re-render edges when canvas-wrap changes size ──
const _ro=new ResizeObserver(()=>{{requestAnimationFrame(renderEdges);}});
_ro.observe(document.getElementById('canvas-wrap'));

// ── Pointer helpers ──
function pxy(e){{
  if(e.touches&&e.touches.length>0) return[e.touches[0].clientX,e.touches[0].clientY];
  if(e.changedTouches&&e.changedTouches.length>0) return[e.changedTouches[0].clientX,e.changedTouches[0].clientY];
  return[e.clientX,e.clientY];
}}

function onNDown(e,id){{
  if(curTool!=='select') return;
  e.stopPropagation();
  isDrag=false;dragNode=id;
  const[cx,cy]=pxy(e);
  const r=document.getElementById('canvas-wrap').getBoundingClientRect();
  dragOX=(cx-r.left-panX)/scale-SYS.nodes[id].x;
  dragOY=(cy-r.top-panY)/scale-SYS.nodes[id].y;
}}

function onNClick(e,id){{
  if(isDrag) return;
  e.stopPropagation();
  if(curTool==='link'){{
    if(!lkSrc){{
      lkSrc=id;
      document.getElementById('node-'+id)?.classList.add('lk-src');
      document.getElementById('link-hint').textContent=`Origem: "${{id}}" — selecione o destino abaixo.`;
      document.getElementById('lk-from').value=id;
      fillLinkTo(id);
      openModal('modal-link');
    }}else if(lkSrc!==id){{
      document.getElementById('lk-to').value=id;
      confirmLink();
    }}
    return;
  }}
  selectNode(id);
}}

function selectNode(id){{
  document.querySelectorAll('.cld-node').forEach(e=>e.classList.remove('selected'));
  selNode=id;
  document.getElementById('node-'+id)?.classList.add('selected');
  const html=buildDetail(id);
  document.getElementById('panel-content').innerHTML=html;
  document.getElementById('sheet-body').innerHTML=html;
  document.getElementById('fab').classList.add('node-sel');
  if(isMobile) openSheet();
}}

function deselect(){{
  document.querySelectorAll('.cld-node').forEach(e=>e.classList.remove('selected'));
  selNode=null;
  const ph='<div class="ph"><div class="ico">⬡</div><p>Clique em um nó para ver seus detalhes.</p></div>';
  document.getElementById('panel-content').innerHTML=ph;
  document.getElementById('sheet-body').innerHTML=ph;
  document.getElementById('fab').classList.remove('node-sel');
}}

function fillLinkTo(excl){{
  document.getElementById('lk-to').innerHTML=
    Object.keys(SYS.nodes).filter(n=>n!==excl).map(n=>`<option value="${{n}}">${{n}}</option>`).join('');
}}

// ── Detail builder ──
function buildDetail(id){{
  const nd=SYS.nodes[id]; if(!nd) return '';
  const out=SYS.links.filter(l=>l.from===id);
  const inc=SYS.links.filter(l=>l.to===id);
  const col=CAT_COL[nd.cat]||'#aaa';
  const fmtVal=v=>typeof v==='number'?v.toPrecision(6).replace(/\\.?0+$/,''):v;
  let h=`<div class="dn-name">${{id}}</div><div class="dn-cat" style="color:${{col}}">${{nd.cat}}</div>`;
  h+=`<div class="dl">Descrição</div><div class="dd">${{nd.desc||'—'}}</div>`;
  h+=`<div class="dl">Valor Atual</div><div class="dv">${{fmtVal(nd.val)}}</div>`;
  if(nd.expr) h+=`<div class="dl">Equação</div><div class="deq">${{nd.expr}}</div>`;
  if(inc.length){{
    h+=`<div class="dl">Causas (${{inc.length}})</div>`;
    inc.forEach(l=>h+=`<div class="rel-row"><span class="rsgn ${{l.sign==='+'?'rpos':'rneg'}}">${{l.sign}}</span><span style="color:var(--text2)">${{l.from}}</span></div>`);
  }}
  if(out.length){{
    h+=`<div class="dl">Efeitos (${{out.length}})</div>`;
    out.forEach(l=>h+=`<div class="rel-row"><span class="rsgn ${{l.sign==='+'?'rpos':'rneg'}}">${{l.sign}}</span><span style="color:var(--text2)">${{l.to}}</span></div>`);
  }}
  h+=`<div class="dact">
    <button class="bi" onclick="openEditModal('${{id}}')">✎ Editar</button>
    <button class="bi" onclick="startLinkFrom('${{id}}')">+ Link</button>
    <button class="bd" onclick="deleteNode('${{id}}')">✕ Excluir</button>
  </div>`;
  return h;
}}

// ── Canvas pan/drag ──
const wrap=document.getElementById('canvas-wrap');

function onWrapDown(e){{
  const t=e.target;
  const isBackground=t===wrap||t===document.getElementById('cld-canvas')||t===document.getElementById('cld-svg')||t.closest('#cld-svg');
  if(isBackground){{
    isPan=true;
    const[cx,cy]=pxy(e);
    panSX=cx-panX;panSY=cy-panY;
    deselect();
    if(isMobile) closeSheet();
  }}
}}
wrap.addEventListener('mousedown',onWrapDown);
wrap.addEventListener('touchstart',e=>{{e.preventDefault();onWrapDown(e);}},{{passive:false}});

function onMove(e){{
  const[cx,cy]=pxy(e);
  if(dragNode){{
    const r=wrap.getBoundingClientRect();
    SYS.nodes[dragNode].x=(cx-r.left-panX)/scale-dragOX;
    SYS.nodes[dragNode].y=(cy-r.top-panY)/scale-dragOY;
    isDrag=true;
    renderAll();
  }}else if(isPan){{
    panX=cx-panSX;panY=cy-panSY;
    document.getElementById('cld-canvas').style.transform=`translate(${{panX}}px,${{panY}}px) scale(${{scale}})`;
    requestAnimationFrame(renderEdges);
  }}
}}
function onUp(){{dragNode=null;isPan=false;setTimeout(()=>{{isDrag=false;}},50);}}
document.addEventListener('mousemove',onMove);
document.addEventListener('mouseup',onUp);
document.addEventListener('touchmove',e=>{{e.preventDefault();onMove(e);}},{{passive:false}});
document.addEventListener('touchend',onUp);

// Pinch zoom
let pinchD=null;
wrap.addEventListener('touchstart',e=>{{if(e.touches.length===2)pinchD=null;}},{{passive:true}});
wrap.addEventListener('touchmove',e=>{{
  if(e.touches.length!==2) return;
  e.preventDefault();
  const d=Math.hypot(e.touches[0].clientX-e.touches[1].clientX,e.touches[0].clientY-e.touches[1].clientY);
  if(pinchD!==null){{
    const r=wrap.getBoundingClientRect();
    const cx=(e.touches[0].clientX+e.touches[1].clientX)/2-r.left;
    const cy=(e.touches[0].clientY+e.touches[1].clientY)/2-r.top;
    setScale(Math.max(.25,Math.min(2.5,scale*(d/pinchD))),cx,cy);
  }}
  pinchD=d;
}},{{passive:false}});

// Mouse wheel
wrap.addEventListener('wheel',e=>{{
  e.preventDefault();
  const r=wrap.getBoundingClientRect();
  setScale(Math.max(.25,Math.min(2.5,scale*(e.deltaY>0?.9:1.1))),e.clientX-r.left,e.clientY-r.top);
}},{{passive:false}});

// ── Tools ──
function setTool(t){{
  curTool=t;lkSrc=null;
  document.querySelectorAll('.cld-node').forEach(e=>e.classList.remove('lk-src'));
  document.querySelectorAll('.tbtn[id^="tool-"]').forEach(b=>b.classList.remove('active'));
  document.getElementById('tool-'+t)?.classList.add('active');
  const badge=t==='select'?'SELECIONAR':'CRIAR LINK';
  document.getElementById('panel-badge').textContent=badge;
  if(t==='link'){{
    document.getElementById('lk-from').value='';
    fillLinkTo('');
    openModal('modal-link');
  }}
}}
function deleteSelected(){{if(selNode)deleteNode(selNode);}}
function deleteNode(id){{
  delete SYS.nodes[id];
  SYS.links=SYS.links.filter(l=>l.from!==id&&l.to!==id);
  selNode=null;
  const ph='<div class="ph"><div class="ico">⬡</div><p>Nó excluído.</p></div>';
  document.getElementById('panel-content').innerHTML=ph;
  document.getElementById('sheet-body').innerHTML=ph;
  document.getElementById('fab').classList.remove('node-sel');
  renderAll();
  if(isMobile)closeSheet();
}}
function startLinkFrom(id){{
  lkSrc=id;
  document.getElementById('lk-from').value=id;
  document.getElementById('link-hint').textContent=`Origem: "${{id}}" — selecione o destino.`;
  fillLinkTo(id);
  openModal('modal-link');
}}

// ── Panel (desktop) ──
let panelVisible=true;
function togglePanel(){{
  panelVisible=!panelVisible;
  const rp=document.getElementById('right-panel');
  const btn=document.getElementById('toggle-panel-btn');
  if(panelVisible){{rp.classList.remove('panel-hidden');btn.textContent='◨ Painel';}}
  else{{rp.classList.add('panel-hidden');btn.textContent='◧ Painel';}}
  setTimeout(renderEdges,300);
}}

// ── Mobile sheet ──
function openSheet(){{document.getElementById('mobile-sheet').classList.add('open');document.getElementById('sheet-backdrop').classList.add('open');}}
function closeSheet(){{document.getElementById('mobile-sheet').classList.remove('open');document.getElementById('sheet-backdrop').classList.remove('open');}}

// ── Modals ──
function openModal(id){{document.getElementById(id).classList.add('open');}}
function closeModal(id){{
  document.getElementById(id).classList.remove('open');
  if(id==='modal-link'){{
    lkSrc=null;
    document.querySelectorAll('.cld-node').forEach(e=>e.classList.remove('lk-src'));
    if(curTool==='link')setTool('select');
  }}
}}
document.querySelectorAll('.modal-overlay').forEach(o=>{{
  o.addEventListener('click',e=>{{if(e.target===o)closeModal(o.id);}});
}});

// ── CRUD Nodes ──
function openAddModal(){{openModal('modal-add');}}
function addNode(){{
  const name=document.getElementById('nn-name').value.trim();
  if(!name){{alert('Nome é obrigatório.');return;}}
  if(SYS.nodes[name]){{alert(`"${{name}}" já existe.`);return;}}
  SYS.nodes[name]={{
    cat:document.getElementById('nn-cat').value,
    val:parseFloat(document.getElementById('nn-val').value)||0,
    expr:document.getElementById('nn-eq').value.trim(),
    desc:document.getElementById('nn-desc').value.trim()||'Sem descrição.',
    x:400+Math.random()*200,y:280+Math.random()*120
  }};
  closeModal('modal-add');
  ['nn-name','nn-eq','nn-desc'].forEach(i=>document.getElementById(i).value='');
  document.getElementById('nn-val').value='0';
  renderAll();selectNode(name);
}}
function openEditModal(id){{
  const nd=SYS.nodes[id];
  document.getElementById('en-id').value=id;
  document.getElementById('en-name').value=id;
  document.getElementById('en-cat').value=nd.cat;
  document.getElementById('en-val').value=nd.val;
  document.getElementById('en-eq').value=nd.expr||'';
  document.getElementById('en-desc').value=nd.desc||'';
  openModal('modal-edit');
}}
function saveEdit(){{
  const oldId=document.getElementById('en-id').value;
  const newName=document.getElementById('en-name').value.trim();
  if(!newName){{alert('Nome é obrigatório.');return;}}
  if(newName!==oldId&&SYS.nodes[newName]){{alert('Nome já existe.');return;}}
  const nd=SYS.nodes[oldId];
  nd.cat=document.getElementById('en-cat').value;
  nd.val=parseFloat(document.getElementById('en-val').value)||0;
  nd.expr=document.getElementById('en-eq').value.trim();
  nd.desc=document.getElementById('en-desc').value.trim()||'Sem descrição.';
  if(newName!==oldId){{
    SYS.nodes[newName]=nd;delete SYS.nodes[oldId];
    SYS.links.forEach(l=>{{if(l.from===oldId)l.from=newName;if(l.to===oldId)l.to=newName;}});
    selNode=newName;
  }}
  closeModal('modal-edit');
  renderAll();
  if(selNode){{
    const h=buildDetail(selNode);
    document.getElementById('panel-content').innerHTML=h;
    document.getElementById('sheet-body').innerHTML=h;
  }}
}}
function confirmLink(){{
  const from=document.getElementById('lk-from').value||lkSrc;
  const to=document.getElementById('lk-to').value;
  const sign=document.getElementById('lk-sign').value;
  const desc=document.getElementById('lk-desc').value.trim()||`${{from}} ${{sign==='+'?'reforça':'reduz'}} ${{to}}`;
  if(!from||!to||from===to){{alert('Origem e destino devem ser diferentes.');return;}}
  const ex=SYS.links.find(l=>l.from===from&&l.to===to);
  if(ex){{ex.sign=sign;ex.desc=desc;}}
  else SYS.links.push({{from,to,sign,desc}});
  document.getElementById('lk-desc').value='';
  closeModal('modal-link');lkSrc=null;setTool('select');
  renderAll();
}}

// ── Keyboard ──
document.addEventListener('keydown',e=>{{
  if(['INPUT','TEXTAREA','SELECT'].includes(e.target.tagName)) return;
  if(e.key==='s'||e.key==='S') setTool('select');
  if(e.key==='l'||e.key==='L') setTool('link');
  if(e.key==='n'||e.key==='N') openAddModal();
  if(e.key==='r'||e.key==='R') zoomReset();
  if(e.key==='Delete'||e.key==='Backspace') deleteSelected();
  if(e.key==='Escape'){{document.querySelectorAll('.modal-overlay.open').forEach(m=>closeModal(m.id));closeSheet();}}
}});

// ── Responsive init ──
function initResponsive(){{
  isMobile=window.innerWidth<700;
  if(isMobile){{
    document.getElementById('fab').classList.add('show');
    document.getElementById('toggle-panel-btn').style.display='none';
    document.getElementById('mobile-sheet').style.display='flex';
    document.getElementById('right-panel').style.display='none';
  }}else{{
    document.getElementById('fab').classList.remove('show');
    document.getElementById('toggle-panel-btn').style.display='';
    document.getElementById('mobile-sheet').style.display='none';
    document.getElementById('right-panel').style.display='flex';
  }}
}}
window.addEventListener('resize',()=>{{
  initResponsive();
  requestAnimationFrame(renderEdges);
}});
initResponsive();
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

with tab_cld:
    components.html(
        get_simulator_html(
            model_json=json.dumps(SYSTEM),
            js_api_key=api_key,
            js_bin_id=bin_id,
        ),
        height=660,
        scrolling=False,
    )
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Recarregar modelo da nuvem (Streamlit)", use_container_width=True):
            fresh = load_system()
            st.session_state.system = fresh
            st.session_state.initial_vals = {k: v["val"] for k, v in fresh["nodes"].items()}
            st.rerun()
    with col2:
        if api_key and bin_id:
            st.caption(
                "✅ Persistência ativa — edições feitas aqui no diagrama só chegam à aba "
                "▶ Simulação depois que você clicar em 💾 Salvar (no diagrama) e depois em "
                "🔄 Recarregar modelo da nuvem (Streamlit) ao lado. São dois estados "
                "diferentes (JS do diagrama vs. Python da simulação) sincronizados via nuvem."
            )
        else:
            st.caption("⚠️ Configure [jsonbin] nas Secrets para persistência")

with tab_sim:
    st.markdown("### KPIs do Ciclo Atual")
    rent    = SYSTEM["nodes"].get("Rentabilidade", {}).get("val", 0)
    receita = SYSTEM["nodes"].get("Receita",       {}).get("val", 0)
    qt      = SYSTEM["nodes"].get("Qt",            {}).get("val", 0)
    st_mk   = SYSTEM["nodes"].get("St",            {}).get("val", 0)

    kpi_cols = st.columns(4)
    for col, (lbl, val) in zip(kpi_cols, [
        ("Rentabilidade", f"R$ {rent/1000:.1f}k"),
        ("Receita Ciclo", f"R$ {receita:,.0f}"),
        ("Qt Atendida",   f"{qt:.0f}"),
        ("Market Share",  f"{st_mk*100:.2f}%"),
    ]):
        with col:
            st.markdown(f'<div class="card"><div class="kpi-label">{lbl}</div><div class="kpi-value">{val}</div></div>', unsafe_allow_html=True)

    st.markdown("### Decisões de Input")
    input_keys  = ['Pt','budget_update','budget_training','budget_infra','budget_promo','Nc']
    label_map   = {'Pt':'Preço (Pt)','budget_update':'P&D','budget_training':'Treinamento',
                   'budget_infra':'Infraestrutura','budget_promo':'Marketing','Nc':'Concorrentes'}
    input_cols  = st.columns(len(input_keys))
    for i, key in enumerate(input_keys):
        if key in SYSTEM["nodes"]:
            nd = SYSTEM["nodes"][key]
            step = 100.0 if nd["val"] > 10 else 0.01
            new_val = input_cols[i].number_input(label_map.get(key, key), value=float(nd["val"]), step=step, format="%.4g")
            if new_val != nd["val"]:
                nd["val"] = float(new_val)
                st.session_state.initial_vals[key] = float(new_val)
                save_system(SYSTEM)

    st.markdown(f"**Ciclo atual:** {st.session_state.sim_cycle}")
    adv_c, res_c = st.columns([3, 1])
    with adv_c:
        if st.button("▶ Avançar Ciclo", use_container_width=True):
            # Antes: recalculava tudo a partir de um único snapshot antigo,
            # fazendo com que Qt/Receita/Custos/Rentabilidade levassem vários
            # cliques para refletir qualquer mudança (ver `advance_cycle`
            # para a explicação completa). Agora a cadeia causal inteira é
            # resolvida corretamente dentro do mesmo ciclo.
            advance_cycle(SYSTEM)
            st.session_state.sim_cycle += 1
            profit = SYSTEM["nodes"].get("Receita", {}).get("val", 0) - SYSTEM["nodes"].get("Custos", {}).get("val", 0)
            st.session_state.sim_history.append({
                "cycle": st.session_state.sim_cycle,
                "profit": profit,
                "rentabilidade": SYSTEM["nodes"].get("Rentabilidade", {}).get("val", 0),
            })
            save_system(SYSTEM); st.rerun()
    with res_c:
        if st.button("↺ Reiniciar", use_container_width=True):
            for k, v in st.session_state.initial_vals.items():
                if k in SYSTEM["nodes"]: SYSTEM["nodes"][k]["val"] = v
            st.session_state.sim_cycle   = 0
            st.session_state.sim_history = []
            save_system(SYSTEM); st.rerun()

    if st.session_state.sim_history:
        hist  = st.session_state.sim_history
        cc    = [h["cycle"] for h in hist]
        rv    = [h["rentabilidade"] for h in hist]
        pv    = [h["profit"] for h in hist]
        gc1, gc2 = st.columns(2)
        with gc1:
            fig1 = go.Figure()
            fig1.add_trace(go.Bar(x=cc, y=rv, marker_color=['#4a6aee' if v>=0 else '#e06060' for v in rv], name="Rentabilidade"))
            fig1.update_layout(title="Rentabilidade Acumulada", template="plotly_dark", height=260, margin=dict(l=10,r=10,t=40,b=20), font=dict(family="DM Sans"))
            st.plotly_chart(fig1, use_container_width=True)
        with gc2:
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(x=cc, y=pv, marker_color=['#52c97a' if v>=0 else '#e06060' for v in pv], name="Lucro"))
            fig2.update_layout(title="Lucro Líquido por Ciclo", template="plotly_dark", height=260, margin=dict(l=10,r=10,t=40,b=20), font=dict(family="DM Sans"))
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("▶ Avance alguns ciclos para visualizar os gráficos.")

with tab_vars:
    st.markdown("### Variáveis do Sistema")
    search = st.text_input("🔍 Filtrar", placeholder="Nome ou categoria…")
    data = []
    for nid, nd in SYSTEM["nodes"].items():
        v = round(nd["val"], 6) if isinstance(nd["val"], float) else nd["val"]
        data.append({"Variável": nid, "Categoria": nd["cat"], "Valor Atual": v,
                     "Equação": nd.get("expr","—") or "—", "Descrição": (nd.get("desc","") or "")[:90]})
    df = pd.DataFrame(data)
    if search:
        mask = df["Variável"].str.contains(search,case=False,na=False)|df["Categoria"].str.contains(search,case=False,na=False)
        df   = df[mask]
    st.dataframe(df, use_container_width=True, hide_index=True,
        column_config={
            "Variável":    st.column_config.TextColumn("Variável",    width="medium"),
            "Categoria":   st.column_config.TextColumn("Categoria",   width="small"),
            "Valor Atual": st.column_config.NumberColumn("Valor Atual", format="%.5g"),
            "Equação":     st.column_config.TextColumn("Equação",     width="large"),
            "Descrição":   st.column_config.TextColumn("Descrição",   width="large"),
        })
    st.markdown(f"**{len(df)} de {len(SYSTEM['nodes'])} variáveis**")
    sel = st.selectbox("Ir para variável:", options=[""]+sorted(SYSTEM["nodes"].keys()))
    if sel:
        st.session_state.selected_node = sel
        st.info(f"Variável **{sel}** selecionada. Volte à aba Diagrama para editá-la.")

st.markdown("---")
st.caption("⬡ LUMINA · Simulador de Laços Causais · Streamlit Colaborativo")
