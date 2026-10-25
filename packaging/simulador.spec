# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec — gera dist/SimuladorLumina/SimuladorLumina(.exe)  (modo onedir)
from pathlib import Path

from PyInstaller.utils.hooks import collect_all, copy_metadata

ROOT = Path(SPECPATH).parent          # SPECPATH = pasta deste .spec (packaging/)
ICON = Path(SPECPATH) / "icon.ico"

datas, binaries, hiddenimports = [], [], []

# Streamlit e Plotly carregam muitos arquivos estáticos (JS/CSS/templates) em runtime.
for pkg in ("streamlit", "plotly"):
    d, b, h = collect_all(pkg)
    datas += d; binaries += b; hiddenimports += h

# Streamlit consulta importlib.metadata em runtime → precisa dos .dist-info.
for pkg in ("streamlit", "plotly", "pandas", "requests"):
    try:
        datas += copy_metadata(pkg, recursive=True)
    except Exception:
        pass

# Código do app: app.py é executado pelo Streamlit como arquivo; o restante é importado.
datas += [
    (str(ROOT / "app.py"), "."),
    (str(ROOT / "frontend" / "assets"), "frontend/assets"),
    (str(ROOT / "backend" / "infrastructure" / "persistence" / "default_model.json"),
     "backend/infrastructure/persistence"),
]
hiddenimports += ["composition_root"]  # o resto é descoberto por análise estática de imports

a = Analysis(
    [str(ROOT / "packaging" / "launcher.py")],
    pathex=[str(ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    excludes=["pytest", "tkinter"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="SimuladorLumina",
    console=True,                      # janela de console = botão "encerrar" do servidor
    icon=str(ICON) if ICON.exists() else None,
    upx=False,
)
coll = COLLECT(exe, a.binaries, a.datas, name="SimuladorLumina", upx=False)
