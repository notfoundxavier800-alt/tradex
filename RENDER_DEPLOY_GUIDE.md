# 🚀 Render.com 100% Free 24/7 Deployment Guide

This guide details how to deploy **TradeX 24-Vector Infallible Engine** to [Render.com](https://render.com) for **100% FREE** with **zero credit card required**.

---

## 📋 Pre-Configured Files Included
The repository already contains the exact production files needed by Render:
* `render.yaml`: Automated blueprint configuring Python 3.11, Free Tier, and auto-build.
* `Procfile`: Declares the Web process `web: python bot.py --no-browser`.
* `requirements.txt`: Includes all required packages (`flask`, `flask-socketio`, `simple-websocket`, `ta`, `pandas`, `numpy`, `websocket-client`, `gunicorn`).
* `.gitignore`: Prevents uploading large binaries like `cloudflared.exe`.

---

## ⚡ Method 1: Push via GitHub & Deploy (Recommended)

### Step 1: Push Code to GitHub
1. Open [https://github.com/new](https://github.com/new) and create a repository called `tradex` (Public or Private).
2. Double-click **`PUSH_TO_GITHUB.bat`** inside your `C:\Users\divya\Desktop\tradex` folder.
3. Paste your GitHub repository URL (e.g., `https://github.com/your-username/tradex.git`) and press Enter.

### Step 2: Deploy on Render
1. Open [https://dashboard.render.com](https://dashboard.render.com) (Log in with your GitHub account).
2. Click the blue **New +** button (top right) -> Select **Web Service**.
3. Under *Connect a repository*, select your **tradex** repository.
4. Render will auto-detect the repository settings:
   - **Name**: `tradex-signals` (or any name you choose)
   - **Region**: Any (e.g., Oregon, Frankfurt, Singapore)
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python bot.py --no-browser`
   - **Instance Type**: **Free** ($0/month)
5. Click **Deploy Web Service**!

---

## 🌐 Alternative: Render Blueprint (1-Click)
1. In Render Dashboard, click **New +** -> **Blueprint**.
2. Connect your `tradex` repository.
3. Render will read `render.yaml` and configure everything automatically.
4. Click **Apply**.

---

## ⏱️ Result
* Render builds the container in ~2 minutes.
* You get a permanent, live HTTPS URL:
  `https://tradex-signals.onrender.com`
* You can open this URL on your phone, tablet, or PC 24 hours a day, 7 days a week, even when your laptop is turned off!
