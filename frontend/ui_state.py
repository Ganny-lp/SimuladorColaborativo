from typing import MutableMapping


class UiState:
    """Estado puramente visual (não pertence ao domínio)."""

    _SELECTED_VARIABLE = "lumina.selected_variable"

    def __init__(self, session_state: MutableMapping) -> None:
        self._state = session_state

    @property
    def selected_variable(self) -> str | None:
        return self._state.get(self._SELECTED_VARIABLE)

    @selected_variable.setter
    def selected_variable(self, name: str | None) -> None:
        self._state[self._SELECTED_VARIABLE] = name
