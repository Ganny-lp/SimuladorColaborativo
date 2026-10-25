from __future__ import annotations

from html import escape

import streamlit as st


class SectionHeader:
    """Título de seção com dica e chip opcionais (HTML próprio: espaçamento e hierarquia consistentes)."""

    @staticmethod
    def html(title: str, *, hint: str | None = None, chip: str | None = None) -> str:
        hint_html = f"<p>{escape(hint)}</p>" if hint else ""
        chip_html = f'<span class="chip">{escape(chip)}</span>' if chip else ""
        return (
            f'<div class="lumina-section"><div><h3>{escape(title)}</h3>{hint_html}</div>{chip_html}</div>'
        )

    def render(self, title: str, *, hint: str | None = None, chip: str | None = None) -> None:
        st.markdown(self.html(title, hint=hint, chip=chip), unsafe_allow_html=True)
