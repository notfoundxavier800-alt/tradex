import unittest
from unittest.mock import patch
import time

from round_manager import RoundManager

class TestRoundManagerPhase(unittest.TestCase):
    def setUp(self):
        # 20-second continuous epoch: 15s betting + 5s battle, lead_time=5s
        self.rm = RoundManager(round_duration=20, lead_time=5)
        # Deterministic start time aligned to round boundary
        self.start_epoch = 1_600_000_000.0  # arbitrary fixed timestamp: 1_600_000_000 % 20 == 0
        self.rm.sync_offset = 0

    def _tick_at(self, seconds_since_start, price):
        """Helper to invoke tick with a mocked time.time()."""
        with patch('time.time', return_value=self.start_epoch + seconds_since_start):
            return self.rm.tick(current_price=price)

    def test_phase_transitions_and_battle_strike(self):
        # At t=0 -> BETTING phase (15s left in betting), no battle_strike yet
        state = self._tick_at(0, 100.0)
        self.assertEqual(state['phase'], 'BETTING')
        self.assertEqual(state['phase_seconds_left'], 15.0)
        self.assertIsNone(self.rm.battle_strike)
        self.assertFalse(state['should_fire_sniper'])
        self.assertFalse(state['is_sniper_window'])

        # At t=5 -> BETTING phase (10s left in betting), still before sniper window
        state = self._tick_at(5, 101.0)
        self.assertEqual(state['phase'], 'BETTING')
        self.assertEqual(state['phase_seconds_left'], 10.0)
        self.assertFalse(state['should_fire_sniper'])
        self.assertFalse(state['is_sniper_window'])

        # At t=10 -> T-5s mark of the 15s betting window: sniper window opens!
        state = self._tick_at(10, 101.5)
        self.assertEqual(state['phase'], 'BETTING')
        self.assertEqual(state['phase_seconds_left'], 5.0)
        self.assertTrue(state['is_sniper_window'])
        self.assertTrue(state['should_fire_sniper'])

        # Simulate firing the sniper at T-5s
        self.rm.mark_sniper_fired(state['round_id'], direction='UP', strength='HIGH')

        # One second later at t=11: still BETTING, but sniper already fired
        state = self._tick_at(11, 101.8)
        self.assertEqual(state['phase'], 'BETTING')
        self.assertTrue(state['is_sniper_window'])
        self.assertFalse(state['should_fire_sniper'])

        # At t=15 -> Transition to BATTLE phase (betting window closed, battle starts)
        # Strike price K is snapped at this exact boundary
        state = self._tick_at(15, 102.0)
        self.assertEqual(state['phase'], 'BATTLE')
        self.assertEqual(state['phase_seconds_left'], 5.0)
        self.assertEqual(self.rm.battle_strike, 102.0)
        self.assertEqual(state['strike_price'], 102.0)
        # Sniper window must be strictly INACTIVE during battle
        self.assertFalse(state['is_sniper_window'])
        self.assertFalse(state['should_fire_sniper'])

        # At t=16 -> Mid-battle fluctuation: price moves to 103.0, strike K remains frozen
        state = self._tick_at(16, 103.0)
        self.assertEqual(state['phase'], 'BATTLE')
        self.assertEqual(state['phase_seconds_left'], 4.0)
        self.assertFalse(state['is_sniper_window'])
        self.assertFalse(state['should_fire_sniper'])
        self.assertEqual(self.rm.battle_strike, 102.0)
        self.assertEqual(state['strike_price'], 102.0)

    def test_new_round_resets_battle_strike(self):
        # Round 1 start at t=0
        self._tick_at(0, 100.0)
        self.assertIsNone(self.rm.battle_strike)

        # Enter battle at t=15, battle_strike snaps
        self._tick_at(15, 101.0)
        self.assertEqual(self.rm.battle_strike, 101.0)

        # Advance to t=20 -> new round opens, battle_strike should reset
        state = self._tick_at(20, 102.0)
        self.assertEqual(state['phase'], 'BETTING')
        self.assertIsNone(self.rm.battle_strike)

if __name__ == '__main__':
    unittest.main()
