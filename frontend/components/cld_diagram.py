from __future__ import annotations

import json
from typing import Any, Mapping


from frontend.assets.asset_template import AssetTemplate
from frontend.compat import render_html_frame
from frontend.config import CloudCredentials


class CldDiagram:
    """Diagrama de laços causais interativo (HTML/CSS/JS estáticos renderizados em iframe)."""

    _HEIGHT = 660

    def __init__(self, credentials: CloudCredentials) -> None:
        self._credentials = credentials
        self._page = AssetTemplate("cld_simulator.html")
        self._styles = AssetTemplate("cld_simulator.css")
        self._script = AssetTemplate("cld_simulator.js")

    def render(self, model_payload: Mapping[str, Any]) -> None:
        render_html_frame(self.build_html(model_payload), height=self._HEIGHT)

    def build_html(self, model_payload: Mapping[str, Any]) -> str:
        script = self._script.render(
            model_json=self._js_literal(model_payload),
            jsonbin_api_key=self._js_literal(self._credentials.api_key),
            jsonbin_bin_id=self._js_literal(self._credentials.bin_id),
        )
        return self._page.render(styles=self._styles.read(), script=script)

    @staticmethod
    def _js_literal(value: Any) -> str:
        # "</" escapado para que um texto de usuário nunca feche a tag <script>.
        return json.dumps(value, ensure_ascii=False).replace("</", "<\\/")
