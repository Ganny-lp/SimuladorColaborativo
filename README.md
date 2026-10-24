# ⬡ LUMINA · Simulador de Laços Causais

Reescrita do `sim.py` (script único de ~1.600 linhas) em **Clean Architecture**, orientada a
objetos, com **backend e frontend separados**. Continua sendo um app **Streamlit**.

```bash
pip install -r requirements.txt
streamlit run app.py
```

Persistência na nuvem (opcional): copie `.streamlit/secrets.toml.example` para
`.streamlit/secrets.toml` e preencha `api_key` / `bin_id` do JSONBin. Sem isso o app roda
normalmente com o modelo padrão.

Testes: `pip install -r requirements-dev.txt && pytest`

---

## Arquitetura

```
                ┌───────────────────────── backend ─────────────────────────┐
                │                                                           │
 frontend ───▶  │  application  ───▶  domain                                │
 (Streamlit)    │  casos de uso       entidades + serviços (regras puras)   │
      │         │  portas (ABC)                  ▲                          │
      │         │  DTOs / mappers                │ implementa portas        │
      │         │                         infrastructure                    │
      │         │                         JSONBin, modelo padrão (JSON)     │
      │         └───────────────────────────────────────────────────────────┘
      └── só enxerga application (use cases + DTOs). Nunca domain/infrastructure.

 composition_root.py  → único lugar que conhece todas as camadas (injeção de dependência)
 app.py               → entrypoint fino do Streamlit
```

A regra de dependência é **verificada automaticamente** por `tests/test_architecture.py`
(lê os imports de cada arquivo e falha se uma camada importar algo proibido).

### Estrutura

```
app.py                         entrypoint Streamlit (3 linhas)
composition_root.py            monta o grafo de objetos
backend/
  domain/                      ← regras de negócio, sem I/O nem framework
    constants.py               nomes de variáveis do modelo (sem magic strings)
    entities/                  Node, Link, CausalSystem, PriceScale, Simulation, CycleRecord
    services/
      expression_evaluator.py  avalia equações (AST + whitelist, sem eval)
      reference_finder.py      quais variáveis uma equação usa
      dependency_graph.py      ordem topológica + nós com memória
      simulation_engine.py     advance_cycle / recompute_derived / reset_state
      initial_state_calculator.py
      model_migrator.py        correções de equações antigas + estado limpo
  application/                 ← casos de uso
    ports/                     ModelRepository, SimulationStore, DefaultModelProvider
    use_cases/                 Start, GetSnapshot, ChangeInput, AdvanceCycle, Restart
    services/model_publisher.py  publica só o MODELO (estado sempre no valor inicial)
    mappers/                   dict JSON ⇄ domínio ; domínio → SimulationSnapshot
    dto.py                     contratos imutáveis entregues ao frontend
  infrastructure/              ← detalhes técnicos
    persistence/               JsonBinModelRepository, NullModelRepository, default_model.json
    config/settings.py         credenciais (lidas de st.secrets pela composition root)
frontend/
  config.py  formatters.py  compat.py
  session/                     adaptador SimulationStore sobre st.session_state, UiState
  assets/                      HTML/CSS/JS do diagrama, da régua e do tema (arquivos reais!)
  components/                  Theme, PageHeader, KpiCards, PriceSlider, CldDiagram,
                               CycleCharts, VariablesTable
  views/                       Tab (ABC) → DiagramTab, SimulationTab, VariablesTab ; MainPage
tests/                         domain · application · infrastructure · frontend · architecture
```

### Como estender

| Quero…                                   | Mexo em…                                                        |
|------------------------------------------|-----------------------------------------------------------------|
| trocar JSONBin por outro banco           | nova classe em `infrastructure/persistence` + 1 linha na composition root |
| novo operador/função em equações         | `domain/services/expression_evaluator.py`                       |
| nova regra de simulação                  | `domain/services/simulation_engine.py`                          |
| nova ação do usuário                     | novo caso de uso em `application/use_cases` + chamá-lo numa view |
| nova aba                                 | subclasse de `Tab` + incluir na lista da composition root       |
| expor o backend por API REST (FastAPI)   | os casos de uso já são o contrato; basta um adaptador HTTP      |

---

## ⚠️ Diferenças em relação ao `sim.py` original

1. **Bug corrigido: `MIN`, `MAX` e `ABS` nunca funcionavam.** O original executava o `eval` com
   `__builtins__` vazio, então essas funções davam `NameError` → `0.0`. Na prática
   `Qt = MIN(Dpt*St, Cap)` era **sempre 0** (receita sempre 0, KPI "Qt Atendida" sempre 0).
   Agora funcionam. **Os resultados numéricos mudam por causa disso**; com o bug neutralizado
   nos dois lados, os dois motores batem exatamente (validado em 6 cenários × 8 ciclos).
2. `eval` substituído por um interpretador de AST com whitelist (equações não executam código).
3. Não grava mais na nuvem a cada *Avançar Ciclo* / *Reiniciar* (o modelo não muda nesses
   casos). Continua gravando ao alterar uma decisão de input.
4. Rentabilidade inicial era `-0.0` (KPI "R$ -0.0k"); agora `0.0`.
5. JS do diagrama: o formatador de valores transformava `100000` em `1` (removia zeros de
   inteiros); corrigido. Textos com `</script>` no modelo não quebram mais o iframe.
6. Falha ao salvar na nuvem agora avisa com um toast em vez de ser silenciosa.
7. Camada de compatibilidade (`frontend/compat.py`) para as APIs depreciadas
   (`components.html`, `use_container_width`).

## Limitação conhecida (herdada do original)

O diagrama roda no navegador e fala direto com o JSONBin, então a `api_key` é entregue ao
cliente. Use uma *Access Key* restrita ao bin (não a Master Key) ou, melhor, faça o diagrama
salvar via backend.
