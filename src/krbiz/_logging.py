import logging


def build_logger() -> logging.Logger:
    import rich.logging

    logger = logging.getLogger("merge-oders")
    logger.addHandler(rich.logging.RichHandler(level="DEBUG"))
    logger.setLevel("DEBUG")
    return logger
