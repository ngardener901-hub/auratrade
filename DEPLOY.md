# AuraTrade Execution Reliability & Edge-Case Audit Report
## AUDIT_RISK_2.md — Stress-Test Findings

**Auditor:** Trading Systems Reliability Engineer  
**Date:** 2025-01-28  
**Scope:** `tradovate_client.py`, `entry_engine.py`, `regime_classifier.py`, `fvg_detector.py`, `risk_guard.py`, `main.py`, `config.py`  
**Focus:** API failure modes, slippage, race conditions, market-structure edge cases, regime reliability, FVG logic bugs.

---

## Overall Reliability Rating: 2 / 10 (Prop-Firm Unsafe)

**Justification:**  
The system lacks broker-side stop-loss protection (stop is only in Streamlit memory), uses `day_of_week` as the **sole** regime signal while explicitly discarding market-structure confirmation, computes FVG age with a mathematically incorrect formula, has no position-reconciliation logic, and requires **manual button clicks** for the "Remove Quickly" emergency exit. In a prop-firm environment where a $2,000 trailing drawdown terminates the account, any one of these flaws is a deal-breaker. The combination makes the system unsuitable for live capital without major architectural fixes.

---

## 1. Regime Classifier Reliability

### 1.1 CRITICAL — `_confirm_regime_with_structure()` is a No-Op
**Severity:** CRITICAL  
**Location:** `regime_classifier.py` lines 48–59  
**Issue:** The function is documented to "adjust regime if market structure strongly contradicts day-of-week bias," but it literally returns `base_regime` unchanged. The `trend_score` and `structure_bias` variables are fetched and then discarded.

**Real-World Impact:**
| Event | Day | Regime Assigned | Actual Market | Risk |
|-------|-----|-----------------|---------------|------|
| Holiday Monday (thin volume, erratic) | Mon | RED / Trap & Revert | Mean-reversion may work, but stops can be gapped through on no liquidity | Trap & Revert on 2-tick range = whipsaw hell |
| FOMC Wednesday (50+ tick moves) | Wed | BLUE / Trend Runner | High vol, directional but with 30-tick reversals | Position sized for normal vol; stop at 2R can be hit in 30 sec |
| NFP Friday (100+ tick spike) | Fri | RED / Trap & Revert | Extreme directional breakout, then range | Stop-loss hunting, slippage on exit |
| Tuesday after 3-day weekend (gaps) | Tue | BLUE / Trend Runner | Large overnight gap, low liquidity at open | Entry at FVG mid may gap through stop before fill |

**Day-of-week classification alone is dangerous** because it ignores:
- Economic calendar (FOMC, NFP, CPI, ECB, BoE)
- Actual volatility (ATR, realized vol)
- Pre-market volume profile
- Overnight gap size

**Fix:**
```python
# regime_classifier.py — Replace _confirm_regime_with_structure()

def _confirm_regime_with_structure(
    base_regime: str,
    market_structure: Dict[str, Any],
    atr_14: float = 0.0,
    premarket_volume_pct: float = 0.0,
    gap_size_ticks: float = 0.0,
    is_holiday: bool = False,
    high_impact_news_within_2h: bool = False,
) -> str:
    """
    Adjust regime if market structure / calendar strongly contradicts
    day-of-week bias. Returns a regime name + optional caution flag.
    """
    trend_score = market_structure.get("trend_score", 0.0)
    structure_bias = market_structure.get("bias", "neutral")

    # --- Absolute trading halts ---
    if high_impact_news_within_2h and base_regime == "BLUE":
        # BLUE (trend) is especially dangerous into news;
        # downgrade to RED with extra caution
        logger.warning("HIGH-IMPACT NEWS detected — downgrading BLUE to CAUTIOUS_RED")
        return "RED_CAUTIOUS"

    if is_holiday or premarket_volume_pct < 0.3:
        logger.warning("Holiday / thin volume — downgrading to CAUTIOUS_RED")
        return "RED_CAUTIOUS"

    if gap_size_ticks > 20:
        # Large gap = potential trap day, not clean trend
        logger.warning(f"Large overnight gap ({gap_size_ticks:.0f} ticks) — regime set to RED")
        return "RED"

    # --- Structure-based override ---
    if base_regime == "BLUE":
        # BLUE expects with-trend continuation
        if trend_score < -0.6 and structure_bias == "short":
            # Strong bearish structure on a BLUE day = likely trap
            logger.warning("BLUE day but strong bearish structure — downgrading to RED")
            return "RED"
        if atr_14 > 25:  # MNQ: 25 ticks = ~$12.50 move on 1-min, very high
            logger.warning("Elevated ATR on BLUE day — capping pyramiding")
            return "BLUE_CAUTIOUS"

    elif base_regime == "RED":
        # RED expects mean-reversion; if structure is strongly trending,
        # we may be catching a falling knife
        if trend_score > 0.7 and structure_bias == "long":
            logger.warning("RED day but strong bullish trend — avoiding counter-trend shorts")
            return "RED_CAUTIOUS"

    return base_regime


# Also update classify_regime() signature and callers
# in config.py, add:
REGIME_CONTEXT["RED_CAUTIOUS"] = {
    "name": "Trap & Revert (Cautious)",
    "pyramiding": False,
    "target_type": "tight",
    "entry_bias": "counter_trend",
    "tight_stops": True,
    "confidence_boost": 0.05,
    "max_contracts_multiplier": 0.5,  # Half size
}
REGIME_CONTEXT["BLUE_CAUTIOUS"] = {
    "name": "Trend Runner (Cautious)",
    "pyramiding": False,  # Disable pyramiding in high vol
    "target_type": "tight",
    "entry_bias": "with_trend",
    "tight_stops": True,
    "confidence_boost": 0.10,
    "max_contracts_multiplier": 0.5,
}
```

**Recommended Calendar Integration (external dependency):**
```python
# Add to config.py or a new calendar module
HIGH_IMPACT_EVENTS = [
    ("FOMC", "Wednesday", 14, 0),      # 14:00 ET, typically Wed
    ("NFP", "Friday", 8, 30),           # 08:30 ET, first Friday
    ("CPI", "variable", 8, 30),        # 08:30 ET
]

def is_high_impact_news_window(dt: datetime, window_minutes: int = 120) -> bool:
    """Return True if we are within `window_minutes` of a known event."""
    # Integrate with econoday.com API or a local JSON calendar
    ...
```

---

## 2. FVG Detection Edge Cases

### 2.1 CRITICAL — `fvg.filled` is Never Updated; Old FVGs Re-Traded Forever
**Severity:** CRITICAL  
**Location:** `fvg_detector.py` lines 32, 196–218; `entry_engine.py` lines 283, 413  
**Issue:** `fvg.filled` defaults to `False` and is never set to `True`. The function `is_fvg_filled()` exists but is **never called** in the main flow. `evaluate_pyramid()` (line 283) and `_filter_candidate_fvgs()` (line 413) both filter on `not f.filled`, which is always `True`.  
**Result:** A 500-bar-old FVG that was filled and traded 2 hours ago can be re-detected, re-evaluated, and re-traded as if it were virgin.

**Fix:**
```python
# fvg_detector.py — Add update helper and call it after detection

def update_fvg_status(fvgs: List[FVG], price_data: pd.DataFrame) -> List[FVG]:
    """
    Mark FVGs as filled or rejected based on price action since creation.
    Must be called every bar with the FULL DataFrame (not just recent bars).
    """
    if price_data.empty:
        return fvgs

    for fvg in fvgs:
        if fvg.filled and fvg.rejected:
            continue  # Already known

        # Determine which bars occurred AFTER this FVG was created
        # (FVG is complete at candle i+2; we need bars after that)
        # Since detect_fvg doesn't store the creation index, we must add it:
        if not hasattr(fvg, "_creation_index"):
            continue  # Can't determine without index

        post_fvg = price_data.iloc[fvg._creation_index + 3:]
        if post_fvg.empty:
            continue

        if not fvg.filled:
            fvg.filled = is_fvg_filled(fvg, post_fvg)
            if fvg.filled:
                fvg.retest_count += 1
                logger.info(f"FVG marked FILLED at index {fvg._creation_index}")

        if not fvg.rejected:
            fvg.rejected = is_fvg_rejected(post_fvg, fvg)
            if fvg.rejected:
                logger.info(f"FVG marked REJECTED at index {fvg._creation_index}")

    return fvgs


# detect_fvg() — store creation index
# In detect_fvg(), when appending an FVG:
#    fvg = FVG(...)
#    fvg._creation_index = i + 2   # completion bar of the 3-candle pattern
#    fvgs.append(fvg)
```

Also fix `is_fvg_filled()` which has a **cross-bar contamination bug**:
```python
# fvg_detector.py — Fix is_fvg_filled()

def is_fvg_filled(fvg: FVG, price_data: pd.DataFrame) -> bool:
    """Check if price has returned to fill the FVG zone."""
    if price_data.empty:
        return False

    if fvg.is_bullish:
        # CORRECT: a SINGLE bar must have its low within [bottom, top]
        return ((price_data["low"] >= fvg.bottom) & (price_data["low"] <= fvg.top)).any()
    else:
        # CORRECT: a SINGLE bar must have its high within [bottom, top]
        return ((price_data["high"] >= fvg.bottom) & (price_data["high"] <= fvg.top)).any()
```

---

### 2.2 HIGH — `age_bars` Computation is Mathematically Incorrect
**Severity:** HIGH  
**Location:** `fvg_detector.py` lines 113–115  
**Current Code:**
```python
for j, fvg in enumerate(fvgs):
    fvg.age_bars = len(df) - (j + 1) * 1  # approximate
```
**Issue:** `j` is the FVG enumeration index (0, 1, 2...), not the bar index where the FVG was formed. If bars 0-4 have no FVG and an FVG forms at bar 5, `j=0` and `age_bars = 100 - 1 = 99`, but the actual age should be ~92 bars. The formula systematically over-ages early FVGs and under-ages later ones when gaps exist between formations.

**Impact:** FVGs are incorrectly filtered by `config.FVG_MAX_AGE_BARS` (50). Valid recent FVGs may be discarded; old FVGs may pass.

**Fix:**
```python
# fvg_detector.py — In detect_fvg(), replace the age loop

def detect_fvg(ohlc: pd.DataFrame) -> List[FVG]:
    ...
    fvgs: List[FVG] = []
    df = ohlc.reset_index(drop=True)
    total_bars = len(df)

    for i in range(len(df) - 2):
        c1 = df.iloc[i]
        c2 = df.iloc[i + 1]
        c3 = df.iloc[i + 2]

        # Bullish FVG
        if c1["low"] > c3["high"]:
            displacement = c1["low"] - c3["high"]
            min_disp = config.FVG_MIN_DISPLACEMENT_TICKS * config.TICK_SIZE_MNQ
            if displacement >= min_disp:
                ts = c3.get("timestamp", pd.Timestamp.now())
                if isinstance(ts, (int, float)):
                    ts = pd.to_datetime(ts, unit='ms')
                fvg = FVG(
                    direction="bullish",
                    top=round(float(c1["low"]), 2),
                    bottom=round(float(c3["high"]), 2),
                    created_at=ts,
                    is_bullish=True,
                    source_level="displacement",
                )
                fvg._creation_index = i + 2   # completion bar
                fvg.age_bars = total_bars - (i + 2) - 1  # bars since completion
                fvgs.append(fvg)

        # Bearish FVG (same pattern)
        if c1["high"] < c3["low"]:
            displacement = c3["low"] - c1["high"]
            if displacement >= min_disp:
                ts = c3.get("timestamp", pd.Timestamp.now())
                if isinstance(ts, (int, float)):
                    ts = pd.to_datetime(ts, unit='ms')
                fvg = FVG(
                    direction="bearish",
                    top=round(float(c3["low"]), 2),
                    bottom=round(float(c1["high"]), 2),
                    created_at=ts,
                    is_bullish=False,
                    source_level="displacement",
                )
                fvg._creation_index = i + 2
                fvg.age_bars = total_bars - (i + 2) - 1
                fvgs.append(fvg)

    return fvgs
```

---

### 2.3 MEDIUM — `_is_currently_retesting()` Wick-Rejection Blind Spot
**Severity:** MEDIUM  
**Location:** `entry_engine.py` lines 455–463  
**Current Code:**
```python
def _is_currently_retesting(close, low, high, fvg):
    if fvg.is_bullish:
        return low <= fvg.top and close >= fvg.bottom
    else:
        return high >= fvg.bottom and close <= fvg.top
```
**Issue:** A bullish scenario where the wick spikes **below** `fvg.bottom` (sweeping liquidity) but closes back inside the zone passes the test (`close >= fvg.bottom` is True). However, a wick that violates the bottom suggests underlying sell pressure and increases the probability that the FVG will be fully violated on the next bar. The code does not penalize or reject entries where the wick extends beyond the FVG boundary.

**Fix:**
```python
def _is_currently_retesting(close: float, low: float, high: float, fvg: FVG) -> bool:
    """Check if current bar is interacting with the FVG zone.
    Rejects entries where the wick spiked through the zone boundary."""
    if fvg.is_bullish:
        in_zone = low <= fvg.top and close >= fvg.bottom
        if not in_zone:
            return False
        # Reject if wick swept below the FVG bottom by more than 2 ticks
        wick_violation = low < fvg.bottom - (2 * config.TICK_SIZE_MNQ)
        if wick_violation:
            logger.debug(f"Bullish retest rejected: wick swept below FVG bottom {low} < {fvg.bottom}")
            return False
        return True
    else:
        in_zone = high >= fvg.bottom and close <= fvg.top
        if not in_zone:
            return False
        # Reject if wick swept above the FVG top by more than 2 ticks
        wick_violation = high > fvg.top + (2 * config.TICK_SIZE_MNQ)
        if wick_violation:
            logger.debug(f"Bearish retest rejected: wick swept above FVG top {high} > {fvg.top}")
            return False
        return True
```

---

## 3. Execution Failure Modes

### 3.1 CRITICAL — No Broker Stop-Loss Order is Ever Placed
**Severity:** CRITICAL  
**Location:** `main.py` lines 291–323  
**Issue:** When "TAKE ENTRY" is clicked, the system sends **only** a `LMT` entry order to Tradovate. The stop-loss (`signal.stop_loss`) is stored only in the `ActivePosition` dataclass inside `st.session_state`.  
**Real-World Failure:** If the Streamlit app crashes, the server restarts, or the user's laptop goes to sleep:
- `st.session_state` is wiped
- The broker still holds the open futures position
- **There is no stop-loss order at the broker**
- A 50-tick adverse move on 2 MNQ contracts = $500 loss in minutes
- With a $2,000 trailing drawdown, two such events end the prop-firm account.

**Fix — Use OCO (One-Cancels-Other) Bracket Orders:**
```python
# tradovate_client.py — Add bracket order support

from typing import Tuple

@dataclass
class BracketOrderRequest:
    """Entry + Stop + Target bracket."""
    symbol: str
    side: OrderSide
    quantity: int
    entry_price: float
    stop_price: float
    target_price: float
    account_id: Optional[int] = None


class TradovateClient:
    ...

    def place_bracket_order(self, bracket: BracketOrderRequest) -> Tuple[OrderResponse, OrderResponse, OrderResponse]:
        """
        Place an OCO bracket: Entry LMT + Stop STP + Target LMT.
        Returns (entry_resp, stop_resp, target_resp).
        """
        if not self.token:
            if not self.authenticate():
                return (OrderResponse(success=False, message="Not authenticated"),) * 3

        # Tradovate API supports OCO via /order/placeOCO or /order/placeOSO
        # Below is the conceptual payload; adjust to Tradovate's actual OCO schema.
        payload = {
            "accountId": bracket.account_id or self.account_id,
            "contractId": config.TRADOVATE_CID,
            "symbol": bracket.symbol,
            "action": bracket.side.value,
            "orderQty": bracket.quantity,
            "orderType": "Limit",          # Entry
            "price": bracket.entry_price,
            "timeInForce": "Day",
            "brackets": [
                {
                    "orderType": "Stop",
                    "stopPrice": bracket.stop_price,
                    "timeInForce": "GTC",    # Keep stop alive until filled/cancelled
                },
                {
                    "orderType": "Limit",
                    "price": bracket.target_price,
                    "timeInForce": "GTC",
                },
            ],
        }

        url = f"{self.base_url}/order/placeorder"  # or /placeOCO if supported
        raw = self._post_with_retry(url, payload)
        # ... parse response ...
        # Store bracket order IDs in session state for later cancellation/modification
        ...
```

**main.py — Replace single LMT with bracket:**
```python
# main.py — In the "TAKE ENTRY" block
if st.button("✅ TAKE ENTRY", type="primary", use_container_width=True):
    if st.session_state["connected"] and st.session_state["client"]:
        side = OrderSide.BUY if signal.direction == "long" else OrderSide.SELL

        # === CRITICAL: Place OCO bracket, not just entry ===
        bracket = BracketOrderRequest(
            symbol=product,
            side=side,
            quantity=signal.contracts,
            entry_price=signal.entry_price,
            stop_price=signal.stop_loss,
            target_price=signal.target,
        )
        entry_resp, stop_resp, target_resp = st.session_state["client"].place_bracket_order(bracket)

        if not entry_resp.success:
            st.error(f"Entry order failed: {entry_resp.message}")
            return  # Do NOT track position if entry failed
        if not stop_resp.success:
            st.error(f"STOP ORDER FAILED — CRITICAL. Cancel entry immediately.")
            st.session_state["client"].cancel_order(entry_resp.order_id)
            return

        st.success(f"Bracket placed: Entry={entry_resp.order_id}, Stop={stop_resp.order_id}")

        # Track broker order IDs in ActivePosition for later exit / modify
        pos = ActivePosition(
            direction=signal.direction,
            entry_price=signal.entry_price,
            stop_loss=signal.stop_loss,
            initial_target=signal.target,
            contracts=signal.contracts,
            entry_time=datetime.now(EASTERN),
            regime_at_entry=regime,
            broker_entry_order_id=entry_resp.order_id,
            broker_stop_order_id=stop_resp.order_id,
            broker_target_order_id=target_resp.order_id,
        )
        st.session_state["active_position"] = pos
        st.session_state["risk_guard"].record_trade_opened()
```

---

### 3.2 CRITICAL — `active_position` Lives Only in `st.session_state`; Lost on Crash
**Severity:** CRITICAL  
**Location:** `main.py` lines 53–68, 311–321  
**Issue:** `st.session_state` is an in-memory Python dict tied to the Streamlit server process. If the process restarts (code change, server reboot, memory pressure), all state is lost. The system will believe it is flat while the broker holds an open position with no stop.

**Fix — Persist to Disk + Reconcile on Startup:**
```python
# main.py — Add persistence and reconciliation

import json
import os

STATE_FILE = "/mnt/agents/output/auratrade/.auratrade_state.json"

def save_state():
    """Persist critical state to disk atomically."""
    pos = st.session_state.get("active_position")
    state = {
        "active_position": {
            "direction": pos.direction,
            "entry_price": pos.entry_price,
            "stop_loss": pos.stop_loss,
            "initial_target": pos.initial_target,
            "contracts": pos.contracts,
            "entry_time": pos.entry_time.isoformat(),
            "regime_at_entry": pos.regime_at_entry,
            "broker_entry_order_id": getattr(pos, "broker_entry_order_id", None),
            "broker_stop_order_id": getattr(pos, "broker_stop_order_id", None),
        } if pos else None,
        "risk_guard": st.session_state["risk_guard"].state.__dict__,
        "last_updated": datetime.now(EASTERN).isoformat(),
    }
    tmp = STATE_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f, default=str)
    os.replace(tmp, STATE_FILE)


def load_state():
    """Load state from disk if available."""
    if not os.path.exists(STATE_FILE):
        return
    with open(STATE_FILE, "r") as f:
        return json.load(f)


def reconcile_with_broker(client: TradovateClient):
    """
    On startup, compare session_state position with broker reality.
    If broker has a position we don't know about, rebuild state.
    If we think we have a position but broker is flat, clear state.
    """
    broker_positions = client.get_positions()
    broker_has_position = bool(broker_positions)
    local_thinks_position = st.session_state.get("active_position") is not None

    if broker_has_position and not local_thinks_position:
        # CRITICAL: Broker has position, we don't know about it
        pos = broker_positions[0]
        logger.critical(
            f"RECONCILE: Broker has {pos.get('netPos', 0)} contract position "
            f"but local state is flat. Rebuilding state from broker."
        )
        # Rebuild ActivePosition from broker data (best-effort)
        st.session_state["active_position"] = ActivePosition(
            direction="long" if pos.get("netPos", 0) > 0 else "short",
            entry_price=pos.get("avgPrice", 0.0),
            stop_loss=0.0,  # Unknown — must be handled manually
            initial_target=0.0,
            contracts=abs(pos.get("netPos", 0)),
            entry_time=datetime.now(EASTERN),  # Approximate
            regime_at_entry="UNKNOWN",
        )
        st.error("🚨 POSITION RECONCILED FROM BROKER — Stop loss unknown. Set immediately!")

    elif not broker_has_position and local_thinks_position:
        # Broker is flat, we think we have a position
        logger.critical("RECONCILE: Broker flat but local state shows position. Clearing.")
        st.session_state["active_position"] = None
        st.warning("Position cleared — broker reports flat.")
```

Call `save_state()` after every trade action (entry, exit, pyramid). Call `reconcile_with_broker()` in `init_session_state()` when a client is connected.

---

### 3.3 CRITICAL — Simultaneous Long + Short Position Risk
**Severity:** CRITICAL  
**Location:** `entry_engine.py` lines 98–232; `main.py` lines 263–271  
**Issue:** `evaluate_entry()` has no concept of "net exposure." If a bullish FVG and a bearish FVG both form and retest on consecutive bars, the system can generate a `long` signal, then a `short` signal. `main.py` will place both orders. For futures, this creates a **hedged position** (long + short) which:
- Doubles commission
- Wastes margin
- If one side is stopped out and the other runs, net PnL is unpredictable
- Prop firms typically prohibit hedged positions

**Fix:**
```python
# entry_engine.py — In evaluate_entry(), after sweep detection

def evaluate_entry(..., active_position: Optional[ActivePosition] = None, ...):
    ...
    # --- 0. Net exposure check ---
    if active_position is not None:
        # If we already have a position, only allow pyramids (same direction)
        # or explicit reversal logic (not currently supported)
        direction_needed = sweep_info.get("direction", None) if sweep_info else None
        if direction_needed and direction_needed != active_position.direction:
            logger.warning(
                f"Entry blocked: have {active_position.direction} position, "
                f"but signal is {direction_needed}"
            )
            return None
    ...
```

Also in `main.py`, verify broker position before placing:
```python
# main.py — Before TAKE ENTRY
if st.session_state["active_position"]:
    # Already in a position; only pyramid allowed in BLUE
    if not signal.pyramid:
        st.warning("Already in position. Entry blocked.")
        return

# Also check broker
if st.session_state["client"] and st.session_state["connected"]:
    broker_pos = st.session_state["client"].get_positions()
    if broker_pos:
        net_pos = broker_pos[0].get("netPos", 0)
        if net_pos != 0 and signal.direction != ("long" if net_pos > 0 else "short"):
            st.error(f"Broker has opposite position ({net_pos}). Entry blocked.")
            return
```

---

### 3.4 HIGH — "Remove Quickly" Exit is Manual, Not Automated; No Failure Handling
**Severity:** HIGH  
**Location:** `main.py` lines 325–344; `entry_engine.py` lines 308–334  
**Issue:** When `should_remove_quickly()` returns `True`, `main.py` displays a red warning and a **manual button** "CONFIRM EXIT." The user must click it. If the user is away, on another screen, or the Streamlit tab is backgrounded, the position runs without a stop. Even if clicked, there is no handling for `cancel_order()` or `place_order()` failure during the exit sequence.

**Fix:** Implement automated bracket exits + failure alerts:
```python
# main.py — Replace manual exit with automated bracket-based exit
# (This assumes OCO brackets are in place from section 3.1)

if st.session_state["active_position"]:
    pos = st.session_state["active_position"]
    remove = should_remove_quickly(pos, price_data, ema9)
    if remove:
        st.error("🚨 REMOVE QUICKLY triggered — 9-EMA breach!")

        # If bracket was placed, the stop-loss order at broker should already
        # be active. But if we want to exit at market (faster than stop fill):
        if st.session_state["connected"] and st.session_state["client"]:
            # 1. Cancel any working entry/target orders
            st.session_state["client"].cancel_all_orders()
            # 2. Place market order to flatten immediately
            flatten_side = OrderSide.SELL if pos.is_long else OrderSide.BUY
            flatten_order = OrderRequest(
                symbol=product,
                side=flatten_side,
                order_type=OrderType.MKT,
                quantity=pos.contracts,
                time_in_force=TimeInForce.DAY,
            )
            resp = st.session_state["client"].place_order(flatten_order)
            if resp.success:
                st.success(f"Flattened at market: {resp.order_id}")
            else:
                # CRITICAL FAILURE: System says exit but broker still has position
                st.error(f"🚨 EXIT ORDER FAILED: {resp.message}")
                # Persist alert state so user sees it on next refresh
                st.session_state["exit_failure_alert"] = {
                    "time": datetime.now(EASTERN).isoformat(),
                    "reason": "Remove Quickly exit order failed",
                    "position": pos,
                }
                # Do NOT clear active_position — we still have risk!
                # Force a page rerun to retry or alert user
                st.rerun()

        # Record PnL from actual fill (placeholder logic needs broker fill price)
        ...
```

---

### 3.5 HIGH — `place_order()` Succeeds but `get_positions()` Fails = Phantom Flat State
**Severity:** HIGH  
**Location:** `tradovate_client.py` lines 238–251; `main.py` lines 311–321  
**Issue:** The order placement loop and the position query loop are independent. A network blip can cause `place_order()` to return success while a subsequent `get_positions()` call returns `[]` (due to the `if raw is None: return []` fallback). The system thinks it is flat and may place a new entry while already holding a position.

**Fix:** Wrap order placement and position verification in an atomic check:
```python
# tradovate_client.py — Add verified order placement

def place_order_verified(self, order: OrderRequest, max_wait_sec: float = 5.0) -> OrderResponse:
    """
    Place an order and verify it appears in the position list.
    Returns OrderResponse with an `verified` flag.
    """
    resp = self.place_order(order)
    if not resp.success:
        return resp

    # Poll position list until order reflects or timeout
    import time
    deadline = time.time() + max_wait_sec
    while time.time() < deadline:
        positions = self.get_positions()
        # Check if position exists (Tradovate position objects contain contract info)
        for p in positions:
            if p.get("contractId") == config.TRADOVATE_CID and p.get("netPos", 0) != 0:
                resp.verified = True
                return resp
        time.sleep(0.5)

    resp.verified = False
    resp.message += " | WARNING: Order placed but position not confirmed."
    logger.critical("ORDER/POSITION MISMATCH: Order accepted but no position found.")
    return resp
```

---

### 3.6 HIGH — Signal-to-Execution Slippage; Limit Order May Never Fill
**Severity:** HIGH  
**Location:** `main.py` lines 295–301; `entry_engine.py` lines 539  
**Issue:** `evaluate_entry()` computes `entry_price = fvg.mid()`. By the time the user clicks "TAKE ENTRY" (or in an automated loop), price may have moved 10+ ticks. A `LMT` order at the old FVG mid will sit unfilled. Meanwhile:
- The system thinks it has an "in-flight" entry (sets `active_position` immediately after `place_order`, not after `fill`)
- If price never returns to the limit, the system is blocked from new entries until the user manually cancels
- No timeout, no price-adjustment, no conversion to MKT

**Fix:** Implement fill-tracking with time-decay:
```python
# main.py — Add order-fill tracking and adjustment

@dataclass
class PendingEntry:
    signal: EntrySignal
    order_id: Optional[str]
    placed_at: datetime
    status: str = "working"  # working, filled, cancelled, expired

# In session state init:
defaults["pending_entry"] = None

# When placing entry:
if st.button("✅ TAKE ENTRY", ...):
    ...
    resp = st.session_state["client"].place_order(order)
    if resp.success:
        st.session_state["pending_entry"] = PendingEntry(
            signal=signal,
            order_id=resp.order_id,
            placed_at=datetime.now(EASTERN),
        )

# On every rerun, check pending entry status
if st.session_state.get("pending_entry"):
    pending = st.session_state["pending_entry"]
    elapsed = (datetime.now(EASTERN) - pending.placed_at).total_seconds()

    # Check open orders
    open_orders = st.session_state["client"].get_open_orders() if st.session_state["connected"] else []
    order_still_open = any(o.get("id") == int(pending.order_id) for o in open_orders)

    if not order_still_open:
        # Order no longer working — check if filled via positions
        positions = st.session_state["client"].get_positions()
        if positions:
            pending.status = "filled"
            # Now promote to active_position
            st.session_state["active_position"] = ActivePosition(...)
            st.session_state["pending_entry"] = None
        else:
            pending.status = "cancelled_or_rejected"
            st.session_state["pending_entry"] = None
            st.warning("Entry order was cancelled or expired without fill.")

    elif elapsed > 30:
        # Limit order sitting unfilled for 30 seconds
        st.warning("Entry LMT unfilled for 30s — consider cancelling or adjusting")
        # Optional: auto-cancel and re-place at new price
        # st.session_state["client"].cancel_order(pending.order_id)
        # new_price = current_close  # or updated FVG mid
        # ...re-place...
```

---

## 4. Market Structure Edge Cases

### 4.1 HIGH — `_detect_level_sweep_and_reclaim()` Only Detects Reversals, Not Breakout-and-Hold
**Severity:** HIGH  
**Location:** `entry_engine.py` lines 341–389  
**Current Logic:** For `London_High` / `Prev_NYAM_High`, it checks `high >= level` then `close < level`. This only detects **sweep + reclaim below** → short signal. It never detects the bullish case where price breaks above a level and **holds** above it (breakout continuation), which is a valid setup in BLUE regime.

**Fix:**
```python
def _detect_level_sweep_and_reclaim(
    price_data: pd.DataFrame,
    key_levels: Dict[str, float],
    lookback: int = 10,
    regime: str = "RED",  # Pass regime to allow breakout logic in BLUE
) -> Optional[Dict[str, Any]]:
    ...
    for level_name in priority:
        ...
        if "High" in level_name:
            # --- Existing: sweep above then reclaim below (reversal / trap) ---
            swept = (recent["high"].max() >= level_price * 0.999)
            reclaimed = latest_close < level_price
            if swept and reclaimed:
                return {"direction": "short", ...}

            # --- NEW: breakout and hold above (BLUE regime only) ---
            if regime == "BLUE":
                breakout_hold = (
                    latest_close > level_price * 1.001
                    and (recent["close"] > level_price).sum() >= 3  # 3+ closes above
                )
                if breakout_hold:
                    return {
                        "direction": "long",
                        "level_name": level_name,
                        "level_price": level_price,
                        "type": "breakout_hold_above",
                    }

        if "Low" in level_name:
            # --- Existing: sweep below then reclaim above (reversal / trap) ---
            swept = (recent["low"].min() <= level_price * 1.001)
            reclaimed = latest_close > level_price
            if swept and reclaimed:
                return {"direction": "long", ...}

            # --- NEW: breakdown and hold below (BLUE regime only) ---
            if regime == "BLUE":
                breakdown_hold = (
                    latest_close < level_price * 0.999
                    and (recent["close"] < level_price).sum() >= 3
                )
                if breakdown_hold:
                    return {
                        "direction": "short",
                        "level_name": level_name,
                        "level_price": level_price,
                        "type": "breakdown_hold_below",
                    }
    ...
```

---

### 4.2 MEDIUM — London High and Prev NYAM High Within 2 Ticks: Noise Confusion
**Severity:** MEDIUM  
**Location:** `entry_engine.py` lines 360–389  
**Issue:** If two levels are within 2 ticks, the code may detect a sweep on one and a "reclaim" that is actually just noise between the levels. The `0.999` / `1.001` tolerance bands also mean a level 5 ticks away can trigger.

**Fix:** Add minimum level separation and stricter reclaim validation:
```python
# In _detect_level_sweep_and_reclaim(), before processing:

# Pre-filter levels that are too close to each other (within 3 ticks)
TICK_SIZE = 0.25
MIN_LEVEL_SEPARATION = 3 * TICK_SIZE  # 0.75 points

filtered_levels = {}
for name in priority:
    if name not in key_levels:
        continue
    price = float(key_levels[name])
    # Check against already-accepted levels
    too_close = any(abs(price - filtered_levels[accepted]) < MIN_LEVEL_SEPARATION for accepted in filtered_levels)
    if not too_close:
        filtered_levels[name] = price

# Process filtered_levels instead of key_levels directly
for level_name, level_price in filtered_levels.items():
    ...
```

---

### 4.3 MEDIUM — VWAP Session Start Assumed but Never Validated
**Severity:** MEDIUM  
**Location:** `config.py` line 65; `entry_engine.py` lines 428–436  
**Issue:** `VWAP_SESSION_START = "09:30"` is hardcoded. If the data provider computes VWAP from midnight, or from 8:30 AM (CME Globex open), the VWAP value passed to `evaluate_entry()` is from a different session anchor. The entire alignment logic (`fvg.bottom >= vwap * 0.998`) becomes meaningless or dangerous.

**Fix:** Validate VWAP anchor at runtime:
```python
# In evaluate_entry() or a new helper:

def validate_vwap_anchor(price_data: pd.DataFrame, expected_start: str = "09:30") -> bool:
    """Check that VWAP resets near expected session start."""
    if "vwap" not in price_data.columns:
        return False
    # VWAP should show a reset (drop to price level) at or near 09:30
    # This is heuristic; ideally the data provider tags VWAP session
    start_idx = price_data.index[price_data.index.strftime("%H:%M") == expected_start]
    if len(start_idx) == 0:
        logger.warning(f"No bars at {expected_start} — cannot validate VWAP anchor")
        return False

    # At session start, VWAP should be very close to open price
    row = price_data.loc[start_idx[0]]
    drift = abs(row["vwap"] - row["open"])
    if drift > 2 * config.TICK_SIZE_MNQ:
        logger.error(f"VWAP anchor mismatch at {expected_start}: VWAP={row['vwap']}, OPEN={row['open']}")
        return False
    return True
```

---

## 5. Streamlit UI Race Conditions

### 5.1 HIGH — `evaluate_entry()` Runs on Every Rerun; Signal Stored in Session State
**Severity:** HIGH  
**Location:** `main.py` lines 263–288  
**Issue:** `main.py` calls `evaluate_entry()` unconditionally on every Streamlit rerun (every button click, auto-refresh, widget interaction). The returned signal is stored in `st.session_state["last_signal"]` (line 277). If a user clicks "ARM SYSTEM" (or any other widget) while a signal is present, the signal is re-stored. If auto-trading were implemented, this would trigger duplicate order placement.

**Fix:** Deduplicate signals by timestamp / bar index:
```python
# main.py — Add signal deduplication

# In init_session_state:
defaults["last_signal_bar_index"] = -1

# When evaluating:
current_bar_count = len(price_data)
if current_bar_count == st.session_state.get("last_signal_bar_index", -1):
    # Same bar — do not re-evaluate, use cached signal
    signal = st.session_state.get("last_signal")
else:
    signal = evaluate_entry(
        price_data=price_data,
        vwap=vwap,
        ema9=ema9,
        regime=regime,
        active_position=st.session_state["active_position"],
        key_levels=key_levels,
        product=product,
    )
    st.session_state["last_signal"] = signal
    st.session_state["last_signal_bar_index"] = current_bar_count
```

---

### 5.2 HIGH — "TAKE ENTRY" Button + `st.rerun()` Can Create Inconsistent State
**Severity:** HIGH  
**Location:** `main.py` lines 291–323  
**Issue:** When the user clicks "TAKE ENTRY", the order is placed, `active_position` is set, and `st.rerun()` is called (line 323). If the API call to `place_order()` takes >2 seconds and a background auto-refresh fires simultaneously (or the user clicks another button), the script reruns mid-execution. Streamlit buttons are supposed to be click-only-once, but rapid interactions can cause:
- Order placed but `active_position` not set (rerun before assignment)
- `risk_guard.record_trade_opened()` called twice

**Fix:** Use a state-machine pattern and disable buttons during execution:
```python
# main.py — Guard entry execution with a lock flag

# In init_session_state:
defaults["entry_in_progress"] = False

# In the TAKE ENTRY block:
if signal and not st.session_state.get("entry_in_progress"):
    if st.button("✅ TAKE ENTRY", type="primary", use_container_width=True,
                 disabled=st.session_state.get("entry_in_progress", False)):
        st.session_state["entry_in_progress"] = True
        try:
            # ... place order, set active_position, record trade ...
            save_state()  # Persist immediately
        finally:
            st.session_state["entry_in_progress"] = False
        st.rerun()
```

---

### 5.3 MEDIUM — RiskGuard State Lost on App Restart
**Severity:** MEDIUM  
**Location:** `main.py` lines 53–68; `risk_guard.py` lines 47–48  
**Issue:** `RiskGuard` is instantiated fresh in `init_session_state()`. If the app restarts, `daily_pnl`, `trades_taken`, and `equity_peak` are all reset to defaults. A trader who lost $250 on 2 trades already could suddenly get 2 more trades and blow past the $300 daily stop.

**Fix:** Already covered in section 3.2 (`save_state` / `load_state`). Load persisted `RiskState` during initialization:
```python
def init_session_state():
    persisted = load_state()
    if persisted and persisted.get("risk_guard"):
        rg = RiskGuard()
        rg.state = RiskState(**persisted["risk_guard"])
        defaults["risk_guard"] = rg
    ...
```

---

### 5.4 LOW — Simulated PnL Placeholder in Production Code
**Severity:** LOW  
**Location:** `main.py` line 333  
**Code:**
```python
pnl = np.random.randn() * 50  # placeholder
```
**Issue:** This is present in the "CONFIRM EXIT" flow for Remove Quickly. Even though the flow is manual, a user clicking through quickly will record a completely fabricated PnL in the trade journal, corrupting all analytics.

**Fix:**
```python
# Replace with actual fill price from broker
if st.session_state["connected"] and st.session_state["client"]:
    acct = st.session_state["client"].get_account()
    # Tradovate account response includes realized PnL per position
    # Or query fills to compute actual PnL
    pnl = compute_pnl_from_fills(pos, st.session_state["client"])
else:
    pnl = 0.0  # Simulated mode — use 0, not random
    st.warning("Simulated mode: PnL recorded as $0.00")
```

---

## Summary Table

| # | Finding | Severity | File | Line(s) |
|---|---------|----------|------|---------|
| 1 | No broker stop-loss order placed; stop only in memory | CRITICAL | `main.py` | 291–323 |
| 2 | `active_position` in `st.session_state` only; lost on crash | CRITICAL | `main.py` | 53–68, 311–321 |
| 3 | `_confirm_regime_with_structure()` is a no-op; day-of-week only | CRITICAL | `regime_classifier.py` | 48–59 |
| 4 | Simultaneous long+short entry possible; no net exposure check | CRITICAL | `entry_engine.py` | 98–232 |
| 5 | `fvg.filled` never updated; old FVGs re-traded | CRITICAL | `fvg_detector.py` | 32, 196–218 |
| 6 | `age_bars` computation mathematically wrong | HIGH | `fvg_detector.py` | 113–115 |
| 7 | `is_fvg_filled()` cross-bar contamination bug | HIGH | `fvg_detector.py` | 213–218 |
| 8 | "Remove Quickly" exit is manual; no automated OCO | HIGH | `main.py` | 325–344 |
| 9 | `place_order()` success + `get_positions()` failure = phantom flat | HIGH | `tradovate_client.py` | 238–251 |
| 10 | Signal-to-fill slippage; LMT may never fill; no timeout | HIGH | `main.py` | 295–301 |
| 11 | `evaluate_entry()` runs every rerun; signal re-stored | HIGH | `main.py` | 263–288 |
| 12 | `_detect_level_sweep_and_reclaim()` no breakout-and-hold | MEDIUM | `entry_engine.py` | 341–389 |
| 13 | VWAP session start never validated | MEDIUM | `config.py`, `entry_engine.py` | 65, 428–436 |
| 14 | Levels within 2 ticks cause noise confusion | MEDIUM | `entry_engine.py` | 360–389 |
| 15 | RiskGuard state lost on restart | MEDIUM | `main.py`, `risk_guard.py` | 53–68, 47–48 |
| 16 | Simulated PnL placeholder in production | LOW | `main.py` | 333 |

---

## Recommendations for Prop-Firm Deployment

1. **Do not deploy to live capital** until all CRITICAL items (1–5) are resolved.
2. **Implement OCO bracket orders** as the first priority. Without broker-side stop loss, a single app crash can blow the account.
3. **Add a position-reconciliation loop** that runs every 5 seconds: compare `st.session_state["active_position"]` with `client.get_positions()`. Alert and auto-heal on mismatch.
4. **Replace day-of-week regime** with a multi-factor model: realized volatility (ATR), economic calendar, overnight gap size, and volume profile. The current `_confirm_regime_with_structure()` must be rewritten or removed.
5. **Add an in-flight order tracker** (`pending_entry`, `pending_exit`) with timeouts and retry logic. Never assume an order state based on `place_order()` response alone.
6. **Use a persistent state store** (JSON file, SQLite, or Redis) for `RiskState` and `ActivePosition`. `st.session_state` is insufficient for financial applications.
7. **Consider migrating from Streamlit** to a persistent daemon (e.g., `asyncio` event loop, `fastapi` dashboard, or dedicated trading platform) to eliminate rerun-based race conditions.

---

*End of Audit Report*
