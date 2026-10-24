import streamlit as st

from frontend.assets.asset_template import AssetTemplate


class Theme:
    """Injeta o CSS global (tema escuro LUMINA) na página."""

    def __init__(self) -> None:
        self._stylesheet = AssetTemplate("global_theme.css")

    def apply(self) -> None:
        st.markdown(f"<style>\n{self._stylesheet.read()}</style>", unsafe_allow_html=True)
