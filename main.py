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
if regime == "NO_TRADE":
    regime_color = "⬛"

# ─── Weekend / Holiday Banner ────────────────────────────────────────────────
if regime == "NO_TRADE":
    st.error("""
    ## ⬛ MARKET CLOSED — AuraTrade in Standby
    Trading is disabled on weekends and holidays. The system will resume active scanning at Monday 09:30 ET.
    
    **Next session:** Monday, {next_monday.strftime('%B %d')} | **Regime:** RED (Trap & Revert)
    """.format(next_monday=datetime.now(EASTERN) + timedelta(days=(7 - datetime.now(EASTERN).weekday()) % 7)))
    st.stop()  # Halt further execution — no signals, no entries, no FVG scanning

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
            st.write(f"🔸 {s['type']} at {s['price']} → {s['direction']}")
    else:
        st.write("None detected")

st.divider()

# ─── Row 3: Fair Value Gaps ──────────────────────────────────────────────────
st.subheader("🎯 Fair Value Gaps")

all_fvgs = detect_fvg(price_data)
active_fvgs = [f for f in all_fvgs if not f.filled]

if active_fvgs:
    fvg_data = []
    for f in active_fvgs:
        fvg_data.append({
            "Direction": "🟢 Bullish" if f.is_bullish else "🔴 Bearish",
            "Zone": f"{f.bottom:.2f} – {f.top:.2f}",
            "Mid": f"{f.mid():.2f}",
            "Ticks": f"{f.height_ticks():.1f}",
            "Age (bars)": f.age_bars,
            "Source": f.source,
        })
    st.dataframe(pd.DataFrame(fvg_data), use_container_width=True)
else:
    st.info("No active Fair Value Gaps detected. Waiting for displacement...")

# ─── Row 4: Holy Grail Entry Signals ─────────────────────────────────────────
st.subheader("⚡ Holy Grail Entry Signals")

# Only evaluate entries if we can trade
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

        st.info(f"**Reason:** {signal.reason}")

        # Execute button
        if st.button("🚀 EXECUTE ENTRY", type="primary"):
            if st.session_state["connected"] and st.session_state["client"]:
                # Place bracket order via Tradovate
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
                    # Record in journal
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
                    st.error("Order placement failed. Check Tradovate connection.")
            else:
                st.warning("Simulated Mode — no live order placed.")
                # Still record for journal
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
                rg.record_trade_open(0)  # Simulated — no real risk recorded
    else:
        st.info("No valid Holy Grail setup detected. Waiting for level reclaim + FVG + retest...")
else:
    st.error("❌ Cannot trade — daily stop reached, max trades taken, or outside market hours.")

# ─── Row 5: Active Position Monitor ──────────────────────────────────────────
st.subdivider()
st.subheader("📈 Active Position")

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

    # Remove Quickly check
    if should_remove_quickly(active, price_data, ema9):
        st.error("🚨 REMOVE QUICKLY triggered — price closed opposite side of 9-EMA!")
        if st.button("Confirm Exit", type="secondary"):
            if st.session_state["connected"] and st.session_state["client"]:
                st.session_state["client"].flatten_position(product)
            # Record PnL
            realized = active.unrealized_pnl  # Simplified
            rg.record_trade_pnl(realized)
            st.session_state["active_position"] = None
            st.success("Position exited.")
            st.rerun()
else:
    st.write("No active position. System scanning for Holy Grail setups...")

# ─── Row 6: Trade Journal ────────────────────────────────────────────────────
st.divider()
st.subheader("📓 Live Journal — AI Analysis")

if st.session_state["trade_history"]:
    for entry in reversed(st.session_state["trade_history"][-10:]):
        with st.expander(f"{entry['timestamp'].strftime('%H:%M:%S')} | {entry['direction'].upper()} @ {entry['entry']}"):
            st.write(f"**Product:** {entry['product']}")
            st.write(f"**Entry:** ${entry['entry']:,.2f}")
            st.write(f"**Stop:** ${entry['stop']:,.2f}")
            st.write(f"**Target:** ${entry['target']:,.2f}")
            st.write(f"**Contracts:** {entry['contracts']}")
            st.write(f"**Regime:** {entry['regime']}")
            st.write(f"**Reason:** {entry['reason']}")

            # AI analysis
            analysis = analyze_trade(entry, entry["regime"], list_patterns())
            st.markdown(f"**🤖 AI Analysis:** {analysis}")
else:
    st.info("No trades recorded yet. Journal will populate when entries execute.")

# ─── Footer ──────────────────────────────────────────────────────────────────
st.divider()
st.caption("AuraTrade v1.0 | Prop Firm Safe by Design | NOT FINANCIAL ADVICE")        ],
        success_factors=[
            "Prior session high was liquidity pool",
            "Displacement FVG showed buyer aggression",
            "VWAP stayed above FVG = strong trend",
        ],
        notes="Expansion play. Previous session high as target.",
    ),
    PatternExample(
        id=3,
        name="Mid-Week Long, VWAP Reclaim + FVG",
        regime="BLUE",
        direction="long",
        key_features=[
            "london_low_sweep_and_reclaim",
            "bullish_fvg_formed",
            "retest_at_vwap",
            "ema9_support",
        ],
        success_factors=[
            "Price reclaimed London Low",
            "Bullish FVG formed with 6-tick displacement",
            "Retest occurred at confluence with VWAP",
            "9-EMA held as trailing support",
        ],
        notes="The textbook 'Holy Grail' — all 4 criteria met.",
    ),
    PatternExample(
        id=4,
        name="Thursday Breakout Continuation",
        regime="BLUE",
        direction="long",
        key_features=[
            "pre_market_high_sweep",
            "bullish_fvg_above_vwap",
            "no_retest_immediate_run",
            "pyramid_on_second_fvg",
        ],
        success_factors=[
            "Pre-market high sweep cleared stops",
            "Immediate displacement without deep retest",
            "Second FVG allowed pyramid add",
        ],
        notes="Aggressive BLUE play. Pyramid added 1 contract at 1R profit.",
    ),
    PatternExample(
        id=5,
        name="Tuesday Afternoon Pullback Long",
        regime="BLUE",
        direction="long",
        key_features=[
            "morning_expansion",
            "pullback_to_vwap",
            "bullish_fvg_on_pullback",
            "continuation_to_highs",
        ],
        success_factors=[
            "Morning trend established direction",
            "VWAP held on pullback = institutional interest",
            "Bullish FVG in pullback = buyer absorption",
        ],
        notes="Afternoon session continuation. Entered on VWAP + FVG confluence.",
    ),
    PatternExample(
        id=6,
        name="Monday Trap Short",
        regime="RED",
        direction="short",
        key_features=[
            "london_high_breakout_fake",
            "price_reclaimed_below_london_high",
            "bearish_fvg_at_reclaim",
            "vwap_rejection",
        ],
        success_factors=[
            "False breakout above London High trapped longs",
            "Reclaim below London High = structure shift",
            "Bearish FVG formed at VWAP rejection",
            "Target = VWAP (tight, no pyramiding)",
        ],
        notes="Classic RED regime Monday trap. Tight target, quick exit.",
    ),
    PatternExample(
        id=7,
        name="Friday Reversal Short",
        regime="RED",
        direction="short",
        key_features=[
            "overnight_high_sweep",
            "bearish_engulfing_post_sweep",
            "bearish_fvg_displacement",
            "vwap_cross_down",
        ],
        success_factors=[
            "Overnight high sweep in early session",
            "Bearish FVG after sweep = seller control",
            "VWAP crossed and held as resistance",
        ],
        notes="Friday fade. End-of-week profit taking pattern.",
    ),
    PatternExample(
        id=8,
        name="Monday Morning Fade",
        regime="RED",
        direction="short",
        key_features=[
            "gap_up_open",
            "prev_nyam_high_sweep",
            "immediate_reversal",
            "bearish_fvg_with_vwap_below",
        ],
        success_factors=[
            "Gap up swept prior NYAM high = liquidity target",
            "Immediate reversal showed seller absorption",
            "Bearish FVG confluence with VWAP below",
        ],
        notes="Gap-and-crap Monday. RED regime characteristic.",
    ),
    PatternExample(
        id=9,
        name="Friday Trap Long (Rare)",
        regime="RED",
        direction="long",
        key_features=[
            "london_low_sweep",
            "quick_reclaim",
            "small_bullish_fvg",
            "vwap_bounce",
        ],
        success_factors=[
            "London Low sweep flushed weak longs",
            "Quick reclaim showed demand at level",
            "Small FVG + VWAP bounce = scalp only",
        ],
        notes="Counter-trend RED play. Only for experienced discretion.",
    ),
    PatternExample(
        id=10,
        name="Wednesday VWAP Failed Break Short",
        regime="BLUE",
        direction="short",
        key_features=[
            "vwap_test_from_below",
            "failed_break_above_vwap",
            "bearish_fvg_at_vwap",
            "trend_still_up_but_chop",
        ],
        success_factors=[
            "VWAP rejection in BLUE = caution flag",
            "Bearish FVG at VWAP = short-term fade",
            "Small size, tight stop, quick target",
        ],
        notes="BLUE regime counter-trend. Only taken when confidence > 75%.",
    ),
    PatternExample(
        id=11,
        name="Thursday High-Confidence Pyramid",
        regime="BLUE",
        direction="long",
        key_features=[
            "first_trade_already_1r",
            "second_bullish_fvg_formed",
            "same_direction",
            "vwap_far_below_add",
        ],
        success_factors=[
            "First position profitable = edge confirmed",
            "Second FVG at higher level = trend strength",
            "Pyramid added within risk limits",
        ],
        notes="Pyramiding example. Added 1 MNQ contract at +1.2R on first position.",
    ),
]


def analyze_trade(trade: Dict[str, Any], regime: str, pattern_db: Optional[List[PatternExample]] = None) -> str:
    """
    AI analysis: match a completed trade against the 11 training examples.

    Parameters
    ----------
    trade : dict
        Must contain keys: direction, entry_price, exit_price, pnl,
        fvg_direction, sweep_level, vwap_at_entry, ema9_aligned.
    regime : str
        "BLUE" or "RED"
    pattern_db : list, optional
        Override default pattern database.

    Returns
    -------
    str
        Human-readable analysis with pattern match and success factors.
    """
    if pattern_db is None:
        pattern_db = PATTERN_DATABASE

    # Filter to regime-relevant patterns
    candidates = [p for p in pattern_db if p.regime == regime]
    if not candidates:
        candidates = pattern_db

    # Score each pattern by feature overlap
    scored_patterns = []
    trade_features = _extract_trade_features(trade)

    for pattern in candidates:
        score = _pattern_similarity(pattern, trade_features)
        scored_patterns.append((score, pattern))

    scored_patterns.sort(key=lambda x: x[0], reverse=True)
    best_score, best_pattern = scored_patterns[0]

    # Build narrative
    lines = []
    lines.append(f"Pattern Match: #{best_pattern.id} – {best_pattern.name}")
    lines.append(f"Match Confidence: {best_score:.0%}")
    lines.append("")
    lines.append("Success Factors:")
    for factor in best_pattern.success_factors:
        match_indicator = "[MATCH]" if any(kw in factor.lower() for kw in trade_features) else "[context]"
        lines.append(f"  {match_indicator} {factor}")
    lines.append("")
    lines.append(f"Notes: {best_pattern.notes}")

    if trade.get("pnl", 0) > 0:
        lines.append(f"Result: +${trade['pnl']:.2f} profit. Pattern validation strengthened.")
    else:
        lines.append(f"Result: ${trade['pnl']:.2f} loss. Review deviation from pattern criteria.")

    return "\n".join(lines)


def _extract_trade_features(trade: Dict[str, Any]) -> List[str]:
    """Extract searchable feature strings from a trade record."""
    features = []
    direction = trade.get("direction", "")
    if direction:
        features.append(direction.lower())
    if trade.get("fvg_direction"):
        features.append(trade["fvg_direction"].lower())
    if trade.get("sweep_level"):
        features.append(trade["sweep_level"].lower().replace("_", " "))
    if trade.get("vwap_aligned"):
        features.append("vwap")
    if trade.get("ema9_aligned"):
        features.append("ema9")
    if trade.get("pyramid"):
        features.append("pyramid")
    return features


def _pattern_similarity(pattern: PatternExample, trade_features: List[str]) -> float:
    """
    Compute similarity score between pattern features and trade.
    Uses keyword overlap + fuzzy string matching.
    """
    if not pattern.key_features:
        return 0.0

    pattern_text = " ".join(pattern.key_features).lower()
    trade_text = " ".join(trade_features).lower()

    # Keyword hits
    hits = sum(1 for feat in trade_features if feat in pattern_text)
    keyword_score = hits / len(pattern.key_features) if pattern.key_features else 0

    # Fuzzy similarity
    fuzzy_score = SequenceMatcher(None, pattern_text, trade_text).ratio()

    return round(keyword_score * 0.7 + fuzzy_score * 0.3, 3)


def get_pattern_by_id(pattern_id: int) -> Optional[PatternExample]:
    """Return a specific pattern from the database."""
    for p in PATTERN_DATABASE:
        if p.id == pattern_id:
            return p
    return None


def list_patterns(regime: Optional[str] = None) -> List[str]:
    """Return formatted list of all patterns (optionally filtered by regime)."""
    patterns = PATTERN_DATABASE if regime is None else [p for p in PATTERN_DATABASE if p.regime == regime]
    return [f"#{p.id} [{p.regime}] {p.name} — {p.direction}" for p in patterns]
