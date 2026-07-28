@echo off
title QuantBacktestEngine Web Dashboard
echo ============================================================
echo      LAUNCHING QUANT BACKTEST ENGINE WEB DASHBOARD
echo ============================================================
echo.

:: Check if virtual environment exists, if not initialize
if not exist ".venv" (
    echo [1/3] Virtual environment not found. Initializing with uv...
    uv venv
    uv pip install -e .
) else (
    echo [1/3] Virtual environment verified.
)

echo.
echo [2/3] Launching web browser dashboard at http://127.0.0.1:8500...
start http://127.0.0.1:8500

echo.
echo [3/3] Starting FastAPI Web Server on port 8500...
echo.
uv run quant-engine ui --host 127.0.0.1 --port 8500

pause
