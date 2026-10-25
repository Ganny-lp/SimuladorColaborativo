from __future__ import annotations

from typing import Sequence

import pandas as pd
import streamlit as st

from backend.application.dto import VariableDTO
from frontend.compat import STRETCH

_DESCRIPTION_MAX_CHARS = 90
_COLUMNS = ["Variável", "Categoria", "Valor Atual", "Equação", "Descrição"]


class VariablesTable:
    """Tabela filtrável com todas as variáveis do sistema."""

    def build_dataframe(
        self, variables: Sequence[VariableDTO], search: str = "", categories: Sequence[str] = ()
    ) -> pd.DataFrame:
        frame = pd.DataFrame(
            [
                {
                    "Variável": v.name,
                    "Categoria": v.category,
                    "Valor Atual": round(v.value, 6),
                    "Equação": v.expression or "—",
                    "Descrição": (v.description or "")[:_DESCRIPTION_MAX_CHARS],
                }
                for v in variables
            ],
            columns=_COLUMNS,
        )
        if search:
            mask = frame["Variável"].str.contains(search, case=False, na=False) | frame[
                "Categoria"
            ].str.contains(search, case=False, na=False)
            frame = frame[mask]
        if categories:
            frame = frame[frame["Categoria"].isin(categories)]
        return frame

    def render(self, frame: pd.DataFrame) -> None:
        st.dataframe(
            frame,
            **STRETCH,
            hide_index=True,
            height=min(560, 38 + 35 * max(len(frame), 3)),
            column_config={
                "Variável": st.column_config.TextColumn("Variável", width="medium"),
                "Categoria": st.column_config.TextColumn("Categoria", width="small"),
                "Valor Atual": st.column_config.NumberColumn("Valor atual", format="%.5g"),
                "Equação": st.column_config.TextColumn("Equação", width="large"),
                "Descrição": st.column_config.TextColumn("Descrição", width="large"),
            },
        )
