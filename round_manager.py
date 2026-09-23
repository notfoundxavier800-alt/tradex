import time
import math
import threading
from typing import Dict, Any, Optional, List
import numpy as np

class RoundManager:
    """
    Authoritative Server-Side Round Manager for Cwallet Market Battle.
    Maintains continuous 20s round epochs (15s betting + 5s battle), automatically
    snaps fresh strike prices at every round boundary / battle start, and coordinates
    zero-drift sniper alerts at T-5s of the betting window.
    """
    def __init__(self, round_duration: int = 20, lead_time: float = 5.0):
        """Initialize the RoundManager.

        round_duration: total seconds per round (betting + battle). Default 20.
        lead_time: seconds before battle when sniper window opens. Default 5.0.
        """
        self.round_duration = round_duration
        self.lead_time = lead_time
        self.battle_duration = 5
        self.betting_duration = 15
        if self.round_duration == 30:
            self.betting_duration = 25
            self.battle_duration = 5
        elif self.round_duration == 60:
            self.betting_duration = 50
            self.battle_duration = 10
        elif self.round_duration == 20:
            self.betting_duration = 15
            self.battle_duration = 5

        self.sync_offset = 0  # Seconds offset relative to UTC Unix epoch
        self.battle_start_time = None  # timestamp when battle phase begins
        
        self.round_number = 1
        now_epoch = time.time()
        self.last_round_id = int(now_epoch // self.round_duration)
        self.round_open_price: Optional[float] = None
        self.round_high: Optional[float] = None
        self.round_low: Optional[float] = None
        self.round_ticks: List[tuple] = []  # (timestamp, price)
        self.last_settled_strike: Optional[float] = None
        self.last_settled_close: Optional[float] = None
        self.last_settled_outcome: Optional[str] = None
        self.is_battle_settled: bool = False
        self.battle_strike: Optional[float] = None  # Price snapped at battle start
        
        self.sniper_fired_for_round = -1
        self.early_radar_fired_for_round = -1
        self.chambering_fired_for_round = -1
        self.upgrade_fired_for_round = -1
        self.last_sniper_direction = "NONE"
        self.last_sniper_strength = ""
        self.sniper_fired_count = 0
        self.lock = threading.Lock()
        
    def set_duration(self, duration: int):
        with self.lock:
            if duration in (20, 30, 60):
                self.round_duration = duration
                if duration == 20:
                    self.betting_duration = 15
                    self.battle_duration = 5
                elif duration == 30:
                    self.betting_duration = 25
                    self.battle_duration = 5
                elif duration == 60:
                    self.betting_duration = 50
                    self.battle_duration = 10

    def set_lead_time(self, lead: float):
        with self.lock:
            self.lead_time = max(5.0, min(28.0, float(lead)))

    def mark_chambering_fired(self, round_id: int):
        with self.lock:
            self.chambering_fired_for_round = int(round_id)

    def is_chambering_fired(self, round_id: int) -> bool:
        with self.lock:
            return self.chambering_fired_for_round == int(round_id)

    def mark_sniper_fired(self, round_id: int, direction: str = "PASS", strength: str = ""):
        with self.lock:
            self.sniper_fired_for_round = int(round_id)
            self.last_sniper_direction = direction
            self.last_sniper_strength = strength
            self.sniper_fired_count += 1

    def mark_early_radar_fired(self, round_id: int, direction: str = "PASS", strength: str = ""):
        with self.lock:
            self.early_radar_fired_for_round = int(round_id)
            if self.last_sniper_direction in ("NONE", "PASS"):
                self.last_sniper_direction = direction
                self.last_sniper_strength = strength

    def is_early_radar_fired(self, round_id: int) -> bool:
        with self.lock:
            return self.early_radar_fired_for_round == int(round_id)

    def mark_upgrade_fired(self, round_id: int):
        with self.lock:
            self.upgrade_fired_for_round = int(round_id)

    def is_upgrade_fired(self, round_id: int) -> bool:
        with self.lock:
            return self.upgrade_fired_for_round == int(round_id)

    def get_last_sniper_direction(self, round_id: int) -> str:
        with self.lock:
            if self.sniper_fired_for_round == round_id or self.early_radar_fired_for_round == round_id:
                return self.last_sniper_direction
            return "NONE"

    def can_upgrade_sniper(self, round_id: int, seconds_left: float) -> bool:
        with self.lock:
            return (
                self.sniper_fired_for_round == round_id and
                self.last_sniper_direction == "PASS" and
                seconds_left >= 4.0
            )

    def lock_strike(self, price: float):
        with self.lock:
            if price > 0:
                self.round_open_price = float(price)
                self.round_high = max(self.round_high or price, price)
                self.round_low = min(self.round_low or price, price)

    def snap_strike(self, price: float) -> None:
        """Manually snap the strike price at the start of the battle phase.
        Sets battle_strike, round_open_price if unset, and records battle_start_time.
        """
        with self.lock:
            if price > 0:
                self.battle_strike = float(price)
                if self.round_open_price is None:
                    self.round_open_price = float(price)
                if self.battle_start_time is None:
                    self.battle_start_time = time.time() + self.sync_offset

    def settle_round(self, strike: float, close_price: float) -> Dict[str, Any]:
        """Settle the round outcome strictly against strike price."""
        with self.lock:
            self.last_settled_strike = float(strike)
            self.last_settled_close = float(close_price)
            if self.last_settled_close > self.last_settled_strike:
                outcome = "UP"
            elif self.last_settled_close < self.last_settled_strike:
                outcome = "DOWN"
            else:
                outcome = "TIE"
            self.last_settled_outcome = outcome
            self.is_battle_settled = True
            return {
                "strike": self.last_settled_strike,
                "close_price": self.last_settled_close,
                "outcome": outcome,
                "won": outcome
            }

    def _reset_battle_start(self):
        self.battle_start_time = None
        self.battle_strike = None
        self.is_battle_settled = False

    def manual_sync(self, seconds_left: Optional[float] = None, open_price: Optional[float] = None, round_number: Optional[int] = None, sync_offset: Optional[int] = None, current_price: Optional[float] = None):
        with self.lock:
            epoch_sec = time.time()
            if sync_offset is not None:
                self.sync_offset = int(sync_offset) % self.round_duration
                effective_time = epoch_sec + self.sync_offset
                self.last_round_id = int(effective_time // self.round_duration)
            elif seconds_left is not None and 1 <= seconds_left <= self.round_duration:
                target_pos = (self.round_duration - float(seconds_left)) % self.round_duration
                self.sync_offset = ((target_pos - (epoch_sec % self.round_duration)) % self.round_duration + self.round_duration) % self.round_duration
                effective_time = epoch_sec + self.sync_offset
                self.last_round_id = int(effective_time // self.round_duration)
                if seconds_left >= 5:
                    self.sniper_fired_for_round = -1
                    self.early_radar_fired_for_round = -1
                    self.chambering_fired_for_round = -1
                    self.upgrade_fired_for_round = -1

            if open_price is not None and open_price > 0:
                self.round_open_price = float(open_price)
                self.round_high = float(open_price)
                self.round_low = float(open_price)
                self.round_ticks = [(epoch_sec, float(open_price))]
            elif seconds_left is not None and seconds_left >= (self.round_duration - 3.0) and current_price and current_price > 0:
                self.round_open_price = float(current_price)
                self.round_high = float(current_price)
                self.round_low = float(current_price)
                self.round_ticks = [(epoch_sec, float(current_price))]

            if round_number is not None and round_number > 0:
                self.round_number = int(round_number)

    def tick(self, current_price: float) -> Dict[str, Any]:
        """Update round clock, track path, handle phase transitions, and freeze battle strike."""
        with self.lock:
            epoch_sec = time.time()
            effective_time = epoch_sec + self.sync_offset
            current_round_id = int(effective_time // self.round_duration)

            pos = effective_time % self.round_duration
            seconds_left = self.round_duration - pos
            if seconds_left <= 0:
                seconds_left = float(self.round_duration)

            is_new_round = (current_round_id != self.last_round_id)
            prev_round_id = self.last_round_id
            just_settled = False
            settled_strike_val = None
            settled_close_val = None
            settled_outcome_val = None

            if is_new_round:
                if self.last_round_id != -1:
                    strike_to_settle = self.battle_strike or self.round_open_price
                    if strike_to_settle is not None and current_price > 0:
                        self.last_settled_strike = strike_to_settle
                        self.last_settled_close = current_price
                        if self.last_settled_close > self.last_settled_strike:
                            self.last_settled_outcome = "UP"
                        elif self.last_settled_close < self.last_settled_strike:
                            self.last_settled_outcome = "DOWN"
                        else:
                            self.last_settled_outcome = "TIE"
                        self.is_battle_settled = True
                        just_settled = True
                        settled_strike_val = self.last_settled_strike
                        settled_close_val = self.last_settled_close
                        settled_outcome_val = self.last_settled_outcome
                    self.round_number += 1
                self.last_round_id = current_round_id
                self.round_open_price = current_price if current_price > 0 else None
                self.round_high = current_price if current_price > 0 else None
                self.round_low = current_price if current_price > 0 else None
                self.round_ticks = [(epoch_sec, current_price)] if current_price > 0 else []
                self.sniper_fired_for_round = -1
                self.early_radar_fired_for_round = -1
                self.chambering_fired_for_round = -1
                self.upgrade_fired_for_round = -1
                self.last_sniper_direction = "NONE"
                self.last_sniper_strength = ""
                self.sniper_fired_count = 0
                self._reset_battle_start()

            if self.round_open_price is None and current_price > 0:
                self.round_open_price = current_price
                self.round_high = current_price
                self.round_low = current_price

            if current_price > 0:
                if self.round_high is None or current_price > self.round_high:
                    self.round_high = current_price
                if self.round_low is None or current_price < self.round_low:
                    self.round_low = current_price
                self.round_ticks.append((epoch_sec, current_price))
                if len(self.round_ticks) > 300:
                    self.round_ticks = self.round_ticks[-200:]

            # Phase classification: 15s betting (pos < 15s) and 5s battle (pos >= 15s)
            if pos < self.betting_duration:
                phase = "BETTING"
                phase_seconds_left = self.betting_duration - pos
            else:
                phase = "BATTLE"
                phase_seconds_left = self.round_duration - pos
                # Freeze battle_strike at boundary between betting close (0s) and battle start
                if self.battle_strike is None and current_price > 0:
                    self.battle_strike = current_price
                if self.battle_start_time is None:
                    self.battle_start_time = effective_time

            strike = self.battle_strike or self.round_open_price or current_price
            delta = (current_price - strike) if (current_price and strike) else 0.0

            r_high = self.round_high or current_price
            r_low = self.round_low or current_price
            r_span = max(1e-6, r_high - r_low)
            range_pct = float(np.clip((current_price - r_low) / r_span, 0.0, 1.0)) if r_span > 1e-5 else 0.5

            if len(self.round_ticks) >= 3:
                dt = max(0.5, self.round_ticks[-1][0] - self.round_ticks[0][0])
                round_velocity = (self.round_ticks[-1][1] - self.round_ticks[0][1]) / dt
            else:
                round_velocity = 0.0

            prices = [p for _, p in self.round_ticks] if self.round_ticks else [current_price]
            in_round_volatility = float(np.std(prices)) if len(prices) >= 2 else 0.0
            in_round_vwap = float(np.mean(prices)) if prices else current_price

            recent_ticks = [(t, p) for t, p in self.round_ticks if (epoch_sec - t) <= 5.0]
            if len(recent_ticks) >= 2:
                recent_dt = max(0.2, recent_ticks[-1][0] - recent_ticks[0][0])
                recent_momentum = (recent_ticks[-1][1] - recent_ticks[0][1]) / recent_dt
            else:
                recent_momentum = round_velocity

            # Sniper timing: True when phase == "BETTING" and phase_seconds_left <= lead_time
            # Must strictly be False during BATTLE phase
            is_sniper_window = (phase == "BETTING" and phase_seconds_left <= self.lead_time)
            is_sniper_fired = (self.sniper_fired_for_round == current_round_id)
            should_fire_sniper = is_sniper_window and not is_sniper_fired

            return {
                "round_id": current_round_id,
                "prev_round_id": prev_round_id,
                "round_number": self.round_number,
                "seconds_left": round(seconds_left, 3),
                "phase_seconds_left": round(phase_seconds_left, 3),
                "round_seconds_left": round(seconds_left, 3),
                "round_duration": self.round_duration,
                "betting_duration": self.betting_duration,
                "battle_duration": self.battle_duration,
                "round_open_price": round(strike, 2) if strike else 0.0,
                "strike_price": round(strike, 2) if strike else 0.0,
                "strike_delta": round(delta, 2),
                "round_high": round(r_high, 2),
                "round_low": round(r_low, 2),
                "range_pct": round(range_pct, 3),
                "round_velocity": round(round_velocity, 3),
                "in_round_volatility": round(in_round_volatility, 3),
                "in_round_vwap": round(in_round_vwap, 2),
                "recent_momentum": round(recent_momentum, 3),
                "phase": phase,
                "sync_offset": self.sync_offset,
                "is_new_round": is_new_round,
                "just_settled": just_settled,
                "settled_round_id": prev_round_id if just_settled else None,
                "settled_strike": round(settled_strike_val, 2) if settled_strike_val else None,
                "settled_close": round(settled_close_val, 2) if settled_close_val else None,
                "settled_outcome": settled_outcome_val,
                "is_sniper_window": is_sniper_window,
                "should_fire_sniper": should_fire_sniper,
                "sniper_fired_for_round": self.sniper_fired_for_round,
                "early_radar_fired_for_round": self.early_radar_fired_for_round,
                "chambering_fired_for_round": self.chambering_fired_for_round,
                "lead_time": self.lead_time,
                "battle_strike": self.battle_strike,
                "battle_start_time": self.battle_start_time,
            }

    def get_state(self, current_price: float = 0.0) -> Dict[str, Any]:
        with self.lock:
            epoch_sec = time.time()
            effective_time = epoch_sec + self.sync_offset
            current_round_id = int(effective_time // self.round_duration)
            pos = effective_time % self.round_duration
            seconds_left = self.round_duration - pos
            if seconds_left <= 0:
                seconds_left = float(self.round_duration)

            if pos < self.betting_duration:
                phase_state = "BETTING"
                phase_seconds_left = self.betting_duration - pos
            else:
                phase_state = "BATTLE"
                phase_seconds_left = self.round_duration - pos

            is_sniper_window = (phase_state == "BETTING" and phase_seconds_left <= self.lead_time)
            strike = self.battle_strike or self.round_open_price or current_price
            delta = (current_price - strike) if (current_price and strike) else 0.0
            r_high = self.round_high or current_price
            r_low = self.round_low or current_price
            r_span = max(1e-6, r_high - r_low)
            range_pct = float(np.clip((current_price - r_low) / r_span, 0.0, 1.0)) if r_span > 1e-5 else 0.5

            return {
                "round_id": current_round_id,
                "round_number": self.round_number,
                "seconds_left": round(seconds_left, 3),
                "phase_seconds_left": round(phase_seconds_left, 3),
                "round_seconds_left": round(seconds_left, 3),
                "round_duration": self.round_duration,
                "betting_duration": self.betting_duration,
                "battle_duration": self.battle_duration,
                "round_open_price": round(strike, 2) if strike else 0.0,
                "strike_price": round(strike, 2) if strike else 0.0,
                "strike_delta": round(delta, 2),
                "round_high": round(r_high, 2),
                "round_low": round(r_low, 2),
                "range_pct": round(range_pct, 3),
                "sync_offset": self.sync_offset,
                "sniper_fired_for_round": self.sniper_fired_for_round,
                "early_radar_fired_for_round": self.early_radar_fired_for_round,
                "chambering_fired_for_round": self.chambering_fired_for_round,
                "lead_time": self.lead_time,
                "phase": phase_state,
                "is_sniper_window": is_sniper_window,
                "battle_strike": self.battle_strike,
                "battle_start_time": self.battle_start_time
            }

    def get_round_state(self, current_price: float = 0.0) -> Dict[str, Any]:
        """Return a comprehensive snapshot of the current round.
        Includes live round data and settlement info for the previous round.
        """
        with self.lock:
            epoch_sec = time.time()
            effective_time = epoch_sec + self.sync_offset
            pos = effective_time % self.round_duration
            seconds_left = self.round_duration - pos
            if seconds_left <= 0:
                seconds_left = float(self.round_duration)

            if pos < self.betting_duration:
                phase = "BETTING"
                phase_seconds_left = self.betting_duration - pos
            else:
                phase = "BATTLE"
                phase_seconds_left = self.round_duration - pos

            is_sniper_window = (phase == "BETTING" and phase_seconds_left <= self.lead_time)
            strike_price = self.battle_strike or self.round_open_price or current_price

            settled_strike = self.last_settled_strike
            settled_close = self.last_settled_close
            settled_outcome = self.last_settled_outcome
            if settled_outcome is None and settled_strike is not None and settled_close is not None:
                if settled_close > settled_strike:
                    settled_outcome = "UP"
                elif settled_close < settled_strike:
                    settled_outcome = "DOWN"
                else:
                    settled_outcome = "TIE"

            is_battle_settled = self.is_battle_settled or (phase == "BETTING" and settled_strike is not None and settled_close is not None)

            return {
                "round_id": int(effective_time // self.round_duration),
                "epoch_time": effective_time,
                "phase": phase,
                "phase_seconds_left": round(phase_seconds_left, 3),
                "round_seconds_left": round(seconds_left, 3),
                "is_sniper_window": is_sniper_window,
                "strike_price": round(strike_price, 2) if strike_price else 0.0,
                "battle_start_time": self.battle_start_time,
                "is_battle_settled": is_battle_settled,
                "settled_strike": round(settled_strike, 2) if settled_strike else None,
                "settled_close": round(settled_close, 2) if settled_close else None,
                "settled_outcome": settled_outcome,
            }

    def get_round_state_at(self, epoch_sec: float, current_price: float = 0.0) -> Dict[str, Any]:
        """Calculate round state for an arbitrary epoch timestamp without mutating state."""
        with self.lock:
            effective_time = epoch_sec + self.sync_offset
            pos = effective_time % self.round_duration
            seconds_left = self.round_duration - pos
            if seconds_left <= 0:
                seconds_left = float(self.round_duration)

            if pos < self.betting_duration:
                phase = "BETTING"
                phase_seconds_left = self.betting_duration - pos
            else:
                phase = "BATTLE"
                phase_seconds_left = self.round_duration - pos

            is_sniper_window = (phase == "BETTING" and phase_seconds_left <= self.lead_time)
            strike_price = self.battle_strike or self.round_open_price or current_price

            settled_strike = self.last_settled_strike
            settled_close = self.last_settled_close
            settled_outcome = self.last_settled_outcome
            if settled_outcome is None and settled_strike is not None and settled_close is not None:
                if settled_close > settled_strike:
                    settled_outcome = "UP"
                elif settled_close < settled_strike:
                    settled_outcome = "DOWN"
                else:
                    settled_outcome = "TIE"

            is_battle_settled = self.is_battle_settled or (phase == "BETTING" and settled_strike is not None and settled_close is not None)

            return {
                "round_id": int(effective_time // self.round_duration),
                "epoch_time": effective_time,
                "phase": phase,
                "phase_seconds_left": round(phase_seconds_left, 3),
                "round_seconds_left": round(seconds_left, 3),
                "is_sniper_window": is_sniper_window,
                "strike_price": round(strike_price, 2) if strike_price else 0.0,
                "battle_start_time": self.battle_start_time,
                "is_battle_settled": is_battle_settled,
                "settled_strike": round(settled_strike, 2) if settled_strike else None,
                "settled_close": round(settled_close, 2) if settled_close else None,
                "settled_outcome": settled_outcome,
            }
