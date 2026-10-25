"""
Launcher do Simulador LUMINA.

Sobe o servidor Streamlit embutido no executável, abre o navegador padrão e mantém o
servidor rodando enquanto a janela do console estiver aberta (feche-a para encerrar).

Funciona tanto congelado pelo PyInstaller quanto direto:  python packaging/launcher.py

Variáveis de ambiente opcionais:
    LUMINA_PORT        porta fixa (padrão: 8501, ou a próxima livre)
    LUMINA_NO_BROWSER  "1" para não abrir o navegador (usado nos testes de CI)
"""
from __future__ import annotations

import multiprocessing
import os
import socket
import sys
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path

APP_NAME = "Simulador LUMINA"
DEFAULT_PORT = 8501

SECRETS_EXAMPLE = """\
# Persistência na nuvem (opcional) via JSONBin.
# Para ativar: copie este arquivo para "secrets.toml" (mesma pasta), descomente e preencha.
# Sem isso o simulador roda normalmente com o modelo padrão.
#
# [jsonbin]
# api_key = "SUA_ACCESS_KEY"
# bin_id  = "SEU_BIN_ID"
"""


def bundle_dir() -> Path:
    """Pasta onde estão app.py e os dados: _MEIPASS (congelado) ou a raiz do projeto."""
    frozen = getattr(sys, "_MEIPASS", None)
    return Path(frozen) if frozen else Path(__file__).resolve().parent.parent


def user_data_dir() -> Path:
    """Pasta gravável do usuário (secrets). O diretório de instalação não é gravável."""
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home()))
        return base / "SimuladorLumina"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "SimuladorLumina"
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "simulador-lumina"


def prepare_user_dir() -> Path:
    data = user_data_dir()
    st_dir = data / ".streamlit"
    st_dir.mkdir(parents=True, exist_ok=True)
    example = st_dir / "secrets.toml.example"
    if not example.exists():
        example.write_text(SECRETS_EXAMPLE, encoding="utf-8")
    return data


def port_is_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
        return s.connect_ex(("127.0.0.1", port)) != 0


def pick_port() -> int:
    wanted = os.environ.get("LUMINA_PORT")
    if wanted:
        return int(wanted)
    for port in range(DEFAULT_PORT, DEFAULT_PORT + 50):
        if port_is_free(port):
            return port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:  # qualquer porta livre
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def open_browser_when_ready(port: int) -> None:
    url = f"http://127.0.0.1:{port}"
    health = f"{url}/_stcore/health"
    for _ in range(120):  # até ~60 s
        try:
            with urllib.request.urlopen(health, timeout=1) as resp:
                if resp.status == 200:
                    break
        except Exception:
            time.sleep(0.5)
    else:
        return
    if os.environ.get("LUMINA_NO_BROWSER") != "1":
        webbrowser.open(url)


def main() -> int:
    multiprocessing.freeze_support()
    root = bundle_dir()
    app = root / "app.py"
    if not app.exists():
        print(f"[erro] app.py não encontrado em {root}")
        return 1

    # Garante que `import composition_root`, `backend`, `frontend` resolvam.
    sys.path.insert(0, str(root))

    # Secrets do Streamlit são lidos de <cwd>/.streamlit/secrets.toml.
    os.chdir(prepare_user_dir())

    port = pick_port()
    print(f"=== {APP_NAME} ===")
    print(f"Endereço: http://127.0.0.1:{port}")
    print("O navegador abrirá em instantes. Para ENCERRAR, feche esta janela.\n")

    threading.Thread(target=open_browser_when_ready, args=(port,), daemon=True).start()

    from streamlit.web import cli as stcli

    sys.argv = [
        "streamlit", "run", str(app),
        "--global.developmentMode=false",   # obrigatório quando congelado
        f"--server.port={port}",
        "--server.address=127.0.0.1",
        "--server.headless=true",           # o navegador é aberto pelo launcher
        "--server.fileWatcherType=none",
        "--server.runOnSave=false",
        "--browser.gatherUsageStats=false",
        "--theme.base=dark",
    ]
    return stcli.main() or 0


if __name__ == "__main__":
    sys.exit(main())
