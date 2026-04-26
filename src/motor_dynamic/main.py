"""
Motor Data Ingestion Service — entry point.

Reads every CSV / TXT file from DATA_DIR (set DATA_DIR in .env),
slices each file into windows, and publishes to RabbitMQ motor.raw queue.

Run:
    python main.py                          # batch ingest
    uvicorn api.routes:app --reload         # HTTP API + background trigger
    python consumer.py                      # teammate consumer
"""

import logging
import sys

from config.settings import settings
from services.logic import IngestionService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("ingestion")


def main() -> None:
    logger.info("═" * 60)
    logger.info("Motor Data Ingestion Service — starting")
    logger.info(f"DATA_DIR    : {settings.DATA_DIR}")
    logger.info(f"EXTENSIONS  : {settings.extensions}")
    logger.info(f"HAS_HEADER  : {settings.HAS_HEADER}")
    logger.info(f"DELIMITER   : {repr(settings.CSV_DELIMITER) or 'auto-detect'}")
    logger.info(f"WINDOW_SIZE : {settings.WINDOW_SIZE} samples")
    logger.info(f"WINDOW_STEP : {settings.WINDOW_STEP} samples")
    logger.info(f"RabbitMQ    : {settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}")
    logger.info(f"Queue       : {settings.RABBITMQ_QUEUE}")
    logger.info("═" * 60)

    try:
        result = IngestionService().run()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
    except Exception as exc:
        logger.exception(f"Fatal error: {exc}")
        sys.exit(1)

    logger.info("═" * 60)
    logger.info(
        f"DONE — published: {result.published}  "
        f"failed: {result.failed}  skipped: {result.skipped}"
    )
    if result.errors:
        logger.warning(f"{len(result.errors)} error(s):")
        for err in result.errors:
            logger.warning(f"  {err}")
    logger.info("═" * 60)


if __name__ == "__main__":
    main()
