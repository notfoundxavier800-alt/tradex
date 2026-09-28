import os
import sys
import time
import math
import threading
from datetime import datetime, timezone
from flask import Flask, render_template, request, send_file
from flask_socketio import SocketIO

# UTF-8 line-buffered stdout and stderr on Windows
sys.stdout.reconfigure(line_buffering=True, encoding='utf-8', errors='replace')
sys.stderr.reconfigure(line_buffering=True, encoding='utf-8', errors='replace')

from data_feed import BinanceDataFeed, CURATED_CRYPTO_MARKETS
from indian_market_feed import IndianMarketFeed, CURATED_INDIAN_MARKETS
from international_market_feed import InternationalMarketFeed, CURATED_INTERNATIONAL_MARKETS
from analysis import TechnicalAnalyzer
from signal_engine import SignalEngine
from round_manager import RoundManager
import notifier
from ai_agents_hub import ai_hub

# ---------------------------------------------------------------------------
# Flask / Socket.IO setup (threading mode)
# ---------------------------------------------------------------------------
app = Flask(__name__)
app.config["SECRET_KEY"] = "cwallet-signal-bot-secret"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# ---------------------------------------------------------------------------
# Core components & Multi-Market State
# ---------------------------------------------------------------------------
crypto_feed: BinanceDataFeed | None = None
indian_feed: IndianMarketFeed | None = None
international_feed: InternationalMarketFeed | None = None
analyzer: TechnicalAnalyzer | None = None
signal_engine: SignalEngine | None = None
round_manager: RoundManager = RoundManager(round_duration=20, lead_time=5.0)
_running = False

active_market_type: str = "crypto"  # "crypto" or "indian"
active_symbol: str = "btcusdt"
active_name: str = "Bitcoin (BTC)"
active_currency_symbol: str = "$"
zero_defect_mode: bool = False
crypto_price_source: str = "auto"  # "auto", "futures", "spot"

# ---------------------------------------------------------------------------
# CORS & Network Headers
# ---------------------------------------------------------------------------
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS, PUT, DELETE"
    response.headers["Access-Control-Allow-Private-Network"] = "true"
    return response

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("dashboard.html")

@app.route("/download/apk")
@app.route("/apk")
@app.route("/download-apk")
@app.route("/tradex.apk")
def download_apk():
    # Serve the signed Android APK for instant mobile download
    possible_paths = [
        os.path.join(os.path.dirname(__file__), "static", "tradex.apk"),
        os.path.join(os.path.dirname(__file__), "tradex.apk"),
        r"C:\Users\divya\Desktop\tradex.apk",
        os.path.join(os.path.dirname(__file__), "static", "Cwallet-Signal-Bot.apk"),
        os.path.join(os.path.dirname(__file__), "Cwallet-Signal-Bot.apk"),
        r"C:\Users\divya\Desktop\Cwallet-Signal-Bot.apk"
    ]
    for p in possible_paths:
        if os.path.exists(p):
            return send_file(p, as_attachment=True, download_name="tradex.apk", mimetype="application/vnd.android.package-archive")
    return {"error": "APK file not found"}, 404

@app.route("/api/status")
def api_status():
    if active_market_type == "indian":
        feed = indian_feed
    elif active_market_type == "international":
        feed = international_feed
    else:
        feed = crypto_feed
    connected = feed.is_connected() if feed else False
    return {
        "status": "running" if _running else "stopped",
        "market_type": active_market_type,
        "symbol": active_symbol,
        "name": active_name,
        "currency_symbol": active_currency_symbol,
        "connected": connected,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

@app.route("/api/market_list")
def api_market_list():
    intl_status = InternationalMarketFeed.get_market_status(active_symbol) if active_market_type == "international" else InternationalMarketFeed.get_market_status("^GSPC")
    return {
        "active_type": active_market_type,
        "active_symbol": active_symbol,
        "active_name": active_name,
        "currency_symbol": active_currency_symbol,
        "crypto_markets": CURATED_CRYPTO_MARKETS,
        "indian_markets": CURATED_INDIAN_MARKETS,
        "international_markets": CURATED_INTERNATIONAL_MARKETS,
        "indian_market_status": IndianMarketFeed.get_market_status(),
        "international_market_status": intl_status
    }

@app.route("/api/search_symbol")
def api_search_symbol():
    q = request.args.get("q", "").strip().upper()
    if not q:
        return {"results": []}

    results = []
    # 1. Search Indian Markets
    for m in CURATED_INDIAN_MARKETS:
        if q in m["symbol"].upper() or q in m["name"].upper():
            results.append({
                "market_type": "indian",
                "symbol": m["symbol"],
                "name": m["name"],
                "exchange": m["exchange"],
                "currency_symbol": "₹"
            })

    # 2. Search Crypto Markets
    for m in CURATED_CRYPTO_MARKETS:
        if q in m["symbol"].upper() or q in m["name"].upper() or q in m["ticker"]:
            results.append({
                "market_type": "crypto",
                "symbol": m["symbol"],
                "name": f"{m['name']} ({m['ticker']})",
                "exchange": "Binance",
                "currency_symbol": "$"
            })

    # 3. Search International Markets
    for m in CURATED_INTERNATIONAL_MARKETS:
        if q in m["symbol"].upper() or q in m["name"].upper() or q in m.get("category", "").upper():
            results.append({
                "market_type": "international",
                "symbol": m["symbol"],
                "name": m["name"],
                "exchange": m["exchange"],
                "currency_symbol": m["currency_symbol"]
            })

    # 4. Dynamic Custom Symbol Search if not already found
    if not any(r["symbol"] == q for r in results):
        if q.endswith(".NS") or q.endswith(".BO") or q.startswith("^NSE") or q.startswith("^BSE"):
            results.append({
                "market_type": "indian",
                "symbol": q,
                "name": f"Indian Stock ({q})",
                "exchange": "NSE/BSE",
                "currency_symbol": "₹"
            })
        else:
            curr = "¥" if "JPY" in q else ("€" if "EUR" in q or "DAX" in q or "GDAXI" in q else ("£" if "FTSE" in q or "GBP" in q else "$"))
            results.append({
                "market_type": "international",
                "symbol": q,
                "name": f"International Asset ({q})",
                "exchange": "Global Markets",
                "currency_symbol": curr
            })

    return {"results": results[:14]}

@app.route("/api/switch_symbol", methods=["POST"])
def api_switch_symbol():
    global active_market_type, active_symbol, active_name, active_currency_symbol
    try:
        data = request.get_json(force=True, silent=True) or {}
        m_type = data.get("market_type", "crypto").lower()
        sym = data.get("symbol", "").strip()

        if not sym:
            return {"error": "Missing symbol parameter"}, 400

        if m_type == "indian":
            if not indian_feed:
                return {"error": "Indian market feed not initialized"}, 500
            success = indian_feed.switch_symbol(sym)
            if not success:
                return {"error": f"Could not find Indian stock '{sym}'"}, 404
            
            m_info = indian_feed.get_market_info()
            active_market_type = "indian"
            active_symbol = m_info["symbol"]
            active_name = m_info["name"]
            active_currency_symbol = m_info["currency_symbol"]
            candles = indian_feed.get_candles()
        elif m_type == "international":
            if not international_feed:
                return {"error": "International market feed not initialized"}, 500
            success = international_feed.switch_symbol(sym)
            if not success:
                return {"error": f"Could not find International market '{sym}'"}, 404
            
            m_info = international_feed.get_market_info()
            active_market_type = "international"
            active_symbol = m_info["symbol"]
            active_name = m_info["name"]
            active_currency_symbol = m_info["currency_symbol"]
            candles = international_feed.get_candles()
        else:
            if not crypto_feed:
                return {"error": "Crypto feed not initialized"}, 500
            clean_sym = sym.lower().replace("/", "").replace("-", "")
            if not clean_sym.endswith("usdt"):
                clean_sym = f"{clean_sym}usdt"
            crypto_feed.switch_symbol(clean_sym)
            active_market_type = "crypto"
            active_symbol = clean_sym
            active_currency_symbol = "$"
            active_name = active_symbol.upper()
            for item in CURATED_CRYPTO_MARKETS:
                if item["symbol"].lower() == clean_sym.lower():
                    active_name = f"{item['name']} ({item['ticker']})"
                    break
            candles = crypto_feed.get_candles()

        # Reset signal engine state so market switches start completely fresh
        if signal_engine:
            signal_engine.reset_state()

        # Build initial candle history
        history_list = []
        if candles is not None and not candles.empty:
            for _, row in candles.iterrows():
                try:
                    t = int(row["timestamp"].timestamp()) if hasattr(row["timestamp"], "timestamp") else int(time.time())
                    history_list.append({
                        "time": t,
                        "open": float(row["open"]),
                        "high": float(row["high"]),
                        "low": float(row["low"]),
                        "close": float(row["close"]),
                    })
                except Exception:
                    continue

        payload = {
            "market_type": active_market_type,
            "symbol": active_symbol,
            "name": active_name,
            "currency_symbol": active_currency_symbol,
            "candles": history_list
        }
        socketio.emit("market_switched", payload)
        return {"status": "ok", **payload}

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"[api_switch_symbol ERROR]\n{tb}")
        return {"error": str(e), "traceback": tb}, 500

@app.route("/api/live")
def api_live():
    try:
        if active_market_type == "indian":
            feed = indian_feed
            market_info = indian_feed.get_market_info() if indian_feed else None
        elif active_market_type == "international":
            feed = international_feed
            market_info = international_feed.get_market_info() if international_feed else None
        else:
            feed = crypto_feed
            market_info = None

        candles = feed.get_candles() if feed else None
        order_flow = feed.get_order_flow() if feed else None
        history = signal_engine.get_signal_history() if signal_engine else []

        spot_p = crypto_feed.get_latest_price() if crypto_feed else 0
        fut_p = crypto_feed.get_futures_price() if crypto_feed else 0
        k_ref = round_manager.external_strike if (round_manager and round_manager.external_strike) else None
        if crypto_price_source == "futures":
            cur_p = fut_p if fut_p > 0 else spot_p
        elif crypto_price_source == "spot":
            cur_p = spot_p if spot_p > 0 else fut_p
        else:
            if k_ref and k_ref > 0 and fut_p > 0 and spot_p > 0:
                cur_p = fut_p if abs(k_ref - fut_p) < abs(k_ref - spot_p) else spot_p
            else:
                cur_p = spot_p if spot_p > 0 else fut_p

        return {
            "market_type": active_market_type,
            "symbol": active_symbol,
            "name": active_name,
            "currency_symbol": active_currency_symbol,
            "connected": feed.is_connected() if feed else False,
            "candles": len(candles) if candles is not None else 0,
            "price": cur_p if active_market_type == "crypto" else (feed.get_latest_price() if feed else 0),
            "spot_price": spot_p,
            "futures_price": fut_p,
            "price_source": crypto_price_source,
            "order_flow": order_flow,
            "market_info": market_info,
            "cwallet_round": round_manager.get_state(cur_p if active_market_type == "crypto" else (feed.get_latest_price() if feed else 0)) if round_manager else None,
            "last_signal": history[-1] if history else None,
            "stats": signal_engine.get_accuracy_stats() if signal_engine else {},
            "zero_defect_mode": zero_defect_mode
        }
    except Exception as e:
        return {"error": str(e)}, 500

@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.route("/api/test-notification")
def api_test_notification():
    return {"status": "ok"}

@app.route("/api/sync_cwallet", methods=["POST", "OPTIONS"])
def api_sync_cwallet():
    if request.method == "OPTIONS":
        return "", 204
    try:
        data = request.get_json(force=True, silent=True) or {}
        sec = data.get("seconds_left")
        p = data.get("open_price")
        rnd = data.get("round_number")
        dur = data.get("round_duration")
        lead = data.get("lead_time")
        offset = data.get("sync_offset")
        phase = data.get("phase")

        spot_p = crypto_feed.get_latest_price() if crypto_feed else 0.0
        fut_p = crypto_feed.get_futures_price() if crypto_feed else 0.0
        k_ref = round_manager.external_strike if (round_manager and round_manager.external_strike) else None
        target_k = float(p) if (p and float(p) > 0) else k_ref
        if crypto_price_source == "futures":
            curr_p = fut_p if fut_p > 0 else spot_p
        elif crypto_price_source == "spot":
            curr_p = spot_p if spot_p > 0 else fut_p
        else: # "auto"
            if target_k and target_k > 0 and fut_p > 0 and spot_p > 0:
                curr_p = fut_p if abs(target_k - fut_p) < abs(target_k - spot_p) else spot_p
            else:
                curr_p = spot_p if spot_p > 0 else fut_p

        if dur:
            round_manager.set_duration(int(dur))
        if lead:
            round_manager.set_lead_time(float(lead))
        round_manager.manual_sync(
            seconds_left=float(sec) if sec is not None else None,
            open_price=float(p) if p is not None and float(p) > 0 else None,
            round_number=int(rnd) if rnd is not None else None,
            sync_offset=int(offset) if offset is not None else None,
            current_price=curr_p,
            phase=phase
        )
        t_state = round_manager.tick(curr_p)
        socketio.emit("cwallet_round_update", t_state)
        return {"status": "ok", "state": t_state}
    except Exception as e:
        return {"error": str(e)}, 400

@app.route("/api/set_crypto_price_source", methods=["POST", "OPTIONS"])
def api_set_crypto_price_source():
    global crypto_price_source
    if request.method == "OPTIONS":
        return "", 204
    try:
        data = request.get_json(force=True, silent=True) or {}
        src = data.get("source", "auto")
        if src in ("auto", "futures", "spot"):
            crypto_price_source = src
            socketio.emit("price_source_switched", {"price_source": crypto_price_source})
        return {"status": "ok", "price_source": crypto_price_source}
    except Exception as e:
        return {"error": str(e)}, 400

@app.route("/api/cwallet_state")
def api_cwallet_state():
    curr_p = crypto_feed.get_latest_price() if crypto_feed else 0.0
    return round_manager.get_state(curr_p)

@app.route("/api/settle_round", methods=["POST"])
def api_settle_round():
    try:
        data = request.get_json(force=True, silent=True) or {}
        strike = float(data.get("strike", 0.0))
        close_price = float(data.get("close_price", 0.0))
        round_id = data.get("round_id", round_manager.last_round_id)
        res = round_manager.settle_round(strike=strike, close_price=close_price)
        last_pred = round_manager.get_last_sniper_direction(round_id)
        won = (last_pred == res["outcome"]) if last_pred in ("UP", "DOWN") else (res["outcome"] == "UP")
        settled_payload = {
            "round_id": round_id,
            "strike": res["strike"],
            "close_price": res["close_price"],
            "outcome": res["outcome"],
            "won": won
        }
        socketio.emit("cwallet_round_settled", settled_payload)
        return {"status": "ok", "settlement": settled_payload}
    except Exception as e:
        return {"error": str(e)}, 400

@app.route("/api/toggle_zero_defect", methods=["GET", "POST"])
def api_toggle_zero_defect():
    global zero_defect_mode
    if request.method == "POST":
        data = request.get_json(force=True, silent=True) or {}
        if "enabled" in data:
            zero_defect_mode = bool(data["enabled"])
        else:
            zero_defect_mode = not zero_defect_mode
    else:
        if request.args.get("toggle") == "1":
            zero_defect_mode = not zero_defect_mode
        elif "enabled" in request.args:
            zero_defect_mode = request.args.get("enabled").lower() in ("true", "1", "yes")

    if signal_engine:
        signal_engine.set_zero_defect_mode(zero_defect_mode)
    socketio.emit("zero_defect_mode_switched", {"zero_defect_mode": zero_defect_mode})
    return {"status": "ok", "zero_defect_mode": zero_defect_mode}

# ---------------------------------------------------------------------------
# AI Multi-Agent & Investor Council Endpoints (TradingAgents + AI Hedge Fund)
# ---------------------------------------------------------------------------
@app.route("/api/ai/status")
def api_ai_status():
    return ai_hub.get_status()

def _extract_tech_summary(last_sig):
    if not isinstance(last_sig, dict):
        return {"overall_bias": "UP", "score": 0.0, "rsi": 50.0, "adx": 25.0}
    direction = last_sig.get("direction", "UP")
    score = last_sig.get("composite_score", last_sig.get("score", 0.0))
    inds = last_sig.get("indicators", {})
    rsi = 50.0
    adx = 25.0
    if isinstance(inds, dict):
        rsi = inds.get("rsi", 50.0)
        adx = inds.get("adx", 25.0)
    elif isinstance(inds, list):
        for item in inds:
            if isinstance(item, dict):
                if item.get("name") == "rsi" or "rsi" in item:
                    rsi = item.get("value", item.get("rsi", 50.0))
                if item.get("name") == "adx" or "adx" in item:
                    adx = item.get("value", item.get("adx", 25.0))
    return {
        "overall_bias": direction,
        "score": float(score) if isinstance(score, (int, float)) else 0.0,
        "rsi": float(rsi) if isinstance(rsi, (int, float)) else 50.0,
        "adx": float(adx) if isinstance(adx, (int, float)) else 25.0,
    }

@app.route("/api/ai/consensus")
def api_ai_consensus():
    try:
        sym = request.args.get("symbol", active_symbol).strip().upper()
        force = request.args.get("force", "0") in ("1", "true", "True") or request.args.get("refresh", "0") in ("1", "true", "True")
        if not force:
            cached = ai_hub.get_cached_analysis(sym)
            if cached:
                return {"status": "ok", "cached": True, **cached}
        
        feed = indian_feed if active_market_type == "indian" else (international_feed if active_market_type == "international" else crypto_feed)
        curr_p = feed.get_latest_price() if (feed and hasattr(feed, "get_latest_price")) else 0.0
        history = signal_engine.get_signal_history() if signal_engine else []
        last_sig = history[-1] if history else {}
        tech = _extract_tech_summary(last_sig)
        result = ai_hub.evaluate_symbol_sync(
            symbol=sym,
            market_type=active_market_type,
            current_price=curr_p,
            technical_summary=tech
        )
        return {"status": "ok", "cached": False, **result}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "error": str(e)}, 500


@app.route("/api/ai/analyze", methods=["POST"])
def api_ai_analyze():
    data = request.get_json(force=True, silent=True) or {}
    sym = data.get("symbol", active_symbol).strip().upper()
    feed = indian_feed if active_market_type == "indian" else (international_feed if active_market_type == "international" else crypto_feed)
    curr_p = feed.get_latest_price() if feed else 0.0
    history = signal_engine.get_signal_history() if signal_engine else []
    last_sig = history[-1] if history else {}
    tech = _extract_tech_summary(last_sig)

    def _on_done(res):
        socketio.emit("ai_analysis_complete", res)

    ai_hub.evaluate_symbol_async(
        symbol=sym,
        market_type=active_market_type,
        current_price=curr_p,
        technical_summary=tech,
        callback=_on_done
    )
    return {"status": "started", "symbol": sym, "market_type": active_market_type}


@app.route("/api/ai/investors")
def api_ai_investors():
    sym = request.args.get("symbol", active_symbol).strip().upper()
    cached = ai_hub.get_cached_analysis(sym)
    if cached and "investor_council" in cached:
        return {"status": "ok", "symbol": sym, "investors": cached["investor_council"]}
    
    feed = indian_feed if active_market_type == "indian" else (international_feed if active_market_type == "international" else crypto_feed)
    curr_p = feed.get_latest_price() if feed else 0.0
    res = ai_hub.evaluate_symbol_sync(sym, active_market_type, curr_p)
    return {"status": "ok", "symbol": sym, "investors": res.get("investor_council", {})}

@app.route("/api/ai/config", methods=["GET", "POST"])
def api_ai_config():
    if request.method == "POST":
        data = request.get_json(force=True, silent=True) or {}
        if "gemini_key" in data and data["gemini_key"]:
            os.environ["GOOGLE_API_KEY"] = data["gemini_key"]
            os.environ["GEMINI_API_KEY"] = data["gemini_key"]
        if "openai_key" in data and data["openai_key"]:
            os.environ["OPENAI_API_KEY"] = data["openai_key"]
        if "anthropic_key" in data and data["anthropic_key"]:
            os.environ["ANTHROPIC_API_KEY"] = data["anthropic_key"]
        if "deepseek_key" in data and data["deepseek_key"]:
            os.environ["DEEPSEEK_API_KEY"] = data["deepseek_key"]
        ai_hub._detect_environment()
        socketio.emit("ai_config_updated", ai_hub.get_status())
        return {"status": "ok", "config": ai_hub.get_status()}
    return {"status": "ok", "config": ai_hub.get_status()}

# ---------------------------------------------------------------------------
# Socket.IO events
# ---------------------------------------------------------------------------
@socketio.on("connect")

def handle_connect():
    socketio.emit("zero_defect_mode_switched", {"zero_defect_mode": zero_defect_mode})
    feed = indian_feed if active_market_type == "indian" else crypto_feed
    if feed and feed.is_connected():
        price = feed.get_latest_price()
        if price:
            socketio.emit("price_update", {
                "price": price,
                "currency_symbol": active_currency_symbol,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        candles = feed.get_candles()
        if candles is not None and not candles.empty:
            history_list = []
            for _, row in candles.iterrows():
                try:
                    t = int(row["timestamp"].timestamp()) if hasattr(row["timestamp"], "timestamp") else int(time.time())
                    history_list.append({
                        "time": t,
                        "open": float(row["open"]),
                        "high": float(row["high"]),
                        "low": float(row["low"]),
                        "close": float(row["close"]),
                    })
                except Exception:
                    continue
            if history_list:
                socketio.emit("candle_history", history_list)

    if signal_engine:
        history = signal_engine.get_signal_history()
        if history:
            socketio.emit("signal_update", history[-1])

    # Send initial market info
    socketio.emit("market_switched", {
        "market_type": active_market_type,
        "symbol": active_symbol,
        "name": active_name,
        "currency_symbol": active_currency_symbol
    })

@socketio.on("sync_cwallet")
def handle_sync_cwallet(data):
    if isinstance(data, dict):
        try:
            sec = data.get("seconds_left")
            p = data.get("open_price")
            rnd = data.get("round_number")
            dur = data.get("round_duration")
            lead = data.get("lead_time")
            offset = data.get("sync_offset")
            phase = data.get("phase")

            spot_p = crypto_feed.get_latest_price() if crypto_feed else 0.0
            fut_p = crypto_feed.get_futures_price() if crypto_feed else 0.0
            k_ref = round_manager.external_strike if (round_manager and round_manager.external_strike) else None
            target_k = float(p) if (p and float(p) > 0) else k_ref
            if crypto_price_source == "futures":
                curr_p = fut_p if fut_p > 0 else spot_p
            elif crypto_price_source == "spot":
                curr_p = spot_p if spot_p > 0 else fut_p
            else: # "auto"
                if target_k and target_k > 0 and fut_p > 0 and spot_p > 0:
                    curr_p = fut_p if abs(target_k - fut_p) < abs(target_k - spot_p) else spot_p
                else:
                    curr_p = spot_p if spot_p > 0 else fut_p

            if dur:
                round_manager.set_duration(int(dur))
            if lead:
                round_manager.set_lead_time(float(lead))
            round_manager.manual_sync(
                seconds_left=float(sec) if sec is not None else None,
                open_price=float(p) if p is not None and float(p) > 0 else None,
                round_number=int(rnd) if rnd is not None else None,
                sync_offset=int(offset) if offset is not None else None,
                current_price=curr_p,
                phase=phase
            )
            socketio.emit("cwallet_round_update", round_manager.tick(curr_p))
        except Exception:
            pass

@socketio.on("set_crypto_price_source")
def handle_set_crypto_price_source(data):
    global crypto_price_source
    if isinstance(data, dict) and "source" in data:
        src = data["source"]
        if src in ("auto", "futures", "spot"):
            crypto_price_source = src
            socketio.emit("price_source_switched", {"price_source": crypto_price_source})

@socketio.on("lock_strike")
def handle_lock_strike(data):
    if isinstance(data, dict):
        try:
            p = data.get("price") or data.get("open_price")
            if p and float(p) > 0:
                round_manager.lock_strike(float(p))
                curr_p = crypto_feed.get_latest_price() if crypto_feed else 0.0
                socketio.emit("cwallet_round_update", round_manager.tick(curr_p))
        except Exception:
            pass

@socketio.on("settle_round")
def handle_settle_round(data):
    if isinstance(data, dict):
        try:
            strike = float(data.get("strike", 0.0))
            close_price = float(data.get("close_price", 0.0))
            round_id = data.get("round_id", round_manager.last_round_id)
            res = round_manager.settle_round(strike=strike, close_price=close_price)
            last_pred = round_manager.get_last_sniper_direction(round_id)
            won = (last_pred == res["outcome"]) if last_pred in ("UP", "DOWN") else (res["outcome"] == "UP")
            settled_payload = {
                "round_id": round_id,
                "strike": res["strike"],
                "close_price": res["close_price"],
                "outcome": res["outcome"],
                "won": won
            }
            socketio.emit("cwallet_round_settled", settled_payload)
            curr_p = crypto_feed.get_latest_price() if crypto_feed else 0.0
            socketio.emit("cwallet_round_update", round_manager.get_state(curr_p))
        except Exception:
            pass

@socketio.on("toggle_zero_defect")
def handle_toggle_zero_defect(data=None):
    global zero_defect_mode
    if isinstance(data, dict) and "enabled" in data:
        zero_defect_mode = bool(data["enabled"])
    else:
        zero_defect_mode = not zero_defect_mode
    if signal_engine:
        signal_engine.set_zero_defect_mode(zero_defect_mode)
    socketio.emit("zero_defect_mode_switched", {"zero_defect_mode": zero_defect_mode})

@socketio.on("request_ai_analysis")
def handle_request_ai_analysis(data=None):
    try:
        sym = (data.get("symbol") if isinstance(data, dict) else None) or active_symbol
        feed = indian_feed if active_market_type == "indian" else (international_feed if active_market_type == "international" else crypto_feed)
        curr_p = feed.get_latest_price() if (feed and hasattr(feed, "get_latest_price")) else 0.0
        history = signal_engine.get_signal_history() if signal_engine else []
        last_sig = history[-1] if history else {}
        tech = _extract_tech_summary(last_sig)

        def _emit_result(res):
            try:
                socketio.emit("ai_analysis_complete", res)
            except Exception as emit_err:
                print(f"[Socket.IO AI emit error]: {emit_err}")

        ai_hub.evaluate_symbol_async(
            symbol=sym,
            market_type=active_market_type,
            current_price=curr_p,
            technical_summary=tech,
            callback=_emit_result
        )
    except Exception as e:
        print(f"[handle_request_ai_analysis error]: {e}")


# ---------------------------------------------------------------------------
# Background signal loop
# ---------------------------------------------------------------------------
def _signal_loop(interval: float = 1.0):
    global _running
    _running = True
    last_price_by_sym = {}
    print(f"[Signal Loop] Universal Quant Engine analysing every {interval}s")
    next_deadline = time.time() + interval

    while _running:
        try:
            sym_key = f"{active_market_type}:{active_symbol}"
            if active_market_type == "indian":
                # --- INDIAN STOCK MARKET MODE ---
                if indian_feed and indian_feed.is_connected():
                    current_price = indian_feed.get_latest_price() or 0.0
                    m_info = indian_feed.get_market_info()
                    candles = indian_feed.get_candles()
                    order_flow = indian_feed.get_order_flow()

                    if candles is not None and len(candles) >= 3:
                        result = signal_engine.generate_signal(
                            candles,
                            order_flow=order_flow,
                            is_equity=True,
                            market_info=m_info
                        )
                        result["market_type"] = "indian"
                        result["symbol"] = active_symbol
                        result["name"] = active_name
                        result["currency_symbol"] = "₹"
                        result["market_status"] = m_info["market_status"]
                        socketio.emit("signal_update", result)

                        if current_price:
                            p_dir = "neutral"
                            prev_p = last_price_by_sym.get(sym_key)
                            if prev_p is not None:
                                if current_price > prev_p: p_dir = "up"
                                elif current_price < prev_p: p_dir = "down"
                            last_price_by_sym[sym_key] = current_price
                            socketio.emit("price_update", {
                                "price": current_price,
                                "direction": p_dir,
                                "currency_symbol": "₹",
                                "timestamp": datetime.now(timezone.utc).isoformat()
                            })

                        if len(candles) > 0:
                            lc = candles.iloc[-1]
                            t = int(lc["timestamp"].timestamp()) if hasattr(lc["timestamp"], "timestamp") else int(time.time())
                            socketio.emit("candle_update", {
                                "time": t,
                                "open": float(lc["open"]),
                                "high": float(lc["high"]),
                                "low": float(lc["low"]),
                                "close": float(lc["close"]),
                            })

            elif active_market_type == "international":
                # --- INTERNATIONAL MARKET MODE ---
                if international_feed and international_feed.is_connected():
                    current_price = international_feed.get_latest_price() or 0.0
                    m_info = international_feed.get_market_info()
                    candles = international_feed.get_candles()
                    order_flow = international_feed.get_order_flow()

                    if candles is not None and len(candles) >= 3:
                        result = signal_engine.generate_signal(
                            candles,
                            order_flow=order_flow,
                            is_equity=True,
                            market_info=m_info
                        )
                        result["market_type"] = "international"
                        result["symbol"] = active_symbol
                        result["name"] = active_name
                        result["currency_symbol"] = active_currency_symbol
                        result["market_status"] = m_info["market_status"]
                        socketio.emit("signal_update", result)

                        if current_price:
                            p_dir = "neutral"
                            prev_p = last_price_by_sym.get(sym_key)
                            if prev_p is not None:
                                if current_price > prev_p: p_dir = "up"
                                elif current_price < prev_p: p_dir = "down"
                            last_price_by_sym[sym_key] = current_price
                            socketio.emit("price_update", {
                                "price": current_price,
                                "direction": p_dir,
                                "currency_symbol": active_currency_symbol,
                                "timestamp": datetime.now(timezone.utc).isoformat()
                            })

                        if len(candles) > 0:
                            lc = candles.iloc[-1]
                            t = int(lc["timestamp"].timestamp()) if hasattr(lc["timestamp"], "timestamp") else int(time.time())
                            socketio.emit("candle_update", {
                                "time": t,
                                "open": float(lc["open"]),
                                "high": float(lc["high"]),
                                "low": float(lc["low"]),
                                "close": float(lc["close"]),
                            })

            else:
                # --- CRYPTO (CWALLET) MODE ---
                if crypto_feed and crypto_feed.is_connected():
                    spot_p = crypto_feed.get_latest_price() or 0.0
                    fut_p = crypto_feed.get_futures_price() or 0.0

                    k_ref = round_manager.external_strike if (round_manager and round_manager.external_strike) else None
                    if crypto_price_source == "futures":
                        current_price = fut_p if fut_p > 0 else spot_p
                        eff_source = "futures"
                    elif crypto_price_source == "spot":
                        current_price = spot_p if spot_p > 0 else fut_p
                        eff_source = "spot"
                    else:  # "auto"
                        if k_ref and k_ref > 0 and fut_p > 0 and spot_p > 0:
                            if abs(k_ref - fut_p) < abs(k_ref - spot_p):
                                current_price = fut_p
                                eff_source = "futures"
                            else:
                                current_price = spot_p
                                eff_source = "spot"
                        else:
                            current_price = spot_p if spot_p > 0 else fut_p
                            eff_source = "spot" if spot_p > 0 else "futures"

                    r_state = round_manager.tick(current_price)
                    r_state["price_source"] = crypto_price_source
                    r_state["effective_price_source"] = eff_source
                    r_state["futures_price"] = fut_p
                    r_state["spot_price"] = spot_p
                    socketio.emit("cwallet_round_update", r_state)

                    if r_state.get("just_settled"):
                        s_round_id = r_state.get("settled_round_id")
                        s_strike = r_state.get("settled_strike")
                        s_close = r_state.get("settled_close")
                        s_outcome = r_state.get("settled_outcome")
                        last_pred = round_manager.get_last_sniper_direction(s_round_id)
                        if last_pred in ("UP", "DOWN"):
                            s_won = (last_pred == s_outcome)
                        else:
                            s_won = (s_outcome == "UP") if (s_strike is not None and s_close is not None and s_close != s_strike) else False

                        settled_payload = {
                            "round_id": s_round_id,
                            "strike": s_strike,
                            "close_price": s_close,
                            "outcome": s_outcome,
                            "won": s_won
                        }
                        socketio.emit("cwallet_round_settled", settled_payload)

                    candles = crypto_feed.get_candles()
                    if candles is not None and len(candles) >= 8:
                        if current_price > 0 and not candles.empty:
                            candles = candles.copy()
                            candles.loc[candles.index[-1], 'close'] = current_price
                        order_flow = crypto_feed.get_order_flow()
                        result = signal_engine.generate_signal(
                            candles,
                            order_flow=order_flow,
                            round_open_price=r_state["round_open_price"],
                            time_left=r_state["seconds_left"],
                            is_equity=False,
                            round_info=r_state,
                            zero_defect_mode=zero_defect_mode
                        )
                        result["market_type"] = "crypto"
                        result["symbol"] = active_symbol
                        result["name"] = active_name
                        result["currency_symbol"] = "$"
                        result["cwallet_round"] = r_state
                        socketio.emit("signal_update", result)

                        # Authoritative Server-Side Sniper Call Coordination
                        # Analyzes full round order flow and coordinates dynamic zero-drift sniper alerts
                        round_id = r_state["round_id"]
                        early_radar_already_fired = (r_state.get("early_radar_fired_for_round", -1) == round_id)
                        sniper_already_fired = (r_state.get("sniper_fired_for_round", -1) == round_id)
                        secs_left = r_state["seconds_left"]
                        target_lead = int(round_manager.lead_time)
                        open_strike = r_state.get("round_open_price") or 0.0
                        round_dur = int(r_state.get("round_duration", 20))

                        is_early_radar = False
                        is_primary_sniper = False
                        is_dynamic_upgrade = False
                        is_emergency_reversal = False

                        # Trigger 1.5: Stage 1.5 Pre-Sniper Chambering Alert (T-8s to T-6s in 20s/30s round)
                        phase_secs = r_state.get("phase_seconds_left", secs_left)
                        chamber_window = (r_state.get("phase") == "BETTING" and phase_secs <= 8 and phase_secs >= 6) if round_dur == 20 else ((secs_left <= 8 and secs_left >= 6) if round_dur == 30 else (secs_left <= 15 and secs_left >= 12))
                        chambering_already_fired = (r_state.get("chambering_fired_for_round", -1) == round_id)
                        if not chambering_already_fired and chamber_window and open_strike > 0:
                            strike_diff_cb = current_price - open_strike
                            cb_model = result.get("chambering_model", {})
                            is_cb = cb_model.get("is_chambering", False)
                            cb_dir = cb_model.get("prep_direction", "NONE")
                            if not is_cb:
                                if strike_diff_cb >= 0.60 and result.get("direction") == "UP":
                                    is_cb = True
                                    cb_dir = "UP"
                                elif strike_diff_cb <= -0.60 and result.get("direction") == "DOWN":
                                    is_cb = True
                                    cb_dir = "DOWN"

                            if is_cb and cb_dir in ("UP", "DOWN"):
                                round_manager.mark_chambering_fired(round_id)
                                w_shield = result.get("whale_shield", {})
                                shield_val = float(w_shield.get("shield_usd", 0.0))
                                socketio.emit("chambering_prep", {
                                    "round_id": round_id,
                                    "round_number": r_state["round_number"],
                                    "seconds_left": secs_left,
                                    "prep_direction": cb_dir,
                                    "confluence": result.get("confluence_count", 18),
                                    "message": f"⚡ PRE-SNIPER READY (T-{secs_left}s): HOVER FINGER ON BET {cb_dir} — 05s SNIPER IMMINENT",
                                    "whale_shield_usd": round(shield_val, 0)
                                })

                        # Trigger 2: Stage 2 Primary Quantum Apex Sniper (Fires at EXACTLY T-5s of betting window)
                        # IMMUTABLE SINGLE PREDICTION: Fires strictly once at T-5s and never changes mid-round
                        if not sniper_already_fired and r_state.get("is_sniper_window", False):
                            if open_strike > 0 or current_price > 0:
                                is_primary_sniper = True
                                strike_diff = current_price - (open_strike or current_price)

                        is_early_sniper = is_primary_sniper

                        if is_early_sniper:
                            # Unified Institutional Microstructure Confluence from signal_engine
                            call_direction = result.get("direction", "PASS")
                            if call_direction == "WAIT":
                                call_direction = "PASS"
                            call_confidence = float(result.get("confidence", 50.0))
                            call_strength = result.get("strength", "🛡️ CAPITAL SHIELD: CHOP NOISE PASS (0x UNIT)")
                            call_kelly = result.get("kelly_unit", "0x (PASS)")
                            confluence_count = int(result.get("confluence_count", 0))
                            is_conviction_call = (call_direction in ("UP", "DOWN") and call_confidence >= 75.0)
                            is_zero_defect_call = bool(result.get("is_zero_defect", False))

                            math_models = result.get("math_models", {})
                            roll_m = math_models.get("roll_noise", {})
                            hawkes_m = math_models.get("hawkes_process", {})
                            merton_m = math_models.get("merton_jump", {})
                            kalman_m = math_models.get("kalman_velocity", {})
                            ou_m = math_models.get("ornstein_uhlenbeck", {})
                            book_wall_m = result.get("book_wall_model") or math_models.get("book_wall_absorption", {})
                            tri_venue_m = result.get("tri_venue_model") or math_models.get("tri_venue_triangulation", {})
                            barrier_m = result.get("barrier_model", {})

                            noise_ratio = float(roll_m.get("noise_ratio", 0.0))
                            is_noise_dom = bool(roll_m.get("is_noise_dominant", False)) or (noise_ratio >= 0.50)
                            vpin_val = float(order_flow.get("vpin", 0.0)) if order_flow else 0.0
                            kal_v = float(kalman_m.get("velocity_bps", 0.0))
                            ou_z = float(ou_m.get("z_score", 0.0))
                            bid_wall_btc = float(book_wall_m.get("bid_wall_btc", 0.0))
                            ask_wall_btc = float(book_wall_m.get("ask_wall_btc", 0.0))
                            burn_ratio_up = float(book_wall_m.get("burn_ratio_up", 1.0))
                            burn_ratio_down = float(book_wall_m.get("burn_ratio_down", 1.0))
                            is_book_wall_secured = bool(book_wall_m.get("is_wall_secured", False))
                            is_tri_venue_aligned = bool(tri_venue_m.get("is_aligned", False))
                            of_cb_price = float(order_flow.get("coinbase_price", current_price)) if order_flow else current_price
                            exp_margin = float(barrier_m.get("expected_margin", strike_diff))
                            proj_expiry_p = float(barrier_m.get("projected_expiry_price", current_price))


                            # ABSOLUTE DIRECTIONAL INTEGRITY CHECK
                            if call_direction == "UP" and strike_diff < -0.05:
                                call_direction = "PASS"
                                is_conviction_call = False
                            elif call_direction == "DOWN" and strike_diff > 0.05:
                                call_direction = "PASS"
                                is_conviction_call = False

                            # AI COUNCIL FIRST PRIORITY SUPREME INTEGRITY CHECK
                            ai_eng_payload = result.get("ai_engine", {})
                            if call_direction in ("UP", "DOWN") and ai_eng_payload:
                                ai_v = bool(ai_eng_payload.get("veto", False))
                                ai_r_status = str(ai_eng_payload.get("risk_status", "APPROVED"))
                                ai_s = float(ai_eng_payload.get("score", 0.0))
                                ai_d = int(ai_eng_payload.get("signal", 0))
                                if ai_v or ai_r_status == "REJECTED":
                                    call_direction = "PASS"
                                    is_conviction_call = False
                                    call_strength = "🛡️ CAPITAL SHIELD: AI COUNCIL RISK VETO (Munger / Risk Gate)"
                                elif call_direction == "UP" and (ai_s <= -0.15 or ai_d < 0):
                                    call_direction = "PASS"
                                    is_conviction_call = False
                                    call_strength = "🛡️ CAPITAL SHIELD: AI COUNCIL DIRECTIONAL VETO (BEARISH MANDATE)"
                                elif call_direction == "DOWN" and (ai_s >= 0.15 or ai_d > 0):
                                    call_direction = "PASS"
                                    is_conviction_call = False
                                    call_strength = "🛡️ CAPITAL SHIELD: AI COUNCIL DIRECTIONAL VETO (BULLISH MANDATE)"

                            # Record sniper state in round manager (fires strictly once at T-5s)
                            round_manager.mark_sniper_fired(round_id, direction=call_direction, strength=call_strength)

                            should_emit = is_primary_sniper
                            if should_emit:
                                socketio.emit("cwallet_sniper_call", {
                                    "round_number": r_state["round_number"],
                                    "direction": call_direction,
                                    "is_pass": (call_direction == "PASS"),
                                    "confidence": call_confidence,
                                    "strength": call_strength,
                                    "price": current_price,
                                    "open_strike": r_state["round_open_price"],
                                    "strike_delta": r_state["strike_delta"],
                                    "seconds_left": r_state["seconds_left"],
                                    "kelly_unit": call_kelly,
                                    "win_prob": call_confidence if is_conviction_call else 50.0,
                                    "confluence_count": confluence_count,
                                    "confluence_total": result.get("confluence_total", 26),
                                    "confluence_score": result.get("confluence_score", f"{confluence_count}/26 CONFLUENCE"),
                                    "ai_engine": result.get("ai_engine", {}),
                                    "hawkes_is_cascade": bool(hawkes_m.get("is_cascade", False)),
                                    "hawkes_branching": hawkes_m.get("branching_ratio", 0.5),
                                    "gkyz_volatility": (result.get("gkyz_model") or {}).get("sigma_gkyz", 0.0),
                                    "merton_win_prob": merton_m.get("win_prob", 50.0),
                                    "roll_noise_ratio": round(noise_ratio, 3),
                                    "is_noise_dominant": is_noise_dom,
                                    "vpin": round(vpin_val, 3),
                                    "kalman_velocity": round(kal_v, 2),
                                    "ou_z_score": round(ou_z, 2),
                                    "bid_wall_btc": round(bid_wall_btc, 2),
                                    "ask_wall_btc": round(ask_wall_btc, 2),
                                    "burn_ratio_up": round(burn_ratio_up, 1),
                                    "burn_ratio_down": round(burn_ratio_down, 1),
                                    "coinbase_price": round(of_cb_price, 2),
                                    "is_book_wall_secured": is_book_wall_secured,
                                    "is_tri_venue_aligned": is_tri_venue_aligned,
                                    "projected_expiry_price": proj_expiry_p,
                                    "expected_margin": exp_margin,
                                    "is_early_radar": is_early_radar,
                                    "is_apex": is_primary_sniper,
                                    "is_upgrade": is_dynamic_upgrade,
                                    "is_reversal": is_emergency_reversal,
                                    "is_omniscient": is_conviction_call,
                                    "is_lethal": is_conviction_call,
                                    "is_god_apex": is_conviction_call and not is_zero_defect_call,
                                    "is_god_mode": is_conviction_call,
                                    "is_zero_defect": is_zero_defect_call,
                                    "is_early_breakout": is_dynamic_upgrade,
                                    "tactical_command": call_direction,
                                    "whale_shield_usd": round(float((result.get("whale_shield") or {}).get("shield_usd", 0.0)), 0),
                                    "is_whale_impenetrable": bool((result.get("whale_shield") or {}).get("is_impenetrable", False)),
                                    "symbol": active_symbol.upper()
                                })

                            # Desktop toast notification (Single fire per round, strictly actionable UP/DOWN only)
                            # CRITICAL: Only fire for primary sniper, dynamic upgrade, or emergency reversal! NEVER fire on early radar!
                            if not is_early_radar and is_conviction_call and call_direction in ("UP", "DOWN"):
                                notifier.send_signal_notification(
                                    direction=call_direction,
                                    confidence=float(call_confidence),
                                    price=float(current_price),
                                    strike=float(r_state["round_open_price"] or current_price),
                                    strength=call_strength,
                                    round_id=round_id
                                )

                        # Price update
                        if current_price:
                            p_dir = "neutral"
                            prev_p = last_price_by_sym.get(sym_key)
                            if prev_p is not None:
                                if current_price > prev_p: p_dir = "up"
                                elif current_price < prev_p: p_dir = "down"
                            last_price_by_sym[sym_key] = current_price
                            socketio.emit("price_update", {
                                "price": current_price,
                                "direction": p_dir,
                                "currency_symbol": "$",
                                "timestamp": datetime.now(timezone.utc).isoformat()
                            })

                        # Candle update
                        if len(candles) > 0:
                            lc = candles.iloc[-1]
                            t = int(lc["timestamp"].timestamp()) if hasattr(lc["timestamp"], "timestamp") else int(time.time())
                            socketio.emit("candle_update", {
                                "time": t,
                                "open": float(lc["open"]),
                                "high": float(lc["high"]),
                                "low": float(lc["low"]),
                                "close": float(lc["close"]),
                            })

        except Exception as e:
            print(f"[Signal Loop Error] {e}")

        now = time.time()
        # High-precision 50ms polling when approaching the T-5s sniper window to guarantee zero timing lag
        cur_phase = r_state.get("phase", "BETTING") if 'r_state' in locals() and r_state else "BETTING"
        cur_p_left = r_state.get("phase_seconds_left", 15.0) if 'r_state' in locals() and r_state else 15.0
        cur_s_fired = (r_state.get("sniper_fired_for_round", -1) == r_state.get("round_id", -2)) if 'r_state' in locals() and r_state else False

        if cur_phase == "BETTING" and cur_p_left <= 7.0 and not cur_s_fired:
            dynamic_interval = 0.05  # 50ms ultra-precision sampling right around T-5s
            next_deadline = min(next_deadline, now + dynamic_interval)
        else:
            dynamic_interval = interval

        sleep_time = max(0.005, next_deadline - now)
        if sleep_time > 0:
            time.sleep(sleep_time)
        next_deadline = time.time() + dynamic_interval

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def start_bot(host: str = "127.0.0.1", port: int = 5000, interval: float = 0.5):
    global crypto_feed, indian_feed, international_feed, analyzer, signal_engine, _running

    print("=" * 65)
    print("  CW QUANT TERMINAL — UNIVERSAL CRYPTO & INDIAN STOCK MARKET")
    print("=" * 65)

    print("\n[Boot] 1. Starting Binance Multi-Crypto data feed...")
    crypto_feed = BinanceDataFeed(symbol="btcusdt")
    crypto_feed.start()

    print("[Boot] 2. Starting Indian Stock Market feed (NSE/BSE)...")
    indian_feed = IndianMarketFeed(initial_symbol="^NSEI")
    indian_feed.start()

    print("[Boot] 3. Starting International Market feed (US/Forex/Global)...")
    international_feed = InternationalMarketFeed(initial_symbol="^GSPC")
    international_feed.start()

    print("[Boot] 4. Initialising Institutional Quantitative Analyzer...")
    analyzer = TechnicalAnalyzer()
    signal_engine = SignalEngine(analyzer)

    print(f"[Boot] 4. Starting precision signal loop (every {interval}s)...")
    signal_thread = threading.Thread(target=_signal_loop, args=(interval,), daemon=True)
    signal_thread.start()

    print(f"\n[Boot] Dashboard live at: http://{host}:{port}")

    try:
        socketio.run(app, host=host, port=port, debug=False, use_reloader=False, allow_unsafe_werkzeug=True)
    except KeyboardInterrupt:
        print("\n[Shutdown] Stopping bot...")
    finally:
        _running = False
        if crypto_feed: crypto_feed.stop()
        if indian_feed: indian_feed.stop()
        if international_feed: international_feed.stop()
        print("[Shutdown] Bot stopped cleanly.")

def stop_bot():
    global _running
    _running = False
    if crypto_feed: crypto_feed.stop()
    if indian_feed: indian_feed.stop()
