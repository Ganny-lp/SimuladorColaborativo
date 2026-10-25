@echo off
REM Gera dist\SimuladorLumina\SimuladorLumina.exe e installer\SimuladorLumina-Setup-<versao>.exe
REM Pré-requisitos: Python 3.11/3.12 (64 bits) e Inno Setup 6 (https://jrsoftware.org/isdl.php)
REM Uso (na raiz do projeto):  packaging\build_windows.bat [versao]
setlocal
cd /d "%~dp0\.."
set VERSION=%1
if "%VERSION%"=="" set VERSION=1.0.0

py -3.12 -m venv .venv-build 2>nul || py -3 -m venv .venv-build || goto :err
call .venv-build\Scripts\activate.bat
python -m pip install --upgrade pip || goto :err
pip install -r requirements.txt -r requirements-build.txt || goto :err

python packaging\make_icon.py || goto :err
REM encerra o app caso esteja aberto (senao o Windows bloqueia a limpeza de dist\)
taskkill /f /im SimuladorLumina.exe >nul 2>&1
pyinstaller packaging\simulador.spec --noconfirm --clean --distpath dist --workpath build || goto :err

set ISCC="%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist %ISCC% set ISCC="%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not exist %ISCC% set ISCC="%LocalAppData%\Programs\Inno Setup 6\ISCC.exe"
if not exist %ISCC% for /f "delims=" %%I in ('where ISCC.exe 2^>nul') do set ISCC="%%I"
if not exist %ISCC% (
  echo [aviso] Inno Setup nao encontrado. Executavel pronto em dist\SimuladorLumina\, instalador NAO gerado.
  pause
  exit /b 0
)
%ISCC% /DAppVersion=%VERSION% packaging\installer.iss || goto :err
echo.
echo Pronto: installer\SimuladorLumina-Setup-%VERSION%.exe
pause
exit /b 0

:err
echo.
echo [erro] O build falhou. Leia as mensagens acima.
pause
exit /b 1
