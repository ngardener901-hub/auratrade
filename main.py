"""
AuraTrade — Main Streamlit Dashboard
------------------------------------
Real-time trading assistant UI for MES/MNQ futures.
"""

import logging
import sys
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any

import streamlit as st
import pandas as pd
import numpy as np
import pytz

# AuraTrade Modules
import config
from regime_classifier import classify_regime, detect_market_structure, get_regime_context
from fvg_detector import detect_fvg, FVG
from entry_engine import evaluate_entry, evaluate_pyramid, should_remove_quickly, EntrySignal, ActivePosition
from risk_guard import RiskGuard
from tradovate_client import TradovateClient, OrderRequest, OrderType, OrderSide, TimeInForce
from journal_analyzer import analyze_trade, list_patterns

# Logging
logging.basicConfig(level=getattr(logging, config.LOG_LEVEL), format=config.LOG_FORMAT)
logger = logging.getLogger("AuraTrade")

# Page Config
st.set_page_config(
    page_title="AuraTrade | AI Trading Assistant",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

EASTERN = pytz.timezone("US/Eastern")


def init_session_state():
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


# SIDEBAR
with st.sidebar:
    st.image("https://via.placeholder.com/150x60?text=AURATRADE", width=150)
    st.markdown("### AuraTrade AI Assistant")
    st.markdown("*MES / MNQ Futures | Smart Money Concepts*")
    st.divider()

    product = st.selectbox("Product", ["MNQ", "MES"], index=0)
    st.session_state["product"] = product

    st.markdown(f"**Account:** ${config.ACCOUNT_BALANCE:,.0f}")
    st.markdown(f"**Daily Stop:** -${config.DAILY_STOP_LOSS:,.0f}")
    st.markdown(f"**Max Trades:** {config.MAX_TRADES_PER_SESSION}")

    st.divider()
    st.markdown("#### Tradovate")
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
        st.success("Live")
    else:
        st.warning("Simulated Mode")

    st.divider()
    rg = st.session_state["risk_guard"]
    status = rg.get_status()
    st.markdown("#### Risk Status")
    st.progress(min(1.0, status["drawdown_used"] / status["drawdown_limit"]), text=f"Drawdown: ${status['drawdown_used']:.0f} / ${status['drawdown_limit']:.0f}")
    st.progress(min(1.0, abs(status["daily_pnl"]) / config.DAILY_STOP_LOSS), text=f"Daily PnL: ${status['daily_pnl']:.0f}")
    st.write(f"Trades: {status['trades_taken']} / {status['max_trades']}")
    st.write(f"Can Trade: {'Yes' if status['can_trade'] else 'NO'}")

    st.divider()
    if st.button("Reset Daily", type="secondary"):
        st.session_state["risk_guard"].reset_daily()
        st.session_state["active_position"] = None
        st.session_state["last_signal"] = None
        st.rerun()

    if st.button("Close All / Flatten", type="secondary"):
        if st.session_state["client"] and st.session_state["connected"]:
            st.session_state["client"].cancel_all_orders()
        st.session_state["active_position"] = None
        st.info("Position flattened.")


# MAIN DASHBOARD
st.title("AuraTrade | AI Trading Assistant")
st.caption(f"Smart Money Concepts for {product} | {datetime.now(EASTERN).strftime('%A %H:%M:%S %Z')}")

col1, col2, col3, col4 = st.columns(4)

dow = datetime.now(EASTERN).weekday()
regime = classify_regime(dow)
regime_ctx = get_regime_context(regime)

regime_color = "Blue" if regime == "BLUE" else "Red"
if regime == "NO_TRADE":
    regime_color = "Gray"

# Weekend guard — simple, no formatting tricks
if regime == "NO_TRADE":
    st.error("MARKET CLOSED — AuraTrade in Standby")
    st.write("Trading is disabled on weekends and holidays.")
    st.write("The system will resume active scanning at Monday 09:30 ET.")
    st.write("Next session: Monday | Regime: RED (Trap & Revert)")
    st.stop()

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

# Market Structure
st.subheader("Market Structure")

if st.session_state["price_data"].empty:
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
            st.write(f"{s['type']} at {s['price']} -> {s['direction']}")
    else:
        st.write("None detected")

st.divider()

# Fair Value Gaps
st.subheader("Fair Value Gaps")

all_fvgs = detect_fvg(price_data)
active_fvgs = [f for f in all_fvgs if not f.filled]

if active_fvgs:
    fvg_data = []
    for f in active_fvgs:
        fvg_data.append({
            "Direction": "Bullish" if f.is_bullish else "Bearish",
            "Zone": f"{f.bottom:.2f} – {f.top:.2f}",
            "Mid": f"{f.mid():.2f}",
            "Ticks": f"{f.height_ticks():.1f}",
            "Age (bars)": f.age_bars,
            "Source": f.source,
        })
    st.dataframe(pd.DataFrame(fvg_data), use_container_width=True)
else:
    st.info("No active Fair Value Gaps detected. Waiting for displacement...")

# Holy Grail Entry Signals
st.subheader("Holy Grail Entry Signals")

rg = st.session_state["risk_guard"]
if rg.can_trade():
    signal = evaluate_entry(
        price_data=price_data,
        vwap=vwap,
        ema9=ema9,
        regime=regime,
        key_levels=structure.get("key_levels", {}),
        active_position=st.session_state["active_position"],
        product=product,
    )

    if signal:
        st.session_state["last_signal"] = signal

        sig_col1, sig_col2, sig_col3 = st.columns(3)
        with sig_col1:
            st.metric("Direction", signal.direction.upper())
            st.metric("Confidence", f"{signal.confidence:.0%}")
        with sig_col2:
            st.metric("Entry Price", f"${signal.entry_price:,.2f}")
            st.metric("Stop Loss", f"${signal.stop_loss:,.2f}")
        with sig_col3:
            st.metric("Target", f"${signal.target:,.2f}")
            st.metric("R:R", f"{signal.rr_ratio}:1")

        st.info(f"Reason: {signal.reason}")

        if st.button("EXECUTE ENTRY", type="primary"):
            if st.session_state["connected"] and st.session_state["client"]:
                client = st.session_state["client"]
                bracket = client.place_bracket_order(
                    entry_price=signal.entry_price,
                    stop_price=signal.stop_loss,
                    target_price=signal.target,
                    contracts=signal.contracts,
                    direction=signal.direction,
                    product=product,
                )
                if bracket:
                    st.success(f"Bracket order placed! Entry: {signal.entry_price}")
                    journal_entry = {
                        "timestamp": datetime.now(EASTERN),
                        "direction": signal.direction,
                        "entry": signal.entry_price,
                        "stop": signal.stop_loss,
                        "target": signal.target,
                        "contracts": signal.contracts,
                        "regime": regime,
                        "reason": signal.reason,
                        "product": product,
                    }
                    st.session_state["trade_history"].append(journal_entry)
                    rg.record_trade_open(signal.contracts * signal.risk_ticks * config.tick_value(product))
                else:
                    st.error("Order placement failed.")
            else:
                st.warning("Simulated Mode — no live order placed.")
                journal_entry = {
                    "timestamp": datetime.now(EASTERN),
                    "direction": signal.direction,
                    "entry": signal.entry_price,
                    "stop": signal.stop_loss,
                    "target": signal.target,
                    "contracts": signal.contracts,
                    "regime": regime,
                    "reason": signal.reason,
                    "product": product,
                }
                st.session_state["trade_history"].append(journal_entry)
                rg.record_trade_open(0)
    else:
        st.info("No valid Holy Grail setup detected. Waiting for level reclaim + FVG + retest...")
else:
    st.error("Cannot trade — daily stop reached, max trades taken, or outside market hours.")

# Active Position Monitor
st.divider()
st.subheader("Active Position")

active = st.session_state["active_position"]
if active:
    pos_col1, pos_col2, pos_col3 = st.columns(3)
    with pos_col1:
        st.metric("Direction", active.direction.upper())
        st.metric("Contracts", active.contracts)
    with pos_col2:
        st.metric("Entry", f"${active.entry_price:,.2f}")
        st.metric("Unrealized PnL", f"${active.unrealized_pnl:,.2f}")
    with pos_col3:
        st.metric("Target", f"${active.initial_target:,.2f}")
        st.metric("Pyramids", active.pyramid_count)

    if should_remove_quickly(active, price_data, ema9):
        st.error("REMOVE QUICKLY triggered — price closed opposite side of 9-EMA!")
        if st.button("Confirm Exit", type="secondary"):
            if st.session_state["connected"] and st.session_state["client"]:
                st.session_state["client"].flatten_position(product)
            realized = active.unrealized_pnl
            rg.record_trade_pnl(realized)
            st.session_state["active_position"] = None
            st.success("Position exited.")
            st.rerun()
else:
    st.write("No active position. System scanning for Holy Grail setups...")

# Trade Journal
st.divider()
st.subheader("Live Journal — AI Analysis")

if st.session_state["trade_history"]:
    for entry in reversed(st.session_state["trade_history"][-10:]):
        with st.expander(f"{entry['timestamp'].strftime('%H:%M:%S')} | {entry['direction'].upper()} @ {entry['entry']}"):
            st.write(f"Product: {entry['product']}")
            st.write(f"Entry: ${entry['entry']:,.2f}")
            st.write(f"Stop: ${entry['stop']:,.2f}")
            st.write(f"Target: ${entry['target']:,.2f}")
            st.write(f"Contracts: {entry['contracts']}")
            st.write(f"Regime: {entry['regime']}")
            st.write(f"Reason: {entry['reason']}")

            analysis = analyze_trade(entry, entry["regime"], list_patterns())
            st.markdown(f"AI Analysis: {analysis}")
else:
    st.info("No trades recorded yet. Journal will populate when entries execute.")

st.divider()
st.caption("AuraTrade v1.0 | Prop Firm Safe by Design | NOT FINANCIAL ADVICE")
