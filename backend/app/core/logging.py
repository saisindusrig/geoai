import logging

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"


def setup_logging() -> None:
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
    # Avoid leaking secrets: never log settings objects wholesale.
    logging.getLogger("httpx").setLevel(logging.WARNING)
