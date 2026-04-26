"""
Risk Guard — Prop Firm Safety Module
------------------------------------
Enforces hard risk limits required for prop firm compliance:
  • $300 daily stop loss
  • Max 2 trades per session (9:30 AM – 4:00 PM ET)
  • $2,000 trailing drawdown from peak equity
  • Max 2 contracts (MNQ) or 1 contract (MES)
  • "Remove Quickly" exit: close if price closes opposite side of 9-EMA
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, Optional
from datetime import datetime, time
import pytz

import config

logger = logging.getLogger(__name__)

EASTERN = pytz.timezone("US/Eastern")


@dataclass
class RiskState:
    """Snapshot of current risk metrics."""
    daily_pnl: float = 0.0
    trades_taken: int = 0
    max_trades_allowed: int = config.MAX_TRADES_PER_SESSION
    equity_peak: float = config.ACCOUNT_BALANCE
    current_equity: float = config.ACCOUNT_BALANCE
    drawdown_used: float = 0.0
    drawdown_limit: float = config.TRAILING_DRAWDOWN
    daily_stop_hit: bool = False
    drawdown_breached: bool = False
    can_trade: bool = True
    last_reset_date: Optional[datetime] = None


class RiskGuard:
    """
    Central risk manager enforcing prop firm rules.
    Must be instantiated once per trading day and persisted across bars.
    """

    def __init__(self):
        self.state = RiskState()
        self._session_start_fired: bool = False
        logger.info("RiskGuard initialized.")

    # ═══════════════════════════════════════════════════════════════════════
    #  Core Checks
    # ═══════════════════════════════════════════════════════════════════════

    def can_trade(self, current_equity: Optional[float] = None) -> bool:
        """
        Returns True ONLY if ALL prop firm rules are satisfied:
          1) Daily stop not hit
          2) Max trades not exceeded
          3) Trailing drawdown not breached
          4) Within market hours
        """
        if current_equity is not None:
            self.state.current_equity = current_equity

        # 1. Daily stop loss
        if self.state.daily_pnl <= -config.DAILY_STOP_LOSS:
            self.state.daily_stop_hit = True
            self.state.can_trade = False
            logger.warning(f"DAILY STOP HIT: PnL ${self.state.daily_pnl:.2f} <= -${config.DAILY_STOP_LOSS}")
            return False

        # 2. Max trades per session
        if self.state.trades_taken >= self.state.max_trades_allowed:
            self.state.can_trade = False
            logger.warning(f"MAX TRADES REACHED: {self.state.trades_taken}/{self.state.max_trades_allowed}")
            return False

        # 3. Trailing drawdown
        if self._check_drawdown(self.state.current_equity):
            self.state.drawdown_breached = True
            self.state.can_trade = False
            logger.warning("TRAILING DRAWDOWN BREACHED — trading halted.")
            return False

        # 4. Market hours
        if not self._in_market_hours():
            self.state.can_trade = False
            return False

        self.state.can_trade = True
        return True

    def check_drawdown(self, current_equity: float) -> bool:
        """
        Update equity peak and check if trailing drawdown is breached.

        Returns
        -------
        bool
            True if drawdown limit is breached (trading must stop).
        """
        self.state.current_equity = current_equity
        return self._check_drawdown(current_equity)

    def update_unrealized(self, unrealized_pnl: float) -> bool:
        """
        Update drawdown tracking with open position PnL.

        Computes effective_equity = current_equity + unrealized_pnl
        and checks whether the trailing drawdown limit is breached.

        Parameters
        ----------
        unrealized_pnl : float
            Current unrealized profit/loss of open position(s).

        Returns
        -------
        bool
            True if drawdown is breached (trading must stop).
        """
        effective_equity = self.state.current_equity + unrealized_pnl
        breached = self._check_drawdown(effective_equity)
        if breached:
            self.state.drawdown_breached = True
            self.state.can_trade = False
            logger.warning("TRAILING DRAWDOWN BREACHED via unrealized PnL — trading halted.")
        return breached

    def _check_drawdown(self, current_equity: float) -> bool:
        """Internal drawdown logic."""
        # Update peak
        if current_equity > self.state.equity_peak:
            self.state.equity_peak = current_equity

        self.state.drawdown_used = self.state.equity_peak - current_equity
        breached = self.state.drawdown_used >= config.TRAILING_DRAWDOWN

        if breached:
            logger.error(
                f"DRAWDOWN: peak=${self.state.equity_peak:,.2f} "
                f"current=${current_equity:,.2f} "
                f"used=${self.state.drawdown_used:,.2f} "
                f"limit=${config.TRAILING_DRAWDOWN:,.2f}"
            )
        return breached

    # ═══════════════════════════════════════════════════════════════════════
    #  Trade Lifecycle
    # ═══════════════════════════════════════════════════════════════════════

    def record_trade_opened(self) -> None:
        """Increment trade counter when a new position is opened."""
        self.state.trades_taken += 1
        logger.info(f"Trade opened. Count: {self.state.trades_taken}/{self.state.max_trades_allowed}")

    def record_trade_closed(self, pnl: float) -> None:
        """
        Record realized PnL when a trade closes.
        Updates daily PnL and equity.
        """
        self.state.daily_pnl += pnl
        self.state.current_equity += pnl

        # Update peak if profitable
        if pnl > 0 and self.state.current_equity > self.state.equity_peak:
            self.state.equity_peak = self.state.current_equity

        # Recalc drawdown
        self.state.drawdown_used = self.state.equity_peak - self.state.current_equity

        logger.info(
            f"Trade closed PnL=${pnl:.2f} | Daily PnL=${self.state.daily_pnl:.2f} | "
            f"Equity=${self.state.current_equity:,.2f}"
        )

    def record_trade_pnl(self, pnl: float) -> None:
        """Alias for record_trade_closed for backward compatibility."""
        self.record_trade_closed(pnl)

    # ═══════════════════════════════════════════════════════════════════════
    #  Remove Quickly — 9-EMA Exit Rule
    # ═══════════════════════════════════════════════════════════════════════

    @staticmethod
    def should_remove_quickly(position_direction: str, close_price: float, ema9: float) -> bool:
        """
        "Remove Quickly" rule: if price closes on the OPPOSITE side of 9-EMA,
        exit the position immediately.

        Parameters
        ----------
        position_direction : str
            "long" or "short"
        close_price : float
            Current candle close.
        ema9 : float
            Current 9-EMA value.

        Returns
        -------
        bool
            True if position should be closed immediately.
        """
        if position_direction == "long":
            # Long: exit if close BELOW ema9
            return close_price < ema9
        elif position_direction == "short":
            # Short: exit if close ABOVE ema9
            return close_price > ema9
        return False

    # ═══════════════════════════════════════════════════════════════════════
    #  Daily Reset
    # ═══════════════════════════════════════════════════════════════════════

    def reset_daily(self, equity_at_open: Optional[float] = None) -> None:
        """
        Call at market open (9:30 AM ET) to reset daily counters.
        Preserves trailing drawdown peak — that is NEVER reset.
        """
        now = datetime.now(EASTERN)
        self.state.last_reset_date = now
        self.state.daily_pnl = 0.0
        self.state.trades_taken = 0
        self.state.daily_stop_hit = False
        self.state.can_trade = True

        if equity_at_open is not None:
            self.state.current_equity = equity_at_open
            # Peak only adjusts UP, never down
            if equity_at_open > self.state.equity_peak:
                self.state.equity_peak = equity_at_open

        self._session_start_fired = True
        logger.info(f"Daily reset at {now.strftime('%H:%M:%S ET')}. Equity=${self.state.current_equity:,.2f}")

    # ═══════════════════════════════════════════════════════════════════════
    #  Contract Limits
    # ═══════════════════════════════════════════════════════════════════════

    @staticmethod
    def max_contracts_for_product(product: str) -> int:
        """Return maximum allowed contracts for product code."""
        return config.get_max_contracts(product.upper())

    # ═══════════════════════════════════════════════════════════════════════
    #  Status & Helpers
    # ═══════════════════════════════════════════════════════════════════════

    def get_status(self) -> Dict:
        """Return current risk metrics as a dict for dashboard display."""
        return {
            "daily_pnl": round(self.state.daily_pnl, 2),
            "trades_taken": self.state.trades_taken,
            "max_trades": self.state.max_trades_allowed,
            "equity_peak": round(self.state.equity_peak, 2),
            "current_equity": round(self.state.current_equity, 2),
            "drawdown_used": round(self.state.drawdown_used, 2),
            "drawdown_limit": self.state.drawdown_limit,
            "daily_stop_hit": self.state.daily_stop_hit,
            "drawdown_breached": self.state.drawdown_breached,
            "can_trade": self.state.can_trade,
            "in_market_hours": self._in_market_hours(),
            "last_reset": (
                self.state.last_reset_date.strftime("%Y-%m-%d %H:%M:%S %Z")
                if self.state.last_reset_date else "Never"
            ),
        }

    @staticmethod
    def _in_market_hours() -> bool:
        """Check if current Eastern Time is within 9:30 AM – 4:00 PM."""
        now = datetime.now(EASTERN)
        market_open = time(config.MARKET_OPEN_HOUR, config.MARKET_OPEN_MINUTE)
        market_close = time(config.MARKET_CLOSE_HOUR, config.MARKET_CLOSE_MINUTE)
        return market_open <= now.time() <= market_close

    def remaining_trades(self) -> int:
        """Return number of trades still allowed today."""
        return max(0, self.state.max_trades_allowed - self.state.trades_taken)

    def daily_pnl_pct(self) -> float:
        """Return daily PnL as percentage of daily stop limit."""
        if config.DAILY_STOP_LOSS == 0:
            return 0.0
        return abs(self.state.daily_pnl) / config.DAILY_STOP_LOSS
