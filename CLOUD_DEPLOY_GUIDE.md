# 🚀 100% Free 24/7 Cloud Hosting Guide (No Credit Card Required)

This guide shows you how to host TradeX on the cloud for **100% FREE** with **ZERO credit card** needed. The bot will run 24 hours a day, 7 days a week, even when your laptop is turned off!

---

## 🌟 Method 1: Hugging Face Spaces (RECOMMENDED — Takes 2 Minutes)

Hugging Face Spaces provides **100% Free Forever** cloud containers with 16GB RAM and 2 vCPUs. You do not need Git, and you do not need a credit card.

### Step 1: Create a Free Account
1. Open [https://huggingface.co/join](https://huggingface.co/join)
2. Sign up with your email (100% free, no credit card asked).

### Step 2: Create a New Space
1. Click your profile picture (top right) and click **"New Space"** (or visit [https://huggingface.co/new-space](https://huggingface.co/new-space)).
2. Set **Space name**: `tradex` (or any name you like).
3. Set **License**: `mit` or `openrail`.
4. Under **Select the Space SDK**, choose **Docker** -> select **Blank**.
5. Set **Space hardware**: Keep the default **CPU basic · 2 vCPU · 16 GB · FREE**.
6. Set privacy to **Public** (or Private).
7. Click **Create Space**.

### Step 3: Upload Files
1. On your new Space page, click the **Files** tab (next to App / Community).
2. Click **Add file** -> **Upload files**.
3. Open your desktop folder: `C:\Users\divya\Desktop\tradex`.
4. Select all files and folders (or drag-and-drop everything into the browser):
   - `bot.py`
   - `server.py`
   - `round_manager.py`
   - `signal_engine.py`
   - `analysis.py`
   - `data_feed.py`
   - `indian_market_feed.py`
   - `international_market_feed.py`
   - `notifier.py`
   - `requirements.txt`
   - `Dockerfile`
   - `README.md`
   - `static` folder
   - `templates` folder
5. Scroll down and click **Commit changes to main**.

### Step 4: Done! Your 24/7 Permanent URL is Live!
- Hugging Face will automatically build the Docker image in ~1–2 minutes.
- Once it says **Running**, click the **App** tab!
- Your permanent direct link is:
  `https://<your-username>-tradex.hf.space`
- You can open this link on your phone, tablet, or any computer. It will work 24/7 forever, even when your laptop is completely powered off!

---

## ⚡ Method 2: Render.com (Alternative Free Cloud Option)

Render offers free cloud web services with no credit card required.

### Step 1: Create a Free Render Account
1. Open [https://render.com](https://render.com) and click **Get Started for Free** (sign in with GitHub or email).

### Step 2: Connect GitHub Repository
1. Push your `tradex` folder to a GitHub repository.
2. In Render, click **New +** -> **Web Service**.
3. Select your GitHub repository.

### Step 3: Settings
- **Name**: `tradex-bot`
- **Region**: Oregon or Frankfurt
- **Runtime**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python bot.py --no-browser`
- **Instance Type**: `Free` ($0/mo, no credit card required)
- Click **Create Web Service**.

### Step 4: Done!
- Render will build and deploy your service.
- You will get a permanent URL like: `https://tradex-bot.onrender.com`.

---

## 💡 Keeping Free Cloud Services Awake 24/7

Free cloud tiers may spin down after long periods of inactivity. To keep your bot running and analyzing 24/7/365 without sleep:
1. Go to [https://cron-job.org](https://cron-job.org) or [https://uptimerobot.com](https://uptimerobot.com) (both 100% free, no credit card).
2. Add your bot URL (e.g. `https://<your-username>-tradex.hf.space` or `https://tradex-bot.onrender.com`).
3. Set the interval to **every 5 minutes**.
4. That's it! This sends a free heartbeat ping every 5 minutes so your cloud bot NEVER goes to sleep!
