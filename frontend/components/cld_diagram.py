from __future__ import annotations

from typing import Any, Mapping

from frontend.assets.asset_template import AssetTemplate, js_literal
from frontend.branding import BrandAssets
from frontend.compat import render_html_frame
from frontend.config import FONTS_URL, CloudCredentials


class CldDiagram:
    """Diagrama de laços causais interativo (HTML/CSS/JS estáticos renderizados em iframe)."""

    _INITIAL_HEIGHT = 640   # o próprio iframe ajusta a altura à janela assim que carrega

    def __init__(self, credentials: CloudCredentials) -> None:
        self._credentials = credentials
        self._page = AssetTemplate("cld_simulator.html")
        self._tokens = AssetTemplate("brand_tokens.css")
        self._styles = AssetTemplate("cld_simulator.css")
        self._script = AssetTemplate("cld_simulator.js")
        self._theme_sync = AssetTemplate("theme_sync.js")

    def render(
        self, model_payload: Mapping[str, Any], *, focus: Mapping[str, Any] | None = None, epoch: int = 0
    ) -> None:
        render_html_frame(self.build_html(model_payload, focus=focus, epoch=epoch), height=self._INITIAL_HEIGHT)

    def build_html(
        self, model_payload: Mapping[str, Any], *, focus: Mapping[str, Any] | None = None, epoch: int = 0
    ) -> str:
        """
        ``focus``: ``{"name": variável, "nonce": n}``: o diagrama seleciona e centraliza a variável
        uma vez por ``nonce``. ``epoch``: muda quando o modelo é recarregado pelo Python; as edições
        locais não salvas do diagrama (guardadas no navegador) só valem dentro da mesma época.
        """
        script = self._script.render(
            model_json=js_literal(model_payload),
            jsonbin_api_key=js_literal(self._credentials.api_key),
            jsonbin_bin_id=js_literal(self._credentials.bin_id),
            epoch=js_literal(int(epoch)),
            focus_json=js_literal(dict(focus) if focus else None),
        )
        # o iframe é um documento à parte: recebe os tokens da marca e o símbolo (data URI).
        styles = f"{self._tokens.read()}\n{self._styles.read()}"
        return self._page.render(
            fonts_url=FONTS_URL,
            theme_sync=self._theme_sync.read(),
            styles=styles,
            script=script,
            logo_mark_dark=BrandAssets.mark_data_uri("dark"),
            logo_mark_light=BrandAssets.mark_data_uri("light"),
        )
