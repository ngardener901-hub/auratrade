# AuraTrade Deployment Guide

## 1-Click Deploy to Streamlit Cloud (Free Hosting)

Streamlit Community Cloud lets you host Python apps online for **free**. No server management, no Docker — just connect your GitHub repo and click deploy.

**Live Preview:** https://kj74pc62xqogm.kimi.show — See the dashboard design and deployment instructions.

---

## Before You Start

**Important:** AuraTrade connects to the Tradovate API for live futures order execution. Until you fully validate the logic:
- Use **demo credentials** (`demo.tradovateapi.com`)
- Test all 3 non-negotiable rules in simulation
- Never deploy with live credentials on the first attempt

---

## Step 1: Create a GitHub Repository

1. Go to [github.com/new](https://github.com/new)
2. Name it `auratrade` (or any name)
3. Make it **Public** (required for free Streamlit Cloud tier)
4. Do **not** initialize with README (we will upload files)
5. Click **Create repository**

## Step 2: Upload AuraTrade Files

Upload all files from this `auratrade/` folder to your new repo:

```
.
├── .streamlit/
│   ├── config.toml          # Dark theme settings
│   └── secrets.toml         # API credentials template (fill in later)
├── main.py                  # Dashboard entry point
├── config.py                # Settings & parameters
├── regime_classifier.py     # BLUE/RED regime logic
├── fvg_detector.py          # Fair Value Gap detection
├── entry_engine.py          # Holy Grail execution engine
├── risk_guard.py            # Prop firm safety ($300 stop, $2K drawdown)
├── tradovate_client.py      # Tradovate API wrapper + OCO brackets
├── journal_analyzer.py      # AI pattern matching vs 11 training sessions
├── requirements.txt         # Python dependencies
└── README.md                # Project description
```

**Method A — GitHub Web UI:**
1. In your new repo, click **Add file** > **Upload files**
2. Drag & drop all files from this folder
3. Click **Commit changes**

**Method B — Git CLI:**
```bash
cd auratrade/
git init
git add .
git commit -m "Initial AuraTrade commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/auratrade.git
git push -u origin main
```

## Step 3: Connect to Streamlit Cloud

1. Go to [streamlit.io/cloud](https://streamlit.io/cloud)
2. Sign in with your GitHub account
3. Click **New app**
4. Select your `auratrade` repository
5. Set **Main file path** to: `main.py`
6. Click **Deploy**

## Step 4: Add Your API Secrets

After first deployment, add your Tradovate demo credentials:

1. In Streamlit Cloud, click your app
2. Click the **(⋯)** menu → **Settings**
3. Go to **Secrets** tab
4. Paste this (with your real values):

```toml
[tradovate]
TRADOVATE_USERNAME = "your_username"
TRADOVATE_PASSWORD = "your_password"
TRADOVATE_BASE_URL = "https://demo.tradovateapi.com/v1"
TRADOVATE_CID = "your_contract_id"
TRADOVATE_ACCOUNT_ID = "your_account_id"
TRADOVATE_DEVICE_ID = "auratrade-device-001"
```

5. Click **Save**
6. Click **Reboot** (forces the app to read new secrets)

## Step 5: Access From Anywhere

Once deployed, Streamlit gives you a permanent URL:

```
https://your-app-name-abc123.streamlit.app
```

**From your phone:**
- Open the URL in any mobile browser
- Streamlit auto-adapts to screen size
- Pin to home screen for app-like access (iOS: Share → Add to Home Screen; Android: Menu → Add to Home Screen)

**Wake after sleep:**
- Free-tier apps sleep after 7 days of inactivity
- Opening the URL wakes it in ~10 seconds

---

## Updating Your Deployed App

Any git push to your repo **automatically redeploys** the app:

```bash
git add .
git commit -m "Update risk parameters"
git push origin main
```

Streamlit Cloud rebuilds and deploys within 2 minutes.

---

## Architecture at a Glance

```
Browser/Phone
      │
      ▼
┌─────────────────────────────────────┐
│  Streamlit Cloud (Free Tier)        │
│  ┌─────────────────────────────┐    │
│  │  main.py  (UI Dashboard)    │    │
│  │  ├─ regime_classifier.py   │    │
│  │  ├─ entry_engine.py         │    │
│  │  ├─ fvg_detector.py        │    │
│  │  ├─ risk_guard.py          │    │
│  │  └─ tradovate_client.py    │    │
│  └─────────────────────────────┘    │
│              │                      │
│              ▼                      │
│     Tradovate API (REST/WebSocket)  │
│              │                      │
│              ▼                      │
│     MES/MNQ Order Execution         │
└─────────────────────────────────────┘
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| App won't start | Check `main.py` is set as main file path in Streamlit Cloud settings |
| Import errors | Verify all `.py` files were uploaded, especially `config.py` |
| API connection fails | Check Secrets tab — credentials must be under `[tradovate]` section |
| "Can't connect to Tradovate" | Use `https://demo.tradovateapi.com/v1` for demo, remove `www.` |
| App sleeps too often | Visit once per week, or upgrade to paid tier for always-on |
| Mobile view broken | This is a Streamlit limitation; use landscape mode for best chart view |

---

## Need Help?

- [Streamlit Cloud Docs](https://docs.streamlit.io/deploy/streamlit-community-cloud)
- [Tradovate API Docs](https://tradovate.github.io/api/)
- Check `AUDIT_RISK_1.md` and `AUDIT_RISK_2.md` for known edge cases before going live
