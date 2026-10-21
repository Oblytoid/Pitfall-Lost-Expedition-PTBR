@echo off
chcp 65001 >nul
REM Gera o patch .xdelta e o pacote para distribuir a partir da ISO de teste mais recente.
REM Antes: rode o gerar_iso.bat e confira a ISO no PCSX2.
cd /d "%~dp0"

set "VERSAO=v0.9.1-beta"
set "ISO=..\ISOs\Pitfall - The Lost Expedition (USA).iso"
set "TRAD=..\build\Pitfall_PTBR_teste.iso"
set "SAIDA=..\patch\Pitfall_The_Lost_Expedition_PTBR_%VERSAO%.xdelta"
set "LEIAME=..\..\..\Cofre\Tradução de jogos\Jogos e suas pecularidade\Playstation 2\Pitfall- The lost Expedition\LEIAME - Patch.md"

if not exist "..\patch" mkdir "..\patch"
python gerar_patch.py "%ISO%" "%TRAD%" "%SAIDA%" "%VERSAO%" "%LEIAME%"
if errorlevel 1 ( pause & exit /b 1 )

echo.
echo Pronto! O pacote para distribuir e o .zip na pasta Jogos\Pitfall\patch
pause
