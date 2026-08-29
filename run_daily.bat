@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

set "PY="

:: 1. Kiem tra python tren PATH co du package khong
where python >nul 2>&1
if %ERRORLEVEL% equ 0 (
    python -c "import PIL, edge_tts" >nul 2>&1
    if !ERRORLEVEL! equ 0 (
        set "PY=python"
        goto :found
    )
)

:: 2. Kiem tra duong dan Python codex-runtime
if exist "C:\Users\huynh\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" (
    "C:\Users\huynh\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -c "import PIL, edge_tts" >nul 2>&1
    if !ERRORLEVEL! equ 0 (
        set "PY=C:\Users\huynh\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
        goto :found
    )
)

:: 3. Kiem tra py launcher
where py >nul 2>&1
if %ERRORLEVEL% equ 0 (
    py -3 -c "import PIL, edge_tts" >nul 2>&1
    if !ERRORLEVEL! equ 0 (
        set "PY=py -3"
        goto :found
    )
)

:found
if not defined PY (
    echo [ERROR] KHONG TIM THAY PYTHON CO CAI DAT DU pillow VA edge-tts!
    echo Vui long mo Terminal va chay: pip install -r requirements.txt
    pause
    exit /b 1
)

echo [CreateVideo] Dang su dung Python: !PY!
!PY! run_daily.py

if !ERRORLEVEL! neq 0 (
    echo [ERROR] Co loi xay ra khi tao video (Ma loi: !ERRORLEVEL!)
    pause
    exit /b !ERRORLEVEL!
)

exit /b 0



