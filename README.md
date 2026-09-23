---
title: TradeX Sniper Bot
emoji: ⚡
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
---

# TradeX — BTC/USDT Precision Signal Predictor

A real-time quantitative trading signal bot that analyses BTC/USDT price action and generates **UP/DOWN predictions** for fast-paced 30-second binary rounds.

## How It Works

```
Binance WebSocket (live BTC/USDT tick data)
        │
        ▼
   Technical Analysis Engine (7 Confluence Vectors)
   RSI · MACD · Bollinger · EMA · VWAP · CVD · Momentum
        │
        ▼
   Signal Aggregator & Zero-Defect Gating
   Confidence: 0–100%  →  UP / DOWN / PASS
        │
        ▼
   Live Web Dashboard & Push Alerts
   🟢 UP  /  🔴 DOWN  /  🛡️ PASS
```

## Quick Start (Local Windows)
Double-click `START_BOT.bat` to launch the terminal on `http://127.0.0.1:5000`.

## 24/7 Cloud Deployment (100% Free)
See `CLOUD_DEPLOY_GUIDE.md` for zero-credit-card, 2-minute cloud hosting instructions.
