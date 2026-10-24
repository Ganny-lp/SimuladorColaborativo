from __future__ import annotations

import ast
import math
import operator
import re
from typing import Any, Callable, Mapping

from backend.domain.exceptions import ExpressionEvaluationError

_FUNCTIONS: dict[str, Callable[..., float]] = {
    "EXP": math.exp,
    "MIN": min,
    "MAX": max,
    "ABS": abs,
    "SQRT": math.sqrt,
    "LOG": math.log10,
    "LN": math.log,
    "SIN": math.sin,
    "COS": math.cos,
    "TAN": math.tan,
}

_BINARY_OPERATORS: dict[type, Callable[[float, float], float]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv,
}

_UNARY_OPERATORS: dict[type, Callable[[float], float]] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

_EVALUATION_ERRORS = (
    SyntaxError,
    ValueError,
    TypeError,
    ZeroDivisionError,
    OverflowError,
    RecursionError,
)


class ExpressionEvaluator:
    """
    Avalia equações como ``"(Pt*Qt)*(1-Carga_Tributaria)"``.

    1. Nomes de variáveis (inclusive com espaços/acentos) são trocados pelo valor numérico;
    2. ``^`` vira potência;
    3. A expressão é interpretada via AST com *whitelist* de operadores e funções
       (nenhum ``eval``), portanto uma equação não consegue executar código arbitrário.

    Equação em branco vale ``0.0``. Qualquer problema levanta ``ExpressionEvaluationError``.
    """

    def evaluate(self, expression: str, variables: Mapping[str, float]) -> float:
        if not expression or not expression.strip():
            return 0.0
        source = self._substitute_variables(expression, variables).replace("^", "**")
        try:
            tree = ast.parse(source.strip(), mode="eval")
            result = self._eval(tree.body)
        except ExpressionEvaluationError:
            raise
        except _EVALUATION_ERRORS as exc:
            raise ExpressionEvaluationError(f"Equação inválida '{expression}': {exc}") from exc
        if not math.isfinite(result):
            raise ExpressionEvaluationError(f"Resultado não finito em '{expression}'.")
        return float(result)

    # ── internos ────────────────────────────────────────────────────────────
    @staticmethod
    def _substitute_variables(expression: str, variables: Mapping[str, float]) -> str:
        if not variables:
            return expression
        longest_first = sorted(variables, key=len, reverse=True)
        pattern = re.compile(r"\b(?:" + "|".join(re.escape(n) for n in longest_first) + r")\b")
        return pattern.sub(lambda m: repr(float(variables[m.group(0)])), expression)

    def _eval(self, node: ast.AST) -> float:
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) \
                and not isinstance(node.value, bool):
            return float(node.value)  # sempre float: evita potências inteiras gigantes
        if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPERATORS:
            return _BINARY_OPERATORS[type(node.op)](self._eval(node.left), self._eval(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPERATORS:
            return _UNARY_OPERATORS[type(node.op)](self._eval(node.operand))
        if isinstance(node, ast.Call):
            return self._eval_call(node)
        raise ExpressionEvaluationError(f"Elemento não suportado na equação: {type(node).__name__}")

    def _eval_call(self, node: ast.Call) -> float:
        function = self._resolve_function(node.func)
        if node.keywords:
            raise ExpressionEvaluationError("Argumentos nomeados não são suportados.")
        arguments = [self._eval(arg) for arg in node.args]
        return float(function(*arguments))

    @staticmethod
    def _resolve_function(func: Any) -> Callable[..., float]:
        if isinstance(func, ast.Name) and func.id.upper() in _FUNCTIONS:
            return _FUNCTIONS[func.id.upper()]
        name = func.id if isinstance(func, ast.Name) else type(func).__name__
        raise ExpressionEvaluationError(f"Função não permitida: {name}")
