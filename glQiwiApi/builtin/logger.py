import logging

from loguru import logger


class InterceptHandler(logging.Handler):
    def __init__(self, level: int = logging.NOTSET) -> None:
        super(InterceptHandler, self).__init__(level)

    def emit(self, record):  # type: ignore
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back  # type: ignore
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logger() -> logging.Logger:
    logger = logging.getLogger("glQiwiApi")
    aiohttp_logger = logging.getLogger("aiohttp.access")
    logger.setLevel(level=logging.DEBUG)
    aiohttp_logger.setLevel(level=logging.DEBUG)
    if not logger.handlers:
        logger.addHandler(InterceptHandler())
        aiohttp_logger.addHandler(InterceptHandler())
    return logger
