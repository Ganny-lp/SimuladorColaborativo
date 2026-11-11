# LUMINA · Simulador de Laços Causais

Simulador didático mensal de uma assistência técnica, com diagrama editável e decisões de preço, investimentos, equipe, estoque e ambiente.

```bash
python -m pip install -r requirements-dev.txt
python -m streamlit run app.py
python -m pytest -q
```

`streamlit run sim.py` abre a mesma aplicação; o motor duplicado antigo foi retirado.

## Modelo e premissas

Veja [modelo-simulacao.md](docs/modelo-simulacao.md) para o mapeamento dos pontos da análise de 11/11/2026 para equações e comportamentos executáveis.

O modelo padrão não utiliza preços de outras assistências. Pt é o preço praticado, escolhido pelo participante; o preço sugerido considera custos, impostos, margem e volume. O preço de equipamento novo representa a alternativa de substituir o produto.

As variáveis Input são descobertas pelo frontend e exibidas por tema. Frações aparecem como porcentagens, com escala e campo exato sincronizados. A digitação e o teclado continuam disponíveis. Alterar uma entrada recalcula os indicadores sem avançar estados. Estoques e desembolsos iniciais são reaplicados ao reiniciar; mudanças após o primeiro ciclo não retroagem sobre o histórico.

Cada ciclo calcula taxas com os estoques iniciais do mês e atualiza todos os estados simultaneamente. Fila, estoque e caixa obedecem a balanços. Resultados com divisão por zero, nomes inexistentes, ciclos algébricos ou números não finitos interrompem a operação sem aplicar um ciclo parcial.

Os coeficientes comportamentais são hipóteses didáticas e precisam de calibração para uso empírico. Nc é uma contagem regional fornecida pelo participante: não há conexão a uma base municipal.

## Persistência opcional

Crie `.streamlit/secrets.toml` (arquivo local ignorado pelo Git):

```toml
[jsonbin]
api_key = "SUA_CHAVE"
bin_id = "SEU_BIN_ID"
```

Sem configuração, o modelo padrão funciona localmente. Edições estruturais feitas no diagrama requerem Salvar e Recarregar modelo para chegar à simulação. Estados de simulação não são publicados ao avançar ou reiniciar.

O editor de diagrama ainda acessa JSONBin pelo navegador e recebe a chave configurada. Essa é uma limitação da arquitetura existente: use credencial restrita ao bin. A revisão não altera o protocolo de persistência do editor.

## Organização

| Área | Responsabilidade |
|---|---|
| `backend/domain` | Entidades, avaliação segura de equações, ordem causal e balanços |
| `backend/application` | Casos de uso, contratos, publicação e mapeamento JSON |
| `backend/infrastructure` | Modelo padrão e repositórios JSONBin/local |
| `frontend/components` | Controles, indicadores, diagrama, tabelas e gráficos |
| `frontend/views` | Abas de simulação, diagrama e variáveis |
| `composition_root.py` | Montagem das dependências |
| `packaging` | Empacotamento Windows com PyInstaller |

O modelo 2 substitui as equações padrão dos modelos antigos durante a migração, preservando decisões e posições existentes. Nós adicionais são preservados; fórmulas que dependam do parâmetro de preço retirado precisam ser reformuladas.

## Validação

A suíte cobre cenários de inflação, sobrecarga, estoque/fornecedores, técnicos, reinvestimento e financiamento; conservação de caixa/estoque; migração; validação de modelos; transações de ciclo; busca literal e fluxos reais do Streamlit com AppTest. O workflow de CI executa Python 3.11/3.12 e verifica a sintaxe do editor JavaScript.

Os testes de interface automatizados não substituem a inspeção visual em navegadores e dispositivos. Os instaladores já presentes em `build/` e `installer/` são versões antigas: devem ser reconstruídos pelo processo em `packaging/` para distribuir as mudanças.
