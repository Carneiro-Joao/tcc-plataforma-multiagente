@echo off
setlocal
title AulaIA - Prototipo
cd /d "%~dp0aula-ia-backend"
if errorlevel 1 (
    echo Nao foi possivel encontrar a pasta aula-ia-backend.
    pause
    exit /b 1
)
where py >nul 2>nul
if errorlevel 1 (
    python iniciar_prototipo.py
) else (
    py -3 iniciar_prototipo.py
)
echo.
echo O servidor foi encerrado. Pressione uma tecla para fechar esta janela.
pause >nul
endlocal
