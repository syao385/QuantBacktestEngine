import argparse
import sys
from quant_engine import __version__

def main():
    parser = argparse.ArgumentParser(
        prog="quant-engine",
        description="QuantBacktestEngine: Standalone Backtesting, Optimization & Strategy Platform"
    )
    
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"%(prog)s {__version__}"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")
    
    # UI Sub-command
    ui_parser = subparsers.add_parser("ui", help="Launch interactive Web Visualization Dashboard")
    ui_parser.add_argument("--host", type=str, default="127.0.0.1", help="Host address (default: 127.0.0.1)")
    ui_parser.add_argument("--port", type=int, default=8500, help="Port to listen on (default: 8500)")
    
    # Run Sub-command placeholder
    run_parser = subparsers.add_parser("run", help="Run a strategy backtest")
    run_parser.add_argument("--spec", type=str, required=False, help="Path to strategy spec YAML file")
    run_parser.add_argument("--symbol", type=str, default="SPY", help="Trading symbol (default: SPY)")
    
    args = parser.parse_args()
    
    if args.command == "ui":
        print(f"🚀 Starting QuantBacktestEngine Web Dashboard on http://{args.host}:{args.port}...")
        try:
            import uvicorn
            # We will wire app when server module is built
            uvicorn.run("quant_engine.server.app:app", host=args.host, port=args.port, reload=True)
        except Exception as e:
            print(f"Error starting server: {e}")
            sys.exit(1)
    elif args.command == "run":
        print(f"📈 Running backtest for {args.symbol}...")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
