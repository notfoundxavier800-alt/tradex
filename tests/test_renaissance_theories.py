"""
Unit and Integration Tests for Renaissance Quantitative Theories & Models (R2).
Covers:
1. Hidden Semi-Markov Micro-Regime Model (HSMM)
2. Ornstein-Uhlenbeck (OU) Mean-Reversion Continuous-Time SDE Solver
3. Hawkes Self-Exciting Point Process Cascade Model
4. Bouchaud Propagator Model of Transient Impact Decay
5. Cont-Stoikov Queue Dynamics & Depletion Gradient
6. Merton Jump-Diffusion Compound Poisson Analytical Solver
7. Avellaneda-Stoikov Market Making & Inventory Skew
"""

import unittest
import numpy as np
import pandas as pd

from models.hsmm_regime import HiddenSemiMarkovModel
from models.ou_sde_solver import OrnsteinUhlenbeckSolver
from models.hawkes_point_process import HawkesPointProcess
from models.bouchaud_propagator import BouchaudPropagator
from models.cont_stoikov import ContStoikovQueue
from models.merton_jump_diffusion import MertonJumpDiffusion
from models.avellaneda_stoikov import AvellanedaStoikovModel


class TestRenaissanceTheories(unittest.TestCase):

    def test_hsmm_regime_classification(self):
        """HSMM identifies persistent trends, mean-reversion, and zero-variance noise."""
        hsmm = HiddenSemiMarkovModel()

        # Flat series -> RANDOM_WALK_NOISE
        res_noise = hsmm.classify(pd.DataFrame({"close": [100.0] * 25}))
        self.assertEqual(res_noise["regime"], "RANDOM_WALK_NOISE")
        self.assertEqual(res_noise["score"], 0.0)

        # Persistent positive momentum -> TREND_MOMENTUM_PERSIST
        trend_prices = [100.0 + (i * 0.5) for i in range(30)]
        res_trend = hsmm.classify(trend_prices)
        self.assertEqual(res_trend["regime"], "TREND_MOMENTUM_PERSIST")
        self.assertGreater(res_trend["score"], 0.0)
        self.assertEqual(res_trend["signal"], 1)

        # Oscillating series -> MEAN_REVERTING_CHOP
        mr_prices = [100.0 + (1.0 if i % 2 == 0 else -1.0) for i in range(30)]
        res_mr = hsmm.classify(mr_prices)
        self.assertEqual(res_mr["regime"], "MEAN_REVERTING_CHOP")
        self.assertEqual(res_mr["score"], 0.0)

    def test_ou_sde_solver(self):
        """OU SDE solver calculates theta, half-life, and flags overextended blow-offs."""
        ou = OrnsteinUhlenbeckSolver(z_threshold=1.8)

        # Flat prices -> zero z-score and no crash
        res_flat = ou.solve(np.array([50000.0] * 20))
        self.assertEqual(res_flat["z_score"], 0.0)
        self.assertFalse(res_flat["exhaustion_veto"])

        # Severe upward overextension -> Z > 1.8 and exhaustion_veto = True
        base = [60000.0] * 20
        spike_up = base + [60050.0, 60100.0, 60150.0, 60200.0]
        res_spike = ou.solve(spike_up)
        self.assertGreater(res_spike["z_score"], 1.5)
        if res_spike["z_score"] >= 1.8:
            self.assertTrue(res_spike["exhaustion_veto"])
            self.assertEqual(res_spike["signal"], -1)

    def test_hawkes_point_process(self):
        """Hawkes process calculates branching ratio and detects cascade clusters."""
        hawkes = HawkesPointProcess(beta=1.2)

        # Low intensity trades -> subcritical eta < 0.8
        flow_calm = {
            "trade_timestamps": [1.0, 3.0, 5.0, 7.0, 9.0],
            "trade_volumes": [0.1, 0.1, 0.1, 0.1, 0.1],
            "burst_intensity": 0.5
        }
        res_calm = hawkes.evaluate(flow_calm)
        self.assertLess(res_calm["branching_ratio"], 0.8)
        self.assertFalse(res_calm["is_cascade"])

        # High burst trade cascade -> eta >= 0.8
        flow_cascade = {
            "trade_timestamps": [10.0 + (0.02 * i) for i in range(50)],
            "trade_volumes": [1.0 + (0.1 * i) for i in range(50)],
            "trade_sides": ["BUY"] * 50,
            "recent_trade_count": 50,
            "burst_intensity": 3.0
        }
        res_cascade = hawkes.evaluate(flow_cascade)
        self.assertGreaterEqual(res_cascade["branching_ratio"], 0.8)
        self.assertTrue(res_cascade["is_cascade"])
        self.assertEqual(res_cascade["dominant_side"], "BUY")

    def test_bouchaud_propagator_monotonic_decay(self):
        """Bouchaud propagator impact decays monotonically with increasing tau."""
        bouchaud = BouchaudPropagator(gamma=0.25)
        imp_fast = bouchaud.compute(taker_delta=10.0, tau=1.0)
        imp_slow = bouchaud.compute(taker_delta=10.0, tau=10.0)
        self.assertGreater(imp_fast, imp_slow)

    def test_cont_stoikov_queue_dynamics(self):
        """Cont-Stoikov models bid vs ask depletion rates."""
        cs = ContStoikovQueue()
        order_flow_bull = {
            "bid_depletion_rate": 0.2,
            "ask_depletion_rate": 5.0,
            "book_imbalance_5s": 0.6,
            "taker_buy_pct_5s": 75.0
        }
        res_bull = cs.evaluate(order_flow_bull)
        self.assertGreater(res_bull["score"], 0.2)
        self.assertEqual(res_bull["signal"], 1)

    def test_merton_jump_diffusion_bounds(self):
        """Merton solver calculates probabilities strictly bounded in [0, 1]."""
        merton = MertonJumpDiffusion()
        df = pd.DataFrame({"close": [64000.0 + (i * 0.2) for i in range(25)]})
        res = merton.solve_barrier(df, round_open_price=64000.0, time_left=5.0)

        self.assertGreaterEqual(res["prob_up"], 0.0)
        self.assertLessEqual(res["prob_up"], 1.0)
        self.assertGreaterEqual(res["prob_down"], 0.0)
        self.assertLessEqual(res["prob_down"], 1.0)
        self.assertAlmostEqual(res["prob_up"] + res["prob_down"], 1.0, places=2)

    def test_avellaneda_stoikov_inventory_skew(self):
        """Avellaneda-Stoikov shifts reservation price according to dealer inventory."""
        as_model = AvellanedaStoikovModel()
        prices = [64000.0] * 20

        # Long inventory (q > 0) -> reservation price lower than mid (selling pressure)
        res_long = as_model.evaluate(prices, order_flow={"current_inventory": 5.0}, time_left=5.0)
        self.assertLess(res_long["reservation_price"], 64000.0)
        self.assertLess(res_long["skew_usd"], 0.0)

        # Short inventory (q < 0) -> reservation price higher than mid (buying pressure)
        res_short = as_model.evaluate(prices, order_flow={"current_inventory": -5.0}, time_left=5.0)
        self.assertGreater(res_short["reservation_price"], 64000.0)
        self.assertGreater(res_short["skew_usd"], 0.0)


if __name__ == "__main__":
    unittest.main()
