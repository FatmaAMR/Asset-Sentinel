"""
Thin wrapper around the public Figshare v2 REST API.
Handles listing files for an article and streaming downloads.
"""

from __future__ import annotations

import logging
import os
from typing import Tuple

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config.settings import settings
from schemas.models import FigshareFileMeta
from utils.helpers import md5_checksum

logger = logging.getLogger(__name__)

_RETRY_STRATEGY = Retry(
    total=settings.MAX_RETRIES,
    backoff_factor=1.5,
    status_forcelist=[429, 500, 502, 503, 504],
)


class FigshareClient:
    """
    Fetches file metadata and raw bytes from the Figshare public API.

    Usage:
        client = FigshareClient()
        files  = client.list_files(article_id)
        bytes_, checksum = client.download_file(files[0])
    """

    def __init__(self) -> None:
        self._session = requests.Session()
        adapter = HTTPAdapter(max_retries=_RETRY_STRATEGY)
        self._session.mount("https://", adapter)

        if settings.FIGSHARE_TOKEN:
            self._session.headers["Authorization"] = f"token {settings.FIGSHARE_TOKEN}"

        os.makedirs(settings.FIGSHARE_DOWNLOAD_DIR, exist_ok=True)

    # ── Public ────────────────────────────────────────────────────────────────

    def list_files(self, article_id: int) -> list[FigshareFileMeta]:
        """Return metadata for every file attached to a Figshare article."""
        url = f"{settings.FIGSHARE_BASE_URL}/articles/{article_id}/files"
        logger.debug(f"GET {url}")

        resp = self._session.get(url, timeout=30)
        resp.raise_for_status()

        return [FigshareFileMeta(**item) for item in resp.json()]

    def download_file(self, meta: FigshareFileMeta) -> Tuple[bytes, str]:
        """
        Download a file and return (raw_bytes, md5_checksum).
        Caches to FIGSHARE_DOWNLOAD_DIR to avoid re-downloading on restart.
        """
        cache_path = os.path.join(settings.FIGSHARE_DOWNLOAD_DIR, meta.name)

        if os.path.exists(cache_path):
            logger.info(f"  Cache hit: {meta.name}")
            data = open(cache_path, "rb").read()
            return data, md5_checksum(data)

        logger.info(f"  Downloading {meta.name} ({meta.size:,} bytes)…")
        resp = self._session.get(meta.download_url, timeout=120, stream=True)
        resp.raise_for_status()

        chunks = []
        for chunk in resp.iter_content(chunk_size=65536):
            if chunk:
                chunks.append(chunk)
        data = b"".join(chunks)

        # Verify checksum if Figshare provides one
        computed = md5_checksum(data)
        if meta.computed_md5 and computed != meta.computed_md5:
            raise ValueError(
                f"Checksum mismatch for {meta.name}: "
                f"expected {meta.computed_md5}, got {computed}"
            )

        # Write cache
        with open(cache_path, "wb") as fh:
            fh.write(data)
        logger.info(f"  Saved to cache: {cache_path}")

        return data, computed
