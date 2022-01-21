# ##############################################################################
#  Copyright (c) 2021.                                                         #
# 
#  Projects from AndreyM                                                       #
#  The best encoder in the world!                                              #
#  email: muraigtor@gmail.com                                                         #
# ##############################################################################
import logging
import logging.config
import sys


class _ExcludeErrorsFilter(logging.Filter):
    def filter(self, record):
        """Only returns log messages with log level below ERROR (numeric value: 40)."""
        return record.levelno < 40


config = {
    'version': 1,
    'filters': {
        'exclude_errors': {
            '()': _ExcludeErrorsFilter
        }
    },
    'formatters': {
        # Modify log message format here or replace with your custom formatter class
        'my_formatter': {
            'format': '(%(process)d) %(asctime)s %(name)s (line %(lineno)s) | %(levelname)s %(message)s',
        }
    #"format": "<level>{level: <8}</level> <green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> request id: {extra[request_id]} - <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
    },
    'handlers': {
        'console_stderr': {
            # Sends log messages with log level ERROR or higher to stderr
            'class': 'logging.StreamHandler',
            'level': 'ERROR',
            'formatter': 'my_formatter',
            'stream': sys.stderr
        },
        'console_stdout': {
            # Sends log messages with log level lower than ERROR to stdout
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'my_formatter',
            'filters': ['exclude_errors'],
            'stream': sys.stdout
        },
        'file': {
            # Sends all log messages to a file
            'class': 'logging.FileHandler',
            'level': 'DEBUG',
            'formatter': 'my_formatter',
            'filename': 'my.log',
            'encoding': 'utf8'
        }
    },
    'root': {
        # In general, this should be kept at 'NOTSET'.
        # Otherwise it would interfere with the log levels set for each handler.
        'level': 'NOTSET',
        'handlers': ['console_stderr', 'console_stdout', 'file']
    },
}

loggers = logging.config.dictConfig(config)