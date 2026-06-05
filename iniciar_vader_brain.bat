@echo off
title Iniciar Vader_Brain GUI
echo ===================================================
echo             Iniciando VADER_BRAIN GUI (Conda)
echo ===================================================
echo.

REM Moverse al directorio donde se encuentra este archivo .bat
cd /d "%~dp0"

echo [1/3] Buscando configuracion de Anaconda...
set CONDA_ACTIVATE="%USERPROFILE%\anaconda3\Scripts\activate.bat"
if exist %CONDA_ACTIVATE% (
    echo Anaconda detectado con exito.
) else (
    echo Error: No se pudo localizar Anaconda en la ruta esperada.
    pause
    exit /b 1
)

echo [2/3] Activando entorno 'agente_ia'...
call %CONDA_ACTIVATE% agente_ia
if errorlevel 1 (
    echo Error: No se pudo activar el entorno de Conda 'agente_ia'.
    echo Asegurate de haberlo creado como dice en tu README.
    pause
    exit /b 1
)

echo [3/3] Actualizando e instalando requerimientos faltantes...
python -m pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt

echo.
echo ===================================================
echo           Todo listo. Abriendo interfaz visual...
echo ===================================================
python gui.py

REM Solo pausar si ocurre un error o al cerrar
echo.
echo La aplicacion se ha cerrado.
pause
