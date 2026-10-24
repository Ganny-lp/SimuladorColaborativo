"""Exceções do domínio."""


class DomainError(Exception):
    """Base de todas as exceções de domínio."""


class InvalidModelError(DomainError):
    """O modelo causal recebido é estruturalmente inválido."""


class NodeNotFoundError(DomainError):
    """Variável inexistente no sistema."""

    def __init__(self, name: str) -> None:
        super().__init__(f"Variável '{name}' não existe no sistema.")
        self.name = name


class ExpressionEvaluationError(DomainError):
    """A equação não pôde ser avaliada (sintaxe, função proibida, valor não finito...)."""
