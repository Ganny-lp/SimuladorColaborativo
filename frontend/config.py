"""Configuração e vocabulário da camada de apresentação."""
from dataclasses import dataclass

# Mude APP_VERSION sempre que alterar equações/estado inicial: sessões abertas antes
# do deploy (que ainda guardam o estado antigo) são recarregadas.
APP_VERSION = "2026-09-28-fix-st-rentabilidade"

PAGE_TITLE = "LUMINA · Simulador de Laços Causais · PUB USP"
PRICE_VARIABLE = "Pt"
PRICE_SYNC_KEY = "pt_hidden_sync"
PRICE_RULER_KEY = "pt_ruler"

# Fontes da marca (Open Sans = alternativa livre da USP ao Univers; Montserrat = wordmark).
FONTS_URL = (
    "https://fonts.googleapis.com/css2?family=Montserrat:wght@500;600;700"
    "&family=Open+Sans:wght@400;500;600;700&family=DM+Mono:wght@400;500&display=swap"
)


@dataclass(frozen=True)
class DecisionInput:
    variable: str
    label: str


DECISION_INPUTS: tuple[DecisionInput, ...] = (
    DecisionInput("budget_update", "P&D"),
    DecisionInput("budget_training", "Treinamento"),
    DecisionInput("budget_infra", "Infraestrutura"),
    DecisionInput("budget_promo", "Marketing"),
    DecisionInput("Nc", "Concorrentes"),
)


@dataclass(frozen=True)
class CloudCredentials:
    """Credenciais entregues ao diagrama (JS roda no navegador e fala direto com o JSONBin)."""

    api_key: str | None = None
    bin_id: str | None = None
