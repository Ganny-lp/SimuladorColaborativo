import streamlit as st

_MARK = '<span class="mark {cls}" role="img" aria-label="Símbolo LUMINA"><i></i><b></b></span>'


class PageHeader:
    """Cabeçalho (símbolo + wordmark LUMINA · PUB USP) e rodapé institucional."""

    def render(self) -> None:
        # HTML sem linhas em branco: o parser de markdown encerraria o bloco HTML nelas.
        st.markdown(
            f'<div class="lumina-header">{_MARK.format(cls="lumina-mark")}'
            f'<div class="lumina-wordmark">'
            f'<span class="main-header">LUMINA</span>'
            f'<span class="pub-tag">PUB · <b>USP</b></span></div>'
            f'<span class="sub-header">SIMULADOR DE LAÇOS CAUSAIS<br>COLABORATIVO</span>'
            f"</div>",
            unsafe_allow_html=True,
        )

    def render_footer(self) -> None:
        st.markdown(
            f'<div class="lumina-footer">{_MARK.format(cls="")}'
            f'<div class="f-text"><b>LUMINA</b> · Simulador de Laços Causais<br>'
            f"PUB · Universidade de São Paulo</div>"
            f'<span class="f-motto">Scientia vinces</span>'
            f"</div>",
            unsafe_allow_html=True,
        )
