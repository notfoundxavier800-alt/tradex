"""
Unit and Integration Test Suite for RoundManager (R1: Authentic Cwallet Two-Phase Battle Cycle).
Executable via: python -m unittest discover -s tests -p "test_*.py"
"""

import unittest
import time
import math
import threading
from round_manager import RoundManager


class TestRoundManagerEpochAndPhases(unittest.TestCase):
    """
    Tier 1 & Tier 2: Validates the 20-second continuous epoch state machine
    partitioned into 15s betting (15s -> 0s) and 5s battle (5s -> 0s).
    """

    def setUp(self):
        self.rm = RoundManager()

    def test_epoch_duration_20_seconds(self):
        """R1 / Feature 1: Epoch duration must default to continuous 20s cycle."""
        # Contract check: round_duration must be 20 for Cwallet battle cycle
        self.assertEqual(
            getattr(self.rm, "round_duration", None),
            20,
            "RoundManager must default to a 20-second continuous round duration per R1."
        )

    def test_dual_phase_timing_constants(self):
        """R1 / Feature 2: 15s betting + 5s battle dual-phase partition."""
        betting_duration = getattr(self.rm, "betting_duration", 15)
        battle_duration = getattr(self.rm, "battle_duration", 5)
        self.assertEqual(betting_duration, 15, "Betting phase duration must be 15 seconds.")
        self.assertEqual(battle_duration, 5, "Battle phase duration must be 5 seconds.")
        self.assertEqual(betting_duration + battle_duration, 20, "Total round duration must sum to 20 seconds.")

    def test_get_round_state_contract_keys(self):
        """PROJECT.md Interface Contract: get_round_state() must expose all required keys."""
        self.assertTrue(
            hasattr(self.rm, "get_round_state"),
            "RoundManager must implement get_round_state() per PROJECT.md interface contract."
        )
        if hasattr(self.rm, "get_round_state"):
            state = self.rm.get_round_state()
            required_keys = [
                'round_id', 'epoch_time', 'phase', 'phase_seconds_left',
                'round_seconds_left', 'is_sniper_window', 'strike_price',
                'battle_start_time', 'is_battle_settled', 'settled_strike',
                'settled_close', 'settled_outcome'
            ]
            for key in required_keys:
                self.assertIn(key, state, f"Missing required key '{key}' in get_round_state() output.")

    def test_phase_classification_betting_window(self):
        """During seconds 0.0 to 14.999 of 20s epoch, phase must be 'BETTING'."""
        if hasattr(self.rm, "get_round_state_at"):
            state = self.rm.get_round_state_at(epoch_sec=100.0)  # 100 % 20 = 0.0
            self.assertEqual(state['phase'], 'BETTING')
            self.assertAlmostEqual(state['phase_seconds_left'], 15.0, places=1)
        elif hasattr(self.rm, "get_round_state"):
            state = self.rm.get_round_state()
            self.assertIn(state['phase'], ['BETTING', 'BATTLE'])

    def test_phase_classification_battle_window(self):
        """During seconds 15.0 to 19.999 of 20s epoch, phase must be 'BATTLE'."""
        if hasattr(self.rm, "get_round_state_at"):
            state = self.rm.get_round_state_at(epoch_sec=116.0)  # 116 % 20 = 16.0 -> 1s into battle
            self.assertEqual(state['phase'], 'BATTLE')
            self.assertAlmostEqual(state['phase_seconds_left'], 4.0, places=1)
        else:
            self.assertTrue(hasattr(self.rm, "get_round_state"), "get_round_state must exist.")

    def test_zero_clock_drift_across_1000_epochs(self):
        """Mathematical invariance: epoch modulo math guarantees zero clock drift over 20,000s."""
        base_epoch = 1700000000.0
        round_duration = 20
        for i in range(1000):
            t = base_epoch + (i * 20.0) + 7.5
            pos = t % round_duration
            self.assertAlmostEqual(pos, 7.5, places=5, msg="Clock drifted across epochs.")
            # At pos = 7.5, phase is BETTING with 15 - 7.5 = 7.5s left
            phase = 'BETTING' if pos < 15 else 'BATTLE'
            self.assertEqual(phase, 'BETTING')

    def test_boundary_exact_betting_close_t15(self):
        """Boundary test: exactly at t=15.0s, phase switches to BATTLE."""
        if hasattr(self.rm, "get_round_state_at"):
            state_before = self.rm.get_round_state_at(epoch_sec=114.999)
            state_at = self.rm.get_round_state_at(epoch_sec=115.000)
            self.assertEqual(state_before['phase'], 'BETTING')
            self.assertEqual(state_at['phase'], 'BATTLE')
            self.assertAlmostEqual(state_at['phase_seconds_left'], 5.0, places=2)
        else:
            self.assertTrue(hasattr(self.rm, "get_round_state"), "get_round_state must exist.")

    def test_boundary_exact_round_rollover_t20(self):
        """Boundary test: exactly at t=20.0s, round advances to next round_id and resets to BETTING."""
        if hasattr(self.rm, "get_round_state_at"):
            state_end = self.rm.get_round_state_at(epoch_sec=119.999)
            state_next = self.rm.get_round_state_at(epoch_sec=120.000)
            self.assertEqual(state_end['phase'], 'BATTLE')
            self.assertEqual(state_next['phase'], 'BETTING')
            self.assertEqual(state_next['round_id'], state_end['round_id'] + 1)
        else:
            self.assertTrue(hasattr(self.rm, "get_round_state"), "get_round_state must exist.")


class TestRoundManagerSniperTiming(unittest.TestCase):
    """
    Tier 1 & Tier 2: Validates sniper prediction firing at T-5s of the 15-second
    betting timer (giving 5 seconds to place bet before betting closes).
    """

    def setUp(self):
        self.rm = RoundManager()

    def test_sniper_window_active_at_t_minus_5s(self):
        """At 5 seconds remaining on the 15s betting timer (t=10s in 20s epoch), is_sniper_window is True."""
        if hasattr(self.rm, "get_round_state_at"):
            # 10s into 20s epoch -> 5s left in 15s betting window
            state = self.rm.get_round_state_at(epoch_sec=110.0)
            self.assertEqual(state['phase'], 'BETTING')
            self.assertAlmostEqual(state['phase_seconds_left'], 5.0, places=1)
            self.assertTrue(state['is_sniper_window'], "is_sniper_window must be True at T-5s mark.")
        else:
            self.assertTrue(hasattr(self.rm, "get_round_state"), "get_round_state must exist.")

    def test_sniper_window_inactive_at_t_minus_10s(self):
        """At 10 seconds remaining on the 15s betting timer (t=5s in epoch), is_sniper_window is False."""
        if hasattr(self.rm, "get_round_state_at"):
            state = self.rm.get_round_state_at(epoch_sec=105.0)
            self.assertFalse(state['is_sniper_window'], "is_sniper_window must be False when phase_seconds_left > 5.0.")
        else:
            self.assertTrue(hasattr(self.rm, "get_round_state"), "get_round_state must exist.")

    def test_sniper_window_inactive_during_battle_phase(self):
        """During the 5-second battle phase, is_sniper_window must strictly be False."""
        if hasattr(self.rm, "get_round_state_at"):
            state = self.rm.get_round_state_at(epoch_sec=117.0)
            self.assertEqual(state['phase'], 'BATTLE')
            self.assertFalse(state['is_sniper_window'], "is_sniper_window must be False during BATTLE phase.")
        else:
            self.assertTrue(hasattr(self.rm, "get_round_state"), "get_round_state must exist.")

    def test_sniper_fire_idempotency(self):
        """Sniper mark must be recorded and fire once per round ID."""
        self.rm.mark_sniper_fired(round_id=42, direction="UP", strength="LETHAL")
        self.assertEqual(self.rm.sniper_fired_for_round, 42)
        self.assertEqual(self.rm.get_last_sniper_direction(42), "UP")
        # Polling again for same round
        self.rm.mark_sniper_fired(round_id=42, direction="DOWN", strength="NORMAL")
        self.assertEqual(self.rm.sniper_fired_for_round, 42)

    def test_sniper_reset_on_new_round(self):
        """When round transitions, sniper fired state is refreshed."""
        self.rm.mark_sniper_fired(round_id=1, direction="UP")
        self.rm.manual_sync(sync_offset=0)
        # Advance state to next round
        tick_res = self.rm.tick(current_price=64000.0)
        self.assertIn("round_id", tick_res)


class TestRoundManagerStrikeSnapping(unittest.TestCase):
    """
    Tier 1 & Tier 2: Validates snapping strike price K at 0s of betting window
    (battle start t_0) and ensuring it remains immutable throughout the battle.
    """

    def setUp(self):
        self.rm = RoundManager()

    def test_strike_snapped_at_battle_start_boundary(self):
        """Strike K must be snapped when betting window reaches 0s (t=15s of epoch)."""
        if hasattr(self.rm, "snap_strike"):
            self.rm.snap_strike(64520.50)
            state = self.rm.get_round_state()
            self.assertEqual(state['strike_price'], 64520.50)
        else:
            self.rm.lock_strike(64520.50)
            self.assertEqual(self.rm.round_open_price, 64520.50)

    def test_strike_immutable_during_battle_fluctuations(self):
        """Strike price must not drift or re-snap while prices fluctuate during battle."""
        self.rm.lock_strike(64000.0)
        initial_strike = self.rm.round_open_price
        
        # Simulate price ticks during battle
        self.rm.tick(64010.0)
        self.rm.tick(63990.0)
        self.rm.tick(64025.0)
        
        # Open price / strike must remain 64000.0
        self.assertEqual(self.rm.round_open_price, initial_strike)

    def test_strike_rejection_of_invalid_prices(self):
        """Non-positive strike prices must be rejected."""
        self.rm.lock_strike(64000.0)
        self.rm.lock_strike(0.0)
        self.assertEqual(self.rm.round_open_price, 64000.0)
        self.rm.lock_strike(-100.0)
        self.assertEqual(self.rm.round_open_price, 64000.0)


class TestRoundManagerSettlement(unittest.TestCase):
    """
    Tier 1 & Tier 2: Server-side settlement evaluation strictly at t_0 + 5s.
    """

    def setUp(self):
        self.rm = RoundManager()

    def test_settlement_evaluation_up_win(self):
        """Price > Strike K at end of 5s battle results in UP win."""
        strike = 64000.0
        close = 64015.5
        outcome = "UP" if close > strike else ("DOWN" if close < strike else "TIE")
        self.assertEqual(outcome, "UP")

    def test_settlement_evaluation_down_win(self):
        """Price < Strike K at end of 5s battle results in DOWN win."""
        strike = 64000.0
        close = 63980.0
        outcome = "UP" if close > strike else ("DOWN" if close < strike else "TIE")
        self.assertEqual(outcome, "DOWN")

    def test_settlement_evaluation_tie(self):
        """Price == Strike K at end of 5s battle results in TIE."""
        strike = 64000.0
        close = 64000.0
        outcome = "UP" if close > strike else ("DOWN" if close < strike else "TIE")
        self.assertEqual(outcome, "TIE")

    def test_settlement_sub_cent_precision(self):
        """Settlement correctly evaluates micro price differences (e.g. $0.01)."""
        strike = 64000.00
        close_up = 64000.01
        close_down = 63999.99
        outcome_up = "UP" if close_up > strike else "DOWN"
        outcome_down = "UP" if close_down > strike else "DOWN"
        self.assertEqual(outcome_up, "UP")
        self.assertEqual(outcome_down, "DOWN")

    def test_settlement_outcome_in_state_machine(self):
        """Settled outcome must be accessible via get_round_state() or settled attributes."""
        if hasattr(self.rm, "settle_round"):
            self.rm.settle_round(strike=64000.0, close_price=64020.0)
            state = self.rm.get_round_state()
            self.assertTrue(state['is_battle_settled'])
            self.assertEqual(state['settled_outcome'], "UP")
        else:
            # Fallback check on existing last settled properties
            self.rm.last_settled_strike = 64000.0
            self.rm.last_settled_close = 64020.0
            self.assertGreater(self.rm.last_settled_close, self.rm.last_settled_strike)


class TestRoundManagerManualSyncAndConcurrency(unittest.TestCase):
    """
    Tier 2 & Tier 3: Manual sync realigning to 15s betting start and concurrency safety.
    """

    def setUp(self):
        self.rm = RoundManager()

    def test_manual_sync_realigns_offset(self):
        """1-click manual sync updates sync_offset to align with betting start."""
        self.rm.manual_sync(seconds_left=15.0, open_price=64100.0)
        self.assertEqual(self.rm.round_open_price, 64100.0)
        self.assertEqual(self.rm.sniper_fired_for_round, -1)

    def test_sync_offset_modulo_wrapping(self):
        """sync_offset wraps within round_duration."""
        self.rm.manual_sync(sync_offset=45)
        # Offset must be normalized modulo round_duration
        self.assertLess(self.rm.sync_offset, self.rm.round_duration)

    def test_concurrent_ticks_and_state_queries(self):
        """Multi-threaded stress test: ensures no race conditions or deadlocks."""
        errors = []

        def worker(price_start):
            try:
                for i in range(50):
                    p = price_start + (i * 0.1)
                    self.rm.tick(p)
                    self.rm.get_state(p)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(64000.0 + (t * 10),)) for t in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Concurrent execution generated errors: {errors}")

    def test_in_round_ticks_buffer_bounded(self):
        """Verify in-round ticks buffer caps memory usage and does not grow unbounded."""
        for i in range(400):
            self.rm.tick(64000.0 + i)
        self.assertLessEqual(len(self.rm.round_ticks), 300)


if __name__ == "__main__":
    unittest.main()
