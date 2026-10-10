@echo off
chcp 65001 >nul
setlocal
title Pitfall: The Lost Expedition - Tradução PT-BR
cd /d "%~dp0"
set "PATCH=__PATCH__"
set "SHA_ORIG=__SHA_ORIG__"
set "SHA_TRAD=__SHA_TRAD__"
set "NOME_SAIDA=Pitfall - The Lost Expedition (PT-BR).iso"

echo ================================================
echo   Pitfall: The Lost Expedition - Tradução PT-BR
echo   __VERSAO__
echo ================================================
echo.

if "%~1"=="" (
  echo Arraste a ISO original do jogo para cima deste arquivo.
  echo ^(versão americana SLUS-20408, formato .iso^)
  echo.
  pause
  exit /b 1
)
if not exist "%~1" (
  echo Arquivo não encontrado: "%~1"
  pause
  exit /b 1
)
if not exist "xdelta3.exe" (
  echo Falta o xdelta3.exe nesta pasta. Descompacte o pacote inteiro antes de usar.
  pause
  exit /b 1
)
if not exist "%PATCH%" (
  echo Falta o arquivo %PATCH% nesta pasta. Descompacte o pacote inteiro antes de usar.
  pause
  exit /b 1
)

set "ISO=%~f1"
set "SAIDA=%~dp1%NOME_SAIDA%"
if /i "%ISO%"=="%SAIDA%" (
  echo Esta já é a ISO traduzida. Arraste a ISO original.
  pause
  exit /b 1
)

echo [1/3] Conferindo a ISO original...
call :sha1 "%ISO%"
if /i not "%H%"=="%SHA_ORIG%" (
  echo.
  echo ATENÇÃO: esta ISO não é a versão esperada.
  echo   esperado:   %SHA_ORIG%
  echo   encontrado: %H%
  echo Ela pode ser de outra região, estar modificada ou ser um CSO/CHD convertido.
  echo O mais provável é a tradução não funcionar.
  echo.
  choice /c SN /m "Tentar mesmo assim"
  if errorlevel 2 exit /b 1
)

echo [2/3] Aplicando a tradução (pode levar um minuto)...
xdelta3.exe -d -f -s "%ISO%" "%PATCH%" "%SAIDA%"
if errorlevel 1 (
  echo.
  echo ERRO ao aplicar a tradução. Confira se a ISO é a original americana.
  if exist "%SAIDA%" del "%SAIDA%"
  pause
  exit /b 1
)

echo [3/3] Conferindo o resultado...
call :sha1 "%SAIDA%"
if /i not "%H%"=="%SHA_TRAD%" (
  echo.
  echo ERRO: a ISO gerada não ficou igual à esperada. Não use este arquivo.
  pause
  exit /b 1
)

echo.
echo Pronto! A ISO traduzida foi criada na mesma pasta da original:
echo   %SAIDA%
echo.
echo A ISO original não foi alterada. Bom jogo!
echo.
pause
exit /b 0

:sha1
set "H="
for /f "skip=1 delims=" %%h in ('certutil -hashfile "%~1" SHA1 2^>nul') do if not defined H set "H=%%h"
if defined H set "H=%H: =%"
exit /b 0
