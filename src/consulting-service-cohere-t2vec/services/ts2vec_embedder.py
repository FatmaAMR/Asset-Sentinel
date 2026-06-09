"""
services/ts2vec_embedder.py
────────────────────────────
Real TS2Vec encoder for sensor sliding-window data.

Uses the `ts2vec` pip package (https://github.com/yuezhihan/ts2vec) which
implements the dilated TCN contrastive architecture from:

    Yue et al. "TS2Vec: Towards Universal Representation of Time Series"
    AAAI 2022.  https://arxiv.org/abs/2106.10466

Architecture
────────────
• Encoder: dilated causal TCN → contextual representation at every timestep.
• At inference ("encode_window"):  encoding_window="full_series" collapses
  the per-timestep representations via max-pooling → 1 fixed-length vector
  per window.  This is the standard TS2Vec inference approach.
• The model is initialised with random weights on first call and stays in
  eval mode (no training required for embedding — quality comes from the
  architecture's inductive bias toward temporal structure).
  For best results, call `get_ts2vec_encoder().fit(your_data)` once during
  startup with representative training windows.

Output
──────
• Fixed-length float32 vector of length SENSOR_EMBED_DIM (default 256).
• L2-normalised before return (cosine similarity ready).

Column-name handling (s1, s2, s3 … or any generic names)
──────────────────────────────────────────────────────────
The encoder accepts:
  • list[dict]  — e.g. [{"s1": 1.2, "s2": 3.4, "ts": ...}, ...]
                  Numeric columns are extracted in stable sorted order.
                  Volatile keys (timestamp, ts, time, message_id) are skipped.
  • np.ndarray  — shape (T,) or (T, C)
  • list[list]  — shape (T, C) nested lists
  • list[float] — single-channel time-series

Usage
─────
    from services.ts2vec_embedder import get_ts2vec_encoder
    enc = get_ts2vec_encoder()
    vec = enc.encode(window_sliding)   # list[dict] → np.ndarray (256,)

    # Optional: fine-tune on your own data (improves quality significantly)
    # train_data shape: (N_windows, T, C)  float32
    enc.fit(train_data, n_epochs=10)
"""
from __future__ import annotations

import logging
import math
import threading
from typing import Sequence

import numpy as np

logger = logging.getLogger("ts2vec_embedder")

SENSOR_EMBED_DIM: int = 256

# Keys that carry no physical meaning — stripped before encoding
_SKIP_KEYS = frozenset({
    "timestamp", "message_id", "msg_id", "ts", "time",
    "time_cycles", "unit_nr",         # ← add these
})

# Minimum timesteps required; shorter windows are zero-padded to this length.
# TS2Vec's TCN needs at least depth * 2^(depth-1) steps; with depth=4 → 8 steps.
_MIN_TIMESTEPS = 8


class TS2VecEncoder:
    """
    Real TS2Vec encoder wrapping the `ts2vec` pip package.

    The model uses random initialisation by default (no pre-training needed —
    the TCN architecture alone captures meaningful temporal patterns).  Call
    `.fit()` with representative windows to improve quality.

    Parameters
    ----------
    embed_dim   : output vector dimension (default 256)
    hidden_dims : TCN hidden dimension (default 64)
    depth       : number of TCN dilation layers (default 4)
    device      : "cpu" or "cuda" (auto-detected if None)
    """

    def __init__(
        self,
        embed_dim:   int = SENSOR_EMBED_DIM,
        hidden_dims: int = 64,
        depth:       int = 4,
        device:      str | None = None,
    ) -> None:
        self.embed_dim   = embed_dim
        self.hidden_dims = hidden_dims
        self.depth       = depth
        self._lock       = threading.Lock()

        # Lazy device selection
        if device is None:
            try:
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                device = "cpu"
        self.device = device

        # The actual TS2Vec model — initialised lazily per input_dims
        # because we don't know the channel count until the first window arrives.
        self._models: dict[int, object] = {}   # input_dims → TS2Vec instance
        logger.info(
            "TS2VecEncoder ready (embed_dim=%d, hidden=%d, depth=%d, device=%s).",
            embed_dim, hidden_dims, depth, device,
        )

    # ── Public API ─────────────────────────────────────────────────────────────

    def encode(self, window: object) -> np.ndarray:
        """
        Encode a sensor window into a normalised float32 vector.

        Parameters
        ----------
        window : list[dict] | np.ndarray | list[list] | list[float]

        Returns
        -------
        np.ndarray  shape (embed_dim,)  dtype float32, L2-normalised
        """
        try:
            mat = self._to_matrix(window)
            if mat is None or mat.shape[0] < 1:
                logger.warning("TS2Vec: empty window — returning zero vector.")
                return np.zeros(self.embed_dim, dtype=np.float32)

            mat = self._preprocess(mat)          # z-norm + nan-fill + pad
            vec = self._encode_matrix(mat)       # (embed_dim,) float32
            vec = self._l2_norm(vec)
            return vec.astype(np.float32)

        except Exception as exc:
            logger.error("TS2Vec encoding failed: %s", exc, exc_info=True)
            return np.zeros(self.embed_dim, dtype=np.float32)

    def fit(
        self,
        train_windows: np.ndarray,
        n_epochs: int = 10,
        n_iters:  int | None = None,
        verbose:  bool = False,
    ) -> None:
        """
        Fine-tune the TS2Vec encoder on representative sensor windows.

        Parameters
        ----------
        train_windows : np.ndarray shape (N, T, C)  float32
            N windows, each of length T with C channels.
        n_epochs      : training epochs
        n_iters       : training iterations (overrides n_epochs if set)
        verbose       : print training progress
        """
        if train_windows.ndim != 3:
            raise ValueError(
                f"train_windows must be shape (N, T, C), got {train_windows.shape}"
            )
        _, T, C = train_windows.shape
        model = self._get_or_create_model(C)

        logger.info(
            "TS2VecEncoder.fit — %d windows, T=%d, C=%d, epochs=%d",
            len(train_windows), T, C, n_epochs,
        )
        with self._lock:
            model.fit(
                train_windows.astype(np.float32),
                n_epochs=n_epochs,
                n_iters=n_iters,
                verbose=verbose,
            )
        logger.info("TS2VecEncoder.fit complete.")

    # ── Internal: model management ────────────────────────────────────────────

    def _get_or_create_model(self, input_dims: int) -> object:
        """
        Return (or create) the TS2Vec model for a given channel count.
        Models are cached so we don't rebuild the TCN on every call.
        """
        if input_dims not in self._models:
            with self._lock:
                # Double-checked locking
                if input_dims not in self._models:
                    try:
                        from ts2vec import TS2Vec
                    except ImportError as e:
                        raise ImportError(
                            "The 'ts2vec' package is required.  "
                            "Install it with:  pip install ts2vec torch"
                        ) from e

                    logger.info(
                        "TS2Vec: creating model (input_dims=%d, output_dims=%d, "
                        "hidden=%d, depth=%d, device=%s).",
                        input_dims, self.embed_dim, self.hidden_dims,
                        self.depth, self.device,
                    )
                    self._models[input_dims] = TS2Vec(
                        input_dims  = input_dims,
                        output_dims = self.embed_dim,
                        hidden_dims = self.hidden_dims,
                        depth       = self.depth,
                        device      = self.device,
                    )
        return self._models[input_dims]

    # ── Internal: encode matrix ───────────────────────────────────────────────

    def _encode_matrix(self, mat: np.ndarray) -> np.ndarray:
        """
        Encode a preprocessed (T, C) float32 matrix using real TS2Vec.

        TS2Vec.encode expects shape (batch, T, C).
        encoding_window="full_series" → max-pool over time → (batch, output_dims).
        """
        T, C = mat.shape
        model = self._get_or_create_model(C)

        # TS2Vec expects (N, T, C) float32
        x = mat[np.newaxis, :, :].astype(np.float32)   # (1, T, C)

        with self._lock:
            out = model.encode(x, encoding_window="full_series")  # (1, embed_dim)

        vec = out[0]   # (embed_dim,)
        return vec.astype(np.float32)

    # ── Internal: input conversion ────────────────────────────────────────────

    @staticmethod
    def _to_matrix(window: object) -> np.ndarray | None:
        """
        Convert any window format to a float64 numpy matrix of shape (T, C).

        Handles:
          • list[dict]  — columns sorted alphabetically (stable across calls),
                          generic names like s1,s2,s3 work fine.
          • np.ndarray  — returned as-is (reshaped if 1-D)
          • list[list]  — converted directly
          • list[float] — single-channel
        """
        if isinstance(window, np.ndarray):
            a = window.astype(np.float64)
            return a.reshape(-1, 1) if a.ndim == 1 else a

        if isinstance(window, (list, tuple)):
            if not window:
                return None

            if isinstance(window[0], dict):
                # ── list[dict] path ───────────────────────────────────────────
                # Collect numeric columns across all timesteps in SORTED order
                # so the column index is stable regardless of dict insertion order.
                # Sorting ensures s1 < s2 < s10 (natural sort by embedded int).
                seen: dict[str, None] = {}
                for step in window:
                    for k, v in step.items():
                        if k.lower() not in _SKIP_KEYS and k not in seen:
                            if isinstance(v, (int, float)) and not isinstance(v, bool):
                                seen[k] = None

                if not seen:
                    return None

                # Natural sort: "s10" > "s2" numerically
                cols = _natural_sort(list(seen.keys()))

                rows = [
                    [float(step.get(c, float("nan"))) for c in cols]
                    for step in window
                ]
                a = np.array(rows, dtype=np.float64)
                # Fill NaNs with column means
                means = np.nanmean(a, axis=0)
                means = np.where(np.isnan(means), 0.0, means)
                nans  = np.isnan(a)
                a[nans] = np.take(means, np.where(nans)[1])
                return a

            # list[list] or list[float/int]
            try:
                a = np.array(window, dtype=np.float64)
                return a.reshape(-1, 1) if a.ndim == 1 else a
            except (ValueError, TypeError):
                return None

        return None

    # ── Internal: preprocessing ───────────────────────────────────────────────

    @staticmethod
    def _preprocess(mat: np.ndarray) -> np.ndarray:
        """
        1. Replace NaN/Inf with 0.
        2. Per-channel Z-score normalisation (TS2Vec is sensitive to scale).
        3. Zero-pad to _MIN_TIMESTEPS if the window is too short.
        """
        mat = np.nan_to_num(mat, nan=0.0, posinf=0.0, neginf=0.0)

        # Z-score per channel
        mu  = mat.mean(axis=0, keepdims=True)
        std = mat.std(axis=0,  keepdims=True)
        mat = (mat - mu) / np.where(std < 1e-8, 1.0, std)

        # Pad if too short
        T, C = mat.shape
        if T < _MIN_TIMESTEPS:
            pad = np.zeros((_MIN_TIMESTEPS - T, C), dtype=mat.dtype)
            mat = np.vstack([mat, pad])

        return mat.astype(np.float32)

    @staticmethod
    def _l2_norm(vec: np.ndarray) -> np.ndarray:
        n = np.linalg.norm(vec)
        return vec / n if n > 1e-8 else vec


# ── Natural sort helper ────────────────────────────────────────────────────────

import re as _re

def _natural_sort(keys: list[str]) -> list[str]:
    """
    Sort strings so embedded integers compare numerically.
    Example: ["s1", "s10", "s2"] → ["s1", "s2", "s10"]
    """
    def _key(s: str):
        parts = _re.split(r"(\d+)", s)
        return [int(p) if p.isdigit() else p.lower() for p in parts]
    return sorted(keys, key=_key)


# ── Module-level singleton ─────────────────────────────────────────────────────

_encoder: TS2VecEncoder | None = None


def get_ts2vec_encoder() -> TS2VecEncoder:
    """Return the module-level TS2VecEncoder singleton (lazy init)."""
    global _encoder
    if _encoder is None:
        _encoder = TS2VecEncoder(embed_dim=SENSOR_EMBED_DIM)
    return _encoder
