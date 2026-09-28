"""
Hawkes Self-Exciting Point Process Cascade Model.
lambda(t) = mu + sum_{t_i < t} alpha * exp(-beta * (t - t_i))

Computes:
1. Instantaneous order arrival intensity lambda(t)
2. Branching ratio eta = alpha / beta
   - eta < 0.8: Sub-critical Poisson flow (calm)
   - 0.8 <= eta < 1.0: Near-critical clustering (cascade alert)
   - eta >= 1.0: Super-critical avalanche (liquidity shock / aggressive sweep)
3. Dominant trade direction (signed intensity)

Pure NumPy implementation without scipy.
"""

from typing import Dict, Any, Optional, List
import numpy as np


class HawkesPointProcess:
    """
    Hawkes Self-Exciting Point Process for predatory order flow detection.
    """

    def __init__(self, beta: float = 1.2):
        self.beta = float(beta)

    def evaluate(self, order_flow: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Calculates Hawkes intensity and branching ratio from trade flow.
        """
        of = order_flow or {}
        timestamps = of.get("trade_timestamps", [])
        volumes = of.get("trade_volumes", [])
        sides = of.get("trade_sides", [])
        burst_intensity = float(of.get("burst_intensity", 1.0))

        if not timestamps or len(timestamps) < 3:
            taker_buy_pct = float(of.get("taker_buy_pct_5s", 50.0))
            delta_5s = float(of.get("delta_5s", 0.0))
            recent_trades = float(of.get("recent_trade_count", 10.0))

            vol_ratio = abs(taker_buy_pct - 50.0) / 50.0
            eta = min(0.99, max(0.20, (recent_trades / 30.0) * 0.5 + vol_ratio * 0.4))
            is_cascade = eta >= 0.80
            sig = 1 if (taker_buy_pct > 52.0 and delta_5s > 0) else (-1 if (taker_buy_pct < 48.0 and delta_5s < 0) else 0)
            score = float(np.clip(sig * (eta if is_cascade else 0.3), -1.0, 1.0))

            return {
                "intensity": round(burst_intensity, 3),
                "branching_ratio": round(float(eta), 3),
                "is_cascade": is_cascade,
                "is_avalanche": eta >= 1.0,
                "score": round(score, 3),
                "signal": sig,
                "dominant_side": "BUY" if sig > 0 else ("SELL" if sig < 0 else "NEUTRAL"),
                "detail": f"Hawkes Aggregate: η={eta:.2f} ({'CASCADE' if is_cascade else 'Normal'})"
            }

        t_arr = np.array(timestamps, dtype=float)
        now = t_arr[-1]
        dt = np.maximum(0.0, now - t_arr[:-1])

        # Exponential decay weights: exp(-beta * dt)
        decay_weights = np.exp(-self.beta * dt)

        # Baseline intensity mu & trade arrival frequency
        time_span = max(0.1, float(t_arr[-1] - t_arr[0]))
        trade_frequency = len(t_arr) / time_span

        # Kernel excitation alpha scaled by frequency and clustering
        clustering = float(np.mean(decay_weights)) if len(decay_weights) > 0 else 0.0
        # When trade_frequency is high (e.g. >= 20 trades/s) or clustering is high
        freq_factor = min(2.0, trade_frequency / 25.0)
        alpha = max(0.05, (freq_factor * 0.70 + clustering * 0.60) * self.beta)
        eta = float(alpha / self.beta)

        # Instantaneous intensity lambda(t)
        mu = max(0.10, trade_frequency * 0.3)
        intensity = mu + float(np.sum(alpha * decay_weights))

        # Directional attribution
        if sides and len(sides) == len(timestamps):
            buy_weights = sum(decay_weights[i] for i in range(len(decay_weights)) if str(sides[i]).upper() == "BUY")
            sell_weights = sum(decay_weights[i] for i in range(len(decay_weights)) if str(sides[i]).upper() == "SELL")
            tot = max(1e-5, buy_weights + sell_weights)
            dir_bias = (buy_weights - sell_weights) / tot
        else:
            taker_buy_pct = float(of.get("taker_buy_pct_5s", 50.0))
            dir_bias = (taker_buy_pct - 50.0) / 50.0

        is_cascade = eta >= 0.80
        is_avalanche = eta >= 1.0

        sig = 1 if dir_bias > 0.15 else (-1 if dir_bias < -0.15 else 0)
        score = float(np.clip(dir_bias * min(1.0, eta * 1.2), -1.0, 1.0))

        detail = f"Hawkes Cascade: η={eta:.2f}, λ={intensity:.1f}/s ({'SUPERCRITICAL AVALANCHE' if is_avalanche else ('CASCADE' if is_cascade else 'Sub-critical')})"

        return {
            "intensity": round(intensity, 3),
            "branching_ratio": round(eta, 3),
            "is_cascade": is_cascade,
            "is_avalanche": is_avalanche,
            "score": round(score, 3),
            "signal": sig,
            "dominant_side": "BUY" if dir_bias > 0 else ("SELL" if dir_bias < 0 else "NEUTRAL"),
            "detail": detail
        }

    def compute(self, order_flow: Optional[Dict[str, Any]] = None) -> float:
        """Returns normalized score in [-1.0, 1.0]."""
        res = self.evaluate(order_flow)
        return float(res.get("score", 0.0))
