"""
Avellaneda-Stoikov High-Frequency Market Making & Inventory Risk Skew.
Reservation Price: r(s, q, t) = s - q * gamma * sigma^2 * (T - t)

Computes:
1. Optimal dealer reservation price r(s, q, t)
2. Inventory skew in USD and basis points
3. Asymmetric quote shading to rebalance directional dealer inventory

Pure NumPy implementation without scipy.
"""

from typing import Dict, Any, Optional, Union, List
import numpy as np
import pandas as pd


class AvellanedaStoikovModel:
    """
    Avellaneda-Stoikov Market Making & Inventory Skew Model.
    """

    def __init__(self, default_gamma: float = 0.1, default_kappa: float = 1.5):
        self.default_gamma = float(default_gamma)  # Risk aversion parameter
        self.default_kappa = float(default_kappa)  # Order arrival liquidity density

    def evaluate(
        self,
        prices: Union[pd.DataFrame, np.ndarray, List[float]],
        order_flow: Optional[Dict[str, Any]] = None,
        time_left: float = 5.0
    ) -> Dict[str, Any]:
        """
        Calculates reservation price and inventory skew.
        """
        if isinstance(prices, pd.DataFrame):
            if prices.empty or "close" not in prices.columns or len(prices) < 2:
                s = 0.0
                sigma = 0.001
            else:
                p_arr = prices["close"].iloc[-30:].values.astype(float)
                s = float(p_arr[-1])
                diffs = np.diff(p_arr)
                sigma = float(np.std(diffs)) if len(diffs) > 1 else 0.0
        elif isinstance(prices, (list, tuple, np.ndarray)):
            p_arr = np.array(prices, dtype=float)
            s = float(p_arr[-1]) if len(p_arr) > 0 else 0.0
            diffs = np.diff(p_arr) if len(p_arr) > 1 else np.array([0.0])
            sigma = float(np.std(diffs)) if len(diffs) > 1 else 0.0
        else:
            s = 0.0
            sigma = 0.001

        of = order_flow or {}
        if s <= 0:
            s = float(of.get("price", of.get("current_price", 0.0)))

        if s <= 0:
            return {
                "reservation_price": 0.0,
                "skew": 0.0,
                "skew_bps": 0.0,
                "score": 0.0,
                "signal": 0,
                "detail": "Avellaneda-Stoikov: Zero Price"
            }

        # Baseline volatility floor
        vol_floor = max(0.50, s * 0.0003)
        effective_sigma = max(vol_floor, sigma)

        q = float(of.get("current_inventory", of.get("inventory_q", 0.0)))
        gamma = float(of.get("gamma_risk_aversion", self.default_gamma))
        tau = max(1.0, float(time_left if time_left is not None else 5.0))

        # Reservation price: r(s, q, t) = s - q * gamma * sigma^2 * (T - t)
        inventory_penalty = q * gamma * (effective_sigma ** 2) * (tau / 10.0)

        reservation_price = s - inventory_penalty
        skew_usd = reservation_price - s
        skew_bps = (skew_usd / s) * 10000.0

        # Score in [-1.0, 1.0]
        # When dealer is short inventory (q < 0), r > s -> upward skew -> bullish pressure
        # When dealer is long inventory (q > 0), r < s -> downward skew -> bearish pressure
        score = float(np.tanh(skew_bps / 2.0))
        sig = 1 if score >= 0.10 else (-1 if score <= -0.10 else 0)

        detail = f"Avellaneda-Stoikov: ResPrice={reservation_price:.2f} (Mid={s:.2f}, q={q:+.1f}, Skew={skew_bps:+.2f}bps)"

        return {
            "reservation_price": round(float(reservation_price), 4),
            "skew": round(float(skew_usd), 4),
            "skew_usd": round(float(skew_usd), 4),
            "skew_bps": round(float(skew_bps), 4),
            "score": round(float(score), 4),
            "signal": sig,
            "q": round(q, 2),
            "detail": detail
        }

    def compute(
        self,
        prices: Union[pd.DataFrame, np.ndarray, List[float]],
        order_flow: Optional[Dict[str, Any]] = None,
        time_left: float = 5.0
    ) -> float:
        """Returns normalized score in [-1.0, 1.0]."""
        res = self.evaluate(prices, order_flow, time_left)
        return float(res.get("score", 0.0))
