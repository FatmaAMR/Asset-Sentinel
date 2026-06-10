"""
services/ts2vec_embedder.py
────────────────────────────
TS2Vec-inspired multi-scale temporal encoder for sensor sliding-window data.

Produces a fixed-length float32 vector (SENSOR_EMBED_DIM = 256) from a list
of sensor-reading dicts (one dict per time-step).  No GPU, no trained model —
uses deterministic multi-scale statistics that mirror what TS2Vec's dilated TCN
learns: fine-to-coarse temporal structure, per-channel Z-score scale-invariance,
cross-channel correlations, and gradient dynamics.

Usage
─────
    from services.ts2vec_embedder import get_ts2vec_encoder
    enc = get_ts2vec_encoder()
    vec = enc.encode(window_sliding)  # list[dict]  →  np.ndarray shape (256,)

Drop-in replacement for the real TS2Vec pip package:
  • Same public API  (get_ts2vec_encoder, SENSOR_EMBED_DIM)
  • Same output shape (256,) float32, L2-normalised
  • No training, no GPU, no model files — fully deterministic
  • Stable vectors as long as the set of sensor columns does not change
    (adding/removing a column changes the raw feature length → re-ingest needed)
"""
from __future__ import annotations

import logging
import math
from typing import Sequence

import numpy as np

logger = logging.getLogger("ts2vec_embedder")

SENSOR_EMBED_DIM: int = 256

# Dilation scales in time-steps (mirrors TS2Vec's multi-resolution hierarchy)
_DILATION_SCALES: tuple[int, ...] = (1, 2, 4, 8, 16)

# Keys that carry no physical meaning — stripped before encoding
_SKIP_KEYS = frozenset({"timestamp", "message_id", "msg_id", "ts", "time",
                         "time_cycles", "unit_nr"})


class TS2VecEncoder:
    """
    Lightweight multi-scale temporal encoder for sensor windows.

    Deterministic — no training required.  Produces vectors that are
    comparable across calls as long as the sensor column set is stable.
    """

    def __init__(self, embed_dim: int = SENSOR_EMBED_DIM) -> None:
        self.embed_dim = embed_dim

    # ── Public ─────────────────────────────────────────────────────────────────

    def encode(self, window: object) -> np.ndarray:
        """
        Encode a sensor window into a normalised float32 vector.

        Parameters
        ----------
        window : list[dict] | np.ndarray | list[list] | list[float]
            Both row-wise  [{"temp": 72, "vib": 4.1}, ...]
            and columnar   {"temp": [72, 74], "vib": [4.1, 4.3]}
            are accepted (columnar is converted internally).

        Returns
        -------
        np.ndarray  shape (embed_dim,)  dtype float32, L2-normalised
        """
        try:
            mat = self._to_matrix(window)
            if mat is None or mat.shape[0] < 1:
                logger.warning("TS2Vec: empty window — returning zero vector.")
                return np.zeros(self.embed_dim, dtype=np.float32)
            mat = self._z_norm(mat)
            vec = self._encode_matrix(mat)
            vec = self._l2_norm(vec)
            return vec.astype(np.float32)
        except Exception as exc:
            logger.error("TS2Vec encoding failed: %s", exc)
            return np.zeros(self.embed_dim, dtype=np.float32)

    # back-compat alias used by SensorEmbedder
    def encode_window(self, window: object) -> np.ndarray:
        return self.encode(window)

    # ── Input conversion ───────────────────────────────────────────────────────

    @staticmethod
    def _to_matrix(window: object) -> np.ndarray | None:
        # --- numpy array passthrough ---
        if isinstance(window, np.ndarray):
            a = window.astype(np.float64)
            return a.reshape(-1, 1) if a.ndim == 1 else a

        # --- columnar dict  {"col": [v1, v2, ...]} ---
        if isinstance(window, dict):
            if any(isinstance(v, (list, tuple)) for v in window.values()):
                # transpose to row-wise list of dicts then fall through
                max_len = max(
                    (len(v) for v in window.values() if isinstance(v, (list, tuple))),
                    default=1,
                )
                window = [
                    {
                        col: (vals[i] if isinstance(vals, (list, tuple)) and i < len(vals) else vals)
                        for col, vals in window.items()
                    }
                    for i in range(max_len)
                ]
            else:
                # scalar dict → single-step list
                window = [window]

        if isinstance(window, (list, tuple)):
            if not window:
                return None

            # --- list of dicts (row-wise) ---
            if isinstance(window[0], dict):
                cols: list[str] = []
                seen: set[str]  = set()
                for step in window:
                    for k, v in step.items():
                        if k.lower() not in _SKIP_KEYS and k not in seen:
                            if isinstance(v, (int, float)) and not isinstance(v, bool):
                                cols.append(k)
                                seen.add(k)
                if not cols:
                    return None
                rows = [[float(step.get(c, float("nan"))) for c in cols] for step in window]
                a    = np.array(rows, dtype=np.float64)
                # fill NaNs with column mean
                means = np.nanmean(a, axis=0)
                means = np.where(np.isnan(means), 0.0, means)
                nans  = np.isnan(a)
                a[nans] = np.take(means, np.where(nans)[1])
                return a

            # --- list of numbers or list of lists ---
            try:
                a = np.array(window, dtype=np.float64)
                return a.reshape(-1, 1) if a.ndim == 1 else a
            except (ValueError, TypeError):
                return None

        return None

    # ── Normalisation ──────────────────────────────────────────────────────────

    @staticmethod
    def _z_norm(mat: np.ndarray) -> np.ndarray:
        mu  = mat.mean(axis=0, keepdims=True)
        std = mat.std(axis=0,  keepdims=True)
        return (mat - mu) / np.where(std < 1e-8, 1.0, std)

    @staticmethod
    def _l2_norm(vec: np.ndarray) -> np.ndarray:
        n = np.linalg.norm(vec)
        return vec / n if n > 1e-8 else vec

    # ── Core encoder ───────────────────────────────────────────────────────────

    def _encode_matrix(self, mat: np.ndarray) -> np.ndarray:
        T, C = mat.shape
        parts: list[np.ndarray] = []

        # 1. Multi-scale pooled statistics (9 stats × C channels × 5 scales)
        for d in _DILATION_SCALES:
            pooled = self._dilated_pool(mat, d) if d <= T else mat.mean(axis=0, keepdims=True)
            parts.append(self._stats9(pooled))       # (9*C,)

        # 2. Cross-channel Pearson correlations (upper triangle)
        if C > 1:
            with np.errstate(divide="ignore", invalid="ignore"):
                corr = np.corrcoef(mat.T)
            corr = np.nan_to_num(corr, nan=0.0, posinf=0.0, neginf=0.0)
            iu   = np.triu_indices(C, k=1)
            parts.append(corr[iu])

        # 3. First-order temporal gradient statistics
        if T > 1:
            d1 = np.diff(mat, axis=0)
            parts.append(np.concatenate([d1.mean(0), d1.std(0), np.abs(d1).max(0)]))
        else:
            parts.append(np.zeros(3 * C))

        # 4. Second-order gradient (acceleration) statistics
        if T > 2:
            d2 = np.diff(mat, n=2, axis=0)
            parts.append(np.concatenate([d2.mean(0), d2.std(0)]))
        else:
            parts.append(np.zeros(2 * C))

        # 5. Per-channel linear trend slope
        parts.append(self._slopes(mat))              # (C,)

        raw = np.concatenate([p for p in parts if len(p) > 0])
        raw = np.nan_to_num(raw, nan=0.0, posinf=0.0, neginf=0.0)

        # Project to embed_dim
        rd = len(raw)
        if rd == 0:
            return np.zeros(self.embed_dim, dtype=np.float64)
        if rd < self.embed_dim:
            raw = np.tile(raw, math.ceil(self.embed_dim / rd))[: self.embed_dim]
        elif rd > self.embed_dim:
            rng  = np.random.default_rng(seed=42 + rd)
            proj = rng.standard_normal((rd, self.embed_dim)) / math.sqrt(self.embed_dim)
            raw  = raw @ proj

        return raw.astype(np.float64)

    # ── Helpers ────────────────────────────────────────────────────────────────

    @staticmethod
    def _dilated_pool(mat: np.ndarray, d: int) -> np.ndarray:
        """Average-pool with window=d along time axis using cumsum trick."""
        T = mat.shape[0]
        if d >= T:
            return mat.mean(axis=0, keepdims=True)
        cs  = np.cumsum(mat, axis=0)
        top = cs[d:, :]
        bot = cs[:-d, :]
        return (top - bot) / d   # shape (T-d, C)

    @staticmethod
    def _stats9(mat: np.ndarray) -> np.ndarray:
        """9 statistics per channel: mean, std, min, max, range, slope, iqr, energy, zcr."""
        T, C = mat.shape
        mean   = mat.mean(0)
        std    = mat.std(0)
        mn     = mat.min(0)
        mx     = mat.max(0)
        rng    = mx - mn
        q75, q25 = np.percentile(mat, [75, 25], axis=0)
        iqr    = q75 - q25
        energy = (mat ** 2).mean(0)
        zcr    = (np.diff(np.sign(mat), axis=0) != 0).mean(0) if T > 1 else np.zeros(C)
        # Slope via dot-product with linear ramp
        if T > 1:
            x     = np.linspace(-1, 1, T)
            slope = (mat * x[:, None]).mean(0)
        else:
            slope = np.zeros(C)
        return np.concatenate([mean, std, mn, mx, rng, slope, iqr, energy, zcr])

    @staticmethod
    def _slopes(mat: np.ndarray) -> np.ndarray:
        T, C = mat.shape
        if T < 2:
            return np.zeros(C)
        x   = np.arange(T, dtype=np.float64)
        xc  = x - x.mean()
        den = (xc ** 2).sum()
        if den < 1e-10:
            return np.zeros(C)
        return ((xc[:, None] * (mat - mat.mean(0))).sum(0)) / den


# ── Module-level singleton ─────────────────────────────────────────────────────

_encoder: TS2VecEncoder | None = None


def get_ts2vec_encoder() -> TS2VecEncoder:
    """Return the module-level TS2VecEncoder singleton (created once)."""
    global _encoder
    if _encoder is None:
        _encoder = TS2VecEncoder(embed_dim=SENSOR_EMBED_DIM)
        logger.info("TS2VecEncoder ready (deterministic, embed_dim=%d).", SENSOR_EMBED_DIM)
    return _encoder
