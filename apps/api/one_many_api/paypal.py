"""PayPal Sandbox Orders v2 adapter. No live mode, no implicit browser-trusted capture.

PayPal docs: https://developer.paypal.com/api/orders/v2/ and
https://developer.paypal.com/api/rest/webhooks/
"""
from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any
from urllib.parse import urlsplit

import httpx

from one_many_api.channel3 import CURRENCY_DECIMALS, price_to_minor
from one_many_api.config import Settings

logger = logging.getLogger("one_many_api")
SANDBOX_API = "https://api-m.sandbox.paypal.com"
# This explicit allowlist excludes INR: Orders v2 does not offer it as a supported payment currency.
PAYPAL_CURRENCIES = frozenset({"USD", "EUR", "GBP", "CAD", "AUD", "JPY"})


class PayPalUnavailable(Exception):
    """Provider failure or missing sandbox credentials. Never fabricate payment success."""


class PayPalInvalid(Exception):
    """Unexpected, mismatched or potentially unsafe PayPal resource."""


def amount_string(amount_minor: int, currency: str) -> str:
    if currency not in PAYPAL_CURRENCIES or amount_minor <= 0:
        raise PayPalInvalid("Currency or amount unsupported by PayPal Sandbox")
    places = CURRENCY_DECIMALS[currency]
    return f"{Decimal(amount_minor) / (10 ** places):.{places}f}"


def approval_link(order: dict) -> str:
    links = order.get("links")
    if not isinstance(links, list):
        raise PayPalInvalid("PayPal order contains no approval links")
    for link in links:
        if not isinstance(link, dict) or link.get("rel") not in ("approve", "payer-action"):
            continue
        url = link.get("href")
        if not isinstance(url, str):
            continue
        parsed = urlsplit(url)
        if parsed.scheme == "https" and parsed.hostname == "www.sandbox.paypal.com":
            return url
    raise PayPalInvalid("PayPal did not return a trusted Sandbox approval URL")


def verify_order(
    order: Any,
    *,
    order_id: str,
    reference_id: str,
    custom_id: str,
    amount_minor: int,
    currency: str,
    merchant_id: str | None = None,
) -> tuple[str, str | None]:
    """Return (approval/payment status, verified capture ID if COMPLETED).

    A reported COMPLETED order alone is insufficient: independently check
    purchase-unit IDs, expected amount/currency, a single capture and capture status.
    """
    if not isinstance(order, dict) or order.get("id") != order_id:
        raise PayPalInvalid("PayPal returned a different order")
    units = order.get("purchase_units")
    if not isinstance(units, list) or len(units) != 1 or not isinstance(units[0], dict):
        raise PayPalInvalid("PayPal returned an unexpected purchase-unit count")
    unit = units[0]
    if unit.get("reference_id") != reference_id or unit.get("custom_id") != custom_id:
        raise PayPalInvalid("PayPal order reference mismatch")
    if merchant_id:
        payee = unit.get("payee")
        if not isinstance(payee, dict) or payee.get("merchant_id") != merchant_id:
            raise PayPalInvalid("PayPal payee mismatch")
    amount = unit.get("amount")
    if not isinstance(amount, dict) or amount.get("currency_code") != currency:
        raise PayPalInvalid("PayPal order currency mismatch")
    try:
        if price_to_minor(amount.get("value"), currency) != amount_minor:
            raise PayPalInvalid("PayPal order amount mismatch")
    except ValueError:
        raise PayPalInvalid("PayPal order amount is invalid") from None

    state = order.get("status")
    if state in ("CREATED", "PAYER_ACTION_REQUIRED", "SAVED", "APPROVED"):
        return state, None
    if state != "COMPLETED":
        raise PayPalInvalid("PayPal order status is not valid for capture")
    payments = unit.get("payments")
    captures = payments.get("captures") if isinstance(payments, dict) else None
    if not isinstance(captures, list) or len(captures) != 1:
        raise PayPalInvalid("PayPal did not return exactly one capture")
    capture = captures[0]
    if not isinstance(capture, dict):
        raise PayPalInvalid("Invalid capture")
    cap_amount = capture.get("amount")
    if not isinstance(cap_amount, dict) or cap_amount.get("currency_code") != currency:
        raise PayPalInvalid("Capture currency mismatch")
    try:
        if price_to_minor(cap_amount.get("value"), currency) != amount_minor:
            raise PayPalInvalid("Capture amount mismatch")
    except ValueError:
        raise PayPalInvalid("Capture amount is invalid") from None
    if capture.get("status") == "PENDING":
        return "PENDING", None
    if capture.get("status") != "COMPLETED":
        raise PayPalInvalid("Capture is not completed")
    capture_id = capture.get("id")
    if not isinstance(capture_id, str) or not capture_id:
        raise PayPalInvalid("Completed capture has no PayPal ID")
    return "COMPLETED", capture_id


class PayPalSandboxClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    def _token(self) -> str:
        if self.settings.paypal_client_id is None or self.settings.paypal_client_secret is None:
            raise PayPalUnavailable("PayPal Sandbox credentials are not configured")
        try:
            response = httpx.post(
                SANDBOX_API + "/v1/oauth2/token",
                data={"grant_type": "client_credentials"},
                auth=httpx.BasicAuth(
                    self.settings.paypal_client_id.get_secret_value(),
                    self.settings.paypal_client_secret.get_secret_value(),
                ),
                headers={"Accept": "application/json"},
                timeout=httpx.Timeout(self.settings.paypal_timeout_seconds, connect=3),
                follow_redirects=False,
            )
            response.raise_for_status()
            token = response.json().get("access_token")
            if not isinstance(token, str) or not token:
                raise PayPalInvalid("PayPal access token is missing")
            return token
        except (httpx.HTTPError, ValueError, TypeError):
            logger.warning("paypal_token_failure")
            raise PayPalUnavailable("PayPal Sandbox token request failed") from None

    def _call(
        self, method: str, path: str, *, payload: dict | None = None, request_id: str | None = None
    ) -> dict:
        token = self._token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }
        if request_id is not None:
            headers["PayPal-Request-Id"] = request_id
        try:
            response = httpx.request(
                method,
                SANDBOX_API + path,
                headers=headers,
                json=payload,
                timeout=httpx.Timeout(self.settings.paypal_timeout_seconds, connect=3),
                follow_redirects=False,
            )
            response.raise_for_status()
            if not response.content:
                return {}
            result = response.json()
            if not isinstance(result, dict):
                raise PayPalInvalid("Unexpected PayPal response format")
            return result
        except (httpx.HTTPError, ValueError, TypeError):
            logger.warning("paypal_api_failure", extra={"operation": method})
            raise PayPalUnavailable("PayPal Sandbox request failed or requires reconciliation") from None

    def create_order(
        self, *, group_id: str, attempt_id: str, amount_minor: int, currency: str,
        description: str, request_id: str
    ) -> tuple[str, str]:
        origin = self.settings.public_web_url.rstrip("/")
        ret = f"{origin}/app?paypal_group={group_id}"
        cancel = f"{origin}/app?paypal_cancel={group_id}"
        result = self._call(
            "POST", "/v2/checkout/orders",
            request_id=request_id,
            payload={
                "intent": "CAPTURE",
                "purchase_units": [{
                    "reference_id": group_id,
                    "custom_id": attempt_id,
                    "description": f"ONE/MANY sandbox shared-item contribution: {description}"[:127],
                    "amount": {"currency_code": currency, "value": amount_string(amount_minor, currency)},
                }],
                "payment_source": {
                    "paypal": {
                        "experience_context": {
                            "return_url": ret,
                            "cancel_url": cancel,
                            "shipping_preference": "NO_SHIPPING",
                            "user_action": "PAY_NOW",
                        }
                    }
                },
            },
        )
        oid = result.get("id")
        if not isinstance(oid, str) or not (8 <= len(oid) <= 100):
            raise PayPalInvalid("PayPal did not return a valid order ID")
        return oid, approval_link(result)

    def get_order(self, order_id: str) -> dict:
        if not order_id.isalnum() or len(order_id) > 100:
            raise PayPalInvalid("Invalid PayPal order ID")
        return self._call("GET", f"/v2/checkout/orders/{order_id}")

    def capture(self, order_id: str, request_id: str) -> dict:
        if not order_id.isalnum() or len(order_id) > 100:
            raise PayPalInvalid("Invalid PayPal order ID")
        return self._call(
            "POST", f"/v2/checkout/orders/{order_id}/capture",
            payload={}, request_id=request_id
        )

    def verify_webhook(self, headers: Any, event: dict) -> bool:
        webhook = self.settings.paypal_webhook_id
        if webhook is None:
            raise PayPalUnavailable("PayPal webhook ID not configured")
        fields = {
            "transmission_id": headers.get("paypal-transmission-id"),
            "transmission_time": headers.get("paypal-transmission-time"),
            "cert_url": headers.get("paypal-cert-url"),
            "auth_algo": headers.get("paypal-auth-algo"),
            "transmission_sig": headers.get("paypal-transmission-sig"),
            "webhook_id": webhook.get_secret_value(),
            "webhook_event": event,
        }
        if any(not value for value in fields.values()):
            return False
        result = self._call("POST", "/v1/notifications/verify-webhook-signature", payload=fields)
        return result.get("verification_status") == "SUCCESS"
