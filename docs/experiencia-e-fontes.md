# Experiência e configuração inicial

A pergunta “Simular abertura da empresa?” inicia desativada. Somente quando ativada e antes do primeiro ciclo os custos de abertura e contratação do financiamento ficam configuráveis. Ao simular uma empresa existente, não se desconta investimento inicial nem se contrata dívida. Reserva e estoque iniciais representam o saldo operacional existente do cenário.

Ao abrir uma empresa, o investimento inicial é descontado da rentabilidade no primeiro ciclo, uma única vez. O caixa operacional já parte da reserva; o empréstimo é recebido no primeiro ciclo uma única vez. Os ativos e estoque iniciais são financiados pelo aporte de abertura contabilizado no investimento inicial. Parcelas são obrigações mensais e permanecem até o prazo contratado. Não se cobra novamente o principal integral. Reiniciar cria uma nova execução. Configurações iniciais não podem ser alteradas no meio da execução.

A tela prioriza preço, técnicos, estoque alvo e quatro orçamentos mensais. Demais ajustes operacionais ficam recolhidos. A taxa de inflação editável fica em **Inflação, fontes e calibração**. Cards têm altura mínima uniforme no desktop e altura livre em celulares. O orçamento fica em painel com faixa proporcional única e legenda com valores e percentuais. Variáveis têm visão geral, filtros e ficha com descrição completa/equação.

## Dados observados e hipóteses

O IPCA oficial é consultado na série SGS 433 do Banco Central, que divulga a variação mensal do IBGE. A consulta exibe o último mês publicado e preserva a taxa do cenário. Use o botão **Usar IPCA no próximo ciclo** para aplicar a referência ou digite sua própria taxa em porcentagem. O campo aceita deflação. A alteração vale para o próximo ciclo, e o histórico registra a taxa usada em cada mês simulado. A fonte da consulta é https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados/ultimos/1?formato=json.

Referência oficial da série: https://www3.bcb.gov.br/sgspub/consultarValoresSeries.do?method=consultarSeries&series=433

O IPCA é macroeconômico, não uma série específica de oficinas. Preço de equipamento e coeficientes comportamentais continuam hipóteses, identificadas como não calibradas. Concorrentes por município/CNAE requerem agregação dos dados públicos do CNPJ: https://www.gov.br/receitafederal/pt-br/assuntos/orientacao-tributaria/cadastros/cnpj . Essa base regional ainda não está integrada neste PR; a interface não alega que a contagem hipotética é real. A API Conecta consulta CNPJ identificado e requer adesão/credenciais, não constitui busca pública irrestrita de concorrentes.

Inspeção dos exemplos anexos e testes Streamlit/financeiros realizados. Inspeção visual final em navegador permanece pendente devido à restrição de sockets já observada neste ambiente.
