"""
Entrypoint to the application
"""
import uvicorn
import argparse

from .tools import setup_logging
from .worker import run, backtest_moving_average

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="entrypoint options.")

    # Add arguments and options to the parser
    parser.add_argument("entrypoint", help="which entrypoint to use.")

    # Parse the command-line arguments
    args = parser.parse_args()
    setup_logging()

    if args.entrypoint == "api":
        uvicorn.run(
            "llama.api.app:create_app",
            workers=1,
            reload=True,
            host="0.0.0.0",
            factory=True,
            port=8000,
        )
    elif args.entrypoint == "worker":
        run()
    elif args.entrypoint == "backtest":
        backtest_moving_average()
    else:
        raise RuntimeError(f"entrypoint {args.entrypoint} not recognised...")
