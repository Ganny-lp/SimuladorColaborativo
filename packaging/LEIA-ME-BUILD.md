# Gerar executável + instalador (Windows)

## Opção A — GitHub Actions (sem precisar de Windows)
1. Suba o projeto (com as pastas `packaging/` e `.github/`) para o GitHub.
2. Aba **Actions → Build Windows → Run workflow** (ou crie uma tag `v1.0.0`).
3. Baixe o artefato **SimuladorLumina-Windows**: `installer/SimuladorLumina-Setup-<versão>.exe`.

## Opção B — na sua máquina Windows
Requisitos: Python 3.12 (64 bits) e [Inno Setup 6](https://jrsoftware.org/isdl.php).
```
packaging\build_windows.bat 1.0.0
```
Saídas: `dist\SimuladorLumina\SimuladorLumina.exe` (portátil) e `installer\SimuladorLumina-Setup-1.0.0.exe`.

## Como funciona
- `launcher.py` sobe o Streamlit embutido numa porta livre (8501+), abre o navegador e fica rodando
  na janela de console; **fechar a janela encerra o app**.
- Secrets do JSONBin (opcional): `%APPDATA%\SimuladorLumina\.streamlit\secrets.toml`
  (há um `secrets.toml.example` criado na primeira execução).
- Os fontes do Google Fonts são carregados da internet; sem conexão o app usa fontes de fallback.

## Problemas comuns
- *Janela abre e fecha*: rode `SimuladorLumina.exe` pelo `cmd` para ver o erro.
- *Antivírus/SmartScreen avisa*: executáveis PyInstaller sem assinatura digital costumam gerar alerta.
- *Falta módulo no exe* (`ModuleNotFoundError`): adicione-o em `hiddenimports` no `simulador.spec`.
