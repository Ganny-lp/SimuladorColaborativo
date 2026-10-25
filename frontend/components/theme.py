import streamlit as st

from frontend.assets.asset_template import AssetTemplate
from frontend.branding import BrandAssets
from frontend.compat import render_html_frame


class Theme:
    """Injeta o CSS global (tokens da marca, claro/escuro) e sincroniza o tema com o do Streamlit."""

    def __init__(self) -> None:
        self._tokens = AssetTemplate("brand_tokens.css")
        self._stylesheet = AssetTemplate("global_theme.css")
        self._theme_sync = AssetTemplate("theme_sync.html")

    def apply(self) -> None:
        css = f"{self._tokens.read()}\n{BrandAssets.mark_css_variable()}\n{self._stylesheet.read()}"
        st.markdown(f"<style>\n{css}</style>", unsafe_allow_html=True)
        # iframe invisível (fora do fluxo, ver global_theme.css) que descobre o tema ativo do Streamlit
        with st.container(key="lumina-themesync"):
            render_html_frame(self._theme_sync.read(), height=0)
