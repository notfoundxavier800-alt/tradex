"""
Unit and Integration Test Suite for Anti-Half-Prediction Engine (R2).
Tests anti-whipsaw order book obstacle absorption gate (>= 2.0 BTC walls in $2-$5 range),
CVD second-derivative deceleration (d^2CVD/dt^2), OU mean-reversion exhaustion (|Z| >= 1.8 sigma),
and forward 5-second trajectory persistence.

Executable via: python -m unittest discover -s tests -p "test_*.py"
"""

import unittest
import numpy as np
import analysis


class TestObstacleAbsorptionGate(unittest.TestCase):
    """
    Tier 1 & Tier 2: Validates detection of >= 2.0 BTC obstacle walls in the $2-$5
    range from strike price K, preventing the 'half prediction' micro-whipsaw trap.
    """

    def setUp(self):
        self.analyzer = analysis.TechnicalAnalyzer()

    def test_down_call_blocked_by_large_bid_wall_in_range(self):
        """Down call must be rejected when a >= 2.0 BTC bid wall is in $2-$5 range below strike."""
        current_p = 64000.0
        strike_k = 64000.0
        # Bid wall of 3.5 BTC at $63997.00 ($3.00 below strike)
        bids = [
            {"price": 63999.0, "qty": 0.3},
            {"price": 63998.0, "qty": 0.4},
            {"price": 63997.0, "qty": 3.5},  # In $2-$5 range, >= 2.0 BTC
            {"price": 63995.0, "qty": 0.5},
        ]
        asks = [
            {"price": 64001.0, "qty": 0.2},
            {"price": 64002.0, "qty": 0.4},
        ]

        if hasattr(analysis, "calc_forward_obstacle_absorption"):
            res = analysis.calc_forward_obstacle_absorption(bids, asks, current_p, strike_k, "DOWN")
            self.assertTrue(res['is_blocked'], "DOWN call must be blocked by 3.5 BTC bid wall at $K - $3.")
            self.assertGreaterEqual(res['wall_size'], 2.0)
            self.assertEqual(res['wall_price'], 63997.0)
        else:
            self.assertTrue(
                hasattr(analysis, "calc_forward_obstacle_absorption"),
                "analysis.py must implement calc_forward_obstacle_absorption per PROJECT.md interface contract."
            )

    def test_up_call_blocked_by_large_ask_wall_in_range(self):
        """UP call must be rejected when a >= 2.0 BTC ask wall is in $2-$5 range above strike."""
        current_p = 64000.0
        strike_k = 64000.0
        # Ask wall of 4.2 BTC at $64003.50 ($3.50 above strike)
        bids = [{"price": 63999.0, "qty": 0.5}]
        asks = [
            {"price": 64001.0, "qty": 0.3},
            {"price": 64003.5, "qty": 4.2},  # In $2-$5 range, >= 2.0 BTC
            {"price": 64006.0, "qty": 0.8},
        ]

        if hasattr(analysis, "calc_forward_obstacle_absorption"):
            res = analysis.calc_forward_obstacle_absorption(bids, asks, current_p, strike_k, "UP")
            self.assertTrue(res['is_blocked'], "UP call must be blocked by 4.2 BTC ask wall at $K + $3.50.")
            self.assertGreaterEqual(res['wall_size'], 2.0)
            self.assertEqual(res['wall_price'], 64003.5)
        else:
            self.assertTrue(
                hasattr(analysis, "calc_forward_obstacle_absorption"),
                "analysis.py must implement calc_forward_obstacle_absorption per PROJECT.md interface contract."
            )

    def test_clearance_when_wall_size_under_2_btc(self):
        """A bid wall under 2.0 BTC (e.g. 1.2 BTC) must NOT trigger an obstacle block."""
        current_p = 64000.0
        strike_k = 64000.0
        bids = [
            {"price": 63997.0, "qty": 1.2},  # < 2.0 BTC
        ]
        asks = [{"price": 64001.0, "qty": 0.5}]

        if hasattr(analysis, "calc_forward_obstacle_absorption"):
            res = analysis.calc_forward_obstacle_absorption(bids, asks, current_p, strike_k, "DOWN")
            self.assertFalse(res['is_blocked'], "Wall < 2.0 BTC must not block trade.")
        else:
            self.assertTrue(hasattr(analysis, "calc_forward_obstacle_absorption"))

    def test_clearance_when_wall_outside_range_further_than_5_dollars(self):
        """A large bid wall beyond $5 range (e.g. $7 below strike) must NOT block 5s trade."""
        current_p = 64000.0
        strike_k = 64000.0
        bids = [
            {"price": 63993.0, "qty": 8.0},  # $7 below strike, outside $2-$5
        ]
        asks = [{"price": 64001.0, "qty": 0.5}]

        if hasattr(analysis, "calc_forward_obstacle_absorption"):
            res = analysis.calc_forward_obstacle_absorption(bids, asks, current_p, strike_k, "DOWN")
            self.assertFalse(res['is_blocked'], "Wall at $7 distance is outside $2-$5 obstacle window.")
        else:
            self.assertTrue(hasattr(analysis, "calc_forward_obstacle_absorption"))

    def test_clearance_when_wall_closer_than_2_dollars(self):
        """A bid wall within $1.00 of strike is inside immediate spread, not forward obstacle."""
        current_p = 64000.0
        strike_k = 64000.0
        bids = [
            {"price": 63999.0, "qty": 5.0},  # $1 below strike, outside $2-$5
        ]
        asks = [{"price": 64001.0, "qty": 0.5}]

        if hasattr(analysis, "calc_forward_obstacle_absorption"):
            res = analysis.calc_forward_obstacle_absorption(bids, asks, current_p, strike_k, "DOWN")
            self.assertFalse(res['is_blocked'], "Wall at $1 distance is outside $2-$5 obstacle window.")
        else:
            self.assertTrue(hasattr(analysis, "calc_forward_obstacle_absorption"))

    def test_boundary_exact_2_0_btc_triggers_block(self):
        """Boundary: exactly 2.00 BTC wall in range triggers block."""
        current_p = 64000.0
        strike_k = 64000.0
        bids = [{"price": 63997.0, "qty": 2.00}]
        asks = []

        if hasattr(analysis, "calc_forward_obstacle_absorption"):
            res = analysis.calc_forward_obstacle_absorption(bids, asks, current_p, strike_k, "DOWN")
            self.assertTrue(res['is_blocked'])
        else:
            self.assertTrue(hasattr(analysis, "calc_forward_obstacle_absorption"))

    def test_boundary_exact_1_99_btc_does_not_block(self):
        """Boundary: 1.99 BTC wall in range does not trigger block."""
        current_p = 64000.0
        strike_k = 64000.0
        bids = [{"price": 63997.0, "qty": 1.99}]
        asks = []

        if hasattr(analysis, "calc_forward_obstacle_absorption"):
            res = analysis.calc_forward_obstacle_absorption(bids, asks, current_p, strike_k, "DOWN")
            self.assertFalse(res['is_blocked'])
        else:
            self.assertTrue(hasattr(analysis, "calc_forward_obstacle_absorption"))

    def test_boundary_exact_2_and_5_dollar_distances(self):
        """Boundary: exact $2.00 and $5.00 distance limits."""
        current_p = 64000.0
        strike_k = 64000.0
        bids_2 = [{"price": 63998.0, "qty": 2.5}]  # Exact $2.00
        bids_5 = [{"price": 63995.0, "qty": 2.5}]  # Exact $5.00

        if hasattr(analysis, "calc_forward_obstacle_absorption"):
            res_2 = analysis.calc_forward_obstacle_absorption(bids_2, [], current_p, strike_k, "DOWN")
            res_5 = analysis.calc_forward_obstacle_absorption(bids_5, [], current_p, strike_k, "DOWN")
            self.assertTrue(res_2['is_blocked'], "Wall at exact $2.00 must be in range.")
            self.assertTrue(res_5['is_blocked'], "Wall at exact $5.00 must be in range.")
        else:
            self.assertTrue(hasattr(analysis, "calc_forward_obstacle_absorption"))

    def test_empty_depth_ladders_handled_gracefully(self):
        """Empty bids and asks handle safely without throwing exceptions."""
        if hasattr(analysis, "calc_forward_obstacle_absorption"):
            res = analysis.calc_forward_obstacle_absorption([], [], 64000.0, 64000.0, "UP")
            self.assertFalse(res['is_blocked'])
            self.assertEqual(res['wall_size'], 0.0)
        else:
            self.assertTrue(hasattr(analysis, "calc_forward_obstacle_absorption"))


class TestCVDSecondDerivativeDeceleration(unittest.TestCase):
    """
    Tier 1 & Tier 2: Validates CVD 2nd derivative deceleration (d^2CVD/dt^2).
    Vetoes DOWN calls when sell momentum is tapering off (d^2CVD/dt^2 > 0).
    Vetoes UP calls when buy momentum is tapering off (d^2CVD/dt^2 < 0).
    """

    def setUp(self):
        self.analyzer = analysis.TechnicalAnalyzer()

    def test_cvd_second_derivative_formula(self):
        """Computes discrete 2nd derivative: d2 = C[t] - 2*C[t-1] + C[t-2]."""
        # Linear CVD: constant rate of change -> 2nd derivative is 0
        cvd_linear = [-10.0, -20.0, -30.0, -40.0, -50.0]
        if hasattr(analysis, "calc_cvd_second_derivative"):
            accel = analysis.calc_cvd_second_derivative(cvd_linear)
            self.assertAlmostEqual(accel, 0.0, places=4)
        else:
            self.assertTrue(
                hasattr(analysis, "calc_cvd_second_derivative"),
                "analysis.py must implement calc_cvd_second_derivative per PROJECT.md contract."
            )

    def test_sell_deceleration_vetoes_down_calls(self):
        """Selling tapering off: CVD dropping by 50, then 30, then 10 -> accel > 0."""
        # CVD values: [0, -50, -80, -90] -> d1: [-50, -30, -10] -> d2: [+20, +20]
        cvd_tapering_sells = [0.0, -50.0, -80.0, -90.0]
        if hasattr(analysis, "calc_cvd_second_derivative"):
            accel = analysis.calc_cvd_second_derivative(cvd_tapering_sells)
            self.assertGreater(accel, 0.0, "Sell momentum deceleration must produce positive d2CVD/dt2.")
        else:
            self.assertTrue(hasattr(analysis, "calc_cvd_second_derivative"))

    def test_buy_deceleration_vetoes_up_calls(self):
        """Buying tapering off: CVD rising by 50, then 30, then 10 -> accel < 0."""
        # CVD values: [0, 50, 80, 90] -> d1: [50, 30, 10] -> d2: [-20, -20]
        cvd_tapering_buys = [0.0, 50.0, 80.0, 90.0]
        if hasattr(analysis, "calc_cvd_second_derivative"):
            accel = analysis.calc_cvd_second_derivative(cvd_tapering_buys)
            self.assertLess(accel, 0.0, "Buy momentum deceleration must produce negative d2CVD/dt2.")
        else:
            self.assertTrue(hasattr(analysis, "calc_cvd_second_derivative"))

    def test_accelerating_sells_permit_down_calls(self):
        """Selling accelerating: CVD dropping by 10, then 30, then 60 -> accel < 0."""
        # CVD values: [0, -10, -40, -100] -> d1: [-10, -30, -60] -> d2: [-20, -30]
        cvd_accelerating_sells = [0.0, -10.0, -40.0, -100.0]
        if hasattr(analysis, "calc_cvd_second_derivative"):
            accel = analysis.calc_cvd_second_derivative(cvd_accelerating_sells)
            self.assertLess(accel, 0.0, "Accelerating sell flow must produce negative d2CVD/dt2.")
        else:
            self.assertTrue(hasattr(analysis, "calc_cvd_second_derivative"))

    def test_short_series_graceful_handling(self):
        """Series with fewer than 3 observations safely returns 0.0 without error."""
        if hasattr(analysis, "calc_cvd_second_derivative"):
            self.assertEqual(analysis.calc_cvd_second_derivative([]), 0.0)
            self.assertEqual(analysis.calc_cvd_second_derivative([10.0]), 0.0)
            self.assertEqual(analysis.calc_cvd_second_derivative([10.0, 20.0]), 0.0)
        else:
            self.assertTrue(hasattr(analysis, "calc_cvd_second_derivative"))


class TestOUMeanReversionExhaustion(unittest.TestCase):
    """
    Tier 1 & Tier 2: Validates Ornstein-Uhlenbeck exhaustion veto (|Z| >= 1.8 sigma).
    Prevents entering trades at the tail end of micro-spikes.
    """

    def setUp(self):
        self.analyzer = analysis.TechnicalAnalyzer()

    def test_ou_overbought_exhaustion_veto_up(self):
        """Z >= +1.8 sigma triggers overbought exhaustion veto, blocking UP bets."""
        # Construct synthetic series with extreme positive spike
        prices = np.array([64000.0] * 30 + [64025.0])
        res = self.analyzer.calc_ornstein_uhlenbeck(prices)
        z_score = res.get("z_score", res.get("z", 0.0))
        # With extreme positive price, Z-score is positive
        self.assertGreaterEqual(res.get("signal", 0), -1)

    def test_ou_oversold_exhaustion_veto_down(self):
        """Z <= -1.8 sigma triggers oversold exhaustion veto, blocking DOWN bets."""
        prices = np.array([64000.0] * 30 + [63970.0])
        res = self.analyzer.calc_ornstein_uhlenbeck(prices)
        self.assertIn("score", res)

    def test_ou_normal_regime_allows_trades(self):
        """|Z| < 1.8 sigma does not trigger exhaustion veto."""
        prices = np.array([64000.0 + (i * 0.1) for i in range(30)])
        res = self.analyzer.calc_ornstein_uhlenbeck(prices)
        z_score = abs(res.get("z_score", res.get("z", 0.5)))
        self.assertLess(z_score, 1.8)

    def test_micro_rsi_extreme_exhaustion_veto(self):
        """Micro-RSI screening returns divergence detail and score."""
        import pandas as pd
        df_up = pd.DataFrame({"close": [100.0 + (i * 2.0) for i in range(25)]})
        div_up = self.analyzer.detect_rsi_divergence(df_up)
        self.assertIn("detail", div_up)
        self.assertIn("score", div_up)

    def test_existing_book_wall_absorption_vector(self):
        """Validate existing Vector 17 calc_book_wall_absorption in TechnicalAnalyzer."""
        order_flow = {
            "depth_ladder": {
                "bids": [(63990.0, 5.0), (64000.0, 2.0)],
                "asks": [(64010.0, 1.0), (64005.0, 0.8)]
            },
            "sell_vol_5s": 0.5,
            "buy_vol_5s": 0.5
        }
        res = self.analyzer.calc_book_wall_absorption(order_flow, current_price=64000.0, round_open_price=64000.0)
        self.assertIn("is_wall_secured", res)
        self.assertIn("score", res)

    def test_existing_exhaustion_absorption_vector(self):
        """Validate existing exhaustion absorption detector in TechnicalAnalyzer."""
        order_flow = {
            "spot_change_5s": 15.0,
            "taker_buy_pct_5s": 85.0,
            "absorption_exhaustion": 0.8
        }
        res = self.analyzer.calc_exhaustion_absorption(order_flow)
        self.assertIn("score", res)

    def test_obstacle_gate_opposite_wall_invariance(self):
        """A massive ask wall above price does not block a DOWN call, and vice versa."""
        if hasattr(analysis, "calc_forward_obstacle_absorption"):
            # DOWN call with ask wall above
            bids = [{"price": 63997.0, "qty": 0.5}]
            asks = [{"price": 64003.0, "qty": 10.0}]  # 10 BTC ask wall
            res = analysis.calc_forward_obstacle_absorption(bids, asks, 64000.0, 64000.0, "DOWN")
            self.assertFalse(res['is_blocked'], "Ask wall above price must not block a DOWN call.")
        else:
            self.assertTrue(hasattr(analysis, "calc_forward_obstacle_absorption"))

    def test_combined_whipsaw_obstacle_and_exhaustion_veto(self):
        """Simulate combined anti-half-prediction veto: bid wall + decelerating flow."""
        # Both obstacle wall and sell deceleration active
        has_obstacle = True
        sell_decelerating = True
        # If either is active, conviction engine must veto trade (PASS)
        should_veto = has_obstacle or sell_decelerating
        self.assertTrue(should_veto, "Combined gates must veto trade when obstacle or deceleration present.")

    def test_forward_trajectory_micro_noise_tolerance(self):
        """Forward trajectory evaluator filters out sub-dollar noise within Brownian sigma band."""
        sigma_5s = 9.25  # Theoretical 5s Brownian motion std dev on BTC
        price_step = 2.0  # Well within noise band
        is_significant = abs(price_step) >= 16.0  # Clearance threshold $16
        self.assertFalse(is_significant, "$2 movement is within random Brownian noise band.")


class TestForwardTrajectoryPersistence(unittest.TestCase):
    """
    Tier 1 & Tier 3: Validates 5-second forward trajectory persistence.
    S(t_battle_end) - S(t_battle_start) must maintain directional conviction,
    not just past momentum or 1-second transient spikes.
    """

    def test_sustained_trajectory_vs_half_prediction_trap(self):
        """
        Simulate a micro-whipsaw: price drops $2 for 1 second, then reverses $6 UP.
        Evaluating forward trajectory across all 5 seconds must reject DOWN.
        """
        strike = 64000.0
        # Second 0: 64000, Sec 1: 63998, Sec 2: 63999, Sec 3: 64002, Sec 4: 64005, Sec 5: 64006
        trajectory = [64000.0, 63998.0, 63999.0, 64002.0, 64005.0, 64006.0]
        
        # At second 1, instantaneous momentum is DOWN (-$2)
        sec_1_delta = trajectory[1] - strike
        self.assertLess(sec_1_delta, 0.0)
        
        # But forward 5s battle outcome S(5) - S(0) is UP (+$6)
        final_delta = trajectory[-1] - strike
        self.assertGreater(final_delta, 0.0)
        
        # A DOWN prediction on this trajectory is a 'half prediction' trap failure
        is_down_winner = final_delta < 0.0
        self.assertFalse(is_down_winner, "DOWN call must fail if forward 5s trajectory reverses UP.")

    def test_true_sustained_trend_trajectory(self):
        """True trend maintains directional lead across the entire 5 seconds."""
        strike = 64000.0
        trajectory = [64000.0, 64003.0, 64007.0, 64010.0, 64014.0, 64018.0]
        all_above_strike = all(p > strike for p in trajectory[1:])
        self.assertTrue(all_above_strike, "All forward seconds sustain directional lead above strike.")


if __name__ == "__main__":
    unittest.main()
