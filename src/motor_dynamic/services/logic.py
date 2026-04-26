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
from db.connection import init_db, get_session, is_already_ingested, mark_ingested
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
                    # Use the file's path as the unique registry key
                    file_key = str(filepath.resolve())

                    if is_already_ingested(session, file_key):
                        logger.info(f"Skipping {filepath.name} — already in registry")
                        self.result.skipped += 1
                        continue

                    logger.info(
                        f"[{file_index + 1}/{len(files)}] Processing {filepath.name}  "
                        f"path={filepath}"
                    )

                    windows_published = 0
                    total_rows        = 0
                    file_error        = None

                    try:
                        for record in parse_file(filepath, file_index):
                            if total_rows == 0:
                                total_rows = record.window_size
                            try:
                                envelope = build_envelope(record)
                                self.publisher.publish(envelope)
                                windows_published += 1
                                self.result.published += 1
                            except Exception as exc:
                                logger.warning(
                                    f"  Publish failed {filepath.name} "
                                    f"window {record.window_index}: {exc}"
                                )
                                self.result.failed += 1
                                self.result.errors.append(
                                    f"{filepath.name}[{record.window_index}]: {exc}"
                                )
                    except Exception as exc:
                        file_error = str(exc)
                        logger.error(f"  Parse error in {filepath.name}: {exc}")
                        self.result.failed += 1
                        self.result.errors.append(f"{filepath.name}: {exc}")

                    mark_ingested(
                        session,
                        file_key=file_key,
                        file_name=filepath.name,
                        total_rows=total_rows,
                        windows_published=windows_published,
                        success=file_error is None,
                        error_message=file_error,
                    )
                    logger.info(
                        f"  {filepath.name} done — {windows_published} windows published"
                    )
        finally:
            self.publisher.close()

        return self.result
