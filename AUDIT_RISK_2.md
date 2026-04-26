# AuraTrade Risk Audit #1: Pyramiding & Account Blow-Up Vulnerabilities

**Auditor:** Prop Firm Risk Manager & Quantitative Auditor  
**Date:** 2025-01-28  
**Scope:** `entry_engine.py` pyramiding logic (lines 239-301), `ActivePosition` dataclass, `main.py` execution loop, `risk_guard.py` drawdown tracking  
**Account Profile:** $50,000 prop firm | $300 daily stop | $2,000 trailing drawdown | Max 2 trades/session | Max 2 MNQ contracts  

---

## Executive Summary

**Overall Risk Rating: CRITICAL — DO NOT TRADE LIVE WITHOUT FIXES**

The AuraTrade pyramiding architecture contains **5 separate flaws**, three of which are CRITICAL. The most severe is that `pyramid_count` is checked but **never incremented**, and when a pyramid is executed, `main.py` **replaces** the `ActivePosition` object entirely — discarding the original entry price, stop, and contract count. This creates a complete blind spot where the system tracks the pyramid leg as if it were the only position, while the original leg bleeds unrealized losses that are invisible to risk monitoring.

Combined with the trailing drawdown check only running on `record_trade_closed()` (not intraday), a $2,000 drawdown can be breached during a single position without the system ever knowing until it is too late.

---

## Flaw 1: `pyramid_count` Checked But Never Incremented — Infinite Pyramiding (CRITICAL)

### The Bug

In `entry_engine.py` line 264:

```python
if active_position.pyramid_count >= active_position.max_pyramids:
    return False
```

`pyramid_count` is initialized to `0` in the `ActivePosition` dataclass (line 69). `max_pyramids` defaults to `1` (line 70). The check `0 >= 1` is `False`, so the guard passes.

**The problem:** `pyramid_count` is **never incremented anywhere in the entire codebase.**

A grep across the repo confirms this:

| File | Line | Context |
|------|------|---------|
| `entry_engine.py` | 69 | `pyramid_count: int = 0` (declaration) |
| `entry_engine.py` | 264 | `if active_position.pyramid_count >= ...` (check) |
| `main.py` | 368 | `if pos.pyramid_count < pos.max_pyramids:` (UI button check) |

**Nowhere is `pyramid_count += 1` or any assignment to it.**

### What This Means in Practice

1. **On the first pyramid evaluation:** `0 >= 1` is `False` → pyramid is allowed.
2. **After pyramid executes:** `main.py` creates a **brand new** `ActivePosition` (line 312-320), which initializes `pyramid_count` back to `0`.
3. **On the next bar:** `0 >= 1` is still `False` → pyramid is allowed **again**.

The only backstop is the contract limit check:
```python
signal.contracts = min(signal.contracts, config.MAX_CONTRACTS_MNQ - active_position.contracts)
```

If `active_position.contracts == 2` and `MAX_CONTRACTS_MNQ == 2`, this returns `0` and the pyramid is blocked. But if the user **manually closes 1 contract** (via the broker, not the app), `active_position.contracts` is still `2` in the app's state (there is no position sync from the broker). So the app blocks the pyramid — but for the wrong reason.

**Worse:** If the user partially closes via the "Close All / Flatten" button, `main.py` sets `active_position = None` (line 132). Then a *new* entry can be taken, counting as Trade #2. There is still no `pyramid_count` enforcement.

### Severity: CRITICAL

This breaks the fundamental pyramid safety guard. The system cannot enforce "max 1 pyramid" because it never records that a pyramid happened.

### Code Fix

**File:** `entry_engine.py` — add `pyramid_count` increment inside `evaluate_pyramid`, and `main.py` must update (not replace) the `ActivePosition` on pyramid execution.

```python
# entry_engine.py — inside evaluate_pyramid, BEFORE returning True
def evaluate_pyramid(
    active_position: ActivePosition,
    price_data: pd.DataFrame,
    fvg_list: List[FVG],
    regime: str,
) -> bool:
    ...
    for fvg in sorted(newer_fvgs, key=lambda x: x.created_at, reverse=True):
        if _is_currently_retesting(close, low, high, fvg):
            # INCREMENT COUNT HERE — only when we actually approve
            active_position.pyramid_count += 1
            logger.info(f"Pyramid approved: {direction} FVG retest at {fvg.mid()}, "
                        f"current R={r_multiple:.2f}, count={active_position.pyramid_count}")
            return True
    return False
```

```python
# main.py — inside the "TAKE ENTRY" button handler (~line 291)
if st.button("✅ TAKE ENTRY", type="primary", use_container_width=True):
    # ... broker execution ...

    if signal.pyramid and st.session_state["active_position"] is not None:
        # PYRAMID: UPDATE existing position, do NOT replace
        existing = st.session_state["active_position"]
        # Increment contracts
        existing.contracts += signal.contracts
        # Update to the TIGHTER stop (more conservative)
        existing.stop_loss = max(existing.stop_loss, signal.stop_loss) if existing.is_long else min(existing.stop_loss, signal.stop_loss)
        # Update entry time to original (keep it) — or track pyramid list
        existing.pyramid_count += 1  # defensive; also incremented in evaluate_pyramid
        # Recalculate average entry price
        total_value = (existing.entry_price * (existing.contracts - signal.contracts)) + (signal.entry_price * signal.contracts)
        existing.entry_price = total_value / existing.contracts
        # Update target if more favorable
        if existing.is_long and signal.target > existing.initial_target:
            existing.initial_target = signal.target
        elif not existing.is_long and signal.target < existing.initial_target:
            existing.initial_target = signal.target
        # Risk guard: pyramid does NOT count as a separate trade
        # (do NOT call record_trade_opened())
        st.session_state["active_position"] = existing
    else:
        # NEW ENTRY: create fresh position
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
```

---

## Flaw 2: Pyramid Entry Discards Original Position Data — Complete Risk Blind Spot (CRITICAL)

### The Bug

When a pyramid signal is executed in `main.py` (lines 312-320), the code creates a **brand new** `ActivePosition` and assigns it to session state:

```python
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
```

The **original** `ActivePosition` is overwritten and garbage-collected. Its data is gone forever.

### Consequences

| Original Data | What System Tracks After Pyramid | Risk Impact |
|---------------|-----------------------------------|-------------|
| Original entry price (e.g., 26,000) | Pyramid entry price (e.g., 26,020) | R-multiple, PnL estimates are wrong |
| Original stop (e.g., 25,980) | Pyramid stop (e.g., 25,990) | System thinks stop is higher; doesn't know original is still bleeding |
| Original contracts (e.g., 2) | Pyramid contracts (e.g., 2, or 1, or 0) | Dashboard shows wrong position size |
| Original entry time | Pyramid entry time (now) | Future `evaluate_pyramid` looks for FVGs after the pyramid time, not the original — potentially allowing a 3rd pyramid on the same trend move |
| `realized_pnl`, `unrealized_pnl` | Reset to 0.0 | PnL tracking is broken |

### Concrete Example

**Scenario:** User is long 2 MNQ at 26,000 with stop at 25,980 ($80 risk). Pyramid triggers at 26,020 with stop at 25,990 ($120 risk). `MAX_CONTRACTS_MNQ = 2`, but somehow 1 contract was available (partial close, or config mismatch). Pyramid signal has `contracts = 1`.

After execution, the system tracks:
- `entry_price = 26,020` (not 26,006.67 blended)
- `stop_loss = 25,990` (not 25,980 original)
- `contracts = 1` (not 3 total)
- `entry_time = now` (not original entry time)

**If price drops to 25,985:**
- System computes: `close 25,985 > stop 25,990` → "Position safe, no exit needed"
- Reality: The original 2 contracts at 26,000 are already **$60 underwater** ($30 unrealized loss), and only 5 pts from their $80 stop.
- The system has **zero awareness** of this.

**If price drops to 25,980 (original stop):**
- System still thinks stop is 25,990 → no exit triggered by the app's logic
- Original position is stopped out at broker level (if broker-stop was set), but app doesn't record it
- If the app relies on its own exit logic (e.g., 9-EMA breach), the wrong stop means delayed exit

### Severity: CRITICAL

This is a **complete failure of position tracking**. The system's internal model of the position diverges from reality. Any risk calculation based on `ActivePosition` is invalid after a pyramid.

### Code Fix

See Flaw 1's `main.py` fix above. The key principle: **NEVER replace the ActivePosition on a pyramid. Mutate it in place.**

Additionally, `ActivePosition` needs a list to track pyramid legs:

```python
@dataclass
class ActivePosition:
    direction: str
    entry_price: float
    stop_loss: float
    initial_target: float
    contracts: int
    entry_time: datetime
    regime_at_entry: str
    fvg_reference: Optional[FVG] = None
    pyramid_count: int = 0
    max_pyramids: int = 1
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    # NEW: track each leg for accurate PnL and stop management
    legs: List[Dict[str, Any]] = field(default_factory=list)
```

When a pyramid is added:
```python
existing.legs.append({
    "entry_price": signal.entry_price,
    "stop_loss": signal.stop_loss,
    "contracts": signal.contracts,
    "entry_time": datetime.now(EASTERN),
    "target": signal.target,
})
```

---

## Flaw 3: Double-Loss Scenario — Combined Stop Risk Far Exceeds Per-Trade Assumption (HIGH)

### The Bug

`_build_entry_signal` (line 523) computes the pyramid's stop based on the **new FVG**, not the original position's stop. There is no logic to:
1. Compute a blended average entry price
2. Compute a combined position stop
3. Check whether the combined risk exceeds the prop firm's daily stop or drawdown buffer

### The Math

| Leg | Contracts | Entry | Stop | Risk (pts) | Risk (ticks) | Risk ($/contract) | Total Risk |
|-----|-----------|-------|------|------------|--------------|-------------------|------------|
| Original | 2 | 26,000 | 25,980 | 20 | 80 | $40 | **$80** |
| Pyramid | 2 | 26,020 | 25,990 | 30 | 120 | $60 | **$120** |
| **Combined** | **4** | **26,010** | **??** | **??** | **??** | **??** | **??** |

**Question: What stop does the combined 4-contract position actually use?**

**Case A: Each leg keeps its own stop (broker-managed OCO)**
- If both stops hit: Total loss = $80 + $120 = **$200**
- If price drops to 25,990 first: Pyramid stops out (-$120), original continues
- If price then drops to 25,980: Original stops out (-$80)
- **Total max loss: $200**

**Case B: System naively uses original stop for everything (because main.py replaced the position)**
- Average entry: 26,010
- System tracks stop: 25,990 (pyramid's stop)
- Distance: 30 pts = 120 ticks
- 4 contracts × 120 ticks × $0.50 = **$240** — but the system thinks it's only 2 contracts, so it computes $120

**Case C: Price slices through both levels in a flash crash**
- If MNQ drops 50 points in one bar (rare but possible on NFP/FOMC), both stops fill at much worse prices
- Slippage on MNQ in fast markets can be 5-10 ticks
- Effective loss: ($80 + $120) + slippage on 4 contracts ≈ **$220–$240**

### Daily Stop Interaction

With a **$300 daily stop**, a single pyramided position can consume **67–80%** of the entire day's risk budget in one go. If there was any earlier loss (e.g., first attempt stopped out for -$100), the pyramid's $200 loss pushes total to -$300 — **exactly at the daily limit.**

But the pyramid was evaluated when the first trade was at **+$200 unrealized**. The system saw "+1R profit" and said "OK to pyramid." It never asked: "If this pyramid also fails, what's my total daily loss?"

### Severity: HIGH

The combined risk of a pyramided position is **2.5×–3×** the risk of a single entry, but the system evaluates it as if it's just a normal entry. The $300 daily stop provides no protection because the pyramid bypasses `RiskGuard.can_trade()` (see Flaw 4).

### Code Fix

**File:** `entry_engine.py` — add combined risk check before approving pyramid

```python
def evaluate_pyramid(
    active_position: ActivePosition,
    price_data: pd.DataFrame,
    fvg_list: List[FVG],
    regime: str,
    risk_guard: Optional[RiskGuard] = None,
) -> bool:
    ...
    # NEW: Combined risk ceiling — reject if total position risk exceeds $150
    # (50% of daily stop, leaving buffer for slippage)
    COMBINED_RISK_CAP = 150.0  # USD
    
    # Compute pyramid leg risk
    pyr_risk_ticks = abs(signal_entry_price - signal_stop_loss) / config.TICK_SIZE_MNQ
    pyr_risk_dollars = pyr_risk_ticks * config.TICK_VALUE_MNQ * signal_contracts
    
    # Compute existing position risk (using original stop)
    orig_risk_ticks = abs(active_position.entry_price - active_position.stop_loss) / config.TICK_SIZE_MNQ
    # Use current unrealized to estimate remaining risk on original
    current_price = float(price_data.iloc[-1]["close"])
    if active_position.is_long:
        remaining_orig_risk = max(0, (active_position.stop_loss - current_price) / config.TICK_SIZE_MNQ)
    else:
        remaining_orig_risk = max(0, (current_price - active_position.stop_loss) / config.TICK_SIZE_MNQ)
    
    orig_risk_dollars = remaining_orig_risk * config.TICK_VALUE_MNQ * active_position.contracts
    
    total_risk = pyr_risk_dollars + orig_risk_dollars
    if total_risk > COMBINED_RISK_CAP:
        logger.warning(f"Pyramid rejected: combined risk ${total_risk:.0f} exceeds cap ${COMBINED_RISK_CAP}")
        return False
    ...
```

**Also:** `ActivePosition` should compute blended metrics:

```python
@property
def blended_entry_price(self) -> float:
    """Weighted average entry across all legs."""
    if not self.legs:
        return self.entry_price
    total_contracts = self.contracts + sum(l["contracts"] for l in self.legs)
    total_value = (self.entry_price * self.contracts) + sum(l["entry_price"] * l["contracts"] for l in self.legs)
    return total_value / total_contracts

@property
def worst_case_stop(self) -> float:
    """Most conservative stop across all legs."""
    if not self.legs:
        return self.stop_loss
    if self.is_long:
        return min(self.stop_loss, min(l["stop_loss"] for l in self.legs))
    else:
        return max(self.stop_loss, max(l["stop_loss"] for l in self.legs))

@property
def total_risk_dollars(self) -> float:
    """Total risk if all stops hit simultaneously."""
    risk = 0.0
    for leg in [{"entry": self.entry_price, "stop": self.stop_loss, "contracts": self.contracts}] + self.legs:
        ticks = abs(leg["entry"] - leg["stop"]) / config.TICK_SIZE_MNQ
        risk += ticks * config.TICK_VALUE_MNQ * leg["contracts"]
    return risk
```

---

## Flaw 4: Pyramid Bypasses `RiskGuard.can_trade()` — Daily Stop Not Checked (HIGH)

### The Bug

In `evaluate_entry` (lines 214-225):

```python
if active_position is not None and regime == "BLUE":
    pyramid = evaluate_pyramid(active_position, price_data, all_fvgs, regime)
    if pyramid:
        signal.pyramid = True
        signal.contracts = min(
            signal.contracts,
            config.MAX_CONTRACTS_MNQ - active_position.contracts
        )
        if signal.contracts <= 0:
            return None
        signal.reason = f"[PYRAMID] {signal.reason}"
```

`evaluate_pyramid` does **not** call `RiskGuard.can_trade()`. The `can_trade()` check only happens (presumably) before a *new* entry. But a pyramid is evaluated and approved without any of these checks:
- Daily stop loss status
- Trailing drawdown status
- Remaining trade count (this one is debatable — should a pyramid count as a trade?)

### Why This Matters

**Scenario:**
1. Trade 1: Long 2 MNQ, stopped out for -$100. Daily PnL = -$100.
2. Trade 2: Short 2 MNQ, currently at +$200 unrealized (in profit).
3. Pyramid triggers on the short. The system says: "+1R profit, new FVG, OK to pyramid."
4. Pyramid adds 2 more shorts.
5. Market reverses. Both short legs hit stops.
6. Trade 2 loss: -$80. Pyramid loss: -$120. Total = -$200.
7. Combined with Trade 1: -$100 + (-$200) = **-$300** → **daily stop hit**.

But the pyramid was approved **after** Trade 1 already consumed $100 of the daily buffer. The system never asked: "If this pyramid fails, do I still stay within my $300 limit?"

Also: `main.py` calls `record_trade_opened()` on pyramid execution (line 322). This increments `trades_taken` from 1 to 2. If `MAX_TRADES_PER_SESSION = 2`, the pyramid consumes the last trade slot. That's actually correct if pyramids count as trades. But if the user expected "2 entries + 1 pyramid" (3 executions total), they're surprised.

**More importantly:** If the daily stop was already at -$250, `can_trade()` would return `False`. But `evaluate_pyramid` never checks this. The pyramid gets a green light while the account is already one small loss away from breaching the daily stop.

### Severity: HIGH

The pyramid entry path completely circumvents the prop firm's primary safety guard. A position that is "in profit" is not the same as "the account is safe to add risk."

### Code Fix

**File:** `main.py` — gate the pyramid button behind `risk_guard.can_trade()` AND check daily loss buffer

```python
# main.py — inside the pyramid evaluation / execution block
if signal and signal.pyramid:
    rg = st.session_state["risk_guard"]
    
    # 1. Hard guard: can we trade at all?
    if not rg.can_trade():
        st.error("Pyramid blocked: RiskGuard says trading is halted.")
        signal = None  # Nullify the signal
    else:
        # 2. Soft guard: does this pyramid's risk fit within remaining daily buffer?
        # Compute pyramid leg risk
        pyr_risk_ticks = abs(signal.entry_price - signal.stop_loss) / config.TICK_SIZE_MNQ
        pyr_risk_dollars = pyr_risk_ticks * config.TICK_VALUE_MNQ * signal.contracts
        
        # Add existing unrealized (if negative, it adds to risk)
        pos = st.session_state["active_position"]
        current_price = close
        if pos.is_long:
            unrealized = (current_price - pos.entry_price) / config.TICK_SIZE_MNQ * config.TICK_VALUE_MNQ * pos.contracts
        else:
            unrealized = (pos.entry_price - current_price) / config.TICK_SIZE_MNQ * config.TICK_VALUE_MNQ * pos.contracts
        
        # Worst case: pyramid stops out + original also stops out from here
        # (conservative: assume both fail)
        total_potential_loss = rg.state.daily_pnl + unrealized - pyr_risk_dollars
        # daily_pnl is negative for losses; we want to see if we'd breach -$300
        
        if total_potential_loss <= -config.DAILY_STOP_LOSS:
            st.error(f"Pyramid blocked: would breach daily stop. "
                     f"Current daily PnL=${rg.state.daily_pnl:.0f}, "
                     f"pyramid risk=${pyr_risk_dollars:.0f}")
            signal = None
        else:
            st.warning(f"Pyramid approved. Risk=${pyr_risk_dollars:.0f}, "
                       f"remaining daily buffer=${config.DAILY_STOP_LOSS + rg.state.daily_pnl:.0f}")
```

**File:** `entry_engine.py` — pass `risk_guard` into `evaluate_pyramid` and check it

```python
def evaluate_pyramid(
    active_position: ActivePosition,
    price_data: pd.DataFrame,
    fvg_list: List[FVG],
    regime: str,
    risk_guard: Optional[RiskGuard] = None,
) -> bool:
    if regime != "BLUE":
        return False
    if active_position.pyramid_count >= active_position.max_pyramids:
        return False
    
    # NEW: Check risk guard if provided
    if risk_guard is not None and not risk_guard.can_trade():
        logger.warning("Pyramid rejected: RiskGuard.can_trade() returned False")
        return False
    ...
```

---

## Flaw 5: Trailing Drawdown Only Checked on `record_trade_closed()` — Intraday Breach Blindness (CRITICAL)

### The Bug

In `risk_guard.py`, the drawdown check is only triggered in two places:
1. `can_trade()` → `_check_drawdown(self.state.current_equity)` (line 81)
2. `record_trade_closed(pnl)` → updates equity, then recalcs drawdown (line 147)

**There is NO intraday unrealized PnL tracking.**

`ActivePosition` has `unrealized_pnl: float = 0.0`, but:
- It is never updated in `main.py` or anywhere else
- `current_r_multiple()` computes theoretical R based on current price, but this is not fed back into `RiskGuard`
- `RiskGuard` has no `update_unrealized(pnl)` method

### What This Means

**Scenario:**
1. Account starts at $50,000. Peak = $50,000.
2. Trade opens. Position goes -$1,500 unrealized.
3. `RiskGuard` state:
   - `daily_pnl` = $0 (trade still open)
   - `current_equity` = $50,000 (no realized PnL yet)
   - `drawdown_used` = $0
   - `can_trade` = **True**
4. System sees "no drawdown, no daily loss" and happily takes a **second trade** or approves a **pyramid**.
5. Second trade/pyramid adds more risk.
6. Market continues against the position. Combined unrealized now -$2,100.
7. **Drawdown limit ($2,000) is breached.** But `RiskGuard` doesn't know.
8. System keeps trading. Third entry is evaluated. `can_trade()` returns `True` because `current_equity` is still $50,000 on paper.
9. Eventually the user closes the position. `record_trade_closed(-$2,100)` is called.
10. NOW `RiskGuard` sees: `daily_pnl = -$2,100`, `current_equity = $47,900`, `drawdown_used = $2,100`.
11. `can_trade()` returns `False`. Trading halts.
12. **But the account is already blown past the $2,000 drawdown.** On some prop firms, this means account termination or a forced reset fee.

### Prop Firm Reality

Most prop firms track **realized + unrealized** for drawdown. The $2,000 trailing drawdown is from the **equity peak**, which includes open PnL. AuraTrade's `RiskGuard` only tracks realized PnL. This is a **fatal mismatch** with prop firm risk systems.

### Severity: CRITICAL

This is the single most dangerous flaw for prop firm survival. A $2,000 drawdown can be breached without the system ever knowing, and it will continue adding positions while the account is already in violation.

### Code Fix

**File:** `risk_guard.py` — add intraday unrealized tracking and pre-trade check

```python
class RiskGuard:
    ...
    
    def update_unrealized(self, unrealized_pnl: float) -> None:
        """
        Update with current unrealized PnL from open positions.
        Call this every bar or every 5 seconds.
        """
        effective_equity = self.state.current_equity + unrealized_pnl
        self.state.current_equity = effective_equity
        
        # Update peak (if unrealized pushes equity higher)
        if effective_equity > self.state.equity_peak:
            self.state.equity_peak = effective_equity
        
        # Check drawdown with unrealized included
        self.state.drawdown_used = self.state.equity_peak - effective_equity
        if self.state.drawdown_used >= config.TRAILING_DRAWDOWN:
            self.state.drawdown_breached = True
            self.state.can_trade = False
            logger.error(
                f"DRAWDOWN BREACH (intraday): peak=${self.state.equity_peak:,.2f} "
                f"effective=${effective_equity:,.2f} "
                f"used=${self.state.drawdown_used:,.2f} "
                f"unrealized=${unrealized_pnl:,.2f}"
            )
    
    def can_trade(self, current_equity: Optional[float] = None, unrealized_pnl: float = 0.0) -> bool:
        if current_equity is not None:
            self.state.current_equity = current_equity
        
        # Use effective equity (realized + unrealized) for ALL checks
        effective_equity = self.state.current_equity + unrealized_pnl
        
        # 1. Daily stop (realized only — prop firms usually don't count unrealized against daily stop)
        if self.state.daily_pnl <= -config.DAILY_STOP_LOSS:
            self.state.daily_stop_hit = True
            self.state.can_trade = False
            return False
        
        # 2. Max trades
        if self.state.trades_taken >= self.state.max_trades_allowed:
            self.state.can_trade = False
            return False
        
        # 3. Trailing drawdown (WITH unrealized)
        # Update peak first
        if effective_equity > self.state.equity_peak:
            self.state.equity_peak = effective_equity
        
        self.state.drawdown_used = self.state.equity_peak - effective_equity
        if self.state.drawdown_used >= config.TRAILING_DRAWDOWN:
            self.state.drawdown_breached = True
            self.state.can_trade = False
            logger.error("TRAILING DRAWDOWN BREACHED (effective equity) — trading halted.")
            return False
        
        # 4. Market hours
        if not self._in_market_hours():
            self.state.can_trade = False
            return False
        
        self.state.can_trade = True
        return True
```

**File:** `main.py` — call `update_unrealized()` every loop iteration

```python
# At the top of the main loop or in a periodic callback:
if st.session_state["active_position"]:
    pos = st.session_state["active_position"]
    # Compute true unrealized
    if pos.is_long:
        unrealized = (close - pos.blended_entry_price) / config.TICK_SIZE_MNQ * config.TICK_VALUE_MNQ * pos.contracts
    else:
        unrealized = (pos.blended_entry_price - close) / config.TICK_SIZE_MNQ * config.TICK_VALUE_MNQ * pos.contracts
    
    st.session_state["risk_guard"].update_unrealized(unrealized)
    
    # Display warning if drawdown is approaching
    status = st.session_state["risk_guard"].get_status()
    if status["drawdown_used"] > config.TRAILING_DRAWDOWN * 0.75:
        st.error(f"🚨 DRAWDOWN WARNING: ${status['drawdown_used']:.0f} / ${config.TRAILING_DRAWDOWN:.0f}")
```

---

## Worst-Case Scenario: "Death by a Thousand Cuts" on a $50k Account

### The Perfect Storm

Imagine a BLUE regime Tuesday. The market is trending. All five flaws trigger simultaneously:

**09:45 AM — Trade 1 (New Entry):**
- Long 2 MNQ at 26,000. Stop 25,980. Risk = $80.
- `RiskGuard`: trades_taken = 1, daily_pnl = $0, drawdown_used = $0.
- System says: "All clear."

**10:15 AM — Pyramid #1:**
- Price hits +1R (+20 pts = +$80 unrealized). New FVG forms.
- `evaluate_pyramid()` checks: `pyramid_count = 0 >= 1?` → False. **Pyramid approved.** (Flaw 1)
- `evaluate_pyramid()` does NOT check `RiskGuard.can_trade()`. (Flaw 4)
- `RiskGuard` has no unrealized tracking, so it still sees $0 drawdown. (Flaw 5)
- Pyramid signal: +2 MNQ at 26,020, stop 25,990. Risk = $120.
- `main.py` creates a **new** `ActivePosition`, replacing the original. (Flaw 2)
- New position tracked: 2 contracts at 26,020, stop 25,990. Original data is gone.
- `record_trade_opened()` called. trades_taken = 2. **Max trades reached.**
- `RiskGuard` state: still thinks everything is fine.

**10:30 AM — The Turn:**
- Market reverses. Price drops to 25,985.
- `should_remove_quickly()` checks: close 25,985 vs EMA9 (say, 26,005). Close > EMA9 → **No exit.**
- System dashboard shows: "Stop 25,990 — 5 pts away, safe."
- **Reality:** Original 2 contracts (at 26,000, stop 25,980) are $60 underwater and 5 pts from their real stop. The system has no idea. (Flaw 2)

**10:45 AM — Pyramid #2 (Yes, Really):**
- `pyramid_count` on the *new* `ActivePosition` is still `0` (it was reset when `main.py` replaced the object). (Flaw 1)
- `MAX_CONTRACTS_MNQ = 2`, `active_position.contracts = 2`. Contract limit check returns 0. Pyramid blocked…
- **BUT:** User manually closes 1 contract via broker app to "reduce risk." `main.py` never syncs broker position. `active_position.contracts` is still `2` in the app's state. Contract limit still blocks it.
- **OR WORSE:** User hits "Close All / Flatten" in `main.py`. `active_position = None`. Then a new entry fires immediately (it's a new position, not a pyramid). trades_taken was already 2, so `can_trade()` blocks it. Account survives this path.
- **BUT ALTERNATIVE PATH:** `active_position.contracts` was somehow 1 (partial fill on pyramid, or user manually adjusted). `evaluate_pyramid()` approves again. `pyramid_count` still 0. **Second pyramid fires.** Now the position has 3+ contracts with a completely broken internal model.

**11:00 AM — The Crash:**
- NFP surprise. MNQ drops 40 points in 2 minutes.
- Price slices through 25,990 and 25,980.
- Both stops fill with 5-tick slippage each.
- Original leg: 80 ticks + 5 slippage = 85 ticks × $0.50 × 2 = **$85 loss**
- Pyramid leg: 120 ticks + 5 slippage = 125 ticks × $0.50 × 2 = **$125 loss**
- **Total loss: $210**
- Plus any unrealized bleed before the stops: ~$15
- **Realized daily PnL: -$225**

**11:05 AM — RiskGuard Wakes Up:**
- `record_trade_closed(-$225)` is called.
- `RiskGuard`: daily_pnl = -$225. Under $300 limit. Barely.
- drawdown_used: peak was $50,000. Current equity $49,775. drawdown_used = $225. Under $2,000.
- `can_trade()` returns `False` because max trades (2) reached. Account is "safe" on paper.

**But what if the first trade was also a loss?**
- Trade 1: stopped out for -$100.
- Trade 2 + Pyramid: stopped out for -$210.
- Total: -$310. **Daily stop breached.** Account violation.

**And what if the drawdown was already elevated?**
- Previous day's peak: $51,500 (account had run up).
- Today starts at $50,000, but trailing drawdown peak is still $51,500.
- Drawdown allowance = $51,500 - $2,000 = $49,500 floor.
- After -$310 loss: equity = $49,690. **Above $49,500. Safe.**
- But during the trade, unrealized was -$1,500 at one point. Effective equity hit $48,500. **$3,000 below peak.** Trailing drawdown breached.
- `RiskGuard` never knew because it doesn't track unrealized. (Flaw 5)

### Bottom Line

If all flaws trigger together on a 50k account with $2k drawdown:

1. **The system pyramids without counting** (Flaw 1)
2. **It loses track of the original position** (Flaw 2)
3. **Combined risk hits $200+ in one position** (Flaw 3)
4. **It never checks if the daily stop can absorb that risk** (Flaw 4)
5. **It never sees the -$1,500 unrealized dip that breaches drawdown** (Flaw 5)

**Result:** A single trending morning can rack up $200–$350 in realized losses, potentially breaching the $300 daily stop. During the worst of it, the account may have been $1,500+ underwater unrealized — well past the $2,000 trailing drawdown from a higher peak — but the system kept trading because `RiskGuard` was blind.

On a prop firm account, this means:
- **Daily stop breach:** Account may be locked for the day or reset.
- **Trailing drawdown breach:** Account may be terminated or require a fee to reactivate.
- **Consistency rule violation:** If pyramiding causes a single day to represent >30% of monthly profit target, the payout may be denied.

---

## Additional Concerns (MEDIUM / LOW)

### Concern A: `record_trade_opened()` Called on Pyramid (MEDIUM)

`main.py` line 322 calls `record_trade_opened()` every time "TAKE ENTRY" is pressed, including pyramids. This increments `trades_taken`. If the design intent is "max 2 entries, pyramids free," then pyramids should NOT increment the trade counter. If the intent is "max 2 executions total," then the current behavior is correct but should be documented. **Recommendation:** Make this explicit in config:
```python
PYRAMID_COUNTS_AS_TRADE: bool = False  # Set to True if prop firm counts pyramid as separate trade
```

### Concern B: No Broker Position Sync (MEDIUM)

`main.py` never calls `client.get_positions()` to sync the actual broker position. If the user manually closes a contract, `active_position.contracts` is stale. The contract limit math is wrong. **Recommendation:** Sync position size from broker before every `evaluate_entry()` call.

### Concern C: FVG `filled` Flag Race Condition (LOW)

`evaluate_pyramid` filters on `not f.filled` (line 283). If the original position's entry FVG gets marked `filled` by the detector, a new FVG is required. This is correct logic, but if `is_fvg_filled()` has a bug or lag, pyramids could be approved on stale FVGs. Worth monitoring.

---

## Summary of Fixes Required

| # | Flaw | Severity | File(s) | Fix Summary |
|---|------|----------|---------|-------------|
| 1 | `pyramid_count` never incremented | CRITICAL | `entry_engine.py`, `main.py` | Increment on approval; mutate position in place, don't replace |
| 2 | Pyramid replaces `ActivePosition` | CRITICAL | `main.py` | Update existing position; add `legs` list; track blended entry and worst stop |
| 3 | Combined risk not computed | HIGH | `entry_engine.py`, `ActivePosition` | Add `total_risk_dollars` property; cap combined risk at 50% of daily stop |
| 4 | Pyramid bypasses `can_trade()` | HIGH | `entry_engine.py`, `main.py` | Pass `RiskGuard` into `evaluate_pyramid`; check daily buffer before approval |
| 5 | Drawdown only on close | CRITICAL | `risk_guard.py`, `main.py` | Add `update_unrealized()`; call every bar; use effective equity for drawdown |
| A | Pyramid counts as trade | MEDIUM | `main.py` | Add config flag; conditionally skip `record_trade_opened()` |
| B | No broker sync | MEDIUM | `main.py` | Poll `client.get_positions()` before evaluation |

---

## Auditor's Final Verdict

**Status: NOT CLEARED FOR LIVE TRADING**

The AuraTrade pyramiding system has fundamental architectural flaws that make it unsafe for prop firm accounts. The combination of infinite pyramiding potential, complete position tracking failure, and drawdown blindness creates a material risk of account violation within a single trading session.

**Minimum viable fixes before live deployment:**
1. Implement `pyramid_count` increment and position mutation (not replacement)
2. Add `legs` tracking to `ActivePosition` with blended price and worst-stop computation
3. Wire `RiskGuard.can_trade()` and `update_unrealized()` into every bar of the main loop
4. Add a hard combined-risk ceiling (e.g., $150 max total position risk)
5. Test the full pyramid lifecycle in simulation: entry → pyramid #1 → price reversal → stop-out → verify `RiskGuard` catches the daily stop and drawdown correctly

*End of Audit*
