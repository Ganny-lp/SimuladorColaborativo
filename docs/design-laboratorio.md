# LUMINA: laboratório de decisões

## Referências institucionais

A paleta foi conferida nas referências oficiais da SCS: azul primário #1094ab, secundário #64c4d2 e amarelo #fcb421. Open Sans é a alternativa livre indicada à Univers. Mantemos o símbolo e a assinatura próprios LUMINA/PUB existentes, sem redesenhar o logotipo USP nem o brasão. Esta proposta de interface não representa aprovação institucional da SCS.

- https://scs.usp.br/identidadevisual/identidade-visual-referencias-de-elementos-visuais/
- https://scs.usp.br/identidadevisual/cores/
- https://leginf.usp.br/portarias/portaria-gr-no-8191-de-30-de-agosto-de-2023/

## Diagnóstico e decisões

| Problema | Experiência proposta |
|---|---|
| Interface técnica, sem orientação inicial | Abertura editorial e roteiro Formule / Experimente / Observe |
| Categorias do diagrama competiam com a leitura financeira | Paleta USP no dashboard; categorias multicoloridas permanecem no diagrama |
| Muitos dados misturados às decisões | Fontes e calibração recolhidas em área própria após a evolução |
| Pouca relação entre hipótese e resultado | Caderno por ciclo, hipótese congelada quando o ciclo conclui, exportação CSV |
| Contexto operacional disperso | Faixa de fila, peças e caixa com unidades e descrição do estado |
| Gráfico sugeria trajetória suave entre meses discretos | Segmentos lineares em vez de spline |
| Variáveis apenas tabulares | Ficha com definição, equação e relações de entrada/saída |
| Risco de novas regressões em telas pequenas | Layout testado em 320/390/900/1366 px e dois esquemas de cor |

O roteiro é orientação, não um bloqueio obrigatório nem uma alegação de calibração. A cobertura conta evidências vinculadas ao valor exato e não valida a origem nem o modelo. Resultados continuam separados de projeções e nenhuma equação foi alterada.

## Caderno e privacidade

Anotações são opcionais, limitadas a 1200 caracteres e ficam apenas na sessão. São copiadas para o registro de um ciclo somente após sua conclusão; editar o rascunho não modifica ciclos anteriores. Reiniciar ou recarregar o modelo limpa o caderno. O CSV acompanha somente os ciclos concluídos, com resultado mensal, acumulado, hipótese e preço decidido. Prefixos de fórmulas de planilha são neutralizados. Não há upload das anotações ao modelo compartilhado.

## Acessibilidade e responsividade

Controles nativos preservam teclado e nomes acessíveis. Abas têm alvo mínimo de 44 px, foco visível e não se sobrepõem aos menus do Streamlit. Os indicadores não dependem apenas de cor. Tema claro/escuro usa os tokens existentes e movimento reduzido desativa animações/transições. Roteiro tem três colunas compactas no celular; hero e estado operacional passam a coluna única. Estados vazios orientam a próxima ação.

## Validação

AppTest verifica fluxo do caderno, congelamento da hipótese e reinício. Testes unitários verificam exportação apenas de ciclos concluídos, proteção contra fórmulas e cobertura de evidências. Playwright executa o aplicativo real em quatro larguras e dois temas, mede alinhamento/overflow e percorre hipótese → avanço → exportação. O teste anterior de hit testing das abas é mantido. Capturas do navegador são artefatos temporários do CI para revisão visual, não arquivos de usuário publicados no aplicativo.
