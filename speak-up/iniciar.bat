@echo off
REM Speak Up - inicia o site no Windows (de dois cliques neste arquivo)
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (set PY=py) else (set PY=python)
echo Instalando as bibliotecas (so precisa na primeira vez)...
%PY% -m pip install -r requirements.txt
if errorlevel 1 (
  echo.
  echo Nao foi possivel instalar. Confira se o Python esta instalado: https://www.python.org/downloads/
  pause
  exit /b 1
)
echo.
echo Abra no navegador: http://127.0.0.1:5000   (para parar, feche esta janela ou use Ctrl+C)
start "" http://127.0.0.1:5000
%PY% app.py
pause
