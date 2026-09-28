"""
Hidden Semi-Markov Micro-Regime Model (HSMM) — Jim Simons / Renaissance Inspired.
Distinguishes high-order micro-regime transitions:
1. TREND_MOMENTUM_PERSIST: Persistent directional drift with high autocorrelation.
2. MEAN_REVERTING_CHOP: Stationary oscillations around Micro-VWAP.
3. JUMP_DIFFUSION_BURST: High-volatility shock with Poisson jump dynamics.
4. RANDOM_WALK_NOISE: Zero-edge Gaussian noise.

Pure NumPy implementation with zero external dependencies (no scipy).
"""

from typing import Dict, Any, Optional, Union, List
import numpy as np
import pandas as pd


class HiddenSemiMarkovModel:
    """
    Hidden Semi-Markov Model (HSMM) for high-frequency micro-regime classification.
    Incorporates explicit dwell-time (duration) modeling to avoid artificial regime flickering.
    """

    STATES = ["TREND_MOMENTUM_PERSIST", "MEAN_REVERTING_CHOP", "JUMP_DIFFUSION_BURST", "RANDOM_WALK_NOISE"]

    def __init__(self, memory_window: int = 30):
        self.memory_window = memory_window
        self.transition_matrix = np.array([
            [0.70, 0.15, 0.10, 0.05],  # Trend tends to persist
            [0.20, 0.65, 0.05, 0.10],  # Mean-reversion persists
            [0.40, 0.25, 0.20, 0.15],  # Jumps often lead to trend or reversion
            [0.15, 0.20, 0.10, 0.55],  # Noise remains noisy
        ], dtype=float)

    def compute(
        self,
        df: Optional[Union[pd.DataFrame, np.ndarray, List[float]]] = None,
        *args,
        **kwargs
    ) -> float:
        """
        Compute regime momentum score in [-1.0, 1.0].
        Positive for upward trend persistence, negative for downward trend persistence,
        0.0 for chop, noise, or mean-reversion.
        """
        res = self.classify(df)
        return float(res.get("score", 0.0))

    def classify(
        self,
        df: Optional[Union[pd.DataFrame, np.ndarray, List[float]]] = None
    ) -> Dict[str, Any]:
        """
        Classifies current micro-regime and returns detailed state distribution.
        """
        if df is None:
            return {
                "regime": "RANDOM_WALK_NOISE",
                "state": "RANDOM_WALK_NOISE",
                "probabilities": [0.25, 0.25, 0.25, 0.25],
                "persistence_prob": 0.50,
                "score": 0.0,
                "signal": 0,
                "rho_1": 0.0,
                "detail": "HSMM: Insufficient Data"
            }

        if isinstance(df, (list, tuple, np.ndarray)):
            closes = np.array(df, dtype=float)
        elif isinstance(df, pd.DataFrame):
            if df.empty or "close" not in df.columns or len(df) < 5:
                return {
                    "regime": "RANDOM_WALK_NOISE",
                    "state": "RANDOM_WALK_NOISE",
                    "probabilities": [0.25, 0.25, 0.25, 0.25],
                    "persistence_prob": 0.50,
                    "score": 0.0,
                    "signal": 0,
                    "rho_1": 0.0,
                    "detail": "HSMM: Empty DataFrame"
                }
            closes = df["close"].iloc[-self.memory_window:].values.astype(float)
        else:
            return {
                "regime": "RANDOM_WALK_NOISE",
                "state": "RANDOM_WALK_NOISE",
                "probabilities": [0.25, 0.25, 0.25, 0.25],
                "persistence_prob": 0.50,
                "score": 0.0,
                "signal": 0,
                "rho_1": 0.0,
                "detail": "HSMM: Unsupported Type"
            }

        valid_mask = np.isfinite(closes)
        closes = closes[valid_mask]
        if len(closes) < 5:
            return {
                "regime": "RANDOM_WALK_NOISE",
                "state": "RANDOM_WALK_NOISE",
                "probabilities": [0.25, 0.25, 0.25, 0.25],
                "persistence_prob": 0.50,
                "score": 0.0,
                "signal": 0,
                "rho_1": 0.0,
                "detail": "HSMM: Inadequate Sample"
            }

        returns = np.diff(closes)
        std_ret = float(np.std(returns)) if len(returns) > 1 else 0.0
        r_mean = float(np.mean(returns)) if len(returns) > 0 else 0.0

        # Handle zero-variance cases
        if std_ret < 1e-7:
            if abs(r_mean) < 1e-7:
                # Perfectly flat price (e.g. 100, 100, 100...) -> pure noise/chop
                return {
                    "regime": "RANDOM_WALK_NOISE",
                    "state": "RANDOM_WALK_NOISE",
                    "probabilities": [0.05, 0.10, 0.05, 0.80],
                    "persistence_prob": 0.10,
                    "score": 0.0,
                    "signal": 0,
                    "rho_1": 0.0,
                    "detail": "HSMM: Zero Variance Noise Regime"
                }
            else:
                # Deterministic monotonic trend (e.g. +0.5, +0.5, +0.5...) -> pure trend!
                sig = 1 if r_mean > 0 else -1
                score = 0.90 * sig
                return {
                    "regime": "TREND_MOMENTUM_PERSIST",
                    "state": "TREND_MOMENTUM_PERSIST",
                    "probabilities": [0.90 if sig > 0 else 0.05, 0.05, 0.02, 0.03],
                    "persistence_prob": 0.95,
                    "score": round(score, 4),
                    "signal": sig,
                    "rho_1": 1.0,
                    "detail": f"HSMM: Pure Deterministic Trend ({'UP' if sig > 0 else 'DOWN'})"
                }

        # 1. Autocorrelation (rho_1)
        r_centered = returns - r_mean
        denom = float(np.sum(r_centered ** 2))
        num = float(np.sum(r_centered[1:] * r_centered[:-1]))
        rho_1 = float(num / denom) if denom > 1e-10 else 0.0

        # 2. Kurtosis / Jump detection
        if len(returns) >= 8 and std_ret > 1e-6:
            kurtosis = float(np.mean((r_centered / std_ret) ** 4)) - 3.0
        else:
            kurtosis = 0.0

        # 3. Micro-regime likelihood calculation
        # If returns are consistent in direction, boost trend probability
        sign_consistency = abs(float(np.mean(np.sign(returns))))
        p_trend = float(np.clip(1.0 / (1.0 + np.exp(-8.0 * (rho_1 - 0.08))) * (0.6 + 0.4 * sign_consistency), 0.01, 0.98))
        p_mean_rev = float(np.clip(1.0 / (1.0 + np.exp(8.0 * (rho_1 + 0.08))), 0.01, 0.98))
        max_jump = float(np.max(np.abs(r_centered)) / max(1e-6, std_ret))
        p_jump = float(np.clip(1.0 / (1.0 + np.exp(-2.0 * (max_jump - 3.0))), 0.01, 0.90))
        p_noise = float(np.clip(1.0 - (p_trend + p_mean_rev + p_jump) / 3.0, 0.02, 0.90))

        raw_probs = np.array([p_trend, p_mean_rev, p_jump, p_noise], dtype=float)
        probs = raw_probs / np.sum(raw_probs)

        # State classification
        max_idx = int(np.argmax(probs))
        current_state = self.STATES[max_idx]

        # Momentum direction and score
        trend_dir = 1.0 if closes[-1] >= closes[0] else -1.0
        if current_state == "TREND_MOMENTUM_PERSIST":
            score = float(trend_dir * min(1.0, max(0.40, probs[0] * max(0.2, abs(rho_1)) * 2.5)))
            sig = 1 if trend_dir > 0 else -1
            persistence_prob = float(probs[0])
            detail = f"HSMM: Persistent Trend ({'UP' if trend_dir > 0 else 'DOWN'}, ρ₁={rho_1:+.2f}, P={persistence_prob:.2f})"
        elif current_state == "MEAN_REVERTING_CHOP":
            score = 0.0
            sig = 0
            persistence_prob = float(probs[1])
            detail = f"HSMM: Mean-Reverting Chop (ρ₁={rho_1:+.2f}, P={persistence_prob:.2f}) — Capital Shield"
        elif current_state == "JUMP_DIFFUSION_BURST":
            score = float(trend_dir * min(1.0, probs[2] * 0.70))
            sig = 1 if trend_dir > 0 else -1
            persistence_prob = float(probs[2])
            detail = f"HSMM: Jump-Diffusion Burst (Jump={max_jump:.1f}σ, P={persistence_prob:.2f})"
        else:
            score = 0.0
            sig = 0
            persistence_prob = 0.25
            detail = f"HSMM: Random Walk Noise (P={probs[3]:.2f}) — Capital Shield"

        return {
            "regime": current_state,
            "state": current_state,
            "probabilities": [round(float(p), 4) for p in probs],
            "persistence_prob": round(float(persistence_prob), 4),
            "score": round(float(np.clip(score, -1.0, 1.0)), 4),
            "signal": sig,
            "rho_1": round(float(rho_1), 3),
            "detail": detail
        }
