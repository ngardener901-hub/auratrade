"""
Tradovate API Client
--------------------
Production-ready wrapper for Tradovate REST API with:
  • Authentication (token-based)
  • Order placement (MKT, LMT, STP)
  • Position & account queries
  • Retry logic with exponential backoff
  • Comprehensive error handling
"""

import logging
import time
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from enum import Enum

import requests
import config

logger = logging.getLogger(__name__)


class OrderType(Enum):
    MKT = "Market"
    LMT = "Limit"
    STP = "Stop"
    STP_LMT = "StopLimit"


class OrderSide(Enum):
    BUY = "Buy"
    SELL = "Sell"


class TimeInForce(Enum):
    GTC = "GTC"
    DAY = "Day"
    FOK = "FOK"
    IOC = "IOC"


@dataclass
class OrderRequest:
    """Normalized order request for Tradovate."""
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: int
    price: Optional[float] = None
    stop_price: Optional[float] = None
    time_in_force: TimeInForce = TimeInForce.DAY
    account_id: Optional[int] = None


@dataclass
class OrderResponse:
    """Simplified order response."""
    success: bool
    order_id: Optional[str] = None
    status: str = "unknown"
    message: str = ""
    raw: Optional[Dict] = None


class TradovateClient:
    """
    Tradovate REST API client.

    Usage
    -----
    >>> client = TradovateClient()
    >>> client.authenticate()
    >>> client.place_order(OrderRequest(symbol="MNQ", side=OrderSide.BUY, ...))
    """

    def __init__(self):
        self.base_url = config.TRADOVATE_BASE_URL.rstrip("/")
        self.ws_url = config.TRADOVATE_WS_URL
        self.token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.account_id: int = config.TRADOVATE_ACCOUNT_ID
        self.is_demo = "demo" in self.base_url

        self._session = requests.Session()
        self._session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json",
        })

    # ═══════════════════════════════════════════════════════════════════════
    #  Authentication
    # ═══════════════════════════════════════════════════════════════════════

    def authenticate(self) -> bool:
        """
        Authenticate with Tradovate and obtain access token.
        Uses credentials from environment / config.

        Returns
        -------
        bool
            True if authentication succeeded.
        """
        payload = {
            "name": config.TRADOVATE_USERNAME,
            "password": config.TRADOVATE_PASSWORD,
            "appId": config.TRADOVATE_APP_ID,
            "appVersion": config.TRADOVATE_APP_VERSION,
            "deviceId": config.TRADOVATE_DEVICE_ID,
            "cid": config.TRADOVATE_CID,
        }

        # Remove empty values
        payload = {k: v for k, v in payload.items() if v}

        url = f"{self.base_url}/auth/accesstoken"
        logger.info(f"Authenticating to Tradovate ({'DEMO' if self.is_demo else 'LIVE'})...")

        try:
            resp = self._session.post(url, json=payload, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            self.token = data.get("accessToken") or data.get("token")
            self.refresh_token = data.get("refreshToken")

            if self.token:
                self._session.headers["Authorization"] = f"Bearer {self.token}"
                logger.info("Tradovate authentication successful.")
                return True
            else:
                logger.error("No token in Tradovate auth response.")
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Tradovate authentication failed: {e}")
            return False

    def refresh_auth(self) -> bool:
        """Refresh access token using refresh token."""
        if not self.refresh_token:
            return self.authenticate()

        payload = {"refreshToken": self.refresh_token}
        url = f"{self.base_url}/auth/refresh"

        try:
            resp = self._session.post(url, json=payload, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            self.token = data.get("accessToken") or data.get("token")
            if self.token:
                self._session.headers["Authorization"] = f"Bearer {self.token}"
                return True
        except requests.exceptions.RequestException as e:
            logger.warning(f"Token refresh failed: {e}")
        return self.authenticate()

    # ═══════════════════════════════════════════════════════════════════════
    #  Orders
    # ═══════════════════════════════════════════════════════════════════════

    def place_order(self, order: OrderRequest) -> OrderResponse:
        """
        Submit an order to Tradovate.

        Parameters
        ----------
        order : OrderRequest

        Returns
        -------
        OrderResponse
        """
        if not self.token:
            if not self.authenticate():
                return OrderResponse(success=False, message="Not authenticated")

        payload = self._build_order_payload(order)
        url = f"{self.base_url}/order/placeorder"

        raw_resp = self._post_with_retry(url, payload)
        if raw_resp is None:
            return OrderResponse(success=False, message="API failure after retries")

        # Parse response
        if isinstance(raw_resp, list) and len(raw_resp) > 0:
            data = raw_resp[0]
        elif isinstance(raw_resp, dict):
            data = raw_resp
        else:
            data = {}

        success = "id" in data or "orderId" in data
        order_id = str(data.get("id", data.get("orderId", "")))
        status = data.get("status", "unknown")

        if success:
            logger.info(f"Order placed: {order.side.value} {order.quantity} {order.symbol} @ {order.order_type.value} — ID={order_id}")
        else:
            logger.error(f"Order failed: {data}")

        return OrderResponse(
            success=success,
            order_id=order_id or None,
            status=status,
            message=data.get("errorText", "") or data.get("message", ""),
            raw=data,
        )

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an open order by ID."""
        url = f"{self.base_url}/order/cancelorder"
        payload = {"orderId": int(order_id)}

        raw = self._post_with_retry(url, payload)
        if raw is None:
            return False
        success = "id" in raw or "orderId" in raw if isinstance(raw, dict) else True
        logger.info(f"Cancel order {order_id}: {'OK' if success else 'FAILED'}")
        return success

    def cancel_all_orders(self) -> bool:
        """Cancel all working orders for the account."""
        url = f"{self.base_url}/order/cancelallorders"
        payload = {"accountId": self.account_id}

        raw = self._post_with_retry(url, payload)
        success = raw is not None
        logger.info(f"Cancel all orders: {'OK' if success else 'FAILED'}")
        return success

    def place_bracket_order(
        self,
        entry_price: float,
        stop_price: float,
        target_price: float,
        contracts: int,
        direction: str,
        product: str = "MNQ",
    ) -> OrderResponse:
        """
        Place an OCO (One-Cancels-Other) bracket order.

        Bracket consists of:
          1. Entry: LMT order at entry_price
          2. Stop:  STP order at stop_price (OCO leg 1)
          3. Target: LMT order at target_price (OCO leg 2)

        Parameters
        ----------
        entry_price : float
            Limit entry price.
        stop_price : float
            Stop-loss trigger price.
        target_price : float
            Target / take-profit limit price.
        contracts : int
            Number of contracts.
        direction : str
            "long" or "short".
        product : str
            Symbol (e.g. "MNQ").

        Returns
        -------
        OrderResponse
        """
        if direction not in ("long", "short"):
            return OrderResponse(success=False, message=f"Invalid direction: {direction}")

        entry_side = OrderSide.BUY if direction == "long" else OrderSide.SELL
        exit_side = OrderSide.SELL if direction == "long" else OrderSide.BUY

        # ── 1. Place entry limit order ──
        entry_order = OrderRequest(
            symbol=product,
            side=entry_side,
            order_type=OrderType.LMT,
            quantity=contracts,
            price=entry_price,
            time_in_force=TimeInForce.DAY,
            account_id=self.account_id,
        )
        entry_resp = self.place_order(entry_order)
        if not entry_resp.success:
            logger.error(f"Bracket entry failed: {entry_resp.message}")
            return entry_resp

        # ── 2. Place OCO for stop + target ──
        oco_payload = {
            "accountId": self.account_id,
            "contractId": config.TRADOVATE_CID,
            "symbol": product,
            "orderType": "OCO",
            "timeInForce": TimeInForce.DAY.value,
            "bracket1": {
                "action": exit_side.value,
                "orderQty": contracts,
                "orderType": OrderType.STP.value,
                "stopPrice": stop_price,
            },
            "bracket2": {
                "action": exit_side.value,
                "orderQty": contracts,
                "orderType": OrderType.LMT.value,
                "price": target_price,
            },
        }

        oco_url = f"{self.base_url}/order/placeoco"
        oco_raw = self._post_with_retry(oco_url, oco_payload)
        if oco_raw is None:
            # Attempt to cancel the entry order so we don't hang unprotected
            self.cancel_order(str(entry_resp.order_id or ""))
            return OrderResponse(
                success=False,
                message="Bracket OCO failed after retries; entry cancelled.",
            )

        # Parse OCO response
        if isinstance(oco_raw, list) and len(oco_raw) > 0:
            oco_data = oco_raw[0]
        elif isinstance(oco_raw, dict):
            oco_data = oco_raw
        else:
            oco_data = {}

        oco_success = "id" in oco_data or "orderId" in oco_data
        oco_order_id = str(oco_data.get("id", oco_data.get("orderId", "")))

        if oco_success:
            logger.info(
                f"Bracket placed: {direction} {contracts} {product} @ {entry_price} | "
                f"Stop={stop_price} Target={target_price} | EntryID={entry_resp.order_id} OCOID={oco_order_id}"
            )
        else:
            logger.error(f"Bracket OCO failed: {oco_data}")
            # Cancel entry to avoid naked position
            self.cancel_order(str(entry_resp.order_id or ""))

        return OrderResponse(
            success=oco_success,
            order_id=oco_order_id or None,
            status=oco_data.get("status", "unknown"),
            message=oco_data.get("errorText", "") or oco_data.get("message", ""),
            raw=oco_data,
        )

    # ═══════════════════════════════════════════════════════════════════════
    #  Positions & Account
    # ═══════════════════════════════════════════════════════════════════════

    def get_positions(self) -> List[Dict[str, Any]]:
        """Return current open positions for the account."""
        url = f"{self.base_url}/position/list"
        params = {"accountId": self.account_id}

        raw = self._get_with_retry(url, params)
        if raw is None:
            return []

        if isinstance(raw, list):
            return raw
        if isinstance(raw, dict) and "d" in raw:
            return raw["d"]
        return [raw] if isinstance(raw, dict) else []

    def get_account(self) -> Optional[Dict[str, Any]]:
        """Return account summary."""
        url = f"{self.base_url}/account/item"
        params = {"id": self.account_id}

        raw = self._get_with_retry(url, params)
        if raw is None:
            return None
        return raw if isinstance(raw, dict) else None

    def get_cash_balance(self) -> Optional[float]:
        """Return available cash balance."""
        acct = self.get_account()
        if acct:
            return float(acct.get("cashBalance", 0))
        return None

    def get_open_orders(self) -> List[Dict[str, Any]]:
        """Return list of working orders."""
        url = f"{self.base_url}/order/list"
        params = {"accountId": self.account_id}

        raw = self._get_with_retry(url, params)
        if raw is None:
            return []
        if isinstance(raw, list):
            return [o for o in raw if o.get("status") in ("Working", "Pending")]
        return []

    # ═══════════════════════════════════════════════════════════════════════
    #  Internal Helpers
    # ═══════════════════════════════════════════════════════════════════════

    def _build_order_payload(self, order: OrderRequest) -> Dict:
        """Map OrderRequest to Tradovate REST payload."""
        payload = {
            "accountId": order.account_id or self.account_id,
            "contractId": config.TRADOVATE_CID,
            "symbol": order.symbol,
            "action": order.side.value,
            "orderQty": order.quantity,
            "orderType": order.order_type.value,
            "timeInForce": order.time_in_force.value,
        }
        if order.order_type in (OrderType.LMT, OrderType.STP_LMT) and order.price is not None:
            payload["price"] = order.price
        if order.order_type in (OrderType.STP, OrderType.STP_LMT) and order.stop_price is not None:
            payload["stopPrice"] = order.stop_price
        return payload

    def _post_with_retry(self, url: str, payload: Dict) -> Optional[Any]:
        """POST with exponential backoff retry."""
        for attempt in range(1, config.TRADOVATE_MAX_RETRIES + 1):
            try:
                resp = self._session.post(url, json=payload, timeout=10)
                if resp.status_code == 401 and attempt < config.TRADOVATE_MAX_RETRIES:
                    logger.warning("Token expired, refreshing...")
                    self.refresh_auth()
                    continue
                resp.raise_for_status()
                return resp.json()
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt}/{config.TRADOVATE_MAX_RETRIES}): {e}")
                if attempt < config.TRADOVATE_MAX_RETRIES:
                    time.sleep(config.TRADOVATE_RETRY_DELAY_SECONDS * attempt)
        logger.error(f"Failed after {config.TRADOVATE_MAX_RETRIES} attempts: {url}")
        return None

    def _get_with_retry(self, url: str, params: Optional[Dict] = None) -> Optional[Any]:
        """GET with exponential backoff retry."""
        for attempt in range(1, config.TRADOVATE_MAX_RETRIES + 1):
            try:
                resp = self._session.get(url, params=params, timeout=10)
                if resp.status_code == 401 and attempt < config.TRADOVATE_MAX_RETRIES:
                    logger.warning("Token expired, refreshing...")
                    self.refresh_auth()
                    continue
                resp.raise_for_status()
                return resp.json()
            except requests.exceptions.RequestException as e:
                logger.warning(f"GET failed (attempt {attempt}/{config.TRADOVATE_MAX_RETRIES}): {e}")
                if attempt < config.TRADOVATE_MAX_RETRIES:
                    time.sleep(config.TRADOVATE_RETRY_DELAY_SECONDS * attempt)
        return None
