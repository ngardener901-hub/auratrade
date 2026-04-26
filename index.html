"""
Fair Value Gap (FVG) Detector
-----------------------------
Identifies bullish and bearish Fair Value Gaps using the classic
3-candle displacement pattern.

Bullish FVG: Candle 1 low > Candle 3 high  →  gap = [candle3_high, candle1_low]
Bearish FVG: Candle 1 high < Candle 3 low  →  gap = [candle1_high, candle3_low]
"""

import logging
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
import pandas as pd
import numpy as np

import config

logger = logging.getLogger(__name__)


@dataclass
class FVG:
    """Represents a detected Fair Value Gap."""
    direction: str                    # "bullish" or "bearish"
    top: float                        # Upper boundary of the FVG
    bottom: float                     # Lower boundary of the FVG
    created_at: datetime              # Timestamp of candle 3 completion
    is_bullish: bool = field(repr=True)
    source_level: str = "unknown"     # Level that triggered the displacement
    filled: bool = False              # Has price returned to fill the gap?
    rejected: bool = False            # Was the FVG rejected on retest?
    retest_count: int = 0             # How many times price entered the zone
    age_bars: int = 0                 # Bars since creation
    _creation_index: int = 0          # DataFrame index where FVG was created

    def __post_init__(self):
        if not hasattr(self, 'is_bullish') or self.is_bullish is None:
            object.__setattr__(self, 'is_bullish', self.direction == "bullish")

    def mid(self) -> float:
        """Return midpoint of the FVG zone."""
        return (self.top + self.bottom) / 2.0

    def height_ticks(self, tick_size: float = 0.25) -> float:
        """Return height of FVG in ticks."""
        return round((self.top - self.bottom) / tick_size, 1)

    def contains(self, price: float) -> bool:
        """Check if price falls within the FVG zone."""
        return self.bottom <= price <= self.top


def detect_fvg(ohlc: pd.DataFrame) -> List[FVG]:
    """
    Detect all Fair Value Gaps in the provided OHLC data.

    Parameters
    ----------
    ohlc : pd.DataFrame
        Must contain columns: open, high, low, close, (optional) timestamp

    Returns
    -------
    List[FVG]
        All detected FVGs ordered by creation time (oldest first).
    """
    if ohlc.empty or len(ohlc) < 3:
        return []

    fvgs: List[FVG] = []
    df = ohlc.reset_index(drop=True)

    for i in range(len(df) - 2):
        c1 = df.iloc[i]
        c2 = df.iloc[i + 1]
        c3 = df.iloc[i + 2]

        # ── Bullish FVG: candle1.low > candle3.high ──
        if c1["low"] > c3["high"]:
            displacement = c1["low"] - c3["high"]
            min_disp = config.FVG_MIN_DISPLACEMENT_TICKS * config.TICK_SIZE_MNQ
            if displacement >= min_disp:
                ts = c3.get("timestamp", pd.Timestamp.now())
                if isinstance(ts, (int, float)):
                    ts = pd.to_datetime(ts, unit='ms')
                fvgs.append(FVG(
                    direction="bullish",
                    top=round(float(c1["low"]), 2),
                    bottom=round(float(c3["high"]), 2),
                    created_at=ts,
                    is_bullish=True,
                    source_level="displacement",
                    _creation_index=i + 2,
                ))

        # ── Bearish FVG: candle1.high < candle3.low ──
        if c1["high"] < c3["low"]:
            displacement = c3["low"] - c1["high"]
            min_disp = config.FVG_MIN_DISPLACEMENT_TICKS * config.TICK_SIZE_MNQ
            if displacement >= min_disp:
                ts = c3.get("timestamp", pd.Timestamp.now())
                if isinstance(ts, (int, float)):
                    ts = pd.to_datetime(ts, unit='ms')
                fvgs.append(FVG(
                    direction="bearish",
                    top=round(float(c3["low"]), 2),
                    bottom=round(float(c1["high"]), 2),
                    created_at=ts,
                    is_bullish=False,
                    source_level="displacement",
                    _creation_index=i + 2,
                ))

    # Update age for each FVG using stored creation index
    for fvg in fvgs:
        fvg.age_bars = len(df) - fvg._creation_index - 1

    logger.info(f"Detected {len(fvgs)} FVGs ({sum(1 for f in fvgs if f.is_bullish)} bullish, {sum(1 for f in fvgs if not f.is_bullish)} bearish)")
    return fvgs


def detect_fvg_with_level(
    ohlc: pd.DataFrame,
    level_price: float,
    level_name: str,
    window: int = 10
) -> List[FVG]:
    """
    Detect FVGs that formed after a sweep/reclaim of a specific level.

    Parameters
    ----------
    ohlc : pd.DataFrame
    level_price : float
        The key level that was swept.
    level_name : str
        Human-readable name (e.g. "London_High").
    window : int
        Max bars after sweep to look for displacement FVG.

    Returns
    -------
    List[FVG]
        FVGs tagged with the source level.
    """
    if ohlc.empty or len(ohlc) < 3:
        return []

    df = ohlc.reset_index(drop=True)
    fvgs: List[FVG] = []

    # Find bars where price swept the level then reversed
    for i in range(len(df) - window - 2):
        sweep_high = df.iloc[i]["high"] >= level_price
        sweep_low = df.iloc[i]["low"] <= level_price

        if not (sweep_high or sweep_low):
            continue

        # Look for displacement FVG within window
        for j in range(i + 1, min(i + window, len(df) - 2)):
            c1 = df.iloc[j]
            c2 = df.iloc[j + 1]
            c3 = df.iloc[j + 2]

            if sweep_low and (c1["low"] > c3["high"]):
                displacement = c1["low"] - c3["high"]
                if displacement >= config.FVG_MIN_DISPLACEMENT_TICKS * config.TICK_SIZE_MNQ:
                    ts = c3.get("timestamp", pd.Timestamp.now())
                    fvgs.append(FVG(
                        direction="bullish",
                        top=round(float(c1["low"]), 2),
                        bottom=round(float(c3["high"]), 2),
                        created_at=ts,
                        is_bullish=True,
                        source_level=level_name,
                        _creation_index=j + 2,
                    ))
                    break

            if sweep_high and (c1["high"] < c3["low"]):
                displacement = c3["low"] - c1["high"]
                if displacement >= config.FVG_MIN_DISPLACEMENT_TICKS * config.TICK_SIZE_MNQ:
                    ts = c3.get("timestamp", pd.Timestamp.now())
                    fvgs.append(FVG(
                        direction="bearish",
                        top=round(float(c3["low"]), 2),
                        bottom=round(float(c1["high"]), 2),
                        created_at=ts,
                        is_bullish=False,
                        source_level=level_name,
                        _creation_index=j + 2,
                    ))
                    break

    return fvgs


def update_fvg_status(fvgs: List[FVG], ohlc: pd.DataFrame) -> None:
    """
    Update age_bars and filled status for all FVGs based on current OHLC data.

    Parameters
    ----------
    fvgs : List[FVG]
        Existing FVGs to update in place.
    ohlc : pd.DataFrame
        Current OHLC DataFrame.
    """
    if ohlc.empty:
        return

    df = ohlc.reset_index(drop=True)
    current_len = len(df)

    for fvg in fvgs:
        # Update age
        fvg.age_bars = current_len - fvg._creation_index - 1
        if fvg.age_bars < 0:
            fvg.age_bars = 0

        if fvg.filled:
            continue

        # Look at bars strictly AFTER the FVG creation bar
        post_creation = df.iloc[fvg._creation_index + 1:]
        if post_creation.empty:
            continue

        # Check per-bar containment: bar must enter the FVG zone
        for _, row in post_creation.iterrows():
            low = float(row["low"])
            high = float(row["high"])
            close = float(row["close"])

            # A bar enters the zone if low <= top AND high >= bottom
            entered_zone = (low <= fvg.top) and (high >= fvg.bottom)
            if not entered_zone:
                continue

            # Increment retest count each time price enters the zone
            fvg.retest_count += 1

            # Filled: price entered the zone AND closed beyond it
            if fvg.is_bullish:
                # For bullish FVG: filled if close <= bottom (price closed below the gap)
                if close <= fvg.bottom:
                    fvg.filled = True
                    break
            else:
                # For bearish FVG: filled if close >= top (price closed above the gap)
                if close >= fvg.top:
                    fvg.filled = True
                    break


def is_fvg_filled(fvg: FVG, price_data: pd.DataFrame) -> bool:
    """
    Check if price has returned to fill the FVG zone.

    Parameters
    ----------
    fvg : FVG
    price_data : pd.DataFrame
        Recent OHLC data (should start after FVG creation).

    Returns
    -------
    bool
    """
    if price_data.empty:
        return False

    for _, row in price_data.iterrows():
        low = float(row["low"])
        high = float(row["high"])
        close = float(row["close"])

        # Bar must actually enter the FVG zone
        entered_zone = (low <= fvg.top) and (high >= fvg.bottom)
        if not entered_zone:
            continue

        if fvg.is_bullish:
            # Bullish FVG filled when price closes at or below the bottom of the gap
            if close <= fvg.bottom:
                return True
        else:
            # Bearish FVG filled when price closes at or above the top of the gap
            if close >= fvg.top:
                return True

    return False


def is_fvg_rejected(ohlc_slice: pd.DataFrame, fvg: FVG) -> bool:
    """
    Check for wick rejection within the FVG zone.
    A rejection occurs when price enters the FVG but closes outside of it.

    Parameters
    ----------
    ohlc_slice : pd.DataFrame
        Candles during the retest (after FVG creation).
    fvg : FVG

    Returns
    -------
    bool
    """
    if ohlc_slice.empty:
        return False

    for _, row in ohlc_slice.iterrows():
        if fvg.contains(row["low"]) or fvg.contains(row["high"]):
            # Price touched the zone
            if fvg.is_bullish:
                # For bullish FVG: rejection = close below the zone
                if row["close"] < fvg.bottom:
                    return True
            else:
                # For bearish FVG: rejection = close above the zone
                if row["close"] > fvg.top:
                    return True
    return False


def is_fvg_valid_for_entry(fvg: FVG, current_bar_count: int) -> bool:
    """
    Check if FVG is still valid for entry consideration.
    - Not too old
    - Not already filled (if we want virgin FVGs)
    """
    if fvg.age_bars > config.FVG_MAX_AGE_BARS:
        return False
    if fvg.filled and fvg.retest_count > 0:
        return False
    return True


def get_nearest_active_fvg(
    price: float,
    fvgs: List[FVG],
    direction: str = "bullish",
    max_age: int = 30
) -> Optional[FVG]:
    """
    Return the nearest active FVG to current price.

    Parameters
    ----------
    price : float
    fvgs : List[FVG]
    direction : str
        "bullish" or "bearish"
    max_age : int
        Max bars since creation.

    Returns
    -------
    FVG or None
    """
    candidates = [
        f for f in fvgs
        if f.direction == direction
        and f.age_bars <= max_age
        and not f.filled
    ]
    if not candidates:
        return None

    # Return the one whose mid is closest to current price
    candidates.sort(key=lambda f: abs(f.mid() - price))
    return candidates[0]
