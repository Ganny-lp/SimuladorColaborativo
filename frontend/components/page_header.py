import streamlit as st


class PageHeader:
    def render(self) -> None:
        st.markdown(
            """
<div class="lumina-header">
  <span class="main-header">⬡ LUMINA</span>
  <span class="sub-header">SIMULADOR DE LAÇOS CAUSAIS · COLABORATIVO</span>
</div>
""",
            unsafe_allow_html=True,
        )

    def render_footer(self) -> None:
        st.markdown("---")
        st.caption("⬡ LUMINA · Simulador de Laços Causais · Streamlit Colaborativo")
