"""
Cont-Stoikov-Talreja Order Book Queue Dynamics Model (Feature 8 / Pillar 2).
Models Level-2 limit order queue replenishment vs depletion rates
to forecast whether bids or asks will be consumed over the next 5 seconds.
Pure NumPy implementation without scipy.
"""

from typing import Dict, Any, Optional
import numpy as np


class ContStoikovQueue:
    """
    Cont-Stoikov Queue Dynamics:
    Computes depletion gradient between bid and ask limit queues.
    """

    def __init__(self):
        pass

    def compute(self, order_flow: Optional[Dict[str, Any]] = None, *args, **kwargs) -> float:
        """
        Compute queue depletion gradient score in [-1.0, 1.0].
        """
        if not order_flow:
            if args and isinstance(args[0], dict):
                order_flow = args[0]
            else:
                return 0.0

        imb = float(order_flow.get("book_imbalance_5s", 0.0))
        taker_buy_pct = float(order_flow.get("taker_buy_pct_5s", 50.0))
        bid_depletion_rate = float(order_flow.get("bid_depletion_rate", 0.0))
        ask_depletion_rate = float(order_flow.get("ask_depletion_rate", 0.0))

        if bid_depletion_rate > 0 or ask_depletion_rate > 0:
            tot = max(1e-5, bid_depletion_rate + ask_depletion_rate)
            rate_skew = (ask_depletion_rate - bid_depletion_rate) / tot
        else:
            ask_dep = max(0.0, taker_buy_pct - 50.0) / 50.0
            bid_dep = max(0.0, 50.0 - taker_buy_pct) / 50.0
            rate_skew = ask_dep - bid_dep

        grad = (rate_skew * 0.6) + (imb * 0.4)
        score = float(np.clip(grad * 1.5, -1.0, 1.0))
        return score

    def evaluate(self, order_flow: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Evaluate full queue dynamics dictionary.
        """
        score = self.compute(order_flow)
        sig = 1 if score >= 0.15 else (-1 if score <= -0.15 else 0)
        return {
            "score": round(score, 4),
            "signal": sig,
            "gradient": round(score / 1.5, 4),
            "detail": f"Cont-Stoikov Queue Score: {score:+.3f}"
        }
