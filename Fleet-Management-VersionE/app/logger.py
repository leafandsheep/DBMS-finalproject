# coding=utf-8

import logging
import os
from logging.handlers import RotatingFileHandler


LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')


def _build_formatter():
    return logging.Formatter(
        '[%(asctime)s] %(levelname)-8s %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )


def setup_logger(app):
    os.makedirs(LOGS_DIR, exist_ok=True)

    log_file = os.path.join(LOGS_DIR, 'app.log')
    formatter = _build_formatter()

    if not any(
        isinstance(handler, RotatingFileHandler) and getattr(handler, 'baseFilename', '') == log_file
        for handler in app.logger.handlers
    ):
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding='utf-8',
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        app.logger.addHandler(file_handler)

    if not any(type(handler) is logging.StreamHandler for handler in app.logger.handlers):
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        console_handler.setFormatter(formatter)
        app.logger.addHandler(console_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info('Logger 初始化完成，log 檔案位置：%s', log_file)


def get_api_logger(name):
    os.makedirs(LOGS_DIR, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if logger.handlers:
        return logger

    formatter = _build_formatter()
    log_file = os.path.join(LOGS_DIR, 'api.log')

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding='utf-8',
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger
