import json
import threading
import time
import urllib.request
import urllib.parse
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

# UTC and EST Timezones
EST_OFFSET = timedelta(hours=-5)
EST_TZ = timezone(EST_OFFSET, name="EST")

CURATED_INTERNATIONAL_MARKETS = [
    # US Major Benchmark Indices & ETFs
    {"symbol": "^GSPC", "name": "S&P 500 Index", "category": "US Index", "exchange": "Cboe/NYSE", "currency_symbol": "$"},
    {"symbol": "^IXIC", "name": "NASDAQ Composite", "category": "US Index", "exchange": "NASDAQ", "currency_symbol": "$"},
    {"symbol": "^DJI", "name": "Dow Jones Industrial", "category": "US Index", "exchange": "DJI", "currency_symbol": "$"},
    {"symbol": "^RUT", "name": "Russell 2000 Index", "category": "US Index", "exchange": "Russell", "currency_symbol": "$"},
    {"symbol": "SPY", "name": "SPDR S&P 500 ETF", "category": "US ETF", "exchange": "NYSE Arca", "currency_symbol": "$"},
    {"symbol": "QQQ", "name": "Invesco QQQ Trust", "category": "US ETF", "exchange": "NASDAQ", "currency_symbol": "$"},
    {"symbol": "^VIX", "name": "CBOE Volatility Index", "category": "Volatility", "exchange": "CBOE", "currency_symbol": "$"},

    # US Mega-Cap Blue-Chips & Tech Leaders
    {"symbol": "AAPL", "name": "Apple Inc.", "category": "US Tech", "exchange": "NASDAQ", "currency_symbol": "$"},
    {"symbol": "NVDA", "name": "NVIDIA Corporation", "category": "US Tech / AI", "exchange": "NASDAQ", "currency_symbol": "$"},
    {"symbol": "MSFT", "name": "Microsoft Corporation", "category": "US Tech", "exchange": "NASDAQ", "currency_symbol": "$"},
    {"symbol": "TSLA", "name": "Tesla, Inc.", "category": "US Auto / Clean Tech", "exchange": "NASDAQ", "currency_symbol": "$"},
    {"symbol": "AMZN", "name": "Amazon.com, Inc.", "category": "US Consumer Tech", "exchange": "NASDAQ", "currency_symbol": "$"},
    {"symbol": "GOOGL", "name": "Alphabet Inc. (Google)", "category": "US Tech", "exchange": "NASDAQ", "currency_symbol": "$"},
    {"symbol": "META", "name": "Meta Platforms, Inc.", "category": "US Tech", "exchange": "NASDAQ", "currency_symbol": "$"},
    {"symbol": "AMD", "name": "Advanced Micro Devices", "category": "US Semis", "exchange": "NASDAQ", "currency_symbol": "$"},
    {"symbol": "PLTR", "name": "Palantir Technologies", "category": "US Software / AI", "exchange": "NYSE", "currency_symbol": "$"},

    # Global Commodities & Energy Futures
    {"symbol": "GC=F", "name": "Gold Futures (COMEX)", "category": "Commodity / Metals", "exchange": "CME COMEX", "currency_symbol": "$"},
    {"symbol": "SI=F", "name": "Silver Futures", "category": "Commodity / Metals", "exchange": "CME COMEX", "currency_symbol": "$"},
    {"symbol": "CL=F", "name": "Crude Oil WTI Futures", "category": "Commodity / Energy", "exchange": "NYMEX", "currency_symbol": "$"},
    {"symbol": "BZ=F", "name": "Brent Crude Oil Futures", "category": "Commodity / Energy", "exchange": "ICE", "currency_symbol": "$"},
    {"symbol": "NG=F", "name": "Natural Gas Futures", "category": "Commodity / Energy", "exchange": "NYMEX", "currency_symbol": "$"},
    {"symbol": "HG=F", "name": "Copper Futures", "category": "Commodity / Metals", "exchange": "CME COMEX", "currency_symbol": "$"},

    # Major Forex Currency Pairs (24/5 Trading)
    {"symbol": "EURUSD=X", "name": "EUR / USD", "category": "Forex", "exchange": "FX Spot", "currency_symbol": "$"},
    {"symbol": "GBPUSD=X", "name": "GBP / USD (Cable)", "category": "Forex", "exchange": "FX Spot", "currency_symbol": "$"},
    {"symbol": "USDJPY=X", "name": "USD / JPY", "category": "Forex", "exchange": "FX Spot", "currency_symbol": "¥"},
    {"symbol": "AUDUSD=X", "name": "AUD / USD (Aussie)", "category": "Forex", "exchange": "FX Spot", "currency_symbol": "$"},
    {"symbol": "USDCAD=X", "name": "USD / CAD (Loonie)", "category": "Forex", "exchange": "FX Spot", "currency_symbol": "$"},
    {"symbol": "USDINR=X", "name": "USD / INR", "category": "Forex", "exchange": "FX Spot", "currency_symbol": "₹"},

    # European & Asian Benchmark Indices
    {"symbol": "^FTSE", "name": "FTSE 100 (UK)", "category": "European Index", "exchange": "LSE", "currency_symbol": "£"},
    {"symbol": "^GDAXI", "name": "DAX 40 (Germany)", "category": "European Index", "exchange": "XETRA", "currency_symbol": "€"},
    {"symbol": "^N225", "name": "Nikkei 225 (Japan)", "category": "Asian Index", "exchange": "Tokyo (TSE)", "currency_symbol": "¥"},
    {"symbol": "^HSI", "name": "Hang Seng Index", "category": "Asian Index", "exchange": "HKEX", "currency_symbol": "HK$"},
]

class InternationalMarketFeed:
    """
    Real-Time Data Feed & Microstructure Engine for International Markets:
    - US Equities & Benchmark Indices (NYSE / NASDAQ)
    - Global Commodities & Metals (Gold, Silver, WTI Oil)
    - 24/5 Forex Currencies (EUR/USD, GBP/USD, USD/JPY, etc.)
    - European & Asian Benchmarks (FTSE, DAX, Nikkei)
    """

    def __init__(self, initial_symbol: str = "^GSPC"):
        self.symbol = initial_symbol.upper()
        self.lock = threading.Lock()
        self.candles = pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])
        self.latest_price = 0.0
        self.prev_close = 0.0
        self.day_open = 0.0
        self.day_high = 0.0
        self.day_low = 0.0
        self.day_volume = 0
        self.currency = "USD"
        self.currency_symbol = "$"
        self.instrument_name = "S&P 500 Index"
        self.exchange = "NYSE"
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

        self._resolve_symbol_meta(self.symbol)

    def _resolve_symbol_meta(self, sym: str):
        for item in CURATED_INTERNATIONAL_MARKETS:
            if item["symbol"].upper() == sym.upper():
                self.instrument_name = item["name"]
                self.exchange = item["exchange"]
                self.currency_symbol = item["currency_symbol"]
                return

        if "=X" in sym:
            self.instrument_name = f"Forex Pair ({sym})"
            self.exchange = "FX Spot"
            self.currency_symbol = "¥" if "JPY" in sym else ("$" if not sym.startswith("EUR") else "€")
        elif "=F" in sym:
            self.instrument_name = f"Commodity Futures ({sym})"
            self.exchange = "CME/NYMEX"
            self.currency_symbol = "$"
        elif sym.startswith("^"):
            self.instrument_name = f"Global Index ({sym})"
            self.exchange = "Global Index"
            self.currency_symbol = "£" if "FTSE" in sym else ("€" if "DAX" in sym or "GDAXI" in sym else ("¥" if "N225" in sym else "$"))
        else:
            self.instrument_name = f"US Stock ({sym})"
            self.exchange = "NASDAQ/NYSE"
            self.currency_symbol = "$"

    @staticmethod
    def get_market_status(symbol: str = "^GSPC") -> Dict[str, Any]:
        now_utc = datetime.now(timezone.utc)
        now_est = now_utc.astimezone(EST_TZ)
        weekday = now_est.weekday()

        sym = symbol.upper()
        is_forex = "=X" in sym
        is_commodity = "=F" in sym

        if is_forex:
            if weekday == 5:
                is_open = False
                status_text = "🟡 FOREX CLOSED (Weekend)"
                phase = "WEEKEND"
            elif weekday == 6 and now_est.hour < 17:
                is_open = False
                status_text = "🟡 FOREX CLOSED (Opens Sun 17:00 EST)"
                phase = "PRE_MARKET"
            elif weekday == 4 and now_est.hour >= 17:
                is_open = False
                status_text = "🟡 FOREX CLOSED (Closes Fri 17:00 EST)"
                phase = "WEEKEND"
            else:
                is_open = True
                status_text = "🟢 24/5 FOREX LIVE"
                phase = "OPEN"

        elif is_commodity:
            if weekday == 5 or (weekday == 6 and now_est.hour < 18) or (weekday == 4 and now_est.hour >= 17):
                is_open = False
                status_text = "🟡 COMMODITIES CLOSED (Weekend)"
                phase = "WEEKEND"
            elif 17 <= now_est.hour < 18:
                is_open = False
                status_text = "🟡 CME MAINTENANCE BREAK"
                phase = "BREAK"
            else:
                is_open = True
                status_text = "🟢 COMMODITIES LIVE (CME/NYMEX)"
                phase = "OPEN"

        else:
            is_weekday = weekday < 5
            market_open = now_est.replace(hour=9, minute=30, second=0, microsecond=0)
            market_close = now_est.replace(hour=16, minute=0, second=0, microsecond=0)
            pre_market = now_est.replace(hour=4, minute=0, second=0, microsecond=0)
            after_hours = now_est.replace(hour=20, minute=0, second=0, microsecond=0)

            if not is_weekday:
                is_open = False
                status_text = "🟡 US MARKETS WEEKEND CLOSED"
                phase = "WEEKEND"
            elif market_open <= now_est <= market_close:
                is_open = True
                status_text = "🟢 US MARKET LIVE (NYSE/NASDAQ)"
                phase = "OPEN"
            elif pre_market <= now_est < market_open:
                is_open = False
                status_text = "🟡 US PRE-MARKET (Opens 09:30 EST)"
                phase = "PRE_MARKET"
            elif market_close < now_est <= after_hours:
                is_open = False
                status_text = "🟡 US AFTER-HOURS (Closes 20:00 EST)"
                phase = "POST_MARKET"
            else:
                is_open = False
                status_text = "🟡 US MARKET CLOSED"
                phase = "CLOSED"

        return {
            "is_open": is_open,
            "status_text": status_text,
            "phase": phase,
            "est_time": now_est.strftime("%H:%M:%S EST"),
            "day": now_est.strftime("%A")
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
            except Exception:
                continue

        try:
            result = data.get("chart", {}).get("result") if data else None
            if not result or len(result) == 0:
                return False

            meta = result[0].get("meta", {})
            current_price = meta.get("regularMarketPrice", 0.0)
            prev_close = meta.get("chartPreviousClose", meta.get("previousClose", current_price))
            day_high = meta.get("regularMarketDayHigh", current_price)
            day_low = meta.get("regularMarketDayLow", current_price)
            currency = meta.get("currency", "USD")

            if currency == "INR": curr_sym = "₹"
            elif currency == "EUR": curr_sym = "€"
            elif currency == "GBP": curr_sym = "£"
            elif currency == "JPY": curr_sym = "¥"
            else: curr_sym = "$"

            timestamps = result[0].get("timestamp", [])
            indicators = result[0].get("indicators", {})
            quote = indicators.get("quote", [{}])[0]

            opens = quote.get("open", [])
            highs = quote.get("high", [])
            lows = quote.get("low", [])
            closes = quote.get("close", [])
            volumes = quote.get("volume", [])

            rows = []
            valid_closes = []
            cum_vol = 0
            cum_vol_price = 0.0

            for i in range(len(timestamps)):
                c = closes[i]
                if c is None or (isinstance(c, float) and (np.isnan(c) or not np.isfinite(c))):
                    continue
                o = opens[i] if (opens and i < len(opens) and opens[i] is not None and not np.isnan(opens[i])) else c
                h = highs[i] if (highs and i < len(highs) and highs[i] is not None and not np.isnan(highs[i])) else max(o, c)
                l = lows[i] if (lows and i < len(lows) and lows[i] is not None and not np.isnan(lows[i])) else min(o, c)
                
                raw_v = float(volumes[i]) if (volumes and i < len(volumes) and volumes[i] is not None and not np.isnan(volumes[i])) else 0.0
                # If asset (e.g. Forex) has 0 volume, use synthetic range-weighted volume anchor
                v = raw_v if raw_v > 0 else max(1.0, (float(h) - float(l)) * 10000.0)

                dt = datetime.fromtimestamp(timestamps[i], tz=timezone.utc)
                rows.append({
                    "timestamp": dt,
                    "open": float(o),
                    "high": float(h),
                    "low": float(l),
                    "close": float(c),
                    "volume": float(v)
                })
                valid_closes.append(float(c))
                cum_vol += v
                cum_vol_price += ((float(h) + float(l) + float(c)) / 3.0) * v

            if not rows:
                if current_price > 0:
                    with self.lock:
                        self.latest_price = float(current_price)
                        self.prev_close = float(prev_close)
                        self.currency_symbol = curr_sym
                    return True
                return False

            new_df = pd.DataFrame(rows)
            new_price = float(new_df["close"].iloc[-1]) if not new_df.empty else float(current_price)
            calc_vwap = (cum_vol_price / cum_vol) if cum_vol > 0 else new_price

            rsi_val = 50.0
            ema9_val = new_price
            ema21_val = new_price
            atr_val = 1.0
            poc_val = new_price

            if len(valid_closes) >= 14:
                deltas = np.diff(valid_closes)
                gains = pd.Series(np.where(deltas > 0, deltas, 0.0))
                losses = pd.Series(np.where(deltas < 0, -deltas, 0.0))
                avg_gain = float(gains.ewm(alpha=1.0/14.0, adjust=False).mean().iloc[-1])
                avg_loss = float(losses.ewm(alpha=1.0/14.0, adjust=False).mean().iloc[-1])
                if avg_loss > 1e-6:
                    rs = avg_gain / avg_loss
                    rsi_val = float(100.0 - (100.0 / (1.0 + rs)))
                elif avg_gain > 1e-6:
                    rsi_val = 100.0
                else:
                    rsi_val = 50.0

            if len(valid_closes) >= 9:
                s = pd.Series(valid_closes)
                ema9_val = float(s.ewm(span=9, adjust=False).mean().iloc[-1])
            if len(valid_closes) >= 21:
                s = pd.Series(valid_closes)
                ema21_val = float(s.ewm(span=21, adjust=False).mean().iloc[-1])

            if len(new_df) >= 14:
                h_arr = new_df["high"].values
                l_arr = new_df["low"].values
                c_prev = np.roll(new_df["close"].values, 1)
                c_prev[0] = new_df["open"].values[0]
                tr = np.maximum(h_arr - l_arr, np.maximum(np.abs(h_arr - c_prev), np.abs(l_arr - c_prev)))
                atr_val = float(np.mean(tr[-14:]))

            if len(new_df) >= 10 and cum_vol > 0:
                p_min = new_df["low"].min()
                p_max = new_df["high"].max()
                if p_max > p_min:
                    num_bins = 20
                    bin_edges = np.linspace(p_min, p_max, num_bins + 1)
                    bin_vols = np.zeros(num_bins)
                    for _, r in new_df.iterrows():
                        mid = (r["high"] + r["low"]) / 2.0
                        bin_idx = min(num_bins - 1, max(0, int((mid - p_min) / (p_max - p_min) * num_bins)))
                        bin_vols[bin_idx] += r["volume"] if r["volume"] > 0 else 1.0
                    poc_bin = np.argmax(bin_vols)
                    poc_val = float((bin_edges[poc_bin] + bin_edges[poc_bin + 1]) / 2.0)

            with self.lock:
                self.candles = new_df
                self.latest_price = new_price
                self.prev_close = float(prev_close) if prev_close else new_price
                self.day_high = float(day_high) if day_high else new_df["high"].max()
                self.day_low = float(day_low) if day_low else new_df["low"].min()
                self.day_open = float(new_df["open"].iloc[0])
                self.day_volume = int(cum_vol)
                self.currency = currency
                self.currency_symbol = curr_sym
                self.vwap = float(calc_vwap)
                self.rsi_14 = float(rsi_val)
                self.ema_9 = float(ema9_val)
                self.ema_21 = float(ema21_val)
                self.atr_14 = float(max(1e-4, atr_val))
                self.poc_price = float(poc_val)
                self._is_connected = True
                self.last_fetch_time = time.time()

            return True
        except Exception:
            return False

    def _poll_loop(self):
        while not self._stop_event.is_set():
            try:
                self.fetch_ticker_data(self.symbol)
            except Exception:
                pass
            time.sleep(2.5)

    def start(self):
        if self._poll_thread is None or not self._poll_thread.is_alive():
            self._stop_event.clear()
            self._poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
            self._poll_thread.start()

    def stop(self):
        self._stop_event.set()
        if self._poll_thread:
            self._poll_thread.join(timeout=1.0)

    def switch_symbol(self, new_symbol: str) -> bool:
        clean = new_symbol.strip().upper()
        success = self.fetch_ticker_data(clean)
        if success:
            with self.lock:
                self.symbol = clean
                self._resolve_symbol_meta(clean)
            return True
        return False

    def is_connected(self) -> bool:
        with self.lock:
            return self._is_connected and (time.time() - self.last_fetch_time < 30.0)

    def get_latest_price(self) -> float:
        with self.lock:
            return self.latest_price

    def get_candles(self) -> pd.DataFrame:
        with self.lock:
            return self.candles.copy()

    def get_market_info(self) -> Dict[str, Any]:
        with self.lock:
            chg = self.latest_price - self.prev_close
            chg_pct = (chg / self.prev_close * 100.0) if self.prev_close > 0 else 0.0
            return {
                "symbol": self.symbol,
                "name": self.instrument_name,
                "exchange": self.exchange,
                "currency": self.currency,
                "currency_symbol": self.currency_symbol,
                "price": self.latest_price,
                "prev_close": self.prev_close,
                "day_open": self.day_open,
                "day_high": self.day_high,
                "day_low": self.day_low,
                "day_volume": self.day_volume,
                "change": round(chg, 4),
                "change_pct": round(chg_pct, 2),
                "vwap": round(self.vwap, 4),
                "rsi_14": round(self.rsi_14, 1),
                "ema_9": round(self.ema_9, 4),
                "ema_21": round(self.ema_21, 4),
                "atr_14": round(self.atr_14, 4),
                "poc_price": round(self.poc_price, 4),
                "market_status": self.get_market_status(self.symbol)
            }

    def get_order_flow(self) -> Dict[str, Any]:
        with self.lock:
            df = self.candles
            price = self.latest_price
            vwap = self.vwap or price
            vwap_delta = price - vwap
            if df.empty or len(df) < 2:
                return {
                    "bull_ratio": 50.0, "bear_ratio": 50.0, "delta_5s": 0.0,
                    "book_bid_qty": 500.0, "book_ask_qty": 500.0, "book_imbalance_5s": 0.0,
                    "currency_symbol": self.currency_symbol
                }

            recent = df.iloc[-min(5, len(df)):]
            up_vol = recent[recent["close"] >= recent["open"]]["volume"].sum()
            down_vol = recent[recent["close"] < recent["open"]]["volume"].sum()
            total_v = up_vol + down_vol
            bull_pct = float(up_vol / total_v * 100.0) if total_v > 0 else 50.0
            bear_pct = float(100.0 - bull_pct)
            delta = float(up_vol - down_vol) / float(max(1.0, total_v))
            imb = round((bull_pct - 50.0) / 50.0, 2)

            return {
                "bull_ratio": round(bull_pct, 1),
                "bear_ratio": round(bear_pct, 1),
                "bull_ratio_5s": round(bull_pct, 1),
                "bull_ratio_30s": round(bull_pct, 1),
                "vwap_30s": vwap,
                "vwap_60s": vwap,
                "delta_5s": round(delta, 3),
                "delta_15s": round(delta, 3),
                "micro_price": round(price + (vwap_delta * 0.2), 4 if price < 2.0 else 2),
                "spread": 0.01 if price >= 2.0 else 0.0001,
                "spread_bias": round(delta * 0.1, 3),
                "book_bid_qty": round(float(up_vol), 1),
                "book_ask_qty": round(float(down_vol), 1),
                "book_imbalance_5s": imb,
                "currency_symbol": self.currency_symbol
            }
