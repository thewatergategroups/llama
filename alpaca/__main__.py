import os
import logging
import time
from pathlib import Path

from .src import subscribe

ALPACA_API_KEY = os.environ.get("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.environ.get("ALPACA_SECRET_KEY")
ALPACA_URL="https://paper-api.alpaca.markets"



def run_connection(conn):
    try:
        conn.run()
    except Exception as e:
        print(f'Exception from websocket connection: {e}')
    finally:
        print("Trying to re-establish connection")
        time.sleep(3)
        run_connection(conn)





if __name__ == "__main__":

    if not Path("./logs/logfile.log").is_file():
        os.mkdir("./logs")

    
    logging.basicConfig(format='%(asctime)s  %(levelname)s %(message)s',
                    level=logging.INFO,filename="./logs/logfile.log")
    subscribe.apply_async()