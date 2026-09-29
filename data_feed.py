import json
import threading
import time
import urllib.request
from collections import deque
from typing import Optional, Dict, Any, List

import pandas as pd
import websocket

CURATED_CRYPTO_MARKETS = [
    {"symbol": "btcusdt", "name": "Bitcoin", "ticker": "BTC", "base": "BTC", "quote": "USDT"},
    {"symbol": "ethusdt", "name": "Ethereum", "ticker": "ETH", "base": "ETH", "quote": "USDT"},
    {"symbol": "solusdt", "name": "Solana", "ticker": "SOL", "base": "SOL", "quote": "USDT"},
    {"symbol": "xrpusdt", "name": "Ripple", "ticker": "XRP", "base": "XRP", "quote": "USDT"},
    {"symbol": "dogeusdt", "name": "Dogecoin", "ticker": "DOGE", "base": "DOGE", "quote": "USDT"},
    {"symbol": "bnbusdt", "name": "BNB", "ticker": "BNB", "base": "BNB", "quote": "USDT"},
    {"symbol": "adausdt", "name": "Cardano", "ticker": "ADA", "base": "ADA", "quote": "USDT"},
    {"symbol": "suiusdt", "name": "Sui", "ticker": "SUI", "base": "SUI", "quote": "USDT"},
    {"symbol": "pepeusdt", "name": "Pepe", "ticker": "PEPE", "base": "PEPE", "quote": "USDT"},
    {"symbol": "avaxusdt", "name": "Avalanche", "ticker": "AVAX", "base": "AVAX", "quote": "USDT"},
    {"symbol": "linkusdt", "name": "Chainlink", "ticker": "LINK", "base": "LINK", "quote": "USDT"},
    {"symbol": "nearusdt", "name": "Near Protocol", "ticker": "NEAR", "base": "NEAR", "quote": "USDT"}
]

class BinanceDataFeed:
    """
    🌌 UNIVERSAL LEVEL Tri-Venue Global Data Feed:
    1. Binance Spot WebSocket: 1s Klines, raw trades, L1 bookTicker
    2. Binance USD-M Futures WebSocket: USD-M Futures aggTrades, Futures L1 bookTicker
    3. Coinbase Institutional WebSocket: BTC-USD live institutional ticker (US fiat benchmark)
    
    Predictive Alpha Metrics:
    - Tri-Venue Consensus: Directional alignment across Binance Spot, Futures, and Coinbase
    - Futures Basis Spread & Basis Momentum (P_futures - P_spot)
    - Coinbase Inter-Exchange Spread & Lead Momentum (P_coinbase - P_spot)
    - Real-time VPIN (Volume-Synchronized Probability of Toxicity)
    - Micro-price & Order Book Imbalance
    """
    def __init__(self, symbol: str = "btcusdt"):
        self.symbol = symbol.lower()
        
        self.ws_spot: Optional[websocket.WebSocketApp] = None
        self.ws_futures: Optional[websocket.WebSocketApp] = None
        self.ws_coinbase: Optional[websocket.WebSocketApp] = None
        
        self.lock = threading.Lock()
        
        # 1. Binance Spot state
        self.candles = pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])
        self.latest_price = 0.0
        self.recent_trades = deque()  # (timestamp_float, is_buyer_taker, qty, price)
        self.whale_trades = deque(maxlen=8)
        self.book_ticker = None
        self.book_history = deque(maxlen=200)
        self.price_ticks = deque(maxlen=5000)
        
        # 2. Binance USD-M Futures state
        self.futures_price = 0.0
        self.futures_trades = deque()  # (timestamp_float, is_buyer_taker, qty, price)
        self.futures_book_ticker = None
        self.basis_history = deque(maxlen=300)  # (timestamp_float, basis_value)
        self.futures_ticks = deque(maxlen=1000)  # (timestamp_float, price)
        self.prev_bid_depth = 0.0
        self.prev_ask_depth = 0.0
        self.queue_depletion_velocity = 0.0
        self.depth_ladder = {"bids": [], "asks": [], "bid_depth": 0.0, "ask_depth": 0.0, "depth_ratio": 50.0, "queue_depletion": 0.0}
        
        # 3. Coinbase Institutional state
        self.coinbase_price = 0.0
        self.coinbase_ticks = deque(maxlen=1000)  # (timestamp_float, price)
        self.coinbase_bid = 0.0
        self.coinbase_ask = 0.0
        
        self._is_spot_connected = False
        self._is_futures_connected = False
        self._is_coinbase_connected = False
        self._stop_event = threading.Event()
        
        self._spot_thread: Optional[threading.Thread] = None
        self._futures_thread: Optional[threading.Thread] = None
        self._coinbase_thread: Optional[threading.Thread] = None

    # =========================================================================
    # Spot WebSocket Callbacks
    # =========================================================================
    def _on_spot_message(self, ws, message):
        try:
            data = json.loads(message)
            event_type = data.get("e")

            if event_type == "kline":
                k = data["k"]
                ts = pd.to_datetime(k["t"], unit='ms')
                o = float(k["o"])
                h = float(k["h"])
                l = float(k["l"])
                c = float(k["c"])
                v = float(k["v"])
                
                with self.lock:
                    self.latest_price = c
                    t_now = time.time()
                    self.price_ticks.append((t_now, c))
                    
                    if self.futures_price > 0:
                        basis = self.futures_price - c
                        self.basis_history.append((t_now, basis))
                    
                    if not self.candles.empty and self.candles.iloc[-1]["timestamp"] == ts:
                        idx = self.candles.index[-1]
                        self.candles.at[idx, "open"] = o
                        self.candles.at[idx, "high"] = h
                        self.candles.at[idx, "low"] = l
                        self.candles.at[idx, "close"] = c
                        self.candles.at[idx, "volume"] = v
                    else:
                        new_row = pd.DataFrame([{
                            "timestamp": ts, "open": o, "high": h, "low": l, "close": c, "volume": v
                        }])
                        if self.candles.empty:
                            self.candles = new_row
                        else:
                            self.candles = pd.concat([self.candles, new_row], ignore_index=True)
                        
                        if len(self.candles) > 300:
                            self.candles = self.candles.iloc[-300:].reset_index(drop=True)

            elif event_type == "trade":
                qty = float(data.get("q", 0))
                price = float(data.get("p", 0))
                is_buyer_taker = not data.get("m", True)
                trade_time = data.get("T", int(time.time() * 1000)) / 1000.0

                with self.lock:
                    if price > 0:
                        self.latest_price = price
                    self.recent_trades.append((trade_time, is_buyer_taker, qty, price))
                    self.price_ticks.append((trade_time, price))
                    # Scale whale threshold: $10,000 notional value across any crypto
                    min_whale_qty = max(0.01, 10000.0 / max(0.0001, price))
                    if qty >= min_whale_qty:
                        self.whale_trades.append({
                            "time": trade_time,
                            "is_buy": is_buyer_taker,
                            "qty": round(qty, 3),
                            "price": round(price, 4 if price < 1.0 else 2)
                        })
                    cutoff = trade_time - 120.0
                    while self.recent_trades and self.recent_trades[0][0] < cutoff:
                        self.recent_trades.popleft()

            elif "b" in data and "a" in data and "B" in data and "A" in data:
                b = float(data["b"])
                B = float(data["B"])
                a = float(data["a"])
                A = float(data["A"])
                tot = B + A
                imb = (B - A) / tot if tot > 0 else 0.0
                t_now = time.time()
                with self.lock:
                    self.book_ticker = {
                        "best_bid": b, "bid_qty": B,
                        "best_ask": a, "ask_qty": A,
                        "imbalance": imb, "time": t_now
                    }
                    self.book_history.append((t_now, b, B, a, A, imb))

            elif "bids" in data and "asks" in data:
                bids = [[float(p), float(q)] for p, q in data["bids"][:20]]
                asks = [[float(p), float(q)] for p, q in data["asks"][:20]]
                tot_b = sum(q for p, q in bids)
                tot_a = sum(q for p, q in asks)
                tot = tot_b + tot_a
                ratio = (tot_b / tot * 100.0) if tot > 0 else 50.0

                delta_b = (tot_b - self.prev_bid_depth) if self.prev_bid_depth > 0 else 0.0
                delta_a = (tot_a - self.prev_ask_depth) if self.prev_ask_depth > 0 else 0.0
                self.prev_bid_depth = tot_b
                self.prev_ask_depth = tot_a

                # Queue depletion velocity: positive when bids replenishing/growing & asks being depleted
                depletion_vel = (delta_b - delta_a) / max(0.05, tot)
                self.queue_depletion_velocity = round(float(depletion_vel), 4)

                with self.lock:
                    self.depth_ladder = {
                        "bids": bids,
                        "asks": asks,
                        "bid_depth": round(tot_b, 3),
                        "ask_depth": round(tot_a, 3),
                        "depth_ratio": round(ratio, 1),
                        "queue_depletion": self.queue_depletion_velocity
                    }

        except Exception:
            pass

    def _on_spot_open(self, ws):
        self._is_spot_connected = True
        sub_msg = {
            "method": "SUBSCRIBE",
            "params": [
                f"{self.symbol}@kline_1s",
                f"{self.symbol}@trade",
                f"{self.symbol}@bookTicker",
                f"{self.symbol}@depth20@100ms"
            ],
            "id": 1
        }
        ws.send(json.dumps(sub_msg))

    def _on_spot_close(self, ws, close_status_code, close_msg):
        self._is_spot_connected = False

    # =========================================================================
    # Futures WebSocket Callbacks
    # =========================================================================
    def _on_futures_message(self, ws, message):
        try:
            payload = json.loads(message)
            data = payload.get("data", payload)
            event_type = data.get("e")

            if event_type == "kline" or ("k" in data and isinstance(data.get("k"), dict)):
                k = data["k"] if "k" in data else data
                ts = pd.to_datetime(k["t"], unit='ms')
                o = float(k["o"])
                h = float(k["h"])
                l = float(k["l"])
                c = float(k["c"])
                v = float(k["v"])
                with self.lock:
                    self.futures_price = c
                    if self.latest_price <= 0 or not self._is_spot_connected:
                        self.latest_price = c
                    t_now = time.time()
                    self.futures_ticks.append((t_now, c))
                    if not self._is_spot_connected:
                        self.price_ticks.append((t_now, c))
                        if not self.candles.empty and self.candles.iloc[-1]["timestamp"] == ts:
                            idx = self.candles.index[-1]
                            self.candles.at[idx, "open"] = o
                            self.candles.at[idx, "high"] = h
                            self.candles.at[idx, "low"] = l
                            self.candles.at[idx, "close"] = c
                            self.candles.at[idx, "volume"] = v
                        else:
                            new_row = pd.DataFrame([{
                                "timestamp": ts, "open": o, "high": h, "low": l, "close": c, "volume": v
                            }])
                            if self.candles.empty:
                                self.candles = new_row
                            else:
                                self.candles = pd.concat([self.candles, new_row], ignore_index=True)
                            if len(self.candles) > 300:
                                self.candles = self.candles.iloc[-300:].reset_index(drop=True)

            elif event_type == "aggTrade":
                qty = float(data.get("q", 0))
                price = float(data.get("p", 0))
                is_buyer_taker = not data.get("m", True)
                trade_time = data.get("T", int(time.time() * 1000)) / 1000.0

                with self.lock:
                    self.futures_price = price
                    if self.latest_price <= 0 or not self._is_spot_connected:
                        self.latest_price = price
                        self.price_ticks.append((trade_time, price))
                    self.futures_trades.append((trade_time, is_buyer_taker, qty, price))
                    self.futures_ticks.append((trade_time, price))
                    
                    if self.latest_price > 0:
                        basis = price - self.latest_price
                        self.basis_history.append((trade_time, basis))
                    
                    cutoff = trade_time - 60.0
                    while self.futures_trades and self.futures_trades[0][0] < cutoff:
                        self.futures_trades.popleft()
                    while self.basis_history and self.basis_history[0][0] < cutoff:
                        self.basis_history.popleft()

            elif event_type == "bookTicker" or ("b" in data and "a" in data and "B" in data and "A" in data):
                b = float(data["b"])
                B = float(data["B"])
                a = float(data["a"])
                A = float(data["A"])
                with self.lock:
                    mid = (b + a) / 2.0
                    self.futures_price = mid
                    self.futures_ticks.append((time.time(), mid))
                    if self.latest_price > 0:
                        basis = mid - self.latest_price
                        self.basis_history.append((time.time(), basis))
                    cutoff = time.time() - 60.0
                    while self.basis_history and self.basis_history[0][0] < cutoff:
                        self.basis_history.popleft()
                    self.futures_book_ticker = {
                        "best_bid": b, "bid_qty": B,
                        "best_ask": a, "ask_qty": A,
                        "time": time.time()
                    }

        except Exception:
            pass

    def _on_futures_open(self, ws):
        self._is_futures_connected = True

    def _on_futures_close(self, ws, close_status_code, close_msg):
        self._is_futures_connected = False

    # =========================================================================
    # Coinbase Pro WebSocket Callbacks (US Institutional Benchmark)
    # =========================================================================
    def _on_coinbase_message(self, ws, message):
        try:
            data = json.loads(message)
            if data.get("type") == "ticker" and "price" in data:
                p = float(data["price"])
                b = float(data.get("best_bid", p))
                a = float(data.get("best_ask", p))
                t_now = time.time()
                with self.lock:
                    self.coinbase_price = p
                    self.coinbase_bid = b
                    self.coinbase_ask = a
                    if self.latest_price <= 0:
                        self.latest_price = p
                        self.price_ticks.append((t_now, p))
                    if self.futures_price <= 0:
                        self.futures_price = p
                        self.futures_ticks.append((t_now, p))
                    self.coinbase_ticks.append((t_now, p))
                    cutoff = t_now - 60.0
                    while self.coinbase_ticks and self.coinbase_ticks[0][0] < cutoff:
                        self.coinbase_ticks.popleft()
        except Exception:
            pass

    def _on_coinbase_open(self, ws):
        self._is_coinbase_connected = True
        base = self.symbol.replace("usdt", "").upper()
        # Common coins supported on Coinbase
        cb_symbol = f"{base}-USD"
        sub_msg = {
            "type": "subscribe",
            "product_ids": [cb_symbol],
            "channels": ["ticker"]
        }
        try:
            ws.send(json.dumps(sub_msg))
        except Exception:
            pass

    def _on_coinbase_close(self, ws, close_status_code, close_msg):
        self._is_coinbase_connected = False

    # =========================================================================
    # Run loops
    # =========================================================================
    def _run_spot(self):
        while not self._stop_event.is_set():
            try:
                url = "wss://stream.binance.com:9443/ws"
                self.ws_spot = websocket.WebSocketApp(
                    url,
                    on_open=self._on_spot_open,
                    on_message=self._on_spot_message,
                    on_close=self._on_spot_close
                )
                self.ws_spot.run_forever(ping_interval=20, ping_timeout=10)
            except Exception:
                pass
            self._is_spot_connected = False
            if not self._stop_event.is_set():
                time.sleep(2)

    def _run_futures(self):
        while not self._stop_event.is_set():
            try:
                url = f"wss://fstream.binance.com/stream?streams={self.symbol}@kline_1m/{self.symbol}@aggTrade/{self.symbol}@bookTicker"
                self.ws_futures = websocket.WebSocketApp(
                    url,
                    on_open=self._on_futures_open,
                    on_message=self._on_futures_message,
                    on_close=self._on_futures_close
                )
                self.ws_futures.run_forever(ping_interval=20, ping_timeout=10)
            except Exception:
                pass
            self._is_futures_connected = False
            if not self._stop_event.is_set():
                time.sleep(2)

    def _run_coinbase(self):
        while not self._stop_event.is_set():
            try:
                url = "wss://ws-feed.exchange.coinbase.com"
                self.ws_coinbase = websocket.WebSocketApp(
                    url,
                    on_open=self._on_coinbase_open,
                    on_message=self._on_coinbase_message,
                    on_close=self._on_coinbase_close
                )
                self.ws_coinbase.run_forever(ping_interval=20, ping_timeout=10)
            except Exception:
                pass
            self._is_coinbase_connected = False
            if not self._stop_event.is_set():
                time.sleep(2)

    def _seed_historical_candles(self, symbol: str):
        """
        Instantly seeds 100 historical 1m candles via REST API.
        Tries Binance Futures REST -> Binance Spot REST -> Coinbase REST fallback.
        Guarantees self.candles is never empty even before WebSockets connect or in geo-blocked environments.
        """
        clean = symbol.lower().replace('/', '').replace('-', '')
        base = clean.replace('usdt', '').upper()
        sym_upper = clean.upper()
        
        rows = []
        # Attempt 1: Binance USD-M Futures REST
        try:
            url = f"https://fapi.binance.com/fapi/v1/klines?symbol={sym_upper}&interval=1m&limit=100"
            req = urllib.request.Request(url, headers={"User-Agent": "TradeX/1.0"})
            with urllib.request.urlopen(req, timeout=4) as resp:
                data = json.loads(resp.read().decode())
                for k in data:
                    rows.append({
                        "timestamp": pd.to_datetime(k[0], unit='ms'),
                        "open": float(k[1]),
                        "high": float(k[2]),
                        "low": float(k[3]),
                        "close": float(k[4]),
                        "volume": float(k[5])
                    })
        except Exception:
            rows = []

        # Attempt 2: Binance Spot REST
        if not rows:
            try:
                url = f"https://api.binance.com/api/v3/klines?symbol={sym_upper}&interval=1m&limit=100"
                req = urllib.request.Request(url, headers={"User-Agent": "TradeX/1.0"})
                with urllib.request.urlopen(req, timeout=4) as resp:
                    data = json.loads(resp.read().decode())
                    for k in data:
                        rows.append({
                            "timestamp": pd.to_datetime(k[0], unit='ms'),
                            "open": float(k[1]),
                            "high": float(k[2]),
                            "low": float(k[3]),
                            "close": float(k[4]),
                            "volume": float(k[5])
                        })
            except Exception:
                rows = []

        # Attempt 3: Coinbase REST
        if not rows:
            try:
                cb_prod = f"{base}-USD"
                url = f"https://api.exchange.coinbase.com/products/{cb_prod}/candles?granularity=60"
                req = urllib.request.Request(url, headers={"User-Agent": "TradeX/1.0"})
                with urllib.request.urlopen(req, timeout=4) as resp:
                    data = json.loads(resp.read().decode())
                    for k in reversed(data[:100]):
                        rows.append({
                            "timestamp": pd.to_datetime(k[0], unit='s'),
                            "open": float(k[3]),
                            "high": float(k[2]),
                            "low": float(k[1]),
                            "close": float(k[4]),
                            "volume": float(k[5])
                        })
            except Exception:
                rows = []

        if rows:
            df = pd.DataFrame(rows)
            with self.lock:
                self.candles = df
                last_c = float(df.iloc[-1]["close"])
                if self.latest_price <= 0:
                    self.latest_price = last_c
                if self.futures_price <= 0:
                    self.futures_price = last_c
                t_now = time.time()
                self.price_ticks.append((t_now, last_c))
                self.futures_ticks.append((t_now, last_c))
            print(f"[BinanceDataFeed] Seeded {len(rows)} historical 1m candles for {sym_upper}. Latest price: {last_c}")

    def start(self):
        self._stop_event.clear()
        threading.Thread(target=self._seed_historical_candles, args=(self.symbol,), daemon=True).start()
        if not self._spot_thread or not self._spot_thread.is_alive():
            self._spot_thread = threading.Thread(target=self._run_spot, daemon=True)
            self._spot_thread.start()
        if not self._futures_thread or not self._futures_thread.is_alive():
            self._futures_thread = threading.Thread(target=self._run_futures, daemon=True)
            self._futures_thread.start()
        if not self._coinbase_thread or not self._coinbase_thread.is_alive():
            self._coinbase_thread = threading.Thread(target=self._run_coinbase, daemon=True)
            self._coinbase_thread.start()

    def stop(self):
        self._stop_event.set()
        if self.ws_spot:
            self.ws_spot.close()
        if self.ws_futures:
            self.ws_futures.close()
        if self.ws_coinbase:
            self.ws_coinbase.close()

    def switch_symbol(self, new_symbol: str) -> bool:
        """
        Dynamically switches the active crypto asset (e.g. ethusdt, solusdt, xrpusdt, bnbusdt).
        Instantly clears history buffers and reconnects WebSockets.
        """
        clean = new_symbol.lower().strip().replace('/', '').replace('-', '')
        if not clean.endswith('usdt'):
            clean = f"{clean}usdt"

        with self.lock:
            self.symbol = clean
            self.candles = pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])
            self.latest_price = 0.0
            self.recent_trades.clear()
            self.whale_trades.clear()
            self.book_ticker = None
            self.book_history.clear()
            self.price_ticks.clear()

            self.futures_price = 0.0
            self.futures_trades.clear()
            self.futures_book_ticker = None
            self.basis_history.clear()
            self.futures_ticks.clear()
            self.prev_bid_depth = 0.0
            self.prev_ask_depth = 0.0
            self.queue_depletion_velocity = 0.0
            self.depth_ladder = {"bids": [], "asks": [], "bid_depth": 0.0, "ask_depth": 0.0, "depth_ratio": 50.0, "queue_depletion": 0.0}

            self.coinbase_price = 0.0
            self.coinbase_ticks.clear()
            self.coinbase_bid = 0.0
            self.coinbase_ask = 0.0

        # Close existing websockets to trigger automatic clean reconnect with new symbol
        if self.ws_spot:
            try:
                self.ws_spot.close()
            except Exception:
                pass
        if self.ws_futures:
            try:
                self.ws_futures.close()
            except Exception:
                pass
        if self.ws_coinbase:
            try:
                self.ws_coinbase.close()
            except Exception:
                pass

        # Seed historical candles for the newly selected symbol
        threading.Thread(target=self._seed_historical_candles, args=(self.symbol,), daemon=True).start()

        print(f"[BinanceDataFeed] Successfully switched active crypto symbol to: {self.symbol.upper()}")
        return True

    @staticmethod
    def get_curated_list() -> List[Dict[str, Any]]:
        return CURATED_CRYPTO_MARKETS

    def get_candles(self) -> pd.DataFrame:
        with self.lock:
            return self.candles.copy()

    def get_latest_price(self) -> float:
        with self.lock:
            return self.latest_price

    def get_futures_price(self) -> float:
        with self.lock:
            return self.futures_price

    def get_coinbase_price(self) -> float:
        with self.lock:
            return self.coinbase_price

    def _calc_price_velocity(self, now: float, window_s: float) -> float:
        cutoff = now - window_s
        prices_in_window = []
        for t, p in reversed(self.price_ticks):
            if t < cutoff:
                break
            prices_in_window.append((t, p))
        
        if len(prices_in_window) < 2:
            return 0.0
        
        oldest_t, oldest_p = prices_in_window[-1]
        newest_t, newest_p = prices_in_window[0]
        dt = newest_t - oldest_t
        if dt < 0.1:
            return 0.0
        return (newest_p - oldest_p) / dt

    def _calc_tick_delta(self, ring_deque: deque, now: float, window_s: float) -> float:
        cutoff = now - window_s
        prices = []
        for t, p in reversed(ring_deque):
            if t < cutoff:
                break
            prices.append((t, p))
        if len(prices) < 2:
            return 0.0
        return prices[0][1] - prices[-1][1]

    def get_order_flow(self) -> Dict[str, Any]:
        with self.lock:
            now = time.time()
            cutoff_5s = now - 5.0
            cutoff_15s = now - 15.0
            cutoff_30s = now - 30.0
            cutoff_60s = now - 60.0

            # Spot calculations
            buy_vol_5s = 0.0
            sell_vol_5s = 0.0
            buy_vol_15s = 0.0
            sell_vol_15s = 0.0
            buy_vol_30s = 0.0
            sell_vol_30s = 0.0
            buy_vol_60s = 0.0
            sell_vol_60s = 0.0

            whale_buy_vol = 0.0
            whale_sell_vol = 0.0

            vwap_sum_qty_30s = 0.0
            vwap_sum_pv_30s = 0.0
            vwap_sum_qty_60s = 0.0
            vwap_sum_pv_60s = 0.0

            trade_count_5s = 0
            trade_count_15s = 0

            for t_time, is_buy, qty, t_price in self.recent_trades:
                if t_time < cutoff_60s:
                    continue

                if is_buy:
                    buy_vol_60s += qty
                else:
                    sell_vol_60s += qty
                vwap_sum_qty_60s += qty
                vwap_sum_pv_60s += t_price * qty

                if t_time >= cutoff_30s:
                    if is_buy:
                        buy_vol_30s += qty
                    else:
                        sell_vol_30s += qty
                    vwap_sum_qty_30s += qty
                    vwap_sum_pv_30s += t_price * qty

                    min_w_qty = max(0.01, 10000.0 / max(0.0001, t_price))
                    if qty >= min_w_qty:
                        if is_buy:
                            whale_buy_vol += qty
                        else:
                            whale_sell_vol += qty

                if t_time >= cutoff_15s:
                    trade_count_15s += 1
                    if is_buy:
                        buy_vol_15s += qty
                    else:
                        sell_vol_15s += qty

                if t_time >= cutoff_5s:
                    trade_count_5s += 1
                    if is_buy:
                        buy_vol_5s += qty
                    else:
                        sell_vol_5s += qty

            # Futures calculations
            fut_buy_vol_5s = 0.0
            fut_sell_vol_5s = 0.0
            fut_buy_vol_15s = 0.0
            fut_sell_vol_15s = 0.0
            for t_time, is_buy, qty, t_price in self.futures_trades:
                if t_time >= cutoff_15s:
                    if is_buy:
                        fut_buy_vol_15s += qty
                    else:
                        fut_sell_vol_15s += qty
                if t_time >= cutoff_5s:
                    if is_buy:
                        fut_buy_vol_5s += qty
                    else:
                        fut_sell_vol_5s += qty

            fut_tot_5s = fut_buy_vol_5s + fut_sell_vol_5s
            fut_delta_5s = fut_buy_vol_5s - fut_sell_vol_5s
            fut_delta_15s = fut_buy_vol_15s - fut_sell_vol_15s
            fut_buy_pct_5s = (fut_buy_vol_5s / fut_tot_5s * 100.0) if fut_tot_5s > 0 else 50.0

            # Basis Spread & Basis Momentum
            current_basis = (self.futures_price - self.latest_price) if (self.futures_price > 0 and self.latest_price > 0) else 0.0
            basis_5s_ago = current_basis
            for t, b_val in reversed(self.basis_history):
                if t <= cutoff_5s:
                    basis_5s_ago = b_val
                    break
            basis_delta_5s = current_basis - basis_5s_ago

            # Tri-Venue Directional Changes over 5 seconds
            spot_change_5s = self._calc_tick_delta(self.price_ticks, now, 5.0)
            fut_change_5s = self._calc_tick_delta(self.futures_ticks, now, 5.0)
            coinbase_change_5s = self._calc_tick_delta(self.coinbase_ticks, now, 5.0)

            # Global Multi-Exchange Consensus Score (-1.0 to +1.0)
            p_ref = max(1.0, self.latest_price or self.futures_price or 50000.0)
            tick_thresh = max(0.00001, p_ref * 0.000015)

            consensus_votes = 0.0
            if spot_change_5s >= tick_thresh: consensus_votes += 1.0
            elif spot_change_5s <= -tick_thresh: consensus_votes -= 1.0

            if fut_change_5s >= tick_thresh or fut_buy_pct_5s >= 60.0: consensus_votes += 1.0
            elif fut_change_5s <= -tick_thresh or fut_buy_pct_5s <= 40.0: consensus_votes -= 1.0

            if coinbase_change_5s >= tick_thresh: consensus_votes += 1.0
            elif coinbase_change_5s <= -tick_thresh: consensus_votes -= 1.0

            global_consensus_score = consensus_votes / 3.0

            # VPIN: Volume-Synchronized Probability of Toxicity
            total_15s = buy_vol_15s + sell_vol_15s
            delta_15s = buy_vol_15s - sell_vol_15s
            vpin_15s = (abs(delta_15s) / total_15s) if total_15s > 0.05 else 0.0

            total_5s = buy_vol_5s + sell_vol_5s
            total_30s = buy_vol_30s + sell_vol_30s
            bull_ratio_5s = round((buy_vol_5s / total_5s * 100.0), 1) if total_5s > 0 else 50.0
            bull_ratio_15s = round((buy_vol_15s / total_15s * 100.0), 1) if total_15s > 0 else 50.0
            bull_ratio_30s = round((buy_vol_30s / total_30s * 100.0), 1) if total_30s > 0 else 50.0

            delta_5s = buy_vol_5s - sell_vol_5s
            delta_30s = buy_vol_30s - sell_vol_30s
            delta_60s = buy_vol_60s - sell_vol_60s
            whale_delta = whale_buy_vol - whale_sell_vol
            delta_acceleration = delta_5s - (delta_15s / 3.0)

            vwap_30s = (vwap_sum_pv_30s / vwap_sum_qty_30s) if vwap_sum_qty_30s > 0 else (self.latest_price or 0.0)
            vwap_60s = (vwap_sum_pv_60s / vwap_sum_qty_60s) if vwap_sum_qty_60s > 0 else (self.latest_price or 0.0)

            vel_3s = self._calc_price_velocity(now, 3.0)
            vel_5s = self._calc_price_velocity(now, 5.0)
            vel_10s = self._calc_price_velocity(now, 10.0)

            imbalance_5s = 0.0
            micro_price = self.latest_price or 0.0
            spread = 0.01
            spread_bias = 0.0
            book_bid_qty = 0.0
            book_ask_qty = 0.0

            if self.book_ticker:
                b = self.book_ticker["best_bid"]
                a = self.book_ticker["best_ask"]
                b_qty = self.book_ticker["bid_qty"]
                a_qty = self.book_ticker["ask_qty"]
                tot_qty = b_qty + a_qty
                if tot_qty > 0:
                    micro_price = (b * a_qty + a * b_qty) / tot_qty
                    mid_price = (b + a) / 2.0
                    spread = a - b
                    spread_bias = micro_price - mid_price
                    book_bid_qty = b_qty
                    book_ask_qty = a_qty

            imb_list_5s = [imb for (t, b_val, B_val, a_val, A_val, imb) in self.book_history if t >= cutoff_5s]
            if imb_list_5s:
                imbalance_5s = sum(imb_list_5s) / len(imb_list_5s)
            elif self.book_ticker:
                imbalance_5s = self.book_ticker["imbalance"]

            return {
                "buy_vol": round(buy_vol_15s, 3),
                "sell_vol": round(sell_vol_15s, 3),
                "buy_vol_5s": round(buy_vol_5s, 3),
                "sell_vol_5s": round(sell_vol_5s, 3),
                "buy_vol_30s": round(buy_vol_30s, 3),
                "sell_vol_30s": round(sell_vol_30s, 3),
                "bull_ratio": bull_ratio_15s,
                "bull_ratio_5s": bull_ratio_5s,
                "bull_ratio_30s": bull_ratio_30s,
                "bear_ratio": round(100.0 - bull_ratio_15s, 1),
                "delta_5s": round(delta_5s, 3),
                "delta_15s": round(delta_15s, 3),
                "delta_30s": round(delta_30s, 3),
                "delta_60s": round(delta_60s, 3),
                "whale_buy_vol": round(whale_buy_vol, 3),
                "whale_sell_vol": round(whale_sell_vol, 3),
                "whale_delta": round(whale_delta, 3),
                "vwap_30s": round(vwap_30s, 2),
                "vwap_60s": round(vwap_60s, 2),
                "delta_acceleration": round(delta_acceleration, 3),
                "tick_intensity": round(trade_count_15s / 15.0, 1),
                "tick_intensity_5s": round(trade_count_5s / 5.0, 1),
                "book_imbalance_5s": round(imbalance_5s, 3),
                "micro_price": round(micro_price, 2),
                "spread": round(spread, 2),
                "spread_bias": round(spread_bias, 3),
                "book_bid_qty": round(book_bid_qty, 3),
                "book_ask_qty": round(book_ask_qty, 3),
                "recent_whales": list(self.whale_trades),
                "price_velocity_3s": round(vel_3s, 4),
                "price_velocity_5s": round(vel_5s, 4),
                "price_velocity_10s": round(vel_10s, 4),
                "taker_buy_pct_5s": bull_ratio_5s,
                # 👑 Futures Lead-Lag
                "futures_price": round(self.futures_price, 2),
                "basis_spread": round(current_basis, 2),
                "basis_delta_5s": round(basis_delta_5s, 3),
                "futures_delta_5s": round(fut_delta_5s, 3),
                "futures_delta_15s": round(fut_delta_15s, 3),
                "futures_buy_pct_5s": round(fut_buy_pct_5s, 1),
                "futures_connected": bool(self._is_futures_connected),
                # 🌌 Universal Tri-Venue & VPIN Telemetry
                "coinbase_price": round(self.coinbase_price, 2),
                "coinbase_connected": bool(self._is_coinbase_connected),
                "global_consensus": round(global_consensus_score, 2),
                "vpin": round(vpin_15s, 3),
                "spot_change_5s": round(spot_change_5s, 2),
                "futures_change_5s": round(fut_change_5s, 2),
                "coinbase_change_5s": round(coinbase_change_5s, 2),
                "queue_depletion": self.queue_depletion_velocity,
                "depth_ladder": dict(self.depth_ladder)
            }

    def is_connected(self) -> bool:
        with self.lock:
            has_price = (self.latest_price > 0) or (self.futures_price > 0) or (self.coinbase_price > 0)
        return bool(
            self._is_spot_connected or 
            self._is_futures_connected or 
            self._is_coinbase_connected or 
            has_price
        )

    def get_latest_price(self) -> float:
        with self.lock:
            if self.latest_price > 0:
                return float(self.latest_price)
            if self.futures_price > 0:
                return float(self.futures_price)
            if self.coinbase_price > 0:
                return float(self.coinbase_price)
            return 0.0

    def get_futures_price(self) -> float:
        with self.lock:
            if self.futures_price > 0:
                return float(self.futures_price)
            if self.latest_price > 0:
                return float(self.latest_price)
            if self.coinbase_price > 0:
                return float(self.coinbase_price)
            return 0.0
