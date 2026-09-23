import time
import math
import threading
from typing import Dict, Any, Optional, List
import numpy as np

class RoundManager:
    """
    Authoritative Server-Side Round Manager for Cwallet Market Battle.
    Maintains continuous 30s/60s round epochs, automatically snaps fresh strike
    prices at every round start boundary, and coordinates zero-drift sniper alerts.
    """
    def __init__(self, round_duration: int = 30, lead_time: float = 5.0):
        self.round_duration = round_duration
        self.lead_time = lead_time
        self.sync_offset = 0  # Seconds offset relative to UTC Unix epoch
        
        self.round_number = 1
        self.last_round_id = -1
        self.round_open_price: Optional[float] = None
        self.round_high: Optional[float] = None
        self.round_low: Optional[float] = None
        self.round_ticks: List[tuple] = []  # (timestamp, price)
        self.last_settled_strike: Optional[float] = None
        self.last_settled_close: Optional[float] = None
        
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
            if duration in (30, 60):
                self.round_duration = duration

    def set_lead_time(self, lead: float):
        with self.lock:
            # Allows user to set 8s, 10s, 12s, 15s sniper precision
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
            # Can upgrade if previously fired for this round, it was PASS, and betting is still open (>= 4s)
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

    def manual_sync(self, seconds_left: Optional[float] = None, open_price: Optional[float] = None, round_number: Optional[int] = None, sync_offset: Optional[int] = None, current_price: Optional[float] = None):
        with self.lock:
            epoch_sec = time.time()
            if sync_offset is not None:
                self.sync_offset = int(sync_offset) % self.round_duration
                effective_time = epoch_sec + self.sync_offset
                self.last_round_id = int(effective_time // self.round_duration)
            elif seconds_left is not None and 1 <= seconds_left <= self.round_duration:
                target_pos = (self.round_duration - int(seconds_left)) % self.round_duration
                self.sync_offset = ((target_pos - int(epoch_sec % self.round_duration)) % self.round_duration + self.round_duration) % self.round_duration
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
        """
        Called on every engine cycle. Updates round clock, tracks in-round path integral,
        and snaps fresh strike at t=0.
        """
        with self.lock:
            epoch_sec = time.time()
            effective_time = epoch_sec + self.sync_offset
            current_round_id = int(effective_time // self.round_duration)
            
            pos = int(effective_time) % self.round_duration
            seconds_left = self.round_duration - pos
            if seconds_left <= 0:
                seconds_left = self.round_duration

            is_new_round = (current_round_id != self.last_round_id)
            if is_new_round:
                if self.last_round_id != -1:
                    self.last_settled_strike = self.round_open_price
                    self.last_settled_close = current_price
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

            if self.round_open_price is None and current_price > 0:
                self.round_open_price = current_price
                self.round_high = current_price
                self.round_low = current_price

            # Track in-round price path
            if current_price > 0:
                if self.round_high is None or current_price > self.round_high:
                    self.round_high = current_price
                if self.round_low is None or current_price < self.round_low:
                    self.round_low = current_price
                self.round_ticks.append((epoch_sec, current_price))
                if len(self.round_ticks) > 300:
                    self.round_ticks = self.round_ticks[-200:]

            strike = self.round_open_price or current_price
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
            
            # Momentum of the latest 5 seconds
            recent_ticks = [(t, p) for t, p in self.round_ticks if (epoch_sec - t) <= 5.0]
            if len(recent_ticks) >= 2:
                recent_dt = max(0.2, recent_ticks[-1][0] - recent_ticks[0][0])
                recent_momentum = (recent_ticks[-1][1] - recent_ticks[0][1]) / recent_dt
            else:
                recent_momentum = round_velocity

            phase = "OPEN"
            if seconds_left <= 3:
                phase = "SETTLING"
            elif seconds_left <= self.lead_time:
                phase = "SNIPER"
            elif seconds_left <= (self.lead_time + 4):
                phase = "ANTICIPATION"

            min_sniper_sec = 3
            in_sniper_window = (seconds_left <= self.lead_time and seconds_left >= min_sniper_sec)
            is_sniper_fired = (self.sniper_fired_for_round == current_round_id)
            should_fire_sniper = in_sniper_window and not is_sniper_fired

            return {
                "round_id": current_round_id,
                "round_number": self.round_number,
                "seconds_left": seconds_left,
                "round_duration": self.round_duration,
                "round_open_price": round(strike, 2) if strike else 0.0,
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
                "should_fire_sniper": should_fire_sniper,
                "sniper_fired_for_round": self.sniper_fired_for_round,
                "early_radar_fired_for_round": self.early_radar_fired_for_round,
                "chambering_fired_for_round": self.chambering_fired_for_round,
                "lead_time": self.lead_time
            }

    def get_state(self, current_price: float = 0.0) -> Dict[str, Any]:
        with self.lock:
            epoch_sec = time.time()
            effective_time = epoch_sec + self.sync_offset
            pos = int(effective_time) % self.round_duration
            seconds_left = self.round_duration - pos
            if seconds_left <= 0:
                seconds_left = self.round_duration
            strike = self.round_open_price or current_price
            delta = (current_price - strike) if (current_price and strike) else 0.0
            r_high = self.round_high or current_price
            r_low = self.round_low or current_price
            r_span = max(1e-6, r_high - r_low)
            range_pct = float(np.clip((current_price - r_low) / r_span, 0.0, 1.0)) if r_span > 1e-5 else 0.5

            return {
                "round_number": self.round_number,
                "seconds_left": seconds_left,
                "round_duration": self.round_duration,
                "round_open_price": round(strike, 2) if strike else 0.0,
                "strike_delta": round(delta, 2),
                "round_high": round(r_high, 2),
                "round_low": round(r_low, 2),
                "range_pct": round(range_pct, 3),
                "sync_offset": self.sync_offset,
                "sniper_fired_for_round": self.sniper_fired_for_round,
                "early_radar_fired_for_round": self.early_radar_fired_for_round,
                "chambering_fired_for_round": self.chambering_fired_for_round,
                "lead_time": self.lead_time
            }
