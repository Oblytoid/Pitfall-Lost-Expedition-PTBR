@echo off
chcp 65001 >nul
REM Gera uma ISO de teste com os textos traduzidos.
REM Uso: arraste uma pasta de textos para cima deste arquivo, ou dê dois cliques
REM para usar a pasta "script".
cd /d "%~dp0"

set "TEXTOS=%~1"
if "%TEXTOS%"=="" set "TEXTOS=..\script"
set "DATA=..\extraido\Pitfall - The Lost Expedition (PT-BR)\data"
set "ISO=..\ISOs\Pitfall - The Lost Expedition (PT-BR).iso"
set "BUILD=..\build"

python --version >nul 2>&1
if errorlevel 1 (
  echo Python nao encontrado. Instale em https://www.python.org marcando "Add Python to PATH".
  pause
  exit /b 1
)

echo == Inserindo textos de: %TEXTOS%
python inserir.py "%DATA%" "%TEXTOS%" "%BUILD%"
if errorlevel 1 ( pause & exit /b 1 )

echo.
echo == Montando a ISO de teste (copia de 1,3 GB, pode demorar)
python iso_substituir.py "%ISO%" "%BUILD%\Pitfall_PTBR_teste.iso" DATA/QUICKDAT.ARC="%BUILD%\quickdat.arc" DATA/INDEX.IND="%BUILD%\index.ind" DATA/DATASETS.ARC="%BUILD%\datasets.arc"
if errorlevel 1 ( pause & exit /b 1 )

echo.
echo Pronto! Abra no PCSX2: Jogos\Pitfall\build\Pitfall_PTBR_teste.iso
pause
