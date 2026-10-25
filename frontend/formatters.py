"""Formatação de valores para exibição (pt-BR: vírgula decimal, ponto de milhar)."""

_MINUS = "\u2212"  # sinal de menos tipográfico


def _pt(number: float, decimals: int = 0) -> str:
    text = f"{abs(number):,.{decimals}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{_MINUS}{text}" if number < 0 and float(text.replace(".", "").replace(",", ".")) != 0 else text


def thousands_currency(value: float) -> str:
    """R$ 1.234,5 → ``R$ 1,2 mil``; abaixo de mil mostra o valor inteiro."""
    if abs(value) < 1000:
        return currency(value)
    if abs(value) >= 1_000_000:
        return f"R$ {_pt(value / 1_000_000, 2)} mi"
    return f"R$ {_pt(value / 1000, 1)} mil"


def currency(value: float) -> str:
    return f"R$ {_pt(value, 0)}"


def integer(value: float) -> str:
    return _pt(value, 0)


def percent(fraction: float) -> str:
    return f"{_pt(fraction * 100, 2)}%"
