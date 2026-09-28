"""
Adversarial test for server.py background loop timing.
Simulates the exact loop logic from server.py lines 968-983.
"""
import time
import unittest

def simulate_server_loop(ticks_data, base_interval=0.5):
    """
    Simulates the server.py timing logic over a sequence of states.
    ticks_data is a list of (cur_phase, cur_p_left, cur_s_fired, work_duration)
    Returns list of (sleep_time, dynamic_interval, next_deadline_offset)
    """
    sim_time = 0.0
    interval = base_interval
    next_deadline = sim_time + interval
    records = []

    for idx, (cur_phase, cur_p_left, cur_s_fired, work_dt) in enumerate(ticks_data):
        sim_time += work_dt
        now = sim_time

        if cur_phase == "BETTING" and cur_p_left <= 7.0 and not cur_s_fired:
            dynamic_interval = 0.05
            next_deadline = min(next_deadline, now + dynamic_interval)
        else:
            dynamic_interval = interval

        sleep_time = max(0.005, next_deadline - now)
        records.append({
            "step": idx,
            "phase": cur_phase,
            "phase_seconds_left": cur_p_left,
            "dynamic_interval": dynamic_interval,
            "sleep_time": round(sleep_time, 4),
            "sim_time_before_sleep": round(sim_time, 4)
        })

        if sleep_time > 0:
            sim_time += sleep_time
        next_deadline = sim_time + dynamic_interval

    return records

class TestServerLoopTiming(unittest.TestCase):
    def test_transition_to_50ms(self):
        # Suppose cur_p_left counts down from 8.0s
        ticks = [
            ("BETTING", 8.0, False, 0.01), # step 0
            ("BETTING", 7.5, False, 0.01), # step 1
            ("BETTING", 7.0, False, 0.01), # step 2: drops <= 7.0!
            ("BETTING", 6.95, False, 0.01), # step 3
            ("BETTING", 6.90, False, 0.01), # step 4
            ("BETTING", 5.00, False, 0.01), # step 5: sniper mark
            ("BETTING", 4.95, True, 0.01),  # step 6: sniper fired!
        ]
        records = simulate_server_loop(ticks)
        for r in records:
            print(f"Step {r['step']}: p_left={r['phase_seconds_left']}, dyn_int={r['dynamic_interval']}, sleep={r['sleep_time']}")
        # Step 2 dropped to 7.0s, so sleep_time must be clamped immediately to <= 0.05s
        self.assertLessEqual(records[2]['sleep_time'], 0.05)
        self.assertLessEqual(records[5]['sleep_time'], 0.05)

if __name__ == "__main__":
    unittest.main()
