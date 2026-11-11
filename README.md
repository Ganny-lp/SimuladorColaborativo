# LUMINA · Simulador Colaborativo

Simulador didático mensal de uma assistência técnica, com diagrama causal editável, decisões operacionais e acompanhamento financeiro. O modelo permite explorar cenários; não constitui previsão de mercado nem recomendação de investimento.

**Situação jurídica:** código disponibilizado para visualização, sob [licença provisória restritiva](LICENSE). Não é um projeto com licença de código aberto. Uso adicional depende de autorização dos titulares competentes.

## Começar

Recomendado: Python 3.12, ambiente virtual e execução a partir da raiz. CI cobre Python 3.11 e 3.12.

```bash
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m streamlit run app.py
```

Para executar sem ferramentas de desenvolvimento, instale `requirements.txt`. `streamlit run sim.py` usa a mesma aplicação. Os requisitos atuais são intervalos mínimos; não são um lockfile reproduzível. Antes de distribuir uma versão, registre as versões efetivamente testadas em ambiente limpo.

## Entender a simulação

| Etapa | Comportamento |
|---|---|
| Ciclo 0 | Preparação: receita, serviços concluídos e captação realizados são zero. Variáveis derivadas e preço sugerido são projeções. |
| Avançar ciclo | Calcula o mês com os estados iniciais, aplica os estoques simultaneamente e registra um resultado imutável. |
| Mudar decisão | Recalcula projeções para o próximo mês. Não altera o resultado do mês já concluído. |
| Reiniciar | Reaplica a configuração inicial e limpa os resultados e o histórico. |
| Simular abertura | Desativado por padrão. Ative antes de iniciar para configurar investimento e financiamento. |

A quantidade atendida representa **serviços equivalentes** em um modelo contínuo: pode ser fracionária. Não representa contagem observada de ordens de serviço reais. A captação é uma fração calculada de novos pedidos, não uma participação de mercado empiricamente medida.

Pt é o preço praticado, escolhido pelo participante. A sugestão de preço considera custos, volume e margem; não altera Pt automaticamente. Preço de equipamento novo representa a alternativa ao reparo, sem utilizar preços de outras assistências.

### Abertura, caixa e resultado

O investimento de abertura afeta o acumulado uma única vez no primeiro ciclo, se ativado. O financiamento entra no caixa uma vez; parcelas continuam até o prazo contratado. Reserva e estoque iniciais são os saldos operacionais do cenário. Sem abertura, não se contrata nova dívida nem se desconta investimento inicial.

Resultado mensal, fluxo de caixa, saldo operacional e rentabilidade acumulada são conceitos distintos. Compras de peças afetam caixa; o consumo é ajustado para não cobrar o mesmo estoque duas vezes. Veja [modelo e laços](docs/modelo-simulacao.md) e [configuração inicial e fontes](docs/experiencia-e-fontes.md).

## Dados, premissas e calibração

O programa não pode inferir parâmetros locais confiáveis apenas pelo tipo de negócio. Os valores padrão são hipóteses didáticas, não estimativas calibradas.

| Entrada | Evidência apropriada | Tratamento |
|---|---|---|
| Inflação | IPCA mensal IBGE, distribuído pelo BCB/SGS 433 | Consulta oficial antes de iniciar; converte porcentagem para fração, aceita deflação e registra referência/fonte. |
| Concorrentes | Estabelecimentos ativos por município e CNAE, base CNPJ | Contagem regional ainda exige apuração externa; registre fonte, recorte e data. |
| Carga tributária | Tributos efetivos / receita no período e regime da empresa | Observação contábil declarada, não alíquota universal. |
| Preço de equipamento | Cotações datadas de produtos comparáveis | Observação local declarada; explicitar amostra e critério de agregação. |
| Alfa e coeficientes comportamentais | Histórico de falhas/pedidos e estimação documentada | Estimativa empírica declarada, com amostra e método. Não há ajuste estatístico automático. |

No painel **Registrar evidência do cenário**, informe parâmetro, valor, fonte/recorte, referência e método. Taxas são frações (0,15 = 15%). A evidência é persistida junto do modelo e vinculada ao valor exato. Se o valor for alterado, a evidência anterior não o valida. Dados declarados não são verificados automaticamente; o aplicativo distingue observação, estimação e série oficial, sem rotular tudo como modelo validado.

Calibrar entradas não substitui validar o modelo em dados fora da amostra. Para uso empírico: definir município/CNAE e período, coletar dados auditáveis, estimar coeficientes, executar análise de sensibilidade e comparar previsões com resultados observados. Evite publicar documentos com dados pessoais ou segredos comerciais no campo de fonte; registre uma referência segura.

Fontes: [SGS 433 / BCB](https://www3.bcb.gov.br/sgspub/consultarValoresSeries.do?method=consultarSeries&series=433), [dados CNPJ / Receita Federal](https://www.gov.br/receitafederal/pt-br/assuntos/orientacao-tributaria/cadastros/cnpj). IPCA é referência macroeconômica, não índice específico de oficinas. Falha na consulta mantém o valor anterior e informa indisponibilidade.

## Persistência e segurança

Sem credenciais, o aplicativo funciona com estado da sessão e modelo padrão. Para JSONBin, crie `.streamlit/secrets.toml`, ignorado pelo Git:

```toml
[jsonbin]
api_key = "SUA_CHAVE_RESTRITA"
bin_id = "SEU_BIN_ID"
```

Nunca versionar credenciais, dados pessoais, relatórios privados ou chaves de produção. Não incluir chaves em logs, screenshots ou relatos de bugs. Se uma chave for exposta, revogue-a.

**Limitação existente:** o editor de diagrama acessa JSONBin pelo navegador e recebe a chave configurada. Use credencial restrita ao bin, não uma chave mestra; não hospede modelos confidenciais nessa arquitetura. A migração da escrita do editor para backend autenticado é pendente. Alterações na simulação e edições do diagrama compartilham o modelo remoto: evite edição concorrente sem coordenação.

Salvar no diagrama e Recarregar modelo sincronizam edições estruturais. Avançar e Reiniciar não publicam ciclos no modelo remoto. Evidências de calibração acompanham o JSON do modelo; sem persistência, duram apenas a sessão.

## Arquitetura e padrões de implementação

| Camada | Responsabilidade e regra |
|---|---|
| `backend/domain` | Entidades, avaliação AST, dependências, estoques; sem Streamlit nem acesso à rede. |
| `backend/application` | Casos de uso, DTOs, validação de operações, publicação; dependências concretas injetadas. |
| `backend/infrastructure` | JSONBin, modelo padrão e acesso a dados externos, com timeout e validação. |
| `frontend` | Apresentação e estado visual; usa casos de uso e DTOs. |
| `composition_root.py` | Monta o grafo de dependências. |

Regras para mudanças: separar resultado concluído de projeção; preservar atomicidade em falhas; usar nós Estado para atrasos em laços; rejeitar ciclos algébricos, valores não finitos e referências inválidas; não executar equações com `eval`; validar unidades e proveniência dos dados. Mudanças no contrato de sessão exigem atualizar `APP_VERSION`.

## Testar e revisar

```bash
python -m pytest -q
python -m compileall -q backend frontend
node --check frontend/assets/cld_simulator.js
git diff --check
```

A suíte cobre balanços, abertura única, financiamento, cenários, snapshots, interface Streamlit e fontes externas simuladas. Testes de rede usam mocks para serem determinísticos. CI é definida em `.github/workflows/tests.yml`.

Antes de mesclar: descrever problema e comportamento final, registrar validações e limitações, revisar efeitos em equações/migração/persistência e conferir visualmente desktop e mobile. AppTest não verifica alinhamento em navegador real. Casos essenciais: iniciar, mudar decisões, avançar, reiniciar, ativar/desativar abertura, falhar ao consultar/salvar e recarregar o modelo.

Contribuições devem ser previamente coordenadas com o mantenedor, inclusive permissões de uso e direitos sobre código enviado. Reporte bugs em Issues com passos para reproduzir, versão do Python/app e resultado esperado, sem credenciais ou dados sensíveis.

## Distribuição e direitos

Instaladores já existentes em `build/` e `installer/` podem estar desatualizados. Reconstrua via [instruções de build](packaging/LEIA-ME-BUILD.md) antes de distribuir; esta mudança não reconstrói binários Windows.

[LICENSE](LICENSE) reserva provisoriamente os direitos sobre o material original aos respectivos titulares. O texto não atribui titularidade exclusiva ao mantenedor nem elimina eventuais direitos de coautores ou instituições. Dependências, dados e marcas de terceiros mantêm suas próprias condições. Permissões anteriores válidas não são revogadas retroativamente.

Nenhuma licença impede tecnicamente que um código público seja copiado. O GitHub permite visualização e forks nos limites dos seus termos; um fork não concede automaticamente outros direitos de exploração. Veja [orientação oficial do GitHub](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository). Proteção de software e registro são descritos pelo [INPI](https://www.gov.br/inpi/pt-br/acesso-a-informacao/perguntas-frequentes/programas-de-computador). A definição final de titularidade e licenciamento deve respeitar os contratos e vínculos do projeto.


## Calculadoras de fontes e amostras

No contexto de mercado, **Calcular a partir de fontes e amostras** oferece caminhos executáveis para os sete parâmetros restantes, sem aplicar amostras fictícias.

| Parâmetro | Fonte e operação | Limite |
|---|---|---|
| Carga tributária | [Resolução CGSN 140, arts. 21–22/Anexo III](https://normas.receita.fazenda.gov.br/sijut2consulta/link.action?idAto=92278), fórmula efetiva com RBT12 | Só cenário confirmado no Anexo III em 2026, RBT12 até R$ 3,6 milhões, sem exceções/ISS fora do DAS. Não substitui apuração fiscal. |
| Nc | Recorte completo do arquivo Estabelecimentos, [layout RFB](https://www.gov.br/receitafederal/dados/cnpj-metadados.pdf) | Filtra ativos, UF, código municipal Receita e CNAE principal; deduplica CNPJ e permite excluir a própria empresa. Não cobre informalidade nem CNAE secundário. |
| Preço de equipamento novo | Mediana de cotações novas de uma mesma especificação | Exige amostra datada e origem; não usa preços de concorrentes de reparo. |
| Alfa | Falhas / equipamento-mês observado | Não confundir fracasso de um reparo com falha na população de equipamentos. |
| Beta | Ajuste da própria equação de captação com no mínimo três observações e variação de preço | Exige participação captada sobre demanda potencial, não quantidade concluída limitada por capacidade. Associação, sem identificação causal. |
| Influência de avaliações | Ajuste da equação de reputação, com satisfação e marketing controlados | Exige escala de reputação compatível, no mínimo três meses não saturados. Não é uma elasticidade de receita por estrela do Google. |
| Inovação | Inversão da equação de disponibilidade de peças | Proxy de obsolescência ajustada, não uma medição direta de lançamentos ou inovação dos fabricantes. |

As calculadoras CSV fornecem cabeçalho para download. Use UTF-8, vírgulas e decimal com ponto. Os resultados registram tamanho da amostra e SHA-256 do arquivo, junto com fonte e data. O arquivo original não é publicado no modelo. Não há autenticação automática da origem de arquivos declarados pelo responsável.

Para Nc, o importador espera Latin-1, separador `;`, 30 campos e nenhum cabeçalho conforme o layout oficial. Um fragmento nacional da base NÃO é um recorte municipal completo; a interface exige confirmação de cobertura. O código municipal da Receita não deve ser substituído pelo código IBGE. O endereço de download da RFB pode mudar; use a [página oficial de CNPJ](https://www.gov.br/receitafederal/pt-br/assuntos/orientacao-tributaria/cadastros/cnpj) para localizar os dados.

Fonte setorial pública pesquisada: [Open Repair Alliance / ORDS](https://openrepair.org/open-data/open-standard/) publica tentativas e desfechos em eventos comunitários. Ela não oferece a exposição de toda a base instalada nem todas as variáveis econômicas deste simulador; por isso não foi usada para inventar Alfa, Beta ou efeitos de avaliações brasileiros. Fontes de referência não equivalem a valores calibrados.
