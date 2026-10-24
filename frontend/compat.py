"""
Camada de compatibilidade entre versões do Streamlit (únicos pontos que dependem de versão).

* ``STRETCH``: a partir do 1.50 ``use_container_width`` foi substituído por ``width="stretch"``.
* ``render_html_frame``: ``components.html`` está depreciado em favor de ``st.iframe``.
  Mantém-se o mecanismo original quando existe (comportamento já validado para a régua
  de preço, que acessa o DOM da página pai) e cai para ``st.iframe`` quando ele foi removido.
"""
from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components
from packaging.version import Version

STRETCH: dict[str, object] = (
    {"width": "stretch"}
    if Version(st.__version__) >= Version("1.50")
    else {"use_container_width": True}
)


def render_html_frame(html: str, height: int) -> None:
    legacy = getattr(components, "html", None)
    if legacy is not None:
        legacy(html, height=height, scrolling=False)
    else:  # pragma: no cover - depende da versão instalada
        st.iframe(html, height=height)
