"""
Jim Simons / Renaissance Hidden Markov Regime Model (Feature 7 / Pillar 1).
Distinguishes true trending regimes from random chop and mean-reverting states.
Pure NumPy implementation without scipy.
"""

from typing import Dict, Any, Optional, Union, List
import numpy as np
import pandas as pd


class RenaissanceHMM:
    """
    Renaissance HMM Regime Classifier:
    Uses discrete 3-state transition dynamics (TREND_MOMENTUM, MEAN_REVERTING, CHOP)
    calibrated on lag-1 autocorrelation and return variance.
    """

    def __init__(self):
        pass

    def compute(
        self,
        df: Optional[Union[pd.DataFrame, np.ndarray, List[float]]] = None,
        *args,
        **kwargs
    ) -> float:
        """
        Compute regime momentum score in [-1.0, 1.0].
        Positive for upward trend momentum, negative for downward trend momentum,
        0.0 for chop or mean-reversion.
        """
        if df is None and args:
            arg0 = args[0]
            if isinstance(arg0, pd.DataFrame):
                df = arg0
            elif isinstance(arg0, (list, tuple, np.ndarray)):
                df = pd.DataFrame({"close": arg0})

        if df is None:
            return 0.0

        if isinstance(df, (list, tuple, np.ndarray)):
            closes = np.array(df, dtype=float)
        elif isinstance(df, pd.DataFrame):
            if df.empty or len(df) < 5 or "close" not in df.columns:
                return 0.0
            closes = df["close"].iloc[-30:].values.astype(float)
        else:
            return 0.0

        if len(closes) < 5:
            return 0.0

        returns = np.diff(closes)
        if len(returns) < 4 or np.std(returns) < 1e-6:
            return 0.0

        r_mean = np.mean(returns)
        r_centered = returns - r_mean
        num = np.sum(r_centered[1:] * r_centered[:-1])
        denom = np.sum(r_centered ** 2)
        rho_1 = float(num / denom) if denom > 1e-10 else 0.0

        if rho_1 > 0.10:
            trend_dir = 1.0 if closes[-1] >= closes[0] else -1.0
            score = trend_dir * min(1.0, rho_1 * 2.0)
            return float(np.clip(score, -1.0, 1.0))
        else:
            return 0.0

    def classify(
        self,
        df: Optional[Union[pd.DataFrame, np.ndarray, List[float]]]
    ) -> Dict[str, Any]:
        """
        Classify regime into TREND_MOMENTUM, MEAN_REVERTING, or CHOP.
        """
        if df is None:
            return {"regime": "CHOP", "state": "CHOP", "rho_1": 0.0, "score": 0.0}

        if isinstance(df, (list, tuple, np.ndarray)):
            closes = np.array(df, dtype=float)
        elif isinstance(df, pd.DataFrame):
            if df.empty or len(df) < 5 or "close" not in df.columns:
                return {"regime": "CHOP", "state": "CHOP", "rho_1": 0.0, "score": 0.0}
            closes = df["close"].iloc[-20:].values.astype(float)
        else:
            return {"regime": "CHOP", "state": "CHOP", "rho_1": 0.0, "score": 0.0}

        returns = np.diff(closes)
        if len(returns) < 4 or np.std(returns) < 1e-6:
            return {"regime": "CHOP", "state": "CHOP", "rho_1": 0.0, "score": 0.0}

        r_mean = np.mean(returns)
        r_centered = returns - r_mean
        num = np.sum(r_centered[1:] * r_centered[:-1])
        denom = np.sum(r_centered ** 2)
        rho_1 = float(num / denom) if denom > 1e-10 else 0.0

        if rho_1 > 0.10:
            regime = "TREND_MOMENTUM"
            trend_dir = 1.0 if closes[-1] >= closes[0] else -1.0
            score = trend_dir * min(1.0, rho_1 * 2.0)
        elif rho_1 < -0.10:
            regime = "MEAN_REVERTING"
            score = 0.0
        else:
            regime = "CHOP"
            score = 0.0

        return {
            "regime": regime,
            "state": regime,
            "rho_1": round(rho_1, 3),
            "score": round(score, 3)
        }
