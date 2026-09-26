@echo off
setlocal
title PVN Controle TV
cd /d "%~dp0"
set "VER=dev"
if exist "VERSION" set /p VER=<"VERSION"
echo.
echo   PVN Controle TV %VER%
echo   Abrindo no navegador padrao...
echo.
if not exist "index.html" (
  echo   ERRO: index.html nao encontrado nesta pasta.
  echo   Extraia o pacote inteiro antes de abrir.
  pause
  exit /b 1
)
start "" "%~dp0index.html"
timeout /t 3 >nul
exit /b 0
