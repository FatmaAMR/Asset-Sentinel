"""
IngestionService — discovers all CSV/TXT files in DATA_DIR,
slices each into windows, and publishes every window to RabbitMQ.

Flow per file:
  1. Check registry  (skip if already ingested successfully)
  2. Parse file into windows  (utils/file_parser.py)
  3. Wrap each window in MessageEnvelope  (utils/helpers.py)
  4. Publish to motor.raw queue  (utils/publisher.py)
  5. Mark file in registry  (db/connection.py)
"""

from __future__ import annotations

import logging

from config.settings import settings
from db.connection import (
    init_db,
    get_session,
    is_already_ingested,
    mark_ingested,
)
from schemas.models import IngestionResult
from utils.file_parser import list_data_files, parse_file
from utils.helpers import build_envelope
from utils.publisher import RabbitMQPublisher

logger = logging.getLogger(__name__)


class IngestionService:
    def __init__(self) -> None:
        init_db()
        self.publisher = RabbitMQPublisher()
        self.result = IngestionResult()

    def run(self) -> IngestionResult:
        files = list_data_files()

        if not files:
            logger.error(f"No data files found in {settings.DATA_DIR}")
            return self.result

        self.publisher.connect()

        try:
            with get_session() as session:
                for file_index, filepath in enumerate(files):
                    file_key = str(filepath.resolve())

                    if is_already_ingested(session, file_key):
                        logger.info(f"Skipping already ingested file: {filepath.name}")
                        self.result.skipped += 1
                        continue

                    try:
                        windows = list(parse_file(filepath, file_index=file_index))

                        if not windows:
                            logger.warning(f"No valid windows in {filepath.name}")
                            self.result.failed += 1
                            continue

                        for window in windows:
                            # envelope = build_envelope(
                            #     file_name=filepath.name,
                            #     file_index=file_index,
                            #     window=window,
                            # )
                            envelope = build_envelope(record=window)
                            self.publisher.publish(envelope)
                            self.result.published += 1

                        mark_ingested(
                            session,
                            file_key,
                            filepath.name,
                            len(windows) * settings.WINDOW_SIZE,
                            len(windows),
                            True,
                        )

                        logger.info(
                            f"Ingested {filepath.name}: {len(windows)} windows"
                        )

                    except Exception as exc:
                        logger.error(f"Failed to ingest {filepath.name}: {exc}")

                        mark_ingested(
                            session,
                            file_key,
                            filepath.name,
                            0,
                            0,
                            False,
                            str(exc),
                        )

                        self.result.failed += 1
                        self.result.errors.append(str(exc))

        finally:
            self.publisher.close()

        return self.result