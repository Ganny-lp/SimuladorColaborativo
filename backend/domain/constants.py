"""Nomes de variáveis do modelo LUMINA que a lógica de negócio referencia diretamente."""
from typing import Final


class NodeNames:
    """Vocabulário do modelo padrão (evita *magic strings* espalhadas pelo código)."""

    RENTABILIDADE: Final = "Rentabilidade"
    RECEITA_LIQUIDA: Final = "Receita Líquida"
    CUSTOS: Final = "Custos"
    CUSTOS_ABERTURA: Final = "Custos Abertura"
    PRECO: Final = "Pt"
    QUANTIDADE: Final = "Qt"
    MARKET_SHARE: Final = "St"
    PRECO_MERCADO: Final = "Pm"
    CUSTO_PECAS: Final = "Cp"
    CUSTO_MAO_DE_OBRA: Final = "C_Mao_Obra"
