import logging

logger = logging.getLogger("agentic_db")

handler = logging.StreamHandler()
formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s")

handler.setFormatter(formatter)
logger.addHandler(handler)

logger.setLevel(logging.INFO)
