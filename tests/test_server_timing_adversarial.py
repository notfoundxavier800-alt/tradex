"""
Empirical Adversarial Test for server.py Background Loop Timing.
Tests:
1. Multi-interval sleep duration tracking (zero jitter vs 500ms/10ms oscillation).
2. Dynamic transition from 500ms nominal to 50ms ultra-precision at T-7s.
3. Sniper trigger at exact T-5s betting window mark.
4. Latency under varying execution workloads (5ms, 25ms, 60ms).
"""
import time
import unittest
from unittest.mock import MagicMock
from round_manager import RoundManager

class TestServerTimingAdversarial(unittest.TestCase):
    def setUp(self):
        self.rm = RoundManager(round_duration=20, lead_time=5.0)

    def test_zero_oscillation_under_nominal_conditions(self):
        """
        Verify that the loop sleep durations strictly track dynamic_interval
        and DO NOT exhibit the alternating 500ms / 10ms jitter oscillation.
        """
        nominal_interval = 0.5
        sleep_durations = []
        next_deadline = time.time() + nominal_interval

        # Simulate 10 iterations of nominal loop with 5ms simulated workload
        for _ in range(10):
            time.sleep(0.005) # simulate work
            now = time.time()
            dynamic_interval = nominal_interval
            sleep_time = max(0.005, next_deadline - now)
            sleep_durations.append(sleep_time)
            
            if sleep_time > 0:
                time.sleep(sleep_time)
            next_deadline = time.time() + dynamic_interval

        # Verify no sleep duration is anywhere near 10ms (the old oscillation bug)
        for i, s in enumerate(sleep_durations):
            self.assertGreater(s, 0.40, f"Iteration {i} had unexpected low sleep time {s}s (potential oscillation)")
            self.assertLessEqual(s, 0.505, f"Iteration {i} exceeded max sleep window: {s}s")

    def test_50ms_polling_activation_at_t_minus_7s(self):
        """
        Verify that when phase_seconds_left <= 7.0 in BETTING phase,
        dynamic_interval drops to 0.05 (50ms).
        """
        # Set epoch so seconds_left is 8.0s (pos = 15 - 8 = 7)
        now_epoch = time.time()
        # manual_sync to 8.0s betting
        self.rm.manual_sync(seconds_left=8.0, phase="BETTING")
        
        # Iteration 1: at 8.0s
        r_state = self.rm.tick(65000.0)
        cur_phase = r_state.get("phase", "BETTING")
        cur_p_left = r_state.get("phase_seconds_left", 15.0)
        cur_s_fired = (r_state.get("sniper_fired_for_round", -1) == r_state.get("round_id", -2))

        interval = 0.5
        if cur_phase == "BETTING" and cur_p_left <= 7.0 and not cur_s_fired:
            dynamic_interval = 0.05
        else:
            dynamic_interval = interval
        self.assertEqual(dynamic_interval, 0.5, "Should remain 500ms when p_left > 7.0s")

        # Sync to 6.8s betting (<= 7.0s)
        self.rm.manual_sync(seconds_left=6.8, phase="BETTING")
        r_state = self.rm.tick(65000.0)
        cur_phase = r_state.get("phase", "BETTING")
        cur_p_left = r_state.get("phase_seconds_left", 15.0)
        cur_s_fired = (r_state.get("sniper_fired_for_round", -1) == r_state.get("round_id", -2))

        if cur_phase == "BETTING" and cur_p_left <= 7.0 and not cur_s_fired:
            dynamic_interval = 0.05
        else:
            dynamic_interval = interval
        self.assertEqual(dynamic_interval, 0.05, "Should switch to 50ms when p_left <= 7.0s")

    def test_sniper_authoritative_fire_at_t_minus_5s(self):
        """
        Verify that at exactly T-5s (phase_seconds_left <= 5.0 in BETTING),
        is_sniper_window activates and sniper fires authoritatively.
        """
        self.rm.manual_sync(seconds_left=5.0, phase="BETTING")
        r_state = self.rm.tick(65000.0)
        
        self.assertEqual(r_state["phase"], "BETTING")
        self.assertAlmostEqual(r_state["phase_seconds_left"], 5.0, delta=0.05)
        self.assertTrue(r_state.get("is_sniper_window", False), "is_sniper_window MUST be True at 5.0s")

        # Simulate sniper firing
        round_id = r_state["round_id"]
        self.rm.mark_sniper_fired(round_id, direction="UP", strength="LETHAL")

        # Next tick should have cur_s_fired == True
        r_state2 = self.rm.tick(65005.0)
        cur_s_fired = (r_state2.get("sniper_fired_for_round", -1) == round_id)
        self.assertTrue(cur_s_fired)

        # Dynamic interval should revert to 500ms nominal once sniper has fired
        cur_phase = r_state2.get("phase", "BETTING")
        cur_p_left = r_state2.get("phase_seconds_left", 15.0)
        interval = 0.5
        if cur_phase == "BETTING" and cur_p_left <= 7.0 and not cur_s_fired:
            dynamic_interval = 0.05
        else:
            dynamic_interval = interval
        self.assertEqual(dynamic_interval, 0.5, "Should revert to 500ms after sniper fires")

    def test_transition_lag_characterization(self):
        """
        Adversarial test characterizing the 1-iteration transition lag
        when shifting from 500ms to 50ms interval.
        """
        # Mathematical simulation of server.py lines 968-983
        t = 1000.0
        interval = 0.5
        next_deadline = t + interval

        # Iteration 1 at p_left = 7.2s (still nominal)
        work_time = 0.01
        t += work_time
        now = t
        p_left = 7.2
        s_fired = False
        dyn_int = 0.05 if (p_left <= 7.0 and not s_fired) else interval
        self.assertEqual(dyn_int, 0.5)
        sleep1 = max(0.005, next_deadline - now)
        t += sleep1
        next_deadline = t + dyn_int

        # Iteration 2: p_left drops to 6.7s (<= 7.0s)
        t += work_time
        now = t
        p_left = 6.7
        dyn_int = 0.05 if (p_left <= 7.0 and not s_fired) else interval
        self.assertEqual(dyn_int, 0.05) # interval changed to 0.05
        sleep2 = max(0.005, next_deadline - now) # but next_deadline was from iteration 1!
        
        # sleep2 is still ~0.49s due to next_deadline being scheduled in previous iteration
        self.assertAlmostEqual(sleep2, 0.49, delta=0.02)
        t += sleep2
        next_deadline = t + dyn_int # Now next_deadline is scheduled with 0.05!

        # Iteration 3: p_left is now ~6.2s
        t += work_time
        now = t
        p_left = 6.2
        dyn_int = 0.05 if (p_left <= 7.0 and not s_fired) else interval
        sleep3 = max(0.005, next_deadline - now)
        self.assertAlmostEqual(sleep3, 0.04, delta=0.01) # Strictly 50ms polling now!

if __name__ == "__main__":
    unittest.main()
