import logging
import os
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .settings import Settings
from datetime import datetime
from pydantic import BaseModel
from enum import Enum
from dataclasses import is_dataclass, asdict


def setup_logging(settings: "Settings"):
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


def custom_json_encoder(data):
    if isinstance(data, datetime):
        return data.isoformat()
    elif isinstance(data, Enum):
        return data.value
    elif isinstance(data, set):
        return list(data)
    elif isinstance(data, BaseModel):
        return data.dict()
    elif is_dataclass(data):
        return asdict(data)
    else:
        raise TypeError("Can't serialize item %s of type %s", data, type(data))


def divide_chunks(l, n):
    # looping till length l
    for i in range(0, len(l), n):
        yield l[i : i + n]
