"""
Regime Classifier
-----------------
Determines the trading regime (BLUE = Trend Runner, RED = Trap & Revert)
based on day-of-week and market structure confirmation.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
import pandas as pd
import numpy as np

import config

logger = logging.getLogger(__name__)


def classify_regime(day_of_week: int, market_structure: Optional[Dict[str, Any]] = None) -> str:
    """
    Classify trading regime for the current session.

    Parameters
    ----------
    day_of_week : int
        0=Monday, 1=Tuesday, ..., 6=Sunday.
    market_structure : dict, optional
        Output from detect_market_structure(). Used for confirmation/bias.

    Returns
    -------
    str
        "BLUE" for Trend Runner (Tue/Wed/Thu)
        "RED"  for Trap & Revert (Mon/Fri)
    """
    # Primary signal: day of week
    base_regime = config.get_regime_by_day(day_of_week)
    regime_name = base_regime.value

    # Secondary: market structure can shift regime if extreme divergence
    if market_structure is not None:
        regime_name = _confirm_regime_with_structure(regime_name, market_structure)

    logger.info(f"Regime classified: {regime_name} (day={day_of_week}, structure={market_structure is not None})")
    return regime_name


def _confirm_regime_with_structure(base_regime: str, market_structure: Dict[str, Any]) -> str:
    """
    Adjust regime if market structure strongly contradicts day-of-week bias.

    Logic
    -----
    • BLUE day with strongly bearish structure  (-0.7+ trend_score) -> RED_CAUTIOUS
    • RED day with strongly bullish structure   (+0.7+ trend_score) -> BLUE_CAUTIOUS
    • Extreme volatility (volatility_percentile > 0.85) -> cautious regime regardless
    """
    trend_score = market_structure.get("trend_score", 0.0)   # -1.0 bearish … +1.0 bullish
    volatility_percentile = market_structure.get("volatility_percentile", 0.0)

    # Extreme volatility overrides everything (e.g. FOMC day)
    if volatility_percentile > 0.85:
        if base_regime == "BLUE":
            return "BLUE_CAUTIOUS"
        return "RED_CAUTIOUS"

    # Strong counter-trend structure on BLUE day -> RED_CAUTIOUS
    if base_regime == "BLUE" and trend_score <= -0.7:
        return "RED_CAUTIOUS"

    # Strong counter-trend structure on RED day -> BLUE_CAUTIOUS
    if base_regime == "RED" and trend_score >= 0.7:
        return "BLUE_CAUTIOUS"

    return base_regime


def get_regime_context(regime: str) -> Dict[str, Any]:
    """
    Return trading rules and parameters for the specified regime.

    Parameters
    ----------
    regime : str
        "BLUE" or "RED"

    Returns
    -------
    dict
        Contains pyramiding flag, target type, bias, stop style, etc.
    """
    ctx = config.REGIME_CONTEXT.get(regime, config.REGIME_CONTEXT["RED"]).copy()
    ctx["regime"] = regime
    return ctx


def detect_market_structure(price_data: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyze market structure from OHLC + VWAP DataFrame.

    Expected columns: open, high, low, close, vwap (optional), volume

    Returns
    -------
    dict
        {
            "price_vs_vwap": "above" | "below" | "at",
            "trend_direction": "up" | "down" | "chop",
            "trend_score": float,          # -1.0 … +1.0
            "structure": "bullish" | "bearish" | "neutral",
            "bias": "long" | "short" | "neutral",
            "key_levels": {
                "session_high": float,
                "session_low": float,
                "vwap": float,
                "ema9": float,
            },
            "liquidity_sweeps": List[str]  # levels swept above/below
        }
    """
    if price_data.empty or len(price_data) < 10:
        logger.warning("Insufficient price data for market structure detection.")
        return _empty_structure()

    df = price_data.copy()
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest

    # Price vs VWAP
    vwap = latest.get("vwap", latest["close"])
    price_vs_vwap = "above" if latest["close"] > vwap * 1.0002 else \
                    "below" if latest["close"] < vwap * 0.9998 else "at"

    # Trend direction via slope of last N closes and highs/lows
    lookback = min(20, len(df) // 2)
    recent = df.tail(lookback)
    hh_ll_score = _higher_highs_lower_lows_score(recent)
    slope = np.polyfit(range(len(recent)), recent["close"].values, 1)[0]

    if slope > recent["close"].std() * 0.1 and hh_ll_score > 0.3:
        trend_direction = "up"
    elif slope < -recent["close"].std() * 0.1 and hh_ll_score < -0.3:
        trend_direction = "down"
    else:
        trend_direction = "chop"

    # Trend score composite
    vwap_score = 1.0 if price_vs_vwap == "above" else -1.0 if price_vs_vwap == "below" else 0.0
    trend_score = (vwap_score * 0.4) + (hh_ll_score * 0.4) + (np.sign(slope) * 0.2)
    trend_score = max(-1.0, min(1.0, trend_score))

    # Structure & bias
    if trend_score > 0.5:
        structure = "bullish"
        bias = "long"
    elif trend_score < -0.5:
        structure = "bearish"
        bias = "short"
    else:
        structure = "neutral"
        bias = "neutral"

    # Session high / low from available data (intraday anchor)
    session_high = df["high"].max()
    session_low = df["low"].min()

    # Detect liquidity sweeps — price poked above/below a recent extreme then reversed
    liquidity_sweeps = []
    if len(df) >= 5:
        last5 = df.tail(5)
        # Sweep of session high
        if last5["high"].max() >= session_high * 0.9999 and latest["close"] < last5["high"].max():
            if latest["close"] < last5["high"].iloc[-2]:
                liquidity_sweeps.append("session_high_sweep")
        # Sweep of session low
        if last5["low"].min() <= session_low * 1.0001 and latest["close"] > last5["low"].min():
            if latest["close"] > last5["low"].iloc[-2]:
                liquidity_sweeps.append("session_low_sweep")

    # EMA9
    ema9 = latest.get("ema9", latest["close"])

    return {
        "price_vs_vwap": price_vs_vwap,
        "trend_direction": trend_direction,
        "trend_score": round(trend_score, 3),
        "structure": structure,
        "bias": bias,
        "key_levels": {
            "session_high": round(session_high, 2),
            "session_low": round(session_low, 2),
            "vwap": round(float(vwap), 2),
            "ema9": round(float(ema9), 2),
        },
        "liquidity_sweeps": liquidity_sweeps,
    }


def _higher_highs_lower_lows_score(df: pd.DataFrame) -> float:
    """
    Score based on count of higher highs / lower lows in recent windows.
    Returns value between -1.0 (lower lows dominant) and +1.0 (higher highs dominant).
    """
    highs = df["high"].values
    lows = df["low"].values
    hh = sum(1 for i in range(1, len(highs)) if highs[i] > highs[i - 1])
    ll = sum(1 for i in range(1, len(lows)) if lows[i] < lows[i - 1])
    total = len(highs) - 1
    if total == 0:
        return 0.0
    return (hh - ll) / total


def _empty_structure() -> Dict[str, Any]:
    return {
        "price_vs_vwap": "unknown",
        "trend_direction": "chop",
        "trend_score": 0.0,
        "structure": "neutral",
        "bias": "neutral",
        "key_levels": {},
        "liquidity_sweeps": [],
    }
