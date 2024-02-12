import logging

fmt = {
    'time': '%(asctime)s',
    'name': '%(name)s',
    'level': '%(levelname)s',
    'message': '%(message)s'
}

logging.basicConfig(level=logging.WARNING, format=str(fmt))


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    return logger
