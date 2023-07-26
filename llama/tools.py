import logging
import os
import sys
from .settings import Settings


def setup_logging(settings: Settings):
    """
    Setup a stream handler to stdout and a file handler
    to write to ./logs/logfile.log from the root logger for convenience
    """
    # Create a logger
    logger = logging.getLogger()
    logger.setLevel(settings.log_level.upper())

    # Create a StreamHandler and set the log level
    stream_handler = logging.StreamHandler(stream=sys.stdout)

    logfolder, logfile = os.path.join(os.getcwd(), "logs"), "logfile.log"
    if not os.path.exists(logfolder):
        os.makedirs(logfolder)
    file_handler = logging.FileHandler(f"{logfolder}/{logfile}")
    # Create a formatter for the log messages
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    stream_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    # Add the StreamHandler to the logger
    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)
