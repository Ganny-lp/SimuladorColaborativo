from __future__ import annotations

import streamlit as st

from backend.application.use_cases.get_simulation_snapshot import GetSimulationSnapshotUseCase
from backend.application.use_cases.start_simulation import StartSimulationUseCase
from frontend.components.page_header import PageHeader
from frontend.components.theme import Theme
from frontend.config import PAGE_TITLE
from frontend.views.tab import Tab


class MainPage:
    """Orquestra a página: tema, cabeçalho, abas e rodapé."""

    def __init__(
        self,
        theme: Theme,
        header: PageHeader,
        tabs: list[Tab],
        start_simulation: StartSimulationUseCase,
        get_snapshot: GetSimulationSnapshotUseCase,
    ) -> None:
        self._theme = theme
        self._header = header
        self._tabs = tabs
        self._start_simulation = start_simulation
        self._get_snapshot = get_snapshot

    def render(self) -> None:
        # set_page_config PRECISA ser o primeiro comando Streamlit da execução.
        st.set_page_config(page_title=PAGE_TITLE, layout="wide", initial_sidebar_state="collapsed")
        self._theme.apply()
        self._start_simulation.execute()
        snapshot = self._get_snapshot.execute()

        self._header.render()
        containers = st.tabs([tab.title for tab in self._tabs])
        for container, tab in zip(containers, self._tabs):
            with container:
                tab.render(snapshot)
        self._header.render_footer()
