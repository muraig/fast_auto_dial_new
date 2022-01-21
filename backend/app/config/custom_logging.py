# -*- coding: utf-8 -*-
"""
For logging test
"""
# ##############################################################################
#  Copyright (c) 2021. Projects from AndreyM                                   #
#  The best encoder in the world!                                              #
#  email: muraig@ya.ru                                                         #
# ##############################################################################
# Custom Logger Using Loguru

import logging
import sys
from pathlib import Path

import aiologger
from loguru import logger
import json


class InterceptHandler(logging.Handler):
    loglevel_mapping = {
        50: 'CRITICAL',
        40: 'ERROR',
        30: 'WARNING',
        20: 'INFO',
        10: 'DEBUG',
        0: 'NOTSET',
    }

    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except AttributeError:
            level = self.loglevel_mapping[record.levelno]

        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        log = logger.bind(request_id='app')
        log.opt(
            depth=depth,
            exception=record.exc_info
        ).log(level, record.getMessage())


class CustomizeLogger:

    @classmethod
    def make_logger(cls, config_path: Path):
        config = cls.load_logging_config(config_path)
        logging_config = config.get('logger')

        # logger_ = aiologger.Logger.with_default_handlers()
        logger_ = cls.customize_logging(
            logging_config.get('path'),
            level=logging_config.get('level'),
            retention=logging_config.get('retention'),
            rotation=logging_config.get('rotation'),
            format=logging_config.get('format')
        )
        return logger_

    @classmethod
    def customize_logging(cls,
                          filepath: Path,
                          level: str,
                          rotation: str,
                          retention: str,
                          format: str
                          ):
        # print(f"customize_logging: {filepath, level, rotation, retention, format}")
        #print(f"71::Config file: {logger}")
        logger.remove()
        #print(f"73::Config file: {logger}")
        logger.add(
            sys.stdout,
            enqueue=True,
            backtrace=True,
            level=level.upper(),
            format=format
        )
        #print(f"81::Config file: {logger}")
        logger.add(
            str(filepath),
            rotation=rotation,
            retention=retention,
            enqueue=True,
            backtrace=True,
            level=level.upper(),
            format=format
        )
        #print(f"91::Config file: {logger}")
        # logging.basicConfig(handlers=[InterceptHandler()], level=0)
        # Unexpected argument(s)Possible callees:basicConfig(*, filename: Optional[str] = ...,
        # filemode: str = ..., format: str = ..., datefmt: Optional[str] = ..., level: Union[int, str, None] = ...,
        # stream: IO[str] = ...)basicConfig()

        # log_config = uvicorn.config.LOGGING_CONFIG
        # log_config["formatters"]["access"]["fmt"] = "%(asctime)s - %(levelname)s - %(message)s"
        # uvicorn.run("main:app", host="0.0.0.0", reload=True, port=8888, log_config=log_config)
        '''logging.getLogger("uvicorn.access").handlers = [InterceptHandler()]
        for _log in ['uvicorn',
                     'uvicorn.error',
                     'fastapi'
                     ]:
            _logger = logging.getLogger(_log)
            _logger.handlers = [InterceptHandler()]'''

        # disable handlers for specific uvicorn loggers
        # to redirect their output to the default uvicorn logger
        # works with uvicorn==0.11.6
        loggers = (
            logging.getLogger(name)
            for name in logging.root.manager.loggerDict
            if name.startswith("uvicorn.")
        )
        for uvicorn_logger in loggers:
            uvicorn_logger.handlers = []

        # change handler for default uvicorn logger
        intercept_handler = InterceptHandler()
        logging.getLogger("uvicorn").handlers = [intercept_handler]

        return logger.bind(request_id=None, method=None)

    @classmethod
    def load_logging_config(cls, config_path):
        config = None
        if Path.is_file(config_path):
            config_path
        else:
            config_path = '/app/app/config/logging_config.json'
        # print(f"Config file: {config_path}")
        with open(config_path) as config_file:
            config = json.load(config_file)
        return config
