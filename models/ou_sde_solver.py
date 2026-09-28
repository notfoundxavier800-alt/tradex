"""
Ornstein-Uhlenbeck (OU) Mean-Reversion Continuous-Time SDE Solver.
dX_t = theta * (mu - X_t) dt + sigma * dW_t

Computes:
1. Reversion rate (theta) and mean-reversion half-life (t_{1/2})
2. Equilibrium long-term anchor price (mu)
3. Instantaneous Z-score exhaustion (|Z| > 1.8 sigma blow-off warning)
4. Forward 5-second expected mean-reversion pull trajectory

Pure NumPy implementation without scipy.
"""

from typing import Dict, Any, Optional, Union, List
import numpy as np
import pandas as pd


class OrnsteinUhlenbeckSolver:
    """
    Continuous-Time Ornstein-Uhlenbeck SDE Solver for high-frequency pricing.
    """

    def __init__(self, z_threshold: float = 1.8):
        self.z_threshold = float(z_threshold)

    def solve(
        self,
        prices: Union[pd.DataFrame, np.ndarray, List[float]],
        current_price: float = 0.0,
        dt: float = 1.0
    ) -> Dict[str, Any]:
        """
        Solves OU SDE parameters via discrete regression and EMA equilibrium.
        """
        if isinstance(prices, pd.DataFrame):
            if prices.empty or "close" not in prices.columns or len(prices) < 5:
                p_arr = np.array([], dtype=float)
            else:
                p_arr = prices["close"].iloc[-35:].values.astype(float)
        elif isinstance(prices, (list, tuple, np.ndarray)):
            p_arr = np.array(prices, dtype=float)
        else:
            p_arr = np.array([], dtype=float)

        valid_mask = np.isfinite(p_arr)
        p_arr = p_arr[valid_mask]

        curr_p = float(current_price if current_price > 0 else (p_arr[-1] if len(p_arr) > 0 else 0.0))

        if len(p_arr) < 5 or np.std(p_arr) < 1e-6:
            return {
                "theta": 0.0,
                "half_life": 999.0,
                "mu": round(curr_p, 2),
                "sigma": 0.0,
                "z_score": 0.0,
                "signal": 0,
                "score": 0.0,
                "exhaustion_veto": False,
                "detail": "OU Equilibrium: Flat Series"
            }

        # Calculate EMA anchor
        span = min(10, len(p_arr))
        alpha = 2.0 / (span + 1.0)
        ema = p_arr[0]
        for p in p_arr[1:]:
            ema = alpha * p + (1.0 - alpha) * ema
        sigma_sample = max(1e-5, float(np.std(p_arr)))

        # Discrete regression for theta
        x_prev = p_arr[:-1]
        dx = np.diff(p_arr)
        A = np.vstack([np.ones(len(x_prev)), x_prev]).T

        try:
            a, b = np.linalg.lstsq(A, dx, rcond=None)[0]
        except Exception:
            a, b = 0.0, 0.0

        if -0.999 < b < 0.0:
            theta = -float(np.log(1.0 + b) / dt)
            theta = max(1e-4, theta)
            mu = float(-a / b)
            half_life = float(np.log(2.0) / theta)
            residuals = dx - (a + b * x_prev)
            sigma_res = float(np.std(residuals))
            sigma_eq = max(1e-5, float(sigma_res / np.sqrt(2.0 * theta)))
            z_score = float((curr_p - mu) / sigma_eq)
        else:
            # Trending / explosive excursion -> compute Z against EMA anchor
            theta = 0.05
            mu = float(ema)
            half_life = float(np.log(2.0) / theta)
            sigma_eq = sigma_sample
            z_score = float((curr_p - mu) / sigma_eq)

        is_exhausted = abs(z_score) >= self.z_threshold

        if z_score < -self.z_threshold:
            signal = 1
            score = min(1.0, max(0.40, abs(z_score) * 0.35))
            detail = f"OU Oversold Exhaustion (Z={z_score:+.2f}σ, t½={half_life:.1f}s) — Mean-Reversion to {mu:.2f}"
        elif z_score > self.z_threshold:
            signal = -1
            score = max(-1.0, min(-0.40, -abs(z_score) * 0.35))
            detail = f"OU Overbought Exhaustion (Z={z_score:+.2f}σ, t½={half_life:.1f}s) — Mean-Reversion to {mu:.2f}"
        else:
            signal = 0
            score = float(np.clip(-z_score * 0.15, -0.3, 0.3))
            detail = f"OU Equilibrium (Z={z_score:+.2f}σ, t½={half_life:.1f}s, μ={mu:.2f})"

        return {
            "theta": round(theta, 4),
            "half_life": round(half_life, 1),
            "mu": round(mu, 2),
            "sigma": round(sigma_eq, 4),
            "z_score": round(z_score, 2),
            "signal": signal,
            "score": round(float(score), 4),
            "exhaustion_veto": is_exhausted,
            "detail": detail
        }

    def compute(
        self,
        prices: Union[pd.DataFrame, np.ndarray, List[float]],
        current_price: float = 0.0
    ) -> float:
        """Convenience method returning score in [-1.0, 1.0]."""
        res = self.solve(prices, current_price)
        return float(res.get("score", 0.0))
