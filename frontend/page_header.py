import streamlit as st

from frontend.branding import BrandAssets


class PageHeader:
    """Cabeçalho (símbolo + wordmark LUMINA · PUB USP) e rodapé institucional."""

    def render(self) -> None:
        # HTML sem linhas em branco: o parser de markdown encerraria o bloco HTML nelas.
        st.markdown(
            f'<div class="lumina-header">'
            f'<img class="lumina-mark" src="{BrandAssets.mark_data_uri()}" alt="Símbolo LUMINA">'
            f'<div class="lumina-wordmark">'
            f'<span class="main-header">LUMINA</span>'
            f'<span class="pub-tag">PUB · <b>USP</b></span></div>'
            f'<span class="sub-header">SIMULADOR DE LAÇOS CAUSAIS · COLABORATIVO</span>'
            f"</div>",
            unsafe_allow_html=True,
        )

    def render_footer(self) -> None:
        st.markdown(
            f'<div class="lumina-footer">'
            f'<img src="{BrandAssets.mark_data_uri()}" alt="">'
            f'<div class="f-text"><b>LUMINA</b> · Simulador de Laços Causais<br>'
            f"PUB · Universidade de São Paulo</div>"
            f'<span class="f-motto">Scientia vinces</span>'
            f"</div>",
            unsafe_allow_html=True,
        )
