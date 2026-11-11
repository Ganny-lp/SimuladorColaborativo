# Modelo mensal e análise de 11/11/2026

Cada ciclo representa um mês. As taxas são calculadas com os estoques do início do mês; todos os estoques mudam simultaneamente. Alterar uma entrada não avança o relógio.

| Questão da análise | Implementação |
|---|---|
| Inflação | Corrige peças, logística, equipamento novo, juros efetivos e satisfação. Não reaplica inflação duas vezes às mesmas peças. |
| Preço praticado | Pt é uma decisão. Preco_Sugerido usa custo total, tributação, margem e volume; o retorno resultado → preço exige decisão do participante. Não se apresenta como laço automático. |
| Reputação/fidelização | Satisfação → reputação → confiança → pedidos → fila → prazo → satisfação fecha o equilíbrio da sobrecarga. Satisfação → retorno/perda → base instalada → demanda também retorna pela fila. |
| Crescimento e investimento | Receita → resultado → reinvestimento no mês seguinte → treinamento/tecnologia → capacidade/qualidade → satisfação → reputação → demanda. Reinvestimento só usa resultado positivo e caixa disponível. |
| Estoque e fornecedor | Estoque → disponibilidade → prazo → satisfação → demanda → receita → caixa → reposição → estoque. Prazo do fornecedor limita reposição e aumenta espera. |
| Capital imobilizado | Estoque é pago na compra, reduz caixa e limita reposição futura. Fluxo de caixa adiciona de volta o consumo contábil de peças e deduz compras; não cobra duas vezes. |
| Técnicos e motivação | Número de técnicos afeta capacidade e folha. Qualificação, treinamento e carga afetam motivação, que afeta capacidade e rotatividade. |
| Abertura | Infraestrutura/reforma, marketing inicial, tecnologia e mobiliário são desembolsos iniciais. Reserva é capital de giro, não despesa recorrente. Orçamentos mensais são decisões distintas. Estoque inicial integra o desembolso de abertura. |
| Tributos | Receita líquida = preço × serviços concluídos × (1 − carga tributária). |
| Concorrentes locais | Nc é contagem regional informada pelo participante. Não há integração com uma base municipal no projeto. Nenhuma equação usa preço de outras assistências. |
| Entradas | Todo nó Input sem equação aparece na simulação, inclusive entradas novas criadas no diagrama. |
| Rentabilidade | Acumula fluxo de caixa após desembolso inicial. Resultado mensal, margem e caixa são indicadores separados. |

Os coeficientes comportamentais são hipóteses didáticas, não estimativas calibradas. A relação preço do reparo/equipamento novo representa a alternativa de substituir o equipamento. O preço novo não representa o serviço de outra empresa.

O financiamento entra no caixa inicial e suas prestações cessam no prazo. ROI mede fluxo acumulado em relação ao desembolso inicial; VPL, TIR e payback não são acrescentados nesta etapa, conforme o escopo da análise.

Modelos antigos do simulador são migrados para a versão 2 ao carregar, preservando valores de entradas e posições dos nós existentes. Equações padrão são substituídas deliberadamente; equações de nós adicionais que dependiam do parâmetro removido precisam ser reformuladas. O modelo remoto só é publicado quando o participante altera uma entrada ou salva o diagrama.

Na migração do payload antigo, a folha total é convertida em custo por técnico para evitar multiplicá-la novamente. Sinais das ligações do diagrama indicam efeito local no ponto inicial; saturações podem neutralizar relações.
