from typing import Any, MutableMapping


class UiState:
    """Estado puramente visual (não pertence ao domínio)."""

    PICKER_KEY = "lumina.variable_picker"
    _FOCUS = "lumina.focus_request"
    _EPOCH = "lumina.diagram_epoch"

    def __init__(self, session_state: MutableMapping) -> None:
        self._state = session_state

    # ── variável escolhida na aba Variáveis ─────────────────────────────────
    @property
    def selected_variable(self) -> str | None:
        return self._state.get(self.PICKER_KEY) or None

    def request_focus(self) -> None:
        """Callback do seletor: pede ao diagrama que destaque a variável escolhida (uma vez)."""
        name = self.selected_variable
        previous = self._state.get(self._FOCUS) or {}
        self._state[self._FOCUS] = {"name": name, "nonce": int(previous.get("nonce", 0)) + 1} if name else None

    @property
    def focus_request(self) -> dict[str, Any] | None:
        return self._state.get(self._FOCUS)

    # ── época do modelo no diagrama ─────────────────────────────────────────
    @property
    def diagram_epoch(self) -> int:
        return int(self._state.get(self._EPOCH, 0))

    def bump_diagram_epoch(self) -> None:
        """Chamado ao recarregar o modelo da nuvem: invalida edições locais não salvas do diagrama."""
        self._state[self._EPOCH] = self.diagram_epoch + 1
