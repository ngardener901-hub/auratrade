"""
AuraTrade — Main Streamlit Dashboard
------------------------------------
Real-time trading assistant UI for MES/MNQ futures.

Sections:
  1. Header & Regime Display
  2. Market Structure & Key Levels
  3. FVG Detector Panel
  4. Entry Engine — Holy Grail Signals
  5. Active Position & Risk Guard
  6. Trade Journal (AI Analysis)
  7. Execution Controls
"""

import logging
import sys
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any

import streamlit as st
import pandas as pd
import numpy as np
import pytz

# ─── AuraTrade Modules ──────────────────────────────────────────────────────
import config
from regime_classifier import classify_regime, detect_market_structure, get_regime_context
from fvg_detector import detect_fvg, FVG
from entry_engine import evaluate_entry, evaluate_pyramid, should_remove_quickly, EntrySignal, ActivePosition
from risk_guard import RiskGuard
from tradovate_client import TradovateClient, OrderRequest, OrderType, OrderSide, TimeInForce
from journal_analyzer import analyze_trade, list_patterns

# ─── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(level=getattr(logging, config.LOG_LEVEL), format=config.LOG_FORMAT)
logger = logging.getLogger("AuraTrade")

# ─── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AuraTrade | AI Trading Assistant",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

EASTERN = pytz.timezone("US/Eastern")

# ═══════════════════════════════════════════════════════════════════════════════
#  SESSION STATE
# ═══════════════════════════════════════════════════════════════════════════════

def init_session_state():
    """Initialize Streamlit session state variables."""
    defaults = {
        "risk_guard": RiskGuard(),
        "active_position": None,
        "last_signal": None,
        "trade_history": [],
        "price_data": pd.DataFrame(),
        "key_levels": {},
        "connected": False,
        "client": None,
        "messages": [],
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


init_session_state()


# ═══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.image("https://via.placeholder.com/150x60?text=AURATRADE", width=150)
    st.markdown("### ⚡ AuraTrade AI Assistant")
    st.markdown("*MES / MNQ Futures | Smart Money Concepts*")
    st.divider()

    # Product selector
    product = st.selectbox("Product", ["MNQ", "MES"], index=0)
    st.session_state["product"] = product

    # Account
    st.markdown(f"**Account:** ${config.ACCOUNT_BALANCE:,.0f}")
    st.markdown(f"**Daily Stop:** -${config.DAILY_STOP_LOSS:,.0f}")
    st.markdown(f"**Max Trades:** {config.MAX_TRADES_PER_SESSION}")

    # Tradovate Connect
    st.divider()
    st.markdown("#### 🔗 Tradovate")
    if st.button("Connect to Tradovate", type="primary"):
        client = TradovateClient()
        success = client.authenticate()
        st.session_state["connected"] = success
        st.session_state["client"] = client if success else None
        if success:
            st.success("Connected!")
        else:
            st.error("Connection failed. Check credentials in environment.")

    if st.session_state["connected"]:
        st.success("🟢 Live")
    else:
        st.warning("🟡 Simulated Mode")

    # Risk Status
    st.divider()
    rg = st.session_state["risk_guard"]
    status = rg.get_status()
    st.markdown("#### 🛡️ Risk Status")
    st.progress(min(1.0, status["drawdown_used"] / status["drawdown_limit"]), text=f"Drawdown: ${status['drawdown_used']:.0f} / ${status['drawdown_limit']:.0f}")
    st.progress(min(1.0, abs(status["daily_pnl"]) / config.DAILY_STOP_LOSS), text=f"Daily PnL: ${status['daily_pnl']:.0f}")
    st.write(f"Trades: {status['trades_taken']} / {status['max_trades']}")
    st.write(f"Can Trade: {'✅ Yes' if status['can_trade'] else '❌ NO'}")

    # Manual Controls
    st.divider()
    if st.button("🔄 Reset Daily", type="secondary"):
        st.session_state["risk_guard"].reset_daily()
        st.session_state["active_position"] = None
        st.session_state["last_signal"] = None
        st.rerun()

    if st.button("🚨 Close All / Flatten", type="secondary"):
        if st.session_state["client"] and st.session_state["connected"]:
            st.session_state["client"].cancel_all_orders()
        st.session_state["active_position"] = None
        st.info("Position flattened.")

# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

st.title("⚡ AuraTrade | AI Trading Assistant")
st.caption(f"Smart Money Concepts for {product} | {datetime.now(EASTERN).strftime('%A %H:%M:%S %Z')}")

# ─── Row 1: Regime & Market Structure ────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)

# Regime Classification
dow = datetime.now(EASTERN).weekday()
regime = classify_regime(dow)
regime_ctx = get_regime_context(regime)

regime_color = "🟦" if regime == "BLUE" else "🟥"
with col1:
    st.metric(
        label=f"{regime_color} Regime",
        value=regime,
        delta=regime_ctx["name"],
    )

with col2:
    st.metric(
        label="Trading Mode",
        value="Pyramiding ON" if regime_ctx["pyramiding"] else "No Pyramiding",
        delta=regime_ctx["target_type"],
    )

with col3:
    st.metric(
        label="Bias",
        value=regime_ctx["entry_bias"].replace("_", " ").title(),
        delta="Tight Stops" if regime_ctx["tight_stops"] else "Normal Stops",
    )

with col4:
    st.metric(
        label="Session",
        value=f"{config.MARKET_OPEN_HOUR}:{config.MARKET_OPEN_MINUTE:02d}–{config.MARKET_CLOSE_HOUR}:00 ET",
        delta="OPEN" if rg._in_market_hours() else "CLOSED",
    )

st.divider()

# ─── Row 2: Chart & Structure (placeholder for price feed integration) ───────
st.subheader("📊 Market Structure")

# Simulated price data for demo (integrate with live feed)
if st.session_state["price_data"].empty:
    # Generate sample data for UI skeleton
    np.random.seed(42)
    n = 100
    base_price = 18500.0 if product == "MNQ" else 5500.0
    noise = np.cumsum(np.random.randn(n) * 2)
    df = pd.DataFrame({
        "open": base_price + noise + np.random.randn(n),
        "high": base_price + noise + abs(np.random.randn(n)) * 3,
        "low": base_price + noise - abs(np.random.randn(n)) * 3,
        "close": base_price + noise + np.random.randn(n),
        "volume": np.random.randint(100, 1000, n),
    }, index=pd.date_range("09:30", periods=n, freq="1min"))
    df["vwap"] = df["close"].expanding().mean()
    df["ema9"] = df["close"].ewm(span=9, adjust=False).mean()
    st.session_state["price_data"] = df

price_data = st.session_state["price_data"]
latest = price_data.iloc[-1]
vwap = float(latest["vwap"])
ema9 = float(latest["ema9"])
close = float(latest["close"])

# Market structure
structure = detect_market_structure(price_data)

str_col1, str_col2, str_col3 = st.columns(3)
with str_col1:
    st.markdown("**Price vs VWAP**")
    st.write(structure["price_vs_vwap"].upper())
    st.markdown("**Trend**")
    st.write(f"{structure['trend_direction'].upper()} (score: {structure['trend_score']})")

with str_col2:
    st.markdown("**Key Levels**")
    for name, val in structure.get("key_levels", {}).items():
        st.write(f"• {name}: {val}")

with str_col3:
    st.markdown("**Liquidity Sweeps**")
    sweeps = structure.get("liquidity_sweeps", [])
    if sweeps:
        for s in sweeps:
            st.write(f"⚠️ {s}")
    else:
        st.write("None detected")

st.divider()

# ─── Row 3: FVG Detector ─────────────────────────────────────────────────────
st.subheader("🎯 Fair Value Gaps")

fvgs = detect_fvg(price_data)
if fvgs:
    fvg_data = []
    for f in fvgs[-5:]:  # Show last 5
        fvg_data.append({
            "Direction": "🟩 Bullish" if f.is_bullish else "🟥 Bearish",
            "Zone": f"{f.bottom:.2f} – {f.top:.2f}",
            "Mid": f"{f.mid():.2f}",
            "Ticks": f.height_ticks(),
            "Age (bars)": f.age_bars,
            "Source": f.source_level,
        })
    st.dataframe(pd.DataFrame(fvg_data), use_container_width=True, hide_index=True)
else:
    st.info("No FVGs detected in current window.")

st.divider()

# ─── Row 4: Entry Engine — Holy Grail Signals ──────────────────────────────
st.subheader("🔥 Holy Grail Entry Engine")

key_levels = structure.get("key_levels", {})
# Add some dummy key levels for UI demo
key_levels.setdefault("London_High", close + 20)
key_levels.setdefault("London_Low", close - 20)

signal = evaluate_entry(
    price_data=price_data,
    vwap=vwap,
    ema9=ema9,
    regime=regime,
    active_position=st.session_state["active_position"],
    key_levels=key_levels,
    product=product,
)

sig_col1, sig_col2 = st.columns([2, 1])

with sig_col1:
    if signal:
        st.session_state["last_signal"] = signal
        st.success(f"🚨 SIGNAL: {signal.direction.upper()} | Confidence: {signal.confidence:.0%}")
        st.write(f"**Entry:** {signal.entry_price} | **Stop:** {signal.stop_loss} | **Target:** {signal.target}")
        st.write(f"**R:R:** {signal.rr_ratio} | **Contracts:** {signal.contracts}")
        st.write(f"**Reason:** {signal.reason}")
        if signal.pyramid:
            st.warning("⚠️ This is a PYRAMID add — reduce size accordingly")
    else:
        st.info("No Holy Grail entry signal at this time.")
        if st.session_state["last_signal"]:
            st.caption(f"Last signal: {st.session_state['last_signal'].direction.upper()} @ {st.session_state['last_signal'].entry_price}")

with sig_col2:
    if signal:
        if st.button("✅ TAKE ENTRY", type="primary", use_container_width=True):
            # Execute via Tradovate
            if st.session_state["connected"] and st.session_state["client"]:
                side = OrderSide.BUY if signal.direction == "long" else OrderSide.SELL
                order = OrderRequest(
                    symbol=product,
                    side=side,
                    order_type=OrderType.LMT,
                    quantity=signal.contracts,
                    price=signal.entry_price,
                    time_in_force=TimeInForce.DAY,
                )
                resp = st.session_state["client"].place_order(order)
                if resp.success:
                    st.success(f"Order placed: {resp.order_id}")
                else:
                    st.error(f"Order failed: {resp.message}")
            else:
                st.info("Simulated entry recorded (not connected to Tradovate).")

            # Track position
            pos = ActivePosition(
                direction=signal.direction,
                entry_price=signal.entry_price,
                stop_loss=signal.stop_loss,
                initial_target=signal.target,
                contracts=signal.contracts,
                entry_time=datetime.now(EASTERN),
                regime_at_entry=regime,
            )
            st.session_state["active_position"] = pos
            st.session_state["risk_guard"].record_trade_opened()
            st.rerun()

# ─── Remove Quickly Check ────────────────────────────────────────────────────
if st.session_state["active_position"]:
    pos = st.session_state["active_position"]
    remove = should_remove_quickly(pos, price_data, ema9)
    if remove:
        st.error("🚨 REMOVE QUICKLY: Price closed opposite side of 9-EMA — EXIT NOW!")
        if st.button("CONFIRM EXIT", type="primary"):
            # Simulate exit
            pnl = np.random.randn() * 50  # placeholder
            st.session_state["risk_guard"].record_trade_closed(pnl)
            st.session_state["trade_history"].append({
                "time": datetime.now(EASTERN).isoformat(),
                "direction": pos.direction,
                "entry": pos.entry_price,
                "exit": close,
                "pnl": pnl,
                "reason": "Remove Quickly — 9-EMA breach",
            })
            st.session_state["active_position"] = None
            st.rerun()

st.divider()

# ─── Row 5: Active Position Monitor ────────────────────────────────────────────
st.subheader("📍 Active Position")

if st.session_state["active_position"]:
    pos = st.session_state["active_position"]
    pcol1, pcol2, pcol3, pcol4 = st.columns(4)
    current_r = pos.current_r_multiple(close)
    pnl_est = current_r * abs(pos.entry_price - pos.stop_loss) * pos.contracts * (config.TICK_VALUE_MNQ if product == "MNQ" else config.TICK_VALUE_MES)

    with pcol1:
        st.metric("Direction", pos.direction.upper())
    with pcol2:
        st.metric("Entry", f"{pos.entry_price:.2f}")
    with pcol3:
        st.metric("Current R", f"{current_r:.2f}R")
    with pcol4:
        st.metric("Est. PnL", f"${pnl_est:.0f}")

    st.write(f"Stop: {pos.stop_loss:.2f} | Target: {pos.initial_target:.2f} | Contracts: {pos.contracts}")

    if pos.regime_at_entry == "BLUE" and pos.pyramid_count < pos.max_pyramids:
        if st.button("📈 Evaluate Pyramid"):
            pyramid_ok = evaluate_pyramid(pos, price_data, fvgs, regime)
            if pyramid_ok:
                st.success("Pyramid condition MET — second FVG retest in same direction")
            else:
                st.info("Pyramid not yet valid (need +1R profit + new FVG)")
else:
    st.write("No active position. Awaiting Holy Grail signal...")

st.divider()

# ─── Row 6: Trade Journal with AI Analysis ───────────────────────────────────
st.subheader("📝 Trade Journal (AI Analysis)")

if st.session_state["trade_history"]:
    for trade in reversed(st.session_state["trade_history"][-5:]):
        with st.expander(f"Trade @ {trade['time'][:19]} | {trade['direction'].upper()} | PnL: ${trade['pnl']:.2f}"):
            # AI analysis
            analysis = analyze_trade(trade, regime)
            st.markdown("**AI Pattern Analysis:**")
            st.text(analysis)
else:
    st.info("No completed trades yet. History will appear after exits.")

st.divider()

# ─── Row 7: Pattern Reference ────────────────────────────────────────────────
with st.expander("📚 View All 11 Training Patterns"):
    for line in list_patterns():
        st.write(line)

# ─── Footer ────────────────────────────────────────────────────────────────
st.divider()
st.caption("AuraTrade v1.0 | Smart Money Concepts | Built for prop firm compliance")
st.caption("⚠️ This is algorithmic analysis software. Trading involves substantial risk of loss.")
