# AuraTrade — AI Trading Assistant

**AuraTrade** is a standalone Python trading assistant for **MES / MNQ** futures built on **Smart Money Concepts (SMC)**. It features real-time Fair Value Gap (FVG) detection, regime-based entry logic, prop firm risk guards, and Tradovate API integration — all wrapped in a clean Streamlit dashboard.

---

## 🚀 1-Click Deploy to Streamlit Cloud (Free Hosting)

Access AuraTrade from any browser or phone — no local setup required.

[![Deploy to Streamlit Cloud](https://img.shields.io/badge/Deploy%20to%20Streamlit%20Cloud-FF4B4B?logo=streamlit&logoColor=white&style=for-the-badge)](DEPLOY.md)

**Quick steps:**
1. [Create a public GitHub repo](https://github.com/new) named `auratrade`
2. Upload all files from this folder to the repo
3. Go to [streamlit.io/cloud](https://streamlit.io/cloud) → New app → Select your repo
4. Set **Main file path** to `main.py` → Click Deploy
5. Add your Tradovate demo credentials in **Settings → Secrets**

📖 **Full deployment guide:** See [`DEPLOY.md`](DEPLOY.md) for screenshots, secrets setup, and troubleshooting.

---

## 💻 Local Quick Start

```bash
# 1. Navigate to the project
cd auratrade

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set Tradovate credentials (optional for demo mode)
export TRADOVATE_USERNAME="your_username"
export TRADOVATE_PASSWORD="your_password"
export TRADOVATE_BASE_URL="https://demo.tradovateapi.com/v1"

# 5. Launch the dashboard
streamlit run main.py
```

---

## 📁 Project Structure

```
/mnt/agents/output/auratrade/
├── main.py                  # Streamlit dashboard entry point
├── config.py               # All settings, parameters, constants
├── regime_classifier.py    # Day-based + market structure classification
├── fvg_detector.py         # Fair Value Gap detection algorithm
├── entry_engine.py         # Holy Grail entry logic + pyramiding
├── risk_guard.py           # Prop firm safety (daily stop, max trades, 9-EMA, drawdown)
├── tradovate_client.py     # Tradovate API wrapper
├── journal_analyzer.py     # AI trade analysis (pattern matching against 11 examples)
├── requirements.txt        # Dependencies
└── README.md               # This file
```

---

## 🧠 Trading Logic

### BLUE Regime (Tue / Wed / Thu) — "Trend Runner"
- FVG retests that **ALIGN with VWAP** for expansion moves
- **Pyramiding enabled**: add to winners on second FVG formation (min +1R profit)
- Target: Previous session high/low, expansion moves
- "Remove Quickly" if price closes opposite side of 9-EMA

### RED Regime (Mon / Fri) — "Trap & Revert"
- Failed breakouts above London High or below London Low
- Reclaim of level from opposite side
- Bearish/Bullish FVG rejection
- Tighter profit targets (VWAP, London Low/High)
- **No pyramiding**

### The "Holy Grail" Entry (ALL regimes)
1. Price sweeps/reclaims a major level (London H/L or Prev NYAM H/L)
2. Creates a Fair Value Gap (FVG) through displacement (3-candle pattern)
3. Entry ONLY on retest/fill of that FVG
4. VWAP alignment = maximum confidence

---

## 🛡️ Prop Firm Safety Guards

| Rule | Limit |
|------|-------|
| Daily Stop Loss | $300 (hard stop) |
| Max Trades / Session | 2 (9:30 AM – 4:00 PM ET) |
| Max Contracts (MNQ) | 2 |
| Max Contracts (MES) | 1 |
| Trailing Drawdown | $2,000 from peak |
| Remove Quickly | Exit if close crosses 9-EMA |

---

## ⚙️ Configuration

Edit `config.py` or use environment variables:

```bash
export TRADOVATE_USERNAME="..."
export TRADOVATE_PASSWORD="..."
export TRADOVATE_ACCOUNT_ID="..."
export TRADOVATE_CID="..."           # Contract ID for product
export AURATRADE_LOG_LEVEL="INFO"
```

---

## 📊 Dashboard Features

- **Regime Display**: Auto-classified BLUE / RED with context
- **Market Structure**: Price vs VWAP, trend score, liquidity sweeps
- **FVG Panel**: Live detection of bullish/bearish gaps
- **Entry Engine**: Holy Grail signal generation with confidence scores
- **Risk Guard**: Real-time drawdown, daily PnL, trade count
- **Trade Journal**: AI pattern matching against 11 training examples
- **Execution**: One-click order placement via Tradovate

---

## 🔄 Integrating Live Data

The skeleton uses simulated data for UI preview. To connect a live feed:

1. Replace the simulated `price_data` generation in `main.py` with your data provider
2. Ensure DataFrame includes: `open`, `high`, `low`, `close`, `volume`, `vwap`, `ema9`
3. Update `key_levels` dict with actual pre-market / London / prior session levels

---

## ⚠️ Disclaimer

This software is for **educational and analytical purposes only**. Trading futures involves substantial risk of loss. Past performance does not guarantee future results. Always verify all signals with your own analysis and risk management rules.

---

*AuraTrade v1.0 | Built for serious traders.*
