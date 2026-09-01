"""
INFINI Broker Adapters
=======================
Pluggable connectors so the voice-trading module can talk to a real
broker's API to place/cancel orders and read portfolio/orders/quotes,
instead of only parsing what the user said.

Architecture
------------
BrokerAdapter is the contract every broker connector must implement:
    login()            -> establishes/refreshes a session, returns bool
    get_portfolio()     -> list of current positions
    get_orders()        -> list of open/working orders
    get_quote(symbol)   -> best bid/offer + last price for a symbol
    place_order(...)    -> submit a BUY/SELL order, returns the broker's
                            order id + raw response
    cancel_order(id)    -> cancel a working order

SettradeOpenAPIAdapter implements this against Settrade Open API
(https://developer.settrade.com/open-api/), which is shared
infrastructure used by MANY Thai brokers (Bualuang Securities, Globlex,
Yuanta, Phillip Securities, Pi Securities, Classic Ausiris, Country
Group, and others) — each broker just has its own `broker_id`. So one
adapter here covers "Settrade/Bualuang and other brokers" in one shot,
as long as the broker in question runs on Settrade Open API.

IMPORTANT — things I (Claude) genuinely cannot do for you:
  - I cannot obtain a live app_id / app_secret / broker_id for you.
    Those come from registering as a developer with YOUR broker and
    getting their Open API application approved. This module expects
    you to paste those in via the existing "API Key / Token" field in
    the voice widget (stored as JSON, see _parse_stored_credentials).
  - I have not been able to test this against a live Settrade Open API
    sandbox or production endpoint (no credentials available here).
    The request/response shapes below follow the publicly documented
    auth flow and the official stt-openapi-signer-python reference
    implementation, but you MUST test against Settrade's sandbox
    environment before pointing this at a real money account.
  - A broker that is NOT on Settrade Open API (e.g. an entirely
    different in-house system) needs its own adapter class below —
    the BrokerAdapter contract is designed so that's a small,
    self-contained addition, not a rewrite.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

import httpx


class BrokerError(RuntimeError):
    """Raised for any broker-adapter failure (auth, network, rejected order, ...)."""


@dataclass
class OrderResult:
    ok: bool
    broker_order_id: str | None = None
    status: str = ""
    message: str = ""
    raw: dict[str, Any] = field(default_factory=dict)


class BrokerAdapter:
    """Contract every broker connector implements. Do not instantiate directly."""

    name = "generic"

    def __init__(self, credentials: dict[str, Any]):
        self.credentials = credentials or {}

    def login(self) -> bool:
        raise NotImplementedError

    def get_portfolio(self, account_no: str) -> list[dict[str, Any]]:
        raise NotImplementedError

    def get_orders(self, account_no: str) -> list[dict[str, Any]]:
        raise NotImplementedError

    def get_quote(self, symbol: str) -> dict[str, Any]:
        raise NotImplementedError

    def place_order(
        self,
        account_no: str,
        symbol: str,
        side: str,       # "BUY" | "SELL"
        volume: int,
        price: float | None,
        price_type: str = "LIMIT",  # "LIMIT" | "ATO" | "MP" | ...
    ) -> OrderResult:
        raise NotImplementedError

    def cancel_order(self, account_no: str, order_no: str) -> OrderResult:
        raise NotImplementedError


class SettradeOpenAPIAdapter(BrokerAdapter):
    """
    Real Settrade Open API connector (equity). Used by many Thai brokers
    including Bualuang — set credentials["broker_id"] to the broker's
    own broker_id (Settrade assigns this per broker, e.g. Bualuang is a
    specific numeric id you get from your Open API application page).

    Expected `credentials` dict (this is what you JSON-encode into the
    existing "API Key / Token" field of the voice widget):
        {
          "broker_id": "member broker id, e.g. '023'",
          "app_id": "your registered Open API application id",
          "app_secret": "your registered Open API application secret",
          "app_code": "e.g. 'ALGO' — the service code you registered for",
          "account_no": "the trading account this connection controls",
          "env": "sandbox" | "production"   (defaults to sandbox — safer default)
        }
    """

    name = "settrade_open_api"

    _HOSTS = {
        "sandbox": "https://open-api-test.settrade.com",
        "production": "https://open-api.settrade.com",
    }

    def __init__(self, credentials: dict[str, Any]):
        super().__init__(credentials)
        self.broker_id = str(credentials.get("broker_id") or "").strip()
        self.app_id = str(credentials.get("app_id") or "").strip()
        self.app_secret = str(credentials.get("app_secret") or "").strip()
        self.app_code = str(credentials.get("app_code") or "ALGO").strip()
        self.env = str(credentials.get("env") or "sandbox").strip().lower()
        if self.env not in self._HOSTS:
            self.env = "sandbox"
        self.base_url = self._HOSTS[self.env]
        self._access_token: str | None = None
        self._refresh_token: str | None = None
        self._token_expires_at: float = 0.0
        self._client = httpx.Client(timeout=15.0)

        if not (self.broker_id and self.app_id and self.app_secret):
            raise BrokerError(
                "Settrade Open API needs broker_id, app_id and app_secret — "
                "get these from your broker's Open API developer portal, "
                "then paste them as JSON into the API Key field."
            )

    # ---- auth -----------------------------------------------------
    def _sign(self, params: str, timestamp: str) -> str:
        """
        HMAC-SHA256 signature, matching Settrade's official
        stt-openapi-signer-python: sign(api_key, api_secret, params).
        Message format: f"{api_key}{params}{timestamp}"
        """
        message = f"{self.app_id}{params}{timestamp}"
        return hmac.new(
            self.app_secret.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def login(self) -> bool:
        if self._access_token and time.time() < self._token_expires_at - 30:
            return True  # still valid, no need to re-login

        params = ""
        timestamp = str(int(time.time() * 1000))
        signature = self._sign(params, timestamp)
        url = f"{self.base_url}/api/oam/v1/{self.broker_id}/broker-apps/{self.app_code}/login"
        try:
            resp = self._client.post(
                url,
                json={
                    "apiKey": self.app_id,
                    "params": params,
                    "signature": signature,
                    "timestamp": timestamp,
                },
            )
        except httpx.HTTPError as e:
            raise BrokerError(f"เชื่อมต่อ Settrade Open API ไม่ได้: {e}") from e

        if resp.status_code != 200:
            raise BrokerError(
                f"Login ล้มเหลว ({resp.status_code}): {resp.text[:300]}"
            )
        data = resp.json()
        self._access_token = data.get("access_token")
        self._refresh_token = data.get("refresh_token")
        expires_in = float(data.get("expires_in") or 3600)
        self._token_expires_at = time.time() + expires_in
        return bool(self._access_token)

    def _headers(self) -> dict[str, str]:
        self.login()
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }

    # ---- read endpoints --------------------------------------------
    def get_portfolio(self, account_no: str) -> list[dict[str, Any]]:
        url = f"{self.base_url}/api/seq/v1/{self.broker_id}/accounts/{account_no}/portfolios"
        resp = self._client.get(url, headers=self._headers())
        if resp.status_code != 200:
            raise BrokerError(f"ดึงพอร์ตไม่สำเร็จ ({resp.status_code}): {resp.text[:300]}")
        data = resp.json()
        return data.get("portfolioList") or data.get("results") or []

    def get_orders(self, account_no: str) -> list[dict[str, Any]]:
        url = f"{self.base_url}/api/seq/v1/{self.broker_id}/accounts/{account_no}/orders"
        resp = self._client.get(url, headers=self._headers())
        if resp.status_code != 200:
            raise BrokerError(f"ดึงออเดอร์ไม่สำเร็จ ({resp.status_code}): {resp.text[:300]}")
        data = resp.json()
        return data.get("orders") or data.get("results") or []

    def get_quote(self, symbol: str) -> dict[str, Any]:
        url = f"{self.base_url}/api/seq/v1/{self.broker_id}/market/quote-symbols/{symbol.upper()}"
        resp = self._client.get(url, headers=self._headers())
        if resp.status_code != 200:
            raise BrokerError(f"ดึงราคาไม่สำเร็จ ({resp.status_code}): {resp.text[:300]}")
        return resp.json()

    # ---- write endpoints (real money — use with care) ---------------
    def place_order(
        self,
        account_no: str,
        symbol: str,
        side: str,
        volume: int,
        price: float | None,
        price_type: str = "LIMIT",
    ) -> OrderResult:
        side = side.upper()
        if side not in ("BUY", "SELL"):
            return OrderResult(ok=False, message=f"side ไม่ถูกต้อง: {side}")
        if volume <= 0:
            return OrderResult(ok=False, message="จำนวนหุ้นต้องมากกว่า 0")

        body = {
            "instrument": "EQUITY",
            "accountNo": account_no,
            "symbol": symbol.upper(),
            "side": side,
            "price": price if price_type == "LIMIT" else 0,
            "priceType": price_type,
            "volume": int(volume),
            "validity": "DAY",
        }
        url = f"{self.base_url}/api/seq/v1/{self.broker_id}/accounts/{account_no}/orders"
        try:
            resp = self._client.post(url, headers=self._headers(), json=body)
        except httpx.HTTPError as e:
            return OrderResult(ok=False, message=f"ส่งคำสั่งไม่สำเร็จ: {e}")

        if resp.status_code not in (200, 201):
            return OrderResult(
                ok=False,
                message=f"โบรกเกอร์ปฏิเสธคำสั่ง ({resp.status_code}): {resp.text[:300]}",
                raw={"status_code": resp.status_code, "body": resp.text[:1000]},
            )
        data = resp.json()
        return OrderResult(
            ok=True,
            broker_order_id=str(data.get("orderNo") or data.get("id") or ""),
            status=str(data.get("status") or "SENT"),
            message="ส่งคำสั่งสำเร็จ",
            raw=data,
        )

    def cancel_order(self, account_no: str, order_no: str) -> OrderResult:
        url = f"{self.base_url}/api/seq/v1/{self.broker_id}/accounts/{account_no}/orders/{order_no}"
        try:
            resp = self._client.delete(url, headers=self._headers())
        except httpx.HTTPError as e:
            return OrderResult(ok=False, message=f"ยกเลิกไม่สำเร็จ: {e}")
        if resp.status_code not in (200, 204):
            return OrderResult(
                ok=False,
                message=f"ยกเลิกไม่สำเร็จ ({resp.status_code}): {resp.text[:300]}",
            )
        return OrderResult(ok=True, status="CANCELLED", message="ยกเลิกคำสั่งสำเร็จ")


# ---------------------------------------------------------------------
# Registry — add new broker adapters here as they're built.
# ---------------------------------------------------------------------
_ADAPTERS: dict[str, type[BrokerAdapter]] = {
    "settrade_open_api": SettradeOpenAPIAdapter,
    "bualuang": SettradeOpenAPIAdapter,   # Bualuang runs on Settrade Open API
    "settrade": SettradeOpenAPIAdapter,
    # Add other brokers here, e.g.:
    # "my_other_broker": MyOtherBrokerAdapter,
}


def parse_stored_credentials(raw: str) -> dict[str, Any]:
    """
    The voice widget's "API Key / Token" field is a single text box.
    For broker adapters we need several fields (broker_id, app_id,
    app_secret, ...), so that field should contain a small JSON object.
    Falls back to treating the whole string as a single api_key if it
    isn't valid JSON (keeps backward compatibility with the old
    single-token flow).
    """
    raw = (raw or "").strip()
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {"api_key": raw}
    except Exception:
        return {"api_key": raw}


def get_adapter(broker_name: str, raw_credentials: str) -> BrokerAdapter:
    """
    Look up and instantiate the right adapter for `broker_name`
    (case/space-insensitive), using credentials parsed from the stored
    API-key text.
    """
    key = (broker_name or "").strip().lower().replace(" ", "_")
    cls = _ADAPTERS.get(key)
    if cls is None:
        # Unknown broker name — default to Settrade Open API, since
        # that's the shared infra most Thai brokers run on. If this
        # broker uses something else entirely, register a dedicated
        # adapter class above instead of relying on this fallback.
        cls = SettradeOpenAPIAdapter
    creds = parse_stored_credentials(raw_credentials)
    return cls(creds)
