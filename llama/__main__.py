"""
Entrypoint to the application
"""
import argparse
from .entrypoints import ENTRYPOINTS
from .tools import setup_logging
from .settings import Settings

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="entrypoint options.")

    # Add arguments and options to the parser
    parser.add_argument("entrypoint", help="which entrypoint to use.")

    # Parse the command-line arguments
    args = parser.parse_args()

    settings = Settings()
    setup_logging(settings)

    if (entrypoint := ENTRYPOINTS.get(args.entrypoint)) is not None:
        entrypoint(settings)
    else:
        raise RuntimeError(f"entrypoint {args.entrypoint} not recognised...")
