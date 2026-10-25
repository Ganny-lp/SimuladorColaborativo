import time
from typing import Any, MutableMapping


class UiState:
    """Estado puramente visual (não pertence ao domínio)."""

    PICKER_KEY = "lumina.variable_picker"
    _FOCUS = "lumina.focus_request"
    _FOCUS_SEQ = "lumina.focus_seq"
    _EPOCH = "lumina.diagram_epoch"

    def __init__(self, session_state: MutableMapping) -> None:
        self._state = session_state

    # ── variável escolhida na aba Variáveis ─────────────────────────────────
    @property
    def selected_variable(self) -> str | None:
        return self._state.get(self.PICKER_KEY) or None

    def request_focus(self) -> None:
        """Pede ao diagrama que destaque a variável escolhida (uma vez por pedido).

        O ``nonce`` identifica o pedido e o diagrama o guarda no navegador para não repeti-lo a cada
        rerun. Por isso ele nunca pode se repetir: antes, limpar o seletor zerava a contagem e o pedido
        seguinte reaproveitava um nonce já consumido (e o diagrama o ignorava em silêncio). Agora há um
        contador que nunca volta atrás, misturado ao relógio para sobreviver a um F5 (a sessão do
        Streamlit recomeça, mas o sessionStorage da aba continua com o último nonce).
        """
        name = self.selected_variable
        if not name:
            self._state[self._FOCUS] = None
            return
        seq = int(self._state.get(self._FOCUS_SEQ, 0)) + 1
        self._state[self._FOCUS_SEQ] = seq
        self._state[self._FOCUS] = {"name": name, "nonce": f"{time.time_ns()}-{seq}"}

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
