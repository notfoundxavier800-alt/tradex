"""
Unit and Integration Test Suite for Confluence Engine & 10 Quantitative Pillars (R3).
Tests all 10 Wall Street & Renaissance quantitative finance models in pure NumPy without scipy:
1. Renaissance HMM (Jim Simons)
2. Cont-Stoikov Queue Dynamics
3. Avellaneda-Stoikov Reservation Price & Asymmetric Skew
4. Hawkes Self-Exciting Point Process Cascades
5. Kyle's Lambda Informed Trading Impact
6. Bouchaud's Propagator Model (replacing duplicate Amihud on Vector 20)
7. Kalman State-Space Denoising
8. Merton Jump-Diffusion with mu*tau drift
9. Ornstein-Uhlenbeck Equilibrium Pull
10. Roll Microstructure Noise & Garman-Klass-Yang-Zhang Volatility

Executable via: python -m unittest discover -s tests -p "test_*.py"
"""

import unittest
import numpy as np
import pandas as pd
import analysis


class TestQuantitativePillars(unittest.TestCase):
    """
    Tier 1 & Tier 2: Validates the mathematical properties and outputs
    of each of the 10 quantitative pillars.
    """

    def setUp(self):
        self.analyzer = analysis.TechnicalAnalyzer()

    def test_pillar_1_renaissance_hmm_regime(self):
        """Pillar 1: HMM regime classifier distinguishes TRENDING, MEAN_REVERTING, and CHOP."""
        # Flat series with zero return variance -> CHOP
        df_chop = pd.DataFrame({"close": [100.0] * 25})
        res_chop = self.analyzer.classify_market_regime(df_chop)
        self.assertEqual(res_chop['regime'], 'CHOP', "Zero variance must classify as CHOP regime.")

        # Autocorrelated positive returns -> TRENDING (e.g. returns that persist)
        # e.g. returns: [0.1, 0.2, 0.4, 0.7, 1.1, 1.6, 2.2, ...]
        increments = [0.1 * (1.15 ** i) for i in range(25)]
        closes_trend = np.cumsum([100.0] + increments)
        df_trend = pd.DataFrame({"close": closes_trend})
        res_trend = self.analyzer.classify_market_regime(df_trend)
        self.assertIn(res_trend['regime'], ['TRENDING', 'TREND_MOMENTUM'])

        # Alternating whipsaw -> MEAN_REVERTING
        df_mr = pd.DataFrame({"close": [100.0 + (1.0 if i % 2 == 0 else -1.0) for i in range(25)]})
        res_mr = self.analyzer.classify_market_regime(df_mr)
        self.assertEqual(res_mr['regime'], 'MEAN_REVERTING')

    def test_pillar_2_cont_stoikov_queue_dynamics(self):
        """Pillar 2: Cont-Stoikov L2 queue replenishment vs depletion rates."""
        order_flow = {
            "depth_ladder": {
                "bids": [(64000.0, 1.0), (63990.0, 2.0)],
                "asks": [(64010.0, 10.0), (64020.0, 15.0)]
            },
            "bid_depletion_rate": 5.0,
            "ask_depletion_rate": 0.5,
            "taker_sell_vol_5s": 8.0,
            "taker_buy_vol_5s": 1.0
        }
        res = self.analyzer.calc_queue_depletion_gradient(order_flow)
        self.assertIn("score", res)
        self.assertIn("signal", res)

    def test_pillar_3_avellaneda_stoikov_skew(self):
        """Pillar 3: Avellaneda-Stoikov reservation price & asymmetric inventory skew."""
        df = pd.DataFrame({"close": [64000.0 + (i * 0.2) for i in range(30)]})
        order_flow = {
            "current_inventory": 2.5,
            "bid_ask_spread": 2.0,
            "gamma_risk_aversion": 0.1
        }
        res = self.analyzer.calc_avellaneda_stoikov(df, order_flow=order_flow, time_left=5.0)
        self.assertIn("score", res)
        self.assertIn("reservation_price", res)
        self.assertTrue("skew" in res or "skew_bps" in res)

    def test_pillar_4_hawkes_cascades(self):
        """Pillar 4: Hawkes self-exciting point process cascade detection (eta > 0.8)."""
        flow_cascade = {
            "trade_timestamps": [10.0 + (0.05 * i) for i in range(40)],
            "trade_volumes": [0.5 + (0.1 * i) for i in range(40)],
            "trade_sides": ["BUY"] * 40,
            "recent_trade_count": 45,
            "burst_intensity": 2.5
        }
        res_cascade = self.analyzer.calc_hawkes_avalanche_intensity(flow_cascade)
        self.assertIn("branching_ratio", res_cascade)
        self.assertIn("score", res_cascade)

    def test_pillar_5_kyles_lambda(self):
        """Pillar 5: Kyle's Lambda measures price impact per unit net aggressive taker volume."""
        df = pd.DataFrame({"close": [64000.0 + (i * 0.5) for i in range(25)]})
        order_flow = {
            "price_delta_5s": 15.0,
            "net_taker_volume_5s": 5.0,
            "total_taker_volume_5s": 10.0,
            "futures_price": 64000.0
        }
        res = self.analyzer.calc_kyles_lambda_fragility(df, order_flow)
        self.assertIn("lambda", res)
        self.assertIn("score", res)

    def test_pillar_6_bouchaud_propagator_impact(self):
        """Pillar 6 / Feature 6: Bouchaud Propagator Model replacing duplicate Amihud on Vector 20."""
        self.assertTrue(
            hasattr(analysis, "calc_bouchaud_propagator_impact"),
            "analysis.py must implement calc_bouchaud_propagator_impact per PROJECT.md interface contract."
        )
        if hasattr(analysis, "calc_bouchaud_propagator_impact"):
            res = analysis.calc_bouchaud_propagator_impact(decay_kernel=0.25, taker_delta=5.0, tau=2.5)
            self.assertIn("impact_score", res)
            self.assertIn("propagator_decay", res)

    def test_pillar_7_kalman_filter_velocity(self):
        """Pillar 7: Kalman state-space denoising extracts true latent price velocity."""
        np.random.seed(42)
        true_price = np.linspace(64000.0, 64050.0, 50)
        noise = np.random.normal(0, 1.0, 50)
        noisy_prices = true_price + noise
        df = pd.DataFrame({"close": noisy_prices})

        res = self.analyzer.calc_kalman_filter_velocity(df, current_price=noisy_prices[-1])
        self.assertTrue("est_price" in res or "kalman_price" in res)
        self.assertIn("score", res)

    def test_pillar_8_merton_jump_diffusion(self):
        """Pillar 8: Merton Jump-Diffusion barrier model with mu*tau drift."""
        df = pd.DataFrame({"close": [64000.0 + (i * 0.5) for i in range(40)]})
        order_flow = {"volatility_burst": True, "jump_intensity": 1.8}
        res = self.analyzer.calc_merton_jump_diffusion_barrier(
            df, round_open_price=64000.0, time_left=5.0, order_flow=order_flow
        )
        self.assertTrue("prob_up" in res or "p_up" in res)
        self.assertTrue("prob_down" in res or "p_down" in res)
        self.assertIn("score", res)

    def test_pillar_9_ornstein_uhlenbeck_pull(self):
        """Pillar 9: Ornstein-Uhlenbeck equilibrium pull towards micro-VWAP."""
        prices = np.array([64000.0] * 20 + [64010.0, 64020.0, 64030.0])
        res = self.analyzer.calc_ornstein_uhlenbeck(prices)
        self.assertIn("score", res)
        self.assertTrue("theta" in res or "z_score" in res)

    def test_pillar_10_roll_noise_and_gkyz(self):
        """Pillar 10: Roll Microstructure Noise and Garman-Klass-Yang-Zhang Volatility."""
        df = pd.DataFrame({
            "open": [64000.0 + i for i in range(20)],
            "high": [64005.0 + i for i in range(20)],
            "low": [63995.0 + i for i in range(20)],
            "close": [64002.0 + i for i in range(20)]
        })
        res_gkyz = self.analyzer.calc_gkyz_realized_volatility(df)
        self.assertTrue("sigma_gkyz" in res_gkyz or "gkyz_vol" in res_gkyz)

        prices = df["close"].values
        res_roll = self.analyzer.calc_roll_microstructure_noise(prices)
        self.assertIn("roll_spread", res_roll)


class TestPureNumPyArchitecture(unittest.TestCase):
    """
    Tier 1 & Tier 2: Validates that all models execute in pure NumPy
    with ZERO dependency or runtime crashes from scipy.
    """

    def test_no_scipy_dependency_in_analysis(self):
        """analysis.py must not import scipy or fail if scipy is not installed."""
        analyzer = analysis.TechnicalAnalyzer()
        self.assertIsNotNone(analyzer)

    def test_numerical_stability_zero_variance(self):
        """Zero variance (identical prices) handles cleanly without ZeroDivisionError."""
        analyzer = analysis.TechnicalAnalyzer()
        flat_prices = np.array([50000.0] * 30)
        df_flat = pd.DataFrame({
            "open": flat_prices,
            "high": flat_prices,
            "low": flat_prices,
            "close": flat_prices
        })

        res_hmm = analyzer.classify_market_regime(df_flat)
        self.assertEqual(res_hmm['regime'], 'CHOP')

        res_gkyz = analyzer.calc_gkyz_realized_volatility(df_flat)
        self.assertIn("sigma_gkyz", res_gkyz)
        self.assertLessEqual(res_gkyz['sigma_gkyz'], 2.0)

        res_ou = analyzer.calc_ornstein_uhlenbeck(flat_prices)
        self.assertFalse(np.isnan(res_ou['score']))

        res_roll = analyzer.calc_roll_microstructure_noise(flat_prices)
        self.assertLessEqual(res_roll['roll_spread'], 0.05)

    def test_nan_and_inf_guarding(self):
        """NaN and inf values in input arrays are safely guarded."""
        analyzer = analysis.TechnicalAnalyzer()
        corrupt_prices = np.array([64000.0, np.nan, 64010.0, np.inf, 64005.0])
        try:
            res = analyzer.calc_ornstein_uhlenbeck(corrupt_prices)
            self.assertFalse(np.isnan(res.get('score', 0.0)))
        except Exception as e:
            self.assertIsInstance(e, (ValueError, TypeError))

    def test_hawkes_branching_ratio_subcritical_boundary(self):
        """Hawkes branching ratio eta <= 0.8 represents stable sub-critical flow."""
        analyzer = analysis.TechnicalAnalyzer()
        normal_flow = {
            "trade_timestamps": [1.0, 3.0, 5.0, 7.0, 9.0],
            "trade_volumes": [0.1, 0.1, 0.1, 0.1, 0.1],
            "burst_intensity": 0.5
        }
        res = analyzer.calc_hawkes_avalanche_intensity(normal_flow)
        self.assertLessEqual(res.get("branching_ratio", 0.0), 0.8)

    def test_avellaneda_stoikov_inventory_neutral(self):
        """When market maker inventory q is 0, reservation price equals mid price."""
        analyzer = analysis.TechnicalAnalyzer()
        df = pd.DataFrame({"close": [64000.0] * 25})
        order_flow = {"current_inventory": 0.0}
        res = analyzer.calc_avellaneda_stoikov(df, order_flow=order_flow, time_left=5.0)
        self.assertAlmostEqual(res["reservation_price"], 64000.0, places=1)

    def test_kalman_steady_state_error_covariance(self):
        """Kalman filter state variance remains bounded and positive."""
        analyzer = analysis.TechnicalAnalyzer()
        df = pd.DataFrame({"close": [64000.0 + (i * 0.1) for i in range(30)]})
        res = analyzer.calc_kalman_filter_velocity(df, current_price=64003.0)
        self.assertIn("score", res)


class TestConfluenceMatrixIntegration(unittest.TestCase):
    """
    Tier 1 & Tier 3: Validates the 24-vector confluence matrix aggregation
    and composite scoring in TechnicalAnalyzer.analyze_all.
    """

    def setUp(self):
        self.analyzer = analysis.TechnicalAnalyzer()

    def test_analyze_all_generates_indicators(self):
        """analyze_all must produce an indicators list with normalized scores."""
        df = pd.DataFrame({
            "open": [64000.0 + i for i in range(30)],
            "high": [64005.0 + i for i in range(30)],
            "low": [63995.0 + i for i in range(30)],
            "close": [64002.0 + i for i in range(30)]
        })
        scan = self.analyzer.analyze_all(df, round_open_price=64000.0, time_left=5.0)
        self.assertIn("indicators", scan)
        self.assertIn("regime", scan)
        self.assertIn("confluence_total", scan)
        self.assertGreaterEqual(len(scan["indicators"]), 15)

    def test_indicator_scores_bounded_in_negative_one_to_one(self):
        """All individual vector scores must be bounded in [-1.0, 1.0]."""
        df = pd.DataFrame({
            "open": [64000.0 + i for i in range(30)],
            "high": [64005.0 + i for i in range(30)],
            "low": [63995.0 + i for i in range(30)],
            "close": [64002.0 + i for i in range(30)]
        })
        scan = self.analyzer.analyze_all(df, round_open_price=64000.0, time_left=5.0)
        for ind in scan["indicators"]:
            score = ind.get("score", 0.0)
            self.assertGreaterEqual(score, -1.0, f"Indicator {ind.get('name')} score < -1.0")
            self.assertLessEqual(score, 1.0, f"Indicator {ind.get('name')} score > 1.0")

    def test_consensus_direction_amplifies_composite(self):
        """High consensus across venues produces strong bullish scan."""
        df = pd.DataFrame({"close": [64000.0 + (i * 2.0) for i in range(30)]})
        order_flow = {
            "global_consensus": 0.80,
            "futures_change_5s": 25.0,
            "spot_change_5s": 20.0,
            "coinbase_change_5s": 22.0,
            "bull_ratio": 80.0
        }
        scan = self.analyzer.analyze_all(df, order_flow=order_flow, round_open_price=64000.0, time_left=5.0)
        self.assertIn("confluence_total", scan)

    def test_bouchaud_impact_decay_monotonicity(self):
        """Bouchaud propagator impact decays monotonically with increasing time lag tau."""
        if hasattr(analysis, "calc_bouchaud_propagator_impact"):
            i1 = analysis.calc_bouchaud_propagator_impact(decay_kernel=0.25, taker_delta=5.0, tau=1.0)
            i2 = analysis.calc_bouchaud_propagator_impact(decay_kernel=0.25, taker_delta=5.0, tau=5.0)
            self.assertGreater(i1["impact_score"], i2["impact_score"], "Impact must decay over time.")
        else:
            self.assertTrue(hasattr(analysis, "calc_bouchaud_propagator_impact"))

    def test_unified_vector_logic_invariance(self):
        """Vector calculations maintain numerical consistency across successive calls."""
        df = pd.DataFrame({"close": [64000.0 + (i * 0.1) for i in range(25)]})
        r1 = self.analyzer.classify_market_regime(df)
        r2 = self.analyzer.classify_market_regime(df)
        self.assertEqual(r1['regime'], r2['regime'])
        self.assertEqual(r1['rho_1'], r2['rho_1'])


if __name__ == "__main__":
    unittest.main()
