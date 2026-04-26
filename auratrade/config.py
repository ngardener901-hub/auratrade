"""
AuraTrade Configuration
-----------------------
All settings, parameters, and constants for the AuraTrade
AI Trading Assistant for MES/MNQ futures.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List
from enum import Enum


class Regime(Enum):
    BLUE = "BLUE"         # Tue/Wed/Thu — Trend Runner
    RED = "RED"           # Mon/Fri — Trap & Revert
    NO_TRADE = "NO_TRADE"  # Weekend / Holiday — Market Closed


class Product(Enum):
    MES = "MES"    # Micro E-mini S&P 500
    MNQ = "MNQ"    # Micro E-mini Nasdaq-100


# ─── Account & Risk Settings ────────────────────────────────────────────────

ACCOUNT_BALANCE: float = 50_000.0          # Prop firm account size
DAILY_STOP_LOSS: float = 300.0               # Hard daily stop (USD)
MAX_TRADES_PER_SESSION: int = 2            # Max trades 9:30 AM – 4:00 PM ET
TRAILING_DRAWDOWN: float = 2_000.0          # Trailing drawdown from peak
MAX_CONTRACTS_MNQ: int = 2                   # Max contracts for MNQ
MAX_CONTRACTS_MES: int = 1                   # Max contracts for MES
TICK_SIZE_MNQ: float = 0.25                  # MNQ tick size (USD)
TICK_SIZE_MES: float = 0.25                  # MES tick size (USD)
TICK_VALUE_MNQ: float = 0.50                 # USD per tick MNQ
TICK_VALUE_MES: float = 1.25                 # USD per tick MES

# ─── Market Hours (Eastern Time) ─────────────────────────────────────────────

MARKET_OPEN_HOUR: int = 9
MARKET_OPEN_MINUTE: int = 30
MARKET_CLOSE_HOUR: int = 16
MARKET_CLOSE_MINUTE: int = 0

# ─── Regime Mapping ──────────────────────────────────────────────────────────

REGIME_BY_DAY: Dict[int, Regime] = {
    0: Regime.RED,        # Monday
    1: Regime.BLUE,       # Tuesday
    2: Regime.BLUE,       # Wednesday
    3: Regime.BLUE,       # Thursday
    4: Regime.RED,        # Friday
    5: Regime.NO_TRADE,   # Saturday — Market closed
    6: Regime.NO_TRADE,   # Sunday — Market closed
}

# ─── FVG Detection Parameters ────────────────────────────────────────────────

FVG_MIN_DISPLACEMENT_TICKS: int = 4          # Minimum 4-tick displacement
FVG_MAX_RETEST_WAIT_BARS: int = 20           # Bars to wait for retest
FVG_MAX_AGE_BARS: int = 50                   # Maximum age of FVG to consider

# ─── Technical Indicators ────────────────────────────────────────────────────

EMA_PERIOD: int = 9
VWAP_SESSION_START: str = "09:30"            # VWAP anchored to NY open

# ─── Entry / Exit Parameters ─────────────────────────────────────────────────

PYRAMID_MIN_PROFIT_R: float = 1.0             # Need 1R profit before pyramiding
ATR_PERIOD: int = 14                         # ATR lookback for stop placement
STOP_BUFFER_TICKS: int = 2                   # Extra ticks beyond structure
TARGET_R_DEFAULT: float = 2.0                # Default 2R target
TIGHT_TARGET_R_RED: float = 1.5                # Tighter target in RED regime

# ─── Tradovate API Configuration ─────────────────────────────────────────────

TRADOVATE_BASE_URL: str = os.environ.get(
    "TRADOVATE_BASE_URL",
    "https://demo.tradovateapi.com/v1"       # Demo endpoint by default
)
TRADOVATE_WS_URL: str = os.environ.get(
    "TRADOVATE_WS_URL",
    "wss://demo.tradovateapi.com/v1/websocket"
)
TRADOVATE_USERNAME: str = os.environ.get("TRADOVATE_USERNAME", "")
TRADOVATE_PASSWORD: str = os.environ.get("TRADOVATE_PASSWORD", "")
TRADOVATE_APP_ID: str = os.environ.get("TRADOVATE_APP_ID", "AuraTrade")
TRADOVATE_APP_VERSION: str = os.environ.get("TRADOVATE_APP_VERSION", "1.0.0")
TRADOVATE_DEVICE_ID: str = os.environ.get("TRADOVATE_DEVICE_ID", "auratrade-device-001")
TRADOVATE_CID: int = int(os.environ.get("TRADOVATE_CID", "0"))  # Contract ID for MNQ/MES
TRADOVATE_ACCOUNT_ID: int = int(os.environ.get("TRADOVATE_ACCOUNT_ID", "0"))
TRADOVATE_MAX_RETRIES: int = 3
TRADOVATE_RETRY_DELAY_SECONDS: float = 1.5

# ─── Product Specifications ──────────────────────────────────────────────────

PRODUCT_SPECS: Dict[str, Dict[str, any]] = {
    "MNQ": {
        "tick_size": TICK_SIZE_MNQ,
        "tick_value": TICK_VALUE_MNQ,
        "max_contracts": MAX_CONTRACTS_MNQ,
        "description": "Micro E-mini Nasdaq-100",
        "session_volume": "high",
        "margin_day": 500,
    },
    "MES": {
        "tick_size": TICK_SIZE_MES,
        "tick_value": TICK_VALUE_MES,
        "max_contracts": MAX_CONTRACTS_MES,
        "description": "Micro E-mini S&P 500",
        "session_volume": "high",
        "margin_day": 500,
    },
}

# ─── Regime Contexts ─────────────────────────────────────────────────────────

REGIME_CONTEXT: Dict[str, Dict[str, any]] = {
    "BLUE": {
        "name": "Trend Runner",
        "description": (
            "Mid-week trend continuation. Look for FVG retests that "
            "ALIGN with VWAP for expansion moves. Pyramiding enabled."
        ),
        "pyramiding": True,
        "target_type": "expansion",          # Previous session H/L or expansion
        "entry_bias": "with_trend",
        "tight_stops": False,
        "confidence_boost": 0.15,              # +15% confidence for BLUE alignment
    },
    "RED": {
        "name": "Trap & Revert",
        "description": (
            "Mon/Fri reversal traps. Failed breakouts above London High "
            "or below London Low. Reclaim of level. No pyramiding."
        ),
        "pyramiding": False,
        "target_type": "tight",                # VWAP, London H/L only
        "entry_bias": "counter_trend",
        "tight_stops": True,
        "confidence_boost": 0.10,              # +10% for RED alignment
    },
    "BLUE_CAUTIOUS": {
        "name": "Trend Runner (Cautious)",
        "description": (
            "Counter-trend bullish structure on a RED day. Half size, "
            "no pyramiding, tighter stops."
        ),
        "pyramiding": False,
        "target_type": "tight",
        "entry_bias": "with_trend",
        "tight_stops": True,
        "confidence_boost": 0.05,
        "contract_limit_multiplier": 0.5,     # Half-size position limits
    },
    "RED_CAUTIOUS": {
        "name": "Trap & Revert (Cautious)",
        "description": (
            "Counter-trend bearish structure on a BLUE day. Half size, "
            "no pyramiding, tighter stops."
        ),
        "pyramiding": False,
        "target_type": "tight",
        "entry_bias": "counter_trend",
        "tight_stops": True,
        "confidence_boost": 0.05,
        "contract_limit_multiplier": 0.5,     # Half-size position limits
    },
    "NO_TRADE": {
        "name": "Market Closed",
        "description": (
            "Weekend or market holiday. No trading. System in standby. "
            "Globex reopens Sunday 18:00 ET, but trading resumes Monday."
        ),
        "pyramiding": False,
        "target_type": "none",
        "entry_bias": "none",
        "tight_stops": True,
        "confidence_boost": 0.0,
        "contract_limit_multiplier": 0.0,     # Zero contracts allowed
        "can_trade": False,
    },
}

# ─── Key Levels (Session-Based) ──────────────────────────────────────────────

LEVEL_NAMES: List[str] = [
    "London_High",
    "London_Low",
    "PreMarket_High",
    "PreMarket_Low",
    "Prev_NYAM_High",
    "Prev_NYAM_Low",
    "Prev_Session_High",
    "Prev_Session_Low",
    "Overnight_High",
    "Overnight_Low",
]

# ─── Logging ─────────────────────────────────────────────────────────────────

LOG_LEVEL: str = "INFO"
LOG_FORMAT: str = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"

# ─── Helper Functions ────────────────────────────────────────────────────────

def get_regime_by_day(day_of_week: int) -> Regime:
    """Return the default regime for a given day of week (0=Monday … 6=Sunday)."""
    return REGIME_BY_DAY.get(day_of_week, Regime.RED)


def get_max_contracts(product: str) -> int:
    """Return max allowed contracts for a product."""
    return PRODUCT_SPECS.get(product, {}).get("max_contracts", 1)


def get_regime_context(regime: str) -> Dict[str, any]:
    """Return the trading-rule context for a regime string."""
    return REGIME_CONTEXT.get(regime, REGIME_CONTEXT["RED"])


def tick_size(product: str) -> float:
    """Return tick size for a product."""
    return PRODUCT_SPECS.get(product, {}).get("tick_size", 0.25)


def tick_value(product: str) -> float:
    """Return USD value per tick for a product."""
    return PRODUCT_SPECS.get(product, {}).get("tick_value", 0.50)        "entry_bias": "counter_trend",
        "tight_stops": True,
        "confidence_boost": 0.05,
        "contract_limit_multiplier": 0.5,     # Half-size position limits
    },
}

# ─── Key Levels (Session-Based) ──────────────────────────────────────────────

LEVEL_NAMES: List[str] = [
    "London_High",
    "London_Low",
    "PreMarket_High",
    "PreMarket_Low",
    "Prev_NYAM_High",
    "Prev_NYAM_Low",
    "Prev_Session_High",
    "Prev_Session_Low",
    "Overnight_High",
    "Overnight_Low",
]

# ─── Logging ─────────────────────────────────────────────────────────────────

LOG_LEVEL: str = os.environ.get("AURATRADE_LOG_LEVEL", "INFO")
LOG_FORMAT: str = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"

# ─── Dashboard ───────────────────────────────────────────────────────────────

REFRESH_INTERVAL_SECONDS: int = 5            # Streamlit auto-refresh
CHART_LOOKBACK_MINUTES: int = 120              # 2-hour chart view


def get_max_contracts(product: str) -> int:
    """Return max allowed contracts for a given product."""
    return PRODUCT_SPECS.get(product, {}).get("max_contracts", 1)


def get_regime_by_day(day_of_week: int) -> Regime:
    """Return regime classification for a given day (0=Monday)."""
    return REGIME_BY_DAY.get(day_of_week, Regime.RED)
