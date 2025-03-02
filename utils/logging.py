import logging
from enum import Enum


class LoggingLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


logging.basicConfig(
    filename="logs.log",
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode="w",
)

logger = logging.getLogger()

console_handler = logging.StreamHandler()
console_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
)
logger.addHandler(console_handler)


def set_logger_level(level: LoggingLevel):
    logger.setLevel(level.value)
