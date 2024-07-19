# -*- encoding: utf-8 -*-

__all__ = [
    'getFileLogger', 'getLogger'
]

import logging
from logging.handlers import TimedRotatingFileHandler

_formatter = logging.Formatter(
    "%(asctime)s %(filename)s <%(module)s.%(funcName)s> [%(lineno)d] [TID:%(thread)-6d] | %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

_chandler = logging.StreamHandler()
_chandler.setFormatter(_formatter)
_nameToLevel = {
    'CRITICAL': logging.CRITICAL,
    'FATAL': logging.FATAL,
    'ERROR': logging.ERROR,
    'WARN': logging.WARNING,
    'WARNING': logging.WARNING,
    'INFO': logging.INFO,
    'DEBUG': logging.DEBUG,
    'NOTSET': logging.NOTSET,
}


def getFileLogger(name=None, file=None, level='DEBUG'):
    level = _nameToLevel[level.upper()]
    _fhandler = TimedRotatingFileHandler(file, when='midnight', backupCount=10, encoding="utf-8")
    _fhandler.suffix = "%Y-%m-%d"
    _fhandler.setFormatter(_formatter)

    logger = logging.getLogger(name)
    logger.handlers.clear()

    logger.setLevel(level)
    logger.addHandler(_fhandler)
    logger.addHandler(_chandler)

    return logger


def getLogger(name=None, level='DEBUG'):
    level = _nameToLevel[level.upper()]
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(_chandler)

    return logger
