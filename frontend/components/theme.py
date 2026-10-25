import streamlit as st

from frontend.assets.asset_template import AssetTemplate
from frontend.branding import BrandAssets
from frontend.compat import keyed_container, render_html_frame
from frontend.config import FONTS_URL


class Theme:
    """
    Injeta o CSS global (tokens da marca + estilos da página) e a ponte de tema.

    O Streamlit escolhe claro/escuro sozinho; a ponte (``theme_bridge.js``) lê essa escolha e a
    publica como ``data-lumina-theme`` no <html>, de onde o CSS e os iframes a seguem ao vivo.
    """

    def __init__(self) -> None:
        self._tokens = AssetTemplate("brand_tokens.css")
        self._stylesheet = AssetTemplate("global_theme.css")
        self._bridge = AssetTemplate("theme_bridge.js")

    def stylesheet(self) -> str:
        marks = (
            f':root{{--mark-dark:url("{BrandAssets.mark_data_uri("dark")}");'
            f'--mark-light:url("{BrandAssets.mark_data_uri("light")}");}}'
        )
        # @import precisa ser a primeira regra da folha de estilo.
        return f"@import url('{FONTS_URL}');\n{marks}\n{self._tokens.read()}\n{self._stylesheet.read()}"

    def apply(self) -> None:
        st.markdown(f"<style>\n{self.stylesheet()}</style>", unsafe_allow_html=True)
        with keyed_container("lumina-bridge"):   # classe st-key-lumina-bridge: tirada do fluxo pelo CSS
            render_html_frame(f"<script>{self._bridge.read()}</script>", height=1)
