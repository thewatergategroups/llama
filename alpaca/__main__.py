"""
Entrypoint to the application
"""

import logging
import time

from .subscriber import subscribe

def run_connection(conn):
    """starting connection"""
    try:
        conn.run()
    except Exception as exc:
        logging.exception(exc)
    finally:
        logging.info("Trying to re-establish connection")
        time.sleep(3)
        run_connection(conn)

if __name__ == "__main__":
    subscribe()