import logging
import sys

from config.settings import settings
from consumer import run_consumer

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("forecasting_service")


def main() -> None:
    logger.info("Starting forecasting-service consumer")
    logger.info(f"RabbitMQ URL: {settings.RABBITMQ_URL[:50]}...")
    logger.info(f"Queue: {settings.MOTOR_QUEUE}")
    run_consumer()


if __name__ == "__main__":
    main()