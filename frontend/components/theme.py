import streamlit as st

from frontend.assets.asset_template import AssetTemplate


class Theme:
    """Injeta o CSS global (tokens da marca + tema escuro LUMINA · PUB USP) na página."""

    def __init__(self) -> None:
        self._tokens = AssetTemplate("brand_tokens.css")
        self._stylesheet = AssetTemplate("global_theme.css")

    def apply(self) -> None:
        css = f"{self._tokens.read()}\n{self._stylesheet.read()}"
        st.markdown(f"<style>\n{css}</style>", unsafe_allow_html=True)
