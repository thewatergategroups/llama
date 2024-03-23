"""
Entrypoint to the application
"""
import argparse

from yumi import setup_logging

from .entrypoints import Entry
from .settings import Settings

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="entrypoint options.")

    # Add arguments and options to the parser
    parser.add_argument(
        "entrypoint",
        help="which entrypoint to use.",
        choices=Entry.get_all_names(),
    )
    parser.add_argument(
        "db_action", nargs="?", default="upgrade", choices=["upgrade", "downgrade"]
    )
    parser.add_argument(
        "--revision",
        help="which database revision to upgrade / downgrade to.",
        default=None,
    )

    args = parser.parse_args()

    settings = Settings()

    setup_logging(settings.log_config)

    func = Entry.get_entrypoint(args.entrypoint)
    func(settings=settings, action=args.db_action, revision=args.revision)
