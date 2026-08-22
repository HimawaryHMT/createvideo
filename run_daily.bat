@echo off
cd /d "D:\Project Individual\CreateVideo"

set "PY="
for %%P in (
  "C:\Users\huynh\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
  "python"
  "py -3"
) do (
    if not defined PY (
        %%~P -c "import PIL, edge_tts" >nul 2>&1 && set "PY=%%~P"
    )
)

if not defined PY (
    echo KHONG TIM THAY PYTHON CO CAI DAT pillow/edge-tts
    exit /b 1
)

echo Su dung python: %PY%
%PY% run_daily.py
