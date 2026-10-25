"""
Camada de compatibilidade entre versões do Streamlit (únicos pontos que dependem de versão).

* ``STRETCH``: a partir do 1.50 ``use_container_width`` foi substituído por ``width="stretch"``.
* ``render_html_frame``: ``components.html`` está depreciado (remoção anunciada para depois de
  2026-06-01) em favor de ``st.iframe``. Usa ``st.iframe`` quando existe e ``components.html``
  em versões antigas. Os iframes acessam o DOM da página pai (régua, tema, altura).
* ``keyed_container``: ``st.container(key=...)`` gera a classe CSS ``st-key-<key>``; em versões
  que não aceitam ``key`` cai para um contêiner comum (só perde o estilo de cartão).
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
    modern = getattr(st, "iframe", None)
    if modern is not None:
        modern(html, height=height)
    else:  # pragma: no cover - Streamlit sem st.iframe
        components.html(html, height=height, scrolling=False)


def keyed_container(key: str, border: bool = False):
    try:
        return st.container(key=key, border=border)
    except TypeError:  # pragma: no cover - Streamlit antigo, sem ``key``
        return st.container(border=border)
