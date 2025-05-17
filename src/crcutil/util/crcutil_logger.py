import logging

# ruff: noqa: ANN002, ANN003, ANN204, RUF012
import logging.config
from datetime import UTC, datetime
from pathlib import Path


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class CrcutilLogger(metaclass=SingletonMeta):
    def __init__(self, log_dir: Path, log_config: dict) -> None:
        if not hasattr(self, "initialized"):  # Avoid reinitialization
            # Time data in UTC required by date named log files
            day = str(datetime.now(UTC).day)
            month = str(datetime.now(UTC).month)
            year = str(datetime.now(UTC).year)

            log_file_name = f"{year}-{month}-{day}.log"
            # Rewrite contents of YAML config to accomodate
            # for date based log file names
            log_config["handlers"]["regular_file_handler"]["filename"] = (
                log_dir / log_file_name
            )
            # Load config with changes as Dict
            logging.config.dictConfig(log_config)
            # Initialize loggers
            self.logger = logging.getLogger("regular")
            self.console_logger = logging.getLogger("console")
            self.initialized = True

    @classmethod
    def get_logger(cls) -> logging.Logger:
        instance = cls._instances[cls]
        return instance.logger

    @classmethod
    def get_console_logger(cls) -> logging.Logger:
        instance = cls._instances[cls]
        return instance.console_logger
