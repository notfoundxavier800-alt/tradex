import json
import threading
import time
import urllib.request
import urllib.parse
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

IST_OFFSET = timedelta(hours=5, minutes=30)
IST_TZ = timezone(IST_OFFSET, name="IST")

CURATED_INDIAN_MARKETS = [
    {"symbol": "^NSEI", "name": "NIFTY 50", "category": "Index", "exchange": "NSE"},
    {"symbol": "^NSEBANK", "name": "BANK NIFTY", "category": "Index", "exchange": "NSE"},
    {"symbol": "^BSESN", "name": "SENSEX", "category": "Index", "exchange": "BSE"},
    {"symbol": "^CNXIT", "name": "NIFTY IT", "category": "Index", "exchange": "NSE"},
    {"symbol": "^CNXAUTO", "name": "NIFTY AUTO", "category": "Index", "exchange": "NSE"},
    {"symbol": "RELIANCE.NS", "name": "Reliance Industries", "category": "Energy", "exchange": "NSE"},
    {"symbol": "TCS.NS", "name": "Tata Consultancy", "category": "IT Services", "exchange": "NSE"},
    {"symbol": "HDFCBANK.NS", "name": "HDFC Bank", "category": "Banking", "exchange": "NSE"},
    {"symbol": "INFY.NS", "name": "Infosys", "category": "IT Services", "exchange": "NSE"},
    {"symbol": "ICICIBANK.NS", "name": "ICICI Bank", "category": "Banking", "exchange": "NSE"},
    {"symbol": "BHARTIARTL.NS", "name": "Bharti Airtel", "category": "Telecom", "exchange": "NSE"},
    {"symbol": "SBIN.NS", "name": "State Bank of India", "category": "Banking", "exchange": "NSE"},
    {"symbol": "TATAMOTORS.NS", "name": "Tata Motors", "category": "Automotive", "exchange": "NSE"},
    {"symbol": "ITC.NS", "name": "ITC Ltd", "category": "FMCG", "exchange": "NSE"},
    {"symbol": "LT.NS", "name": "Larsen & Toubro", "category": "Infrastructure", "exchange": "NSE"},
    {"symbol": "BAJFINANCE.NS", "name": "Bajaj Finance", "category": "Financials", "exchange": "NSE"},
    {"symbol": "KOTAKBANK.NS", "name": "Kotak Mahindra Bank", "category": "Banking", "exchange": "NSE"},
    {"symbol": "SUNPHARMA.NS", "name": "Sun Pharma", "category": "Pharma", "exchange": "NSE"},
    {"symbol": "MARUTI.NS", "name": "Maruti Suzuki", "category": "Automotive", "exchange": "NSE"},
    {"symbol": "TITAN.NS", "name": "Titan Company", "category": "Consumer", "exchange": "NSE"},
    {"symbol": "ADANIENT.NS", "name": "Adani Enterprises", "category": "Conglomerate", "exchange": "NSE"},
    {"symbol": "ZOMATO.NS", "name": "Zomato", "category": "Consumer Tech", "exchange": "NSE"},
    {"symbol": "PAYTM.NS", "name": "Paytm (One97)", "category": "Fintech", "exchange": "NSE"}
]

class IndianMarketFeed:
    def __init__(self, initial_symbol: str = "^NSEI"):
        self.symbol = initial_symbol.upper()
        self.lock = threading.Lock()
        self.candles = pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])
        self.latest_price = 0.0
        self.prev_close = 0.0
        self.day_open = 0.0
        self.day_high = 0.0
        self.day_low = 0.0
        self.day_volume = 0
        self.currency = "INR"
        self.currency_symbol = "₹"
        self.instrument_name = "NIFTY 50"
        self.exchange = "NSE"
        self.vwap = 0.0
        self.rsi_14 = 50.0
        self.ema_9 = 0.0
        self.ema_21 = 0.0
        self.atr_14 = 1.0
        self.poc_price = 0.0
        self.vol_expansion = 1.0
        self._is_connected = False
        self._stop_event = threading.Event()
        self._poll_thread: Optional[threading.Thread] = None
        self.last_fetch_time = 0.0

    @staticmethod
    def get_market_status() -> Dict[str, Any]:
        now_ist = datetime.now(IST_TZ)
        weekday = now_ist.weekday()
        is_weekday = weekday < 5
        market_open_time = now_ist.replace(hour=9, minute=15, second=0, microsecond=0)
        market_close_time = now_ist.replace(hour=15, minute=30, second=0, microsecond=0)
        is_open = is_weekday and (market_open_time <= now_ist <= market_close_time)
        ist_str = now_ist.strftime("%H:%M:%S IST")
        if is_open:
            status_text = "🟢 NSE/BSE LIVE"
            phase = "OPEN"
        elif not is_weekday:
            status_text = "🟡 NSE/BSE WEEKEND CLOSED"
            phase = "WEEKEND"
        elif now_ist < market_open_time:
            status_text = "🟡 PRE-MARKET (Opens 09:15 IST)"
            phase = "PRE_MARKET"
        else:
            status_text = "🟡 NSE/BSE CLOSED (Closes 15:30 IST)"
            phase = "POST_MARKET"
        return {
            "is_open": is_open,
            "status_text": status_text,
            "phase": phase,
            "ist_time": ist_str,
            "day": now_ist.strftime("%A")
        }

    def fetch_ticker_data(self, ticker: str) -> bool:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "application/json"
        }
        encoded = urllib.parse.quote(ticker)
        data = None

        urls = [
            f"https://query1.finance.yahoo.com/v8/finance/chart/{encoded}?range=1d&interval=1m",
            f"https://query2.finance.yahoo.com/v8/finance/chart/{encoded}?range=1d&interval=1m",
            f"https://query1.finance.yahoo.com/v8/finance/chart/{encoded}?range=5d&interval=5m"
        ]

        for url in urls:
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=12.0) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    res = data.get("chart", {}).get("result")
                    if res and len(res) > 0:
                        break
            except Exception as ex:
                continue

        try:
            result = data.get("chart", {}).get("result") if data else None
            if not result or len(result) == 0:
                return False

            res = result[0]
            meta = res.get("meta", {})
            timestamps = res.get("timestamp", [])
            indicators = res.get("indicators", {})
            quote = indicators.get("quote", [{}])[0]
            opens = quote.get("open", [])
            highs = quote.get("high", [])
            lows = quote.get("low", [])
            closes = quote.get("close", [])
            volumes = quote.get("volume", [])

            live_price = float(meta.get("regularMarketPrice", 0.0))
            prev_close = float(meta.get("chartPreviousClose", meta.get("previousClose", 0.0)))
            currency = meta.get("currency", "INR")
            short_name = meta.get("shortName", meta.get("symbol", ticker))
            exchange = meta.get("exchangeName", "NSE")

            rows = []
            cum_vol = 0.0
            cum_pv = 0.0
            for i in range(len(timestamps)):
                ts = timestamps[i]
                c = closes[i] if i < len(closes) else None
                if c is None:
                    continue
                o = opens[i] if (i < len(opens) and opens[i] is not None) else c
                h = highs[i] if (i < len(highs) and highs[i] is not None) else max(o, c)
                l = lows[i] if (i < len(lows) and lows[i] is not None) else min(o, c)
                raw_v = float(volumes[i]) if (i < len(volumes) and volumes[i] is not None) else 0.0
                # If index has 0 volume, weight typical price by candle range (volatility-weighted anchor)
                v = raw_v if raw_v > 0 else max(1.0, float(h) - float(l))
                typ_p = (float(o) + float(h) + float(l) + float(c)) / 4.0

                t_dt = datetime.fromtimestamp(ts, tz=timezone.utc)
                rows.append({
                    "timestamp": t_dt,
                    "open": float(o),
                    "high": float(h),
                    "low": float(l),
                    "close": float(c),
                    "volume": float(v)
                })
                cum_vol += v
                cum_pv += (typ_p * v)

            if not rows and live_price > 0:
                now_dt = datetime.now(timezone.utc)
                rows.append({
                    "timestamp": now_dt,
                    "open": live_price,
                    "high": live_price,
                    "low": live_price,
                    "close": live_price,
                    "volume": 100.0
                })

            df = pd.DataFrame(rows)
            if df.empty:
                return False

            if live_price <= 0 and not df.empty:
                live_price = float(df["close"].iloc[-1])

            vwap_val = (cum_pv / cum_vol) if cum_vol > 0 else live_price
            closes_series = df["close"]
            ema9_val = float(closes_series.ewm(span=9, adjust=False).mean().iloc[-1]) if len(closes_series) >= 9 else live_price
            ema21_val = float(closes_series.ewm(span=21, adjust=False).mean().iloc[-1]) if len(closes_series) >= 21 else live_price

            rsi_val = 50.0
            if len(closes_series) >= 15:
                delta = closes_series.diff()
                gain = delta.where(delta > 0, 0.0)
                loss = -delta.where(delta < 0, 0.0)
                avg_gain = float(gain.ewm(alpha=1.0/14.0, adjust=False).mean().iloc[-1])
                avg_loss = float(loss.ewm(alpha=1.0/14.0, adjust=False).mean().iloc[-1])
                if avg_loss > 1e-6:
                    rs = avg_gain / avg_loss
                    rsi_val = float(100.0 - (100.0 / (1.0 + rs)))
                elif avg_gain > 1e-6:
                    rsi_val = 100.0
                else:
                    rsi_val = 50.0

            d_high = float(df["high"].max()) if not df.empty else live_price
            d_low = float(df["low"].min()) if not df.empty else live_price
            d_open = float(df["open"].iloc[0]) if not df.empty else live_price

            # ATR-14 True Range
            atr_val = max(1.0, (d_high - d_low) / 15.0 if d_high > d_low else live_price * 0.005)
            if len(df) >= 14:
                h_arr = df["high"].values
                l_arr = df["low"].values
                c_prev = np.roll(df["close"].values, 1)
                c_prev[0] = df["open"].values[0]
                tr = np.maximum(h_arr - l_arr, np.maximum(np.abs(h_arr - c_prev), np.abs(l_arr - c_prev)))
                atr_val = float(np.mean(tr[-14:]))

            # Volume Profile Point of Control (POC)
            poc_val = live_price
            if len(df) >= 10 and cum_vol > 0:
                p_min = float(df["low"].min())
                p_max = float(df["high"].max())
                if p_max > p_min:
                    num_bins = 20
                    bin_edges = np.linspace(p_min, p_max, num_bins + 1)
                    bin_vols = np.zeros(num_bins)
                    for _, r in df.iterrows():
                        mid = (float(r["high"]) + float(r["low"])) / 2.0
                        bin_idx = min(num_bins - 1, max(0, int((mid - p_min) / (p_max - p_min) * num_bins)))
                        bin_vols[bin_idx] += float(r["volume"]) if float(r["volume"]) > 0 else 1.0
                    poc_bin = int(np.argmax(bin_vols))
                    poc_val = float((bin_edges[poc_bin] + bin_edges[poc_bin + 1]) / 2.0)

            with self.lock:
                self.candles = df
                self.latest_price = live_price
                self.prev_close = prev_close
                self.day_open = d_open
                self.day_high = d_high
                self.day_low = d_low
                self.day_volume = cum_vol
                self.currency = currency
                self.currency_symbol = "₹" if currency in ["INR", "₹"] else currency
                self.instrument_name = short_name
                self.exchange = exchange
                self.vwap = round(vwap_val, 2)
                self.ema_9 = round(ema9_val, 2)
                self.ema_21 = round(ema21_val, 2)
                self.rsi_14 = round(rsi_val, 1)
                self.atr_14 = round(float(atr_val), 2)
                self.poc_price = round(float(poc_val), 2)
                self._is_connected = True
                self.last_fetch_time = time.time()
            return True
        except Exception as e:
            import traceback
            traceback.print_exc()
            return False

    def _poll_loop(self):
        while not self._stop_event.is_set():
            try:
                self.fetch_ticker_data(self.symbol)
            except Exception:
                pass
            for _ in range(25):
                if self._stop_event.is_set():
                    break
                time.sleep(0.1)

    def start(self):
        self._stop_event.clear()
        self.fetch_ticker_data(self.symbol)
        if not self._poll_thread or not self._poll_thread.is_alive():
            self._poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
            self._poll_thread.start()

    def stop(self):
        self._stop_event.set()

    def switch_symbol(self, new_symbol: str) -> bool:
        symbol_upper = new_symbol.upper().strip()
        if not symbol_upper.startswith("^") and "." not in symbol_upper:
            symbol_upper = f"{symbol_upper}.NS"

        success = self.fetch_ticker_data(symbol_upper)
        if success:
            with self.lock:
                self.symbol = symbol_upper
            print(f"[IndianMarketFeed] Switched to Indian symbol: {symbol_upper} ({self.instrument_name})")
            return True
        else:
            if symbol_upper.endswith(".NS"):
                bse_symbol = symbol_upper.replace(".NS", ".BO")
                if self.fetch_ticker_data(bse_symbol):
                    with self.lock:
                        self.symbol = bse_symbol
                    print(f"[IndianMarketFeed] Switched to BSE symbol: {bse_symbol} ({self.instrument_name})")
                    return True
            return False

    def get_candles(self) -> pd.DataFrame:
        with self.lock:
            return self.candles.copy()

    def get_latest_price(self) -> float:
        with self.lock:
            return self.latest_price

    def is_connected(self) -> bool:
        with self.lock:
            return self._is_connected and (time.time() - self.last_fetch_time < 30.0)

    def get_market_info(self) -> Dict[str, Any]:
        with self.lock:
            chg = self.latest_price - self.prev_close if self.prev_close > 0 else 0.0
            chg_pct = (chg / self.prev_close * 100.0) if self.prev_close > 0 else 0.0
            status = self.get_market_status()
            return {
                "symbol": self.symbol,
                "name": self.instrument_name,
                "exchange": self.exchange,
                "currency": self.currency,
                "currency_symbol": self.currency_symbol,
                "price": self.latest_price,
                "prev_close": self.prev_close,
                "change": round(chg, 2),
                "change_pct": round(chg_pct, 2),
                "day_open": self.day_open,
                "day_high": self.day_high,
                "day_low": self.day_low,
                "day_volume": self.day_volume,
                "vwap": self.vwap,
                "ema_9": self.ema_9,
                "ema_21": self.ema_21,
                "rsi_14": self.rsi_14,
                "atr_14": self.atr_14,
                "poc_price": self.poc_price,
                "market_status": status
            }

    def get_order_flow(self) -> Dict[str, Any]:
        with self.lock:
            price = self.latest_price
            vwap = self.vwap or price
            vwap_delta = price - vwap
            vwap_bps = (vwap_delta / vwap * 10000.0) if vwap > 0 else 0.0
            bull_pct = 50.0 + float(np.clip(vwap_bps * 1.5, -45.0, 45.0))
            bull_pct = float(np.clip(bull_pct, 5.0, 95.0))
            bear_pct = 100.0 - bull_pct
            rng = self.day_high - self.day_low
            day_pos = ((price - self.day_low) / rng * 100.0) if rng > 0 else 50.0

            # Synthetic L1 book depth proportional to volume
            ref_vol = max(500.0, float(self.day_volume) * 0.001)
            bid_qty = round(ref_vol * (bull_pct / 100.0), 1)
            ask_qty = round(ref_vol * (bear_pct / 100.0), 1)
            imb = round((bull_pct - 50.0) / 50.0, 2)

            return {
                "bull_ratio": round(bull_pct, 1),
                "bear_ratio": round(bear_pct, 1),
                "bull_ratio_5s": round(bull_pct, 1),
                "bull_ratio_30s": round(bull_pct, 1),
                "vwap_30s": vwap,
                "vwap_60s": vwap,
                "delta_5s": round(vwap_delta, 2),
                "delta_15s": round(vwap_delta, 2),
                "delta_30s": round(vwap_delta, 2),
                "delta_60s": round(vwap_delta, 2),
                "micro_price": round(price + (vwap_delta * 0.2), 2),
                "spread": 0.05,
                "spread_bias": round(vwap_delta * 0.1, 3),
                "tick_intensity": 12.0,
                "global_consensus": round(float(np.clip(vwap_bps / 10.0, -1.0, 1.0)), 2),
                "vpin": 0.45,
                "day_range_pos": round(day_pos, 1),
                "day_high": self.day_high,
                "day_low": self.day_low,
                "book_bid_qty": bid_qty,
                "book_ask_qty": ask_qty,
                "book_imbalance_5s": imb,
                "currency_symbol": "₹"
            }

    @staticmethod
    def get_curated_list() -> List[Dict[str, Any]]:
        return CURATED_INDIAN_MARKETS
