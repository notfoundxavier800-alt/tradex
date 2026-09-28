"""
Merton Jump-Diffusion Barrier Model with Compound Poisson Process.
dS_t = (mu - lambda * k) * S_t dt + sigma * S_t dW_t + S_t (exp(Y) - 1) dN_t

Computes:
1. Analytical probability Phi(d) of price finishing > strike K over remaining tau seconds
2. Jump intensity lambda and jump size distribution Y ~ N(mu_J, sigma_J^2)
3. Volatility-adjusted drift expectation E[S_tau]

Pure NumPy and standard library math implementation (no scipy).
"""

from typing import Dict, Any, Optional, Union, List
import math
import numpy as np
import pandas as pd


def norm_cdf(x: float) -> float:
    """Standard normal cumulative distribution function Phi(x)."""
    return 0.5 * (1.0 + math.erf(x / 1.4142135623730951))


class MertonJumpDiffusion:
    """
    Merton Jump-Diffusion Compound Poisson Analytical Solver.
    """

    def __init__(
        self,
        default_jump_intensity: float = 0.5,
        default_mu_j: float = 0.0,
        default_sigma_j: float = 0.001
    ):
        self.default_jump_intensity = float(default_jump_intensity)
        self.default_mu_j = float(default_mu_j)
        self.default_sigma_j = float(default_sigma_j)

    def solve_barrier(
        self,
        prices: Union[pd.DataFrame, np.ndarray, List[float]],
        round_open_price: float = 0.0,
        time_left: float = 5.0,
        order_flow: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Solves analytical jump-diffusion barrier breach probabilities.
        """
        if isinstance(prices, pd.DataFrame):
            if prices.empty or "close" not in prices.columns or len(prices) < 5:
                p_arr = np.array([], dtype=float)
            else:
                p_arr = prices["close"].iloc[-40:].values.astype(float)
        elif isinstance(prices, (list, tuple, np.ndarray)):
            p_arr = np.array(prices, dtype=float)
        else:
            p_arr = np.array([], dtype=float)

        valid_mask = np.isfinite(p_arr)
        p_arr = p_arr[valid_mask]

        s0 = float(p_arr[-1]) if len(p_arr) > 0 else float(round_open_price)
        k = float(round_open_price if round_open_price > 0 else s0)
        tau = max(0.5, float(time_left if time_left is not None else 5.0)) / 31536000.0  # Annualized seconds

        if s0 <= 0 or k <= 0:
            return {
                "prob_up": 0.50,
                "prob_down": 0.50,
                "score": 0.0,
                "signal": 0,
                "detail": "Merton: Invalid Zero Price"
            }

        # Volatility estimation from price differences
        if len(p_arr) >= 5:
            log_returns = np.diff(np.log(np.maximum(1e-5, p_arr)))
            sigma_1s = float(np.std(log_returns)) if len(log_returns) > 1 else 0.0001
            sigma_annual = max(0.05, sigma_1s * np.sqrt(31536000.0))
            drift_1s = float(np.mean(log_returns)) if len(log_returns) > 1 else 0.0
            mu_annual = drift_1s * 31536000.0
        else:
            sigma_annual = 0.50
            mu_annual = 0.0

        of = order_flow or {}
        jump_mult = 2.0 if of.get("volatility_burst") else 1.0
        lam = self.default_jump_intensity * jump_mult

        mu_j = self.default_mu_j
        sigma_j = self.default_sigma_j
        k_jump = math.exp(mu_j + 0.5 * sigma_j * sigma_j) - 1.0

        # Truncated Poisson series summation up to n=5 jumps
        p_up_acc = 0.0
        max_n = 5
        for n in range(max_n):
            poisson_p = math.exp(-lam * tau) * ((lam * tau) ** n) / math.factorial(n)
            sigma_n = math.sqrt(sigma_annual * sigma_annual * tau + n * sigma_j * sigma_j)
            if sigma_n <= 1e-8:
                d2 = 0.0
            else:
                d2 = (
                    math.log(s0 / k) +
                    (mu_annual - lam * k_jump - 0.5 * sigma_annual * sigma_annual) * tau +
                    n * mu_j
                ) / sigma_n
            p_up_acc += poisson_p * norm_cdf(d2)

        prob_up = float(np.clip(p_up_acc, 0.01, 0.99))
        prob_down = float(1.0 - prob_up)

        delta = s0 - k
        sig = 1 if prob_up >= 0.55 else (-1 if prob_down >= 0.55 else 0)
        score = float(np.clip((prob_up - 0.50) * 2.0, -1.0, 1.0))

        detail = f"Merton Jump-Diffusion: P(UP)={prob_up * 100:.1f}%, P(DOWN)={prob_down * 100:.1f}% (Δ={delta:+.2f})"

        return {
            "prob_up": round(prob_up, 4),
            "prob_down": round(prob_down, 4),
            "p_up": round(prob_up, 4),
            "p_down": round(prob_down, 4),
            "score": round(score, 4),
            "signal": sig,
            "annual_vol": round(sigma_annual, 3),
            "detail": detail
        }

    def compute(
        self,
        prices: Union[pd.DataFrame, np.ndarray, List[float]],
        round_open_price: float = 0.0,
        time_left: float = 5.0
    ) -> float:
        """Returns normalized score in [-1.0, 1.0]."""
        res = self.solve_barrier(prices, round_open_price, time_left)
        return float(res.get("score", 0.0))
