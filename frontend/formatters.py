"""Formatação de valores para exibição."""


def thousands_currency(value: float) -> str:
    return f"R$ {value / 1000:.1f}k"


def currency(value: float) -> str:
    return f"R$ {value:,.0f}"


def integer(value: float) -> str:
    return f"{value:.0f}"


def percent(fraction: float) -> str:
    return f"{fraction * 100:.2f}%"
