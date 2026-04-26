"""
Dynamic file parser — reads ANY CSV or TXT file from DATA_DIR.

Key behaviours
──────────────
1. Discovery   — scans DATA_DIR recursively for files whose extension matches
                 FILE_EXTENSIONS (.csv and .txt by default).  No hardcoded
                 filenames or counters.

2. Delimiter   — auto-detected per file (comma, tab, semicolon, pipe) unless
                 CSV_DELIMITER is set in .env.

3. Columns     — read from the header row when HAS_HEADER=true.
                 When HAS_HEADER=false (or the header is missing), columns are
                 named col_0, col_1, col_2, …

4. Numeric     — only numeric columns are kept in the signal window.
                 Non-numeric columns are logged and dropped silently.

5. Windowing   — same sliding-window logic as before (WINDOW_SIZE / WINDOW_STEP).

6. Output      — yields one FileRecord per window.  The `signals` dict carries
                 every numeric column so downstream code never hard-codes field
                 names.
"""

from __future__ import annotations

import csv
import io
import logging
from pathlib import Path
from typing import Dict, Generator, List, Optional, Tuple

import pandas as pd

from config.settings import settings
from schemas.models import FileRecord

logger = logging.getLogger(__name__)


# ── Delimiter detection ───────────────────────────────────────────────────────

def _detect_delimiter(sample: str) -> str:
    """
    Sniff the delimiter from the first ~8 KB of the file.
    Falls back to comma if sniffer fails.
    """
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",\t;|")
        return dialect.delimiter
    except csv.Error:
        return ","


# ── File discovery ────────────────────────────────────────────────────────────

def list_data_files() -> List[Path]:
    """
    Scan DATA_DIR (recursively) for every file whose extension is in
    FILE_EXTENSIONS.  Files are returned sorted by name so processing order
    is deterministic.

    Change DATA_DIR in .env — nothing else needs to touch this function.
    """
    data_dir = Path(settings.DATA_DIR)

    if not data_dir.exists():
        logger.error(f"DATA_DIR does not exist: {data_dir}")
        return []

    if not data_dir.is_dir():
        logger.error(f"DATA_DIR is not a directory: {data_dir}")
        return []

    allowed = set(settings.extensions)           # e.g. {'csv', 'txt'}
    found: List[Path] = []

    for path in sorted(data_dir.rglob("*")):
        if path.is_file() and path.suffix.lstrip(".").lower() in allowed:
            found.append(path)

    if found:
        logger.info(
            f"Discovered {len(found)} file(s) in {data_dir} "
            f"(extensions: {sorted(allowed)})"
        )
        for p in found:
            logger.info(f"  → {p.relative_to(data_dir)}")
    else:
        logger.warning(
            f"No files found in {data_dir} with extensions: {sorted(allowed)}"
        )

    return found


# ── Single-file reader ────────────────────────────────────────────────────────

def _read_dataframe(filepath: Path) -> Optional[Tuple[pd.DataFrame, bool]]:
    """
    Read *filepath* into a DataFrame.

    Returns (df, has_header) or None on failure.

    Column-naming rules
    ───────────────────
    • HAS_HEADER=true  → use the file's own header row as column names.
    • HAS_HEADER=false → assign col_0, col_1, … automatically.

    In both cases non-numeric columns are dropped after loading.
    """
    has_header: bool = settings.HAS_HEADER

    # ── Determine delimiter ───────────────────────────────────────────────────
    if settings.CSV_DELIMITER:
        delimiter = settings.CSV_DELIMITER
    else:
        try:
            with filepath.open("r", encoding="utf-8", errors="replace") as fh:
                sample = fh.read(8192)
            delimiter = _detect_delimiter(sample)
        except Exception as exc:
            logger.warning(f"  Could not sniff delimiter for {filepath.name}: {exc} — using comma")
            delimiter = ","

    logger.debug(f"  {filepath.name}: delimiter={repr(delimiter)}, has_header={has_header}")

    # ── Read the file ─────────────────────────────────────────────────────────
    try:
        read_kwargs: dict = dict(
            sep=delimiter,
            encoding="utf-8",
            encoding_errors="replace",
            on_bad_lines="warn",
        )

        if has_header:
            df = pd.read_csv(filepath, header=0, **read_kwargs)
            # Strip whitespace from column names
            df.columns = [str(c).strip() for c in df.columns]
        else:
            df = pd.read_csv(filepath, header=None, **read_kwargs)
            # Auto-name: col_0, col_1, …
            df.columns = [f"col_{i}" for i in range(len(df.columns))]
            has_header = False

    except Exception as exc:
        logger.error(f"  Cannot read {filepath.name}: {exc}")
        return None

    # ── Keep only numeric columns ─────────────────────────────────────────────
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    dropped = [c for c in df.columns if c not in numeric_cols]
    if dropped:
        logger.info(f"  {filepath.name}: dropping non-numeric columns: {dropped}")

    if not numeric_cols:
        logger.error(f"  {filepath.name}: no numeric columns found — skipping file")
        return None

    df = df[numeric_cols].dropna()

    if len(df) == 0:
        logger.warning(f"  {filepath.name}: 0 usable rows after NaN drop — skipping")
        return None

    logger.info(
        f"  {filepath.name}: {len(df):,} rows × {len(numeric_cols)} columns  "
        f"columns={numeric_cols}"
    )
    return df, has_header


# ── Window generator ──────────────────────────────────────────────────────────

def parse_file(
    filepath: Path,
    file_index: int,
) -> Generator[FileRecord, None, None]:
    """
    Read *filepath* and yield one FileRecord per sliding window.

    Args:
        filepath:   Full path to the CSV/TXT file.
        file_index: Zero-based position among all discovered files.

    Yields:
        FileRecord for each window.
    """
    result = _read_dataframe(filepath)
    if result is None:
        return

    df, has_header = result
    column_names   = df.columns.tolist()
    total_rows     = len(df)
    window_size    = settings.WINDOW_SIZE
    window_step    = settings.WINDOW_STEP
    window_idx     = 0

    i = 0
    while i + window_size <= total_rows:
        chunk = df.iloc[i : i + window_size]

        # Build the dynamic signals dict: {col_name: [float, …]}
        signals: Dict[str, List[float]] = {
            col: chunk[col].tolist() for col in column_names
        }

        yield FileRecord(
            file_index   = file_index,
            file_name    = filepath.name,
            file_path    = str(filepath.resolve()),
            window_index = window_idx,
            row_start    = i,
            row_end      = i + window_size - 1,
            signals      = signals,
            column_names = column_names,
            column_count = len(column_names),
            has_header   = has_header,
        )

        i += window_step
        window_idx += 1

    logger.info(f"  {filepath.name}: yielded {window_idx} windows")
