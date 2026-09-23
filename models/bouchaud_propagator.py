"""
Bouchaud Propagator Model of Transient Market Impact (Feature 6 / Pillar 6).
Models sub-diffusive transient market impact decay I(t) ~ t^{-gamma}
where gamma is typically in [0.2, 0.5] in pure NumPy without scipy.
Prevents entering trades after aggressive market impact has peaked.
"""

from typing import Dict, Any, Optional
import numpy as np


class BouchaudPropagator:
    """
    Bouchaud Propagator Model:
    Evaluates bare propagator decay kernel G(tau) = (1.0 + tau)^{-gamma}
    and calculates expected post-impact price trajectory.
    """

    def __init__(self, gamma: float = 0.25):
        self.gamma = float(gamma)

    def compute(
        self,
        decay_kernel: Optional[float] = None,
        taker_delta: float = 0.0,
        tau: float = 1.0,
        *args,
        **kwargs
    ) -> float:
        """
        Compute normalized impact score in [-1.0, 1.0].
        Decays monotonically with time horizon tau for a given taker_delta.
        """
        g = float(decay_kernel if decay_kernel is not None else self.gamma)
        t = max(0.01, float(tau))
        delta = float(taker_delta)
        kernel = float((1.0 + t) ** (-g))
        impact = float(np.tanh(0.15 * delta * kernel))
        return float(np.clip(impact, -1.0, 1.0))

    def evaluate(
        self,
        decay_kernel: Optional[float] = None,
        taker_delta: float = 0.0,
        tau: float = 1.0
    ) -> Dict[str, Any]:
        """
        Evaluate full model outputs matching confluence matrix contracts.
        """
        g = float(decay_kernel if decay_kernel is not None else self.gamma)
        t = max(0.01, float(tau))
        delta = float(taker_delta)
        kernel = float((1.0 + t) ** (-g))
        impact = float(np.tanh(0.15 * delta * kernel))
        score = float(np.clip(impact, -1.0, 1.0))
        sig = 1 if score >= 0.15 else (-1 if score <= -0.15 else 0)

        return {
            "decay_kernel": round(g, 4),
            "tau": round(t, 2),
            "propagator_decay": round(kernel, 4),
            "impact_score": round(impact, 4),
            "score": round(score, 4),
            "signal": sig,
            "detail": f"Bouchaud Propagator: Impact {impact:+.3f} (Decay G(τ)={kernel:.3f}, γ={g:.2f})"
        }
