# src/helpers/helpers_logging.py
import logging
import os
from logging import config

from .helpers_serialize import get_serialized_data


def init_logger_from_file(logger_name: str, config_full_path: str) -> logging.Logger:
    """
    Initializes the logger from a YAML/JSON/TOML config file.

    :param logger_name: Name of the logger to retrieve.
    :param config_full_path: Full path to the logging config file.
    :return: Configured logger instance.
    :rtype: logging.Logger
    """
    dict_config = get_serialized_data(config_full_path)
    log_file_path = dict_config.get("handlers", {}).get("file", {}).get("filename")
    config.dictConfig(dict_config)
    logger = logging.getLogger(logger_name)
    logger.info(f"start logger {logger_name}")
    logger.info(f"logger filename={log_file_path}")
    if dict_config.get("open_logging_file") and log_file_path:
        os.startfile(log_file_path)
    return logger
