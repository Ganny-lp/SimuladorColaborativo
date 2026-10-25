import streamlit as st


class PageHeader:
    """Cabeçalho (símbolo + wordmark LUMINA · PUB USP) e rodapé institucional."""

    def render(self) -> None:
        # HTML sem linhas em branco: o parser de markdown encerraria o bloco HTML nelas.
        # O símbolo é um <span> com máscara de fundo: troca de variante (claro/escuro) pelo tema.
        st.markdown(
            '<header class="lumina-header">'
            '<span class="lumina-mark" role="img" aria-label="Símbolo LUMINA"></span>'
            '<div class="lumina-wordmark">'
            '<span class="main-header">LUMINA</span>'
            '<span class="pub-tag">PUB · <b>USP</b></span></div>'
            '<p class="sub-header">Simulador de laços causais colaborativo</p>'
            "</header>",
            unsafe_allow_html=True,
        )

    def render_footer(self) -> None:
        st.markdown(
            '<footer class="lumina-footer">'
            '<span class="lumina-mark sm" role="img" aria-label=""></span>'
            '<div class="f-text"><b>LUMINA</b> · Simulador de Laços Causais<br>'
            "PUB · Universidade de São Paulo</div>"
            '<span class="f-motto">Scientia vinces</span>'
            "</footer>",
            unsafe_allow_html=True,
        )
