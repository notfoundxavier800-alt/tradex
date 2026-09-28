"""
Adversarial Stress Testing & Boundary Challenge Suite for RoundManager (Milestone 1).
Targets:
1. Edge values of seconds_left (0.0s, 0.001s, 4.499s, 4.5s, 5.0s, 14.999s, 15.0s, 19.999s, 20.0s, 25.0s, -1.0s).
2. Phase transitions and invariant enforcement: is_sniper_window must NEVER be True during BATTLE.
3. Strict bounds and monotonicity of phase_seconds_left.
4. Sniper re-arm boundary at T >= 4.5s vs lock at T < 4.5s.
5. Multi-round manual sync lifecycle and battle_strike state persistence.
6. High-concurrency rapid manual sync stress test.
"""

import unittest
from unittest.mock import patch
import time
import random
import threading
from round_manager import RoundManager


class TestRoundManagerSniperWindowInvariants(unittest.TestCase):
    """
    Challenge: Under NO circumstance may is_sniper_window become True when phase == 'BATTLE'.
    """

    def setUp(self):
        self.rm = RoundManager(round_duration=20, lead_time=5.0)

    def test_invariant_fuzz_10000_iterations(self):
        """Fuzz 10,000 arbitrary sync calls and ticks to verify is_sniper_window is never True in BATTLE."""
        phases = ["BETTING", "BATTLE", None, "UNKNOWN", ""]
        rnd = random.Random(42)

        for _ in range(10000):
            sec = rnd.uniform(-10.0, 35.0)
            ph = rnd.choice(phases)
            price = rnd.uniform(50000.0, 70000.0)
            self.rm.manual_sync(seconds_left=sec, phase=ph, current_price=price)
            state = self.rm.tick(current_price=price)

            if state["phase"] == "BATTLE":
                self.assertFalse(
                    state["is_sniper_window"],
                    f"INVARIANT VIOLATION: is_sniper_window is True in BATTLE! sec={sec}, phase={ph}, state={state}"
                )
                self.assertFalse(
                    state["should_fire_sniper"],
                    f"INVARIANT VIOLATION: should_fire_sniper is True in BATTLE! sec={sec}, phase={ph}, state={state}"
                )

    def test_get_round_state_invariant_across_all_positions(self):
        """Verify across every 0.1s step in the 20s round that BATTLE never has is_sniper_window == True."""
        base_epoch = 1_700_000_000.0
        self.rm.sync_offset = 0

        for step in range(200):
            t = base_epoch + (step * 0.1)
            state = self.rm.get_round_state_at(epoch_sec=t)
            if state["phase"] == "BATTLE":
                self.assertFalse(
                    state["is_sniper_window"],
                    f"Invariant violated at t={t} (pos={step*0.1:.1f}s): is_sniper_window is True in BATTLE."
                )


class TestRoundManagerPhaseSecondsLeftBoundsAndMonotonicity(unittest.TestCase):
    """
    Challenge: phase_seconds_left must be strictly bounded:
    - BETTING: in [0.0, 15.0]
    - BATTLE: in [0.0, 5.0]
    and strictly monotonically decreasing as time flows forward.
    """

    def setUp(self):
        self.rm = RoundManager(round_duration=20, lead_time=5.0)

    def test_bounds_across_continuous_cycle(self):
        base_epoch = 1_700_000_000.0
        self.rm.sync_offset = 0

        for step in range(400):  # 2 full 20s rounds in 0.1s increments
            t = base_epoch + (step * 0.1)
            state = self.rm.get_round_state_at(epoch_sec=t)
            sec_left = state["phase_seconds_left"]

            if state["phase"] == "BETTING":
                self.assertGreaterEqual(sec_left, 0.0)
                self.assertLessEqual(sec_left, 15.0)
            elif state["phase"] == "BATTLE":
                self.assertGreaterEqual(sec_left, 0.0)
                self.assertLessEqual(sec_left, 5.0)

    def test_monotonic_decrease_within_each_phase(self):
        base_epoch = 1_700_000_000.0
        self.rm.sync_offset = 0

        # Monotonicity in BETTING (0s to 14.9s)
        prev_left = 15.1
        for step in range(150):
            t = base_epoch + (step * 0.1)
            state = self.rm.get_round_state_at(epoch_sec=t)
            self.assertEqual(state["phase"], "BETTING")
            self.assertLess(state["phase_seconds_left"], prev_left)
            prev_left = state["phase_seconds_left"]

        # Monotonicity in BATTLE (15s to 19.9s)
        prev_left = 5.1
        for step in range(150, 200):
            t = base_epoch + (step * 0.1)
            state = self.rm.get_round_state_at(epoch_sec=t)
            self.assertEqual(state["phase"], "BATTLE")
            self.assertLess(state["phase_seconds_left"], prev_left)
            prev_left = state["phase_seconds_left"]


class TestRoundManagerSniperRearmStress(unittest.TestCase):
    """
    Challenge: Sniper re-arming boundary at T >= 4.5s vs lock at T < 4.5s.
    """

    def setUp(self):
        self.rm = RoundManager(round_duration=20, lead_time=5.0)

    def test_sniper_rearm_exact_4_5s_boundary_sweep(self):
        """Test fine-grained boundary values around 4.5s in betting window."""
        cases = [
            (15.000, True),
            (10.000, True),
            (5.000, True),
            (4.501, True),
            (4.500, True),
            (4.499, False),
            (4.490, False),
            (4.000, False),
            (3.000, False),
            (1.000, False),
            (0.500, False),
            (0.001, False),
            (0.000, False),
        ]

        for sec, expected_rearm in cases:
            # Mark sniper fired
            cur_round = self.rm.last_round_id
            self.rm.mark_sniper_fired(cur_round, direction="UP", strength="HIGH")
            self.assertEqual(self.rm.sniper_fired_for_round, cur_round)

            # Manual sync
            self.rm.manual_sync(seconds_left=sec, phase="BETTING")
            rearmed = (self.rm.sniper_fired_for_round == -1)
            self.assertEqual(
                rearmed,
                expected_rearm,
                f"Failed at seconds_left={sec}: expected rearm={expected_rearm}, got {rearmed}"
            )

    def test_sniper_rearm_with_sync_offset(self):
        """Universal re-arm: manual_sync with sync_offset must also obey T >= 4.5s rule."""
        epoch = time.time()
        cur_pos = epoch % 20

        # Offset leaving 10.0s in betting (eff_pos = 5.0) -> >= 4.5s -> should re-arm
        offset_rearm = (5.0 - cur_pos) % 20
        self.rm.mark_sniper_fired(self.rm.last_round_id, direction="UP")
        self.rm.manual_sync(sync_offset=offset_rearm)
        self.assertEqual(self.rm.sniper_fired_for_round, -1, "Should re-arm when sync_offset leaves 10s in betting.")

        # Offset leaving 3.0s in betting (eff_pos = 12.0) -> < 4.5s -> must NOT re-arm
        offset_lock = (12.0 - cur_pos) % 20
        self.rm.mark_sniper_fired(self.rm.last_round_id, direction="UP")
        self.rm.manual_sync(sync_offset=offset_lock)
        self.assertNotEqual(self.rm.sniper_fired_for_round, -1, "Must NOT re-arm when sync_offset leaves 3s in betting.")

        # Offset placing into battle (eff_pos = 17.0) -> must NOT re-arm
        offset_battle = (17.0 - cur_pos) % 20
        self.rm.mark_sniper_fired(self.rm.last_round_id, direction="UP")
        self.rm.manual_sync(sync_offset=offset_battle)
        self.assertNotEqual(self.rm.sniper_fired_for_round, -1, "Must NOT re-arm when sync_offset places in battle.")


class TestRoundManagerEdgeValues(unittest.TestCase):
    """
    Challenge: Test specific boundary values: 0.0s, 0.001s, 5.0s, 5.001s, 14.999s, 15.0s, 19.999s, 20.0s, 25.0s.
    """

    def setUp(self):
        self.rm = RoundManager(round_duration=20, lead_time=5.0)

    def test_betting_boundary_0s(self):
        """Syncing seconds_left=0.0 with phase='BETTING' marks transition to BATTLE."""
        self.rm.manual_sync(seconds_left=0.0, phase="BETTING")
        state = self.rm.tick(100.0)
        self.assertEqual(state["phase"], "BATTLE")
        self.assertAlmostEqual(state["phase_seconds_left"], 5.0, places=2)
        self.assertFalse(state["is_sniper_window"])

    def test_betting_boundary_0_001s(self):
        """Syncing seconds_left=0.001 with phase='BETTING' is just before betting close."""
        self.rm.manual_sync(seconds_left=0.001, phase="BETTING")
        state = self.rm.tick(100.0)
        self.assertEqual(state["phase"], "BETTING")
        self.assertAlmostEqual(state["phase_seconds_left"], 0.001, places=3)
        self.assertTrue(state["is_sniper_window"])

    def test_betting_boundary_5s_sniper(self):
        """Syncing seconds_left=5.0 with phase='BETTING' is exact sniper window trigger."""
        self.rm.manual_sync(seconds_left=5.0, phase="BETTING")
        state = self.rm.tick(100.0)
        self.assertEqual(state["phase"], "BETTING")
        self.assertAlmostEqual(state["phase_seconds_left"], 5.0, places=2)
        self.assertTrue(state["is_sniper_window"])
        self.assertTrue(state["should_fire_sniper"])

    def test_betting_boundary_5_001s(self):
        """Syncing seconds_left=5.001 with phase='BETTING' is just before sniper window."""
        self.rm.manual_sync(seconds_left=5.001, phase="BETTING")
        state = self.rm.tick(100.0)
        self.assertEqual(state["phase"], "BETTING")
        self.assertAlmostEqual(state["phase_seconds_left"], 5.001, places=3)
        self.assertFalse(state["is_sniper_window"])

    def test_betting_boundary_14_999s(self):
        """Syncing seconds_left=14.999 with phase='BETTING' is near start of betting."""
        self.rm.manual_sync(seconds_left=14.999, phase="BETTING")
        state = self.rm.tick(100.0)
        self.assertEqual(state["phase"], "BETTING")
        self.assertAlmostEqual(state["phase_seconds_left"], 14.999, places=3)
        self.assertFalse(state["is_sniper_window"])

    def test_betting_boundary_15s(self):
        """Syncing seconds_left=15.0 with phase='BETTING' is exact start of betting."""
        self.rm.manual_sync(seconds_left=15.0, phase="BETTING")
        state = self.rm.tick(100.0)
        self.assertEqual(state["phase"], "BETTING")
        self.assertAlmostEqual(state["phase_seconds_left"], 15.0, places=2)
        self.assertFalse(state["is_sniper_window"])

    def test_battle_boundary_0s(self):
        """Syncing seconds_left=0.0 with phase='BATTLE' means battle finished -> wraps to new round betting."""
        self.rm.manual_sync(seconds_left=0.0, phase="BATTLE")
        state = self.rm.tick(100.0)
        self.assertEqual(state["phase"], "BETTING")
        self.assertAlmostEqual(state["phase_seconds_left"], 15.0, places=2)
        self.assertFalse(state["is_sniper_window"])

    def test_battle_boundary_0_001s(self):
        """Syncing seconds_left=0.001 with phase='BATTLE' is last moment of battle."""
        self.rm.manual_sync(seconds_left=0.001, phase="BATTLE")
        state = self.rm.tick(100.0)
        self.assertEqual(state["phase"], "BATTLE")
        self.assertAlmostEqual(state["phase_seconds_left"], 0.001, places=3)
        self.assertFalse(state["is_sniper_window"])

    def test_battle_boundary_5s(self):
        """Syncing seconds_left=5.0 with phase='BATTLE' is start of battle."""
        self.rm.manual_sync(seconds_left=5.0, phase="BATTLE")
        state = self.rm.tick(100.0)
        self.assertEqual(state["phase"], "BATTLE")
        self.assertAlmostEqual(state["phase_seconds_left"], 5.0, places=2)
        self.assertFalse(state["is_sniper_window"])

    def test_oversized_seconds_left_in_betting_causes_phase_inversion(self):
        """
        DEFECT CHECK: If caller passes seconds_left=20.0 with phase='BETTING',
        (15 - 20) % 20 = 15.0, which erroneously inverts phase to BATTLE.
        """
        self.rm.manual_sync(seconds_left=20.0, phase="BETTING")
        state = self.rm.tick(100.0)
        self.assertEqual(
            state["phase"],
            "BETTING",
            f"PHASE INVERSION: Syncing seconds_left=20.0 with phase='BETTING' mapped to {state['phase']}!"
        )

    def test_oversized_25s_in_betting_accidentally_triggers_sniper(self):
        """
        DEFECT CHECK: If caller passes seconds_left=25.0 with phase='BETTING',
        (15 - 25) % 20 = 10.0, which is T-5s mark in betting and opens sniper window.
        """
        self.rm.manual_sync(seconds_left=25.0, phase="BETTING")
        state = self.rm.tick(100.0)
        self.assertFalse(
            state["is_sniper_window"],
            f"ERRONEOUS SNIPER TRIGGER: Syncing seconds_left=25.0 opened sniper window (phase_sec={state['phase_seconds_left']})!"
        )



class TestRoundManagerBattleStrikePersistenceBug(unittest.TestCase):
    """
    CRITICAL DEFECT TEST:
    Verify whether battle_strike set during Round N battle leaks into Round N+1 betting,
    poisoning strike_price and preventing the new battle strike from ever snapping.
    """

    def setUp(self):
        self.rm = RoundManager(round_duration=20, lead_time=5.0)

    def test_battle_strike_must_be_none_in_betting(self):
        """
        Invariant: During BETTING phase, self.battle_strike MUST be None.
        If battle_strike is not None during betting, it shadows round_open_price.
        """
        # Step 1: Round 1 enters battle at strike 64,050.0
        self.rm.manual_sync(seconds_left=5.0, current_price=64050.0, phase="BATTLE")
        s1 = self.rm.tick(64050.0)
        self.assertEqual(s1["phase"], "BATTLE")
        self.assertEqual(self.rm.battle_strike, 64050.0)

        # Step 2: Cwallet begins Round 2 betting (15s remaining, new open price 64,100.0)
        self.rm.manual_sync(seconds_left=15.0, open_price=64100.0, current_price=64100.0, phase="BETTING")
        s2 = self.rm.tick(64100.0)
        self.assertEqual(s2["phase"], "BETTING")

        # ASSERTION: battle_strike MUST be None during betting of Round 2!
        # If it is not None, Round 1's battle strike leaked into Round 2!
        self.assertIsNone(
            self.rm.battle_strike,
            f"LEAK DETECTED: rm.battle_strike is {self.rm.battle_strike} during BETTING! Should be None."
        )

        # ASSERTION: strike_price in BETTING must be round_open_price (64,100.0), NOT 64,050.0!
        self.assertEqual(
            s2["strike_price"],
            64100.0,
            f"POISONED STRIKE: strike_price reported as {s2['strike_price']}, expected 64100.0 (open price)."
        )

    def test_settlement_dropped_on_manual_sync_across_rounds(self):
        """
        DEFECT CHECK: If manual_sync is called when transitioning into a new round,
        prematurely updating last_round_id causes tick() to drop prior round settlement.
        """
        # Round 1 battle
        self.rm.manual_sync(seconds_left=5.0, current_price=64000.0, phase="BATTLE")
        self.rm.tick(64000.0)

        # Syncing to Round 2 betting at 64,050.0
        self.rm.manual_sync(seconds_left=15.0, open_price=64050.0, current_price=64050.0, phase="BETTING")
        s2 = self.rm.tick(64050.0)

        # Prior round settlement MUST fire upon round transition!
        self.assertTrue(
            s2["just_settled"],
            "DROPPED SETTLEMENT: just_settled is False; Round 1 outcome was never evaluated!"
        )
        self.assertIsNotNone(
            s2["settled_outcome"],
            "DROPPED SETTLEMENT: settled_outcome is None; Round 1 outcome was lost!"
        )



class TestRoundManagerConcurrency(unittest.TestCase):
    """
    Challenge: Multi-threaded hammer testing to verify absence of race conditions or deadlocks.
    """

    def setUp(self):
        self.rm = RoundManager(round_duration=20, lead_time=5.0)

    def test_concurrent_manual_sync_and_tick_hammer(self):
        errors = []
        stop_flag = threading.Event()

        def sync_worker():
            phases = ["BETTING", "BATTLE", None]
            rnd = random.Random(123)
            while not stop_flag.is_set():
                try:
                    sec = rnd.uniform(0.0, 20.0)
                    ph = rnd.choice(phases)
                    p = rnd.uniform(60000.0, 65000.0)
                    self.rm.manual_sync(seconds_left=sec, phase=ph, current_price=p)
                except Exception as e:
                    errors.append(e)
                    break

        def tick_worker():
            rnd = random.Random(456)
            while not stop_flag.is_set():
                try:
                    p = rnd.uniform(60000.0, 65000.0)
                    state = self.rm.tick(current_price=p)
                    # Verify invariant in concurrent stream
                    if state["phase"] == "BATTLE" and state["is_sniper_window"]:
                        errors.append(ValueError("is_sniper_window was True during BATTLE!"))
                        break
                except Exception as e:
                    errors.append(e)
                    break

        threads = [
            threading.Thread(target=sync_worker) for _ in range(5)
        ] + [
            threading.Thread(target=tick_worker) for _ in range(5)
        ]

        for t in threads:
            t.start()

        time.sleep(1.0)  # Hammer for 1 full second
        stop_flag.set()

        for t in threads:
            t.join(timeout=2.0)

        self.assertEqual(len(errors), 0, f"Concurrent execution errors: {errors}")


if __name__ == "__main__":
    unittest.main()
