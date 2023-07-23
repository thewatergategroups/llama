import logging
import os
import sys


def setup_logging():
    """
    Setup a stream handler to stdout and a file handler
    to write to ./logs/logfile.log from the root logger for convenience
    """
    # Create a logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Create a StreamHandler and set the log level
    stream_handler = logging.StreamHandler(stream=sys.stdout)
    stream_handler.setLevel(logging.INFO)

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
