import pytest

from backend.domain.exceptions import ExpressionEvaluationError


@pytest.mark.parametrize(
    "expression, variables, expected",
    [
        ("1 + 2 * 3", {}, 7.0),
        ("-x^2", {"x": 3.0}, -9.0),                      # ^ vira potência; unário tem menor precedência
        ("2^-3", {}, 0.125),
        ("Receita Líquida - Custos", {"Receita Líquida": 10.0, "Custos": 3.0}, 7.0),  # nomes com espaço/acento
        ("MIN(a, b)^2 - SQRT(a)", {"a": 4.0, "b": 3.0}, 7.0),
        ("MAX(1, x)", {"x": -5.0}, 1.0),
        ("ABS(x)", {"x": -5.0}, 5.0),
        ("exp(0) + ln(1)", {}, 1.0),                      # funções são case-insensitive
        ("Pt - Pm", {"Pt": 150.0, "Pm": -5.0}, 155.0),    # valor negativo não quebra a sintaxe
        ("", {}, 0.0),
        ("   ", {}, 0.0),
    ],
)
def test_evaluates_expressions(evaluator, expression, variables, expected):
    assert evaluator.evaluate(expression, variables) == pytest.approx(expected)


def test_longest_variable_name_wins(evaluator):
    assert evaluator.evaluate("Custo + Custo_Fixo", {"Custo": 1.0, "Custo_Fixo": 10.0}) == 11.0


@pytest.mark.parametrize(
    "expression",
    [
        "1/0",
        "LN(0)",
        "SQRT(-1)",
        "1 +",
        "unknown_var * 2",
        "__import__('os').system('echo hacked')",
        "(1).__class__",
        "open('x')",
        "MIN(a=1)",
        "9**9**9**9",
    ],
)
def test_rejects_invalid_or_unsafe_expressions(evaluator, expression):
    with pytest.raises(ExpressionEvaluationError):
        evaluator.evaluate(expression, {})


def test_min_max_abs_work_unlike_legacy_script(evaluator):
    """Regressão: no sim.py original MIN/MAX/ABS sempre retornavam 0 (builtins vazios no eval)."""
    assert evaluator.evaluate("MIN(3, 5)", {}) == 3.0
    assert evaluator.evaluate("MAX(3, 5)", {}) == 5.0
    assert evaluator.evaluate("ABS(-3)", {}) == 3.0
