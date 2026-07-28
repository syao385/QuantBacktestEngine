#!/usr/bin/env bash
echo "============================================================"
echo "     LAUNCHING QUANT BACKTEST ENGINE WEB DASHBOARD"
echo "============================================================"

if [ ! -d ".venv" ]; then
    echo "[1/3] Virtual environment not found. Initializing with uv..."
    uv venv
    uv pip install -e .
else
    echo "[1/3] Virtual environment verified."
fi

echo "[2/3] Launching web browser dashboard at http://127.0.0.1:8500..."
if command -v open > /dev/null; then
    open http://127.0.0.1:8500
elif command -v xdg-open > /dev/null; then
    xdg-open http://127.0.0.1:8500
fi

echo "[3/3] Starting FastAPI Web Server on port 8500..."
uv run quant-engine ui --host 127.0.0.1 --port 8500
