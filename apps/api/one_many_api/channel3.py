"""Channel3 HTTP adapter. All prices and offers are actual provider response data.

See https://docs.trychannel3.com/api-reference. No scraping and no demo fallback.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any
from urllib.parse import quote, urlsplit

import httpx
from pydantic import BaseModel, Field

from one_many_api.config import Settings
from one_many_api.matching import feature_key

logger = logging.getLogger("one_many_api")

# Explicitly supported currencies for price display and allocation. No FX conversion.
CURRENCY_DECIMALS = {"USD": 2, "INR": 2, "EUR": 2, "GBP": 2, "CAD": 2, "AUD": 2, "JPY": 0}
CURRENCY_SYMBOLS = {
    "USD": "$",
    "INR": "₹",
    "EUR": "€",
    "GBP": "£",
    "CAD": "CA$",
    "AUD": "A$",
    "JPY": "¥",
}
CHANNEL3_URL = "https://api.trychannel3.com"


class CatalogUnavailable(Exception):
    """Credentials, network, or provider failure; never synthesize catalog data."""


class CatalogMalformed(Exception):
    """Unexpected product/detail response; do not charge or make a quote."""


class CatalogOffer(BaseModel):
    domain: str
    url: str
    availability: str
    currency: str
    price_minor: int = Field(ge=1)
    price_display: str


class CatalogProduct(BaseModel):
    id: str
    title: str
    brand: str | None
    description: str | None
    image_url: str | None
    key_features: list[str]
    attributes: dict[str, list[str]]
    offers: list[CatalogOffer]
    required_features_unverified: list[str]
    excluded_features_detected: list[str]
    suitability: str
    checked_at: datetime


class ProductResults(BaseModel):
    provider: str = "Channel3"
    query: str
    country: str
    currency: str
    checked_at: datetime
    products: list[CatalogProduct]
    next_page_available: bool
    notice: str = (
        "Catalog results are suggestions, not proof of local delivery, product suitability, "
        "or stock. Merchant details and shipping/taxes require confirmation."
    )


def _valid_web_url(value: Any) -> str | None:
    if not isinstance(value, str) or len(value) > 2048:
        return None
    url = urlsplit(value)
    if url.scheme != "https" or not url.hostname or url.username or url.password:
        return None
    return value


def price_to_minor(value: Any, currency: str) -> int:
    """Convert exactly to integer minor units, rejecting ambiguous/rounded prices."""
    decimals = CURRENCY_DECIMALS.get(currency)
    if decimals is None or isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise ValueError("Unsupported currency or price type")
    try:
        price = Decimal(str(value))
        if not price.is_finite() or price <= 0 or price > Decimal("1000000"):
            raise ValueError("Invalid amount")
        scaled = price * (Decimal(10) ** decimals)
        if scaled != scaled.to_integral_value():
            raise ValueError("Price has too many fractional digits")
        return int(scaled)
    except (InvalidOperation, OverflowError):
        raise ValueError("Invalid monetary value") from None


def minor_to_display(minor: int, currency: str) -> str:
    digits = CURRENCY_DECIMALS[currency]
    amount = Decimal(minor) / (Decimal(10) ** digits)
    return f"{CURRENCY_SYMBOLS.get(currency, currency + ' ')}{amount:,.{digits}f}"


def _plain_labels(value: Any, limit: int = 40) -> list[str]:
    if not isinstance(value, list):
        return []
    return [x.strip() for x in value[:limit] if isinstance(x, str) and x.strip()][:limit]


def normalize_product(
    raw: Any,
    currency: str,
    required_features: list[str],
    excluded_features: list[str],
    checked_at: datetime | None = None,
) -> CatalogProduct:
    if not isinstance(raw, dict):
        raise CatalogMalformed("Product is not an object")
    product_id, title = raw.get("id"), raw.get("title")
    if not isinstance(product_id, str) or not product_id.strip() or len(product_id) > 250:
        raise CatalogMalformed("Missing product ID")
    if not isinstance(title, str) or not title.strip() or len(title) > 500:
        raise CatalogMalformed("Missing product title")
    brands = raw.get("brands")
    brand = next(
        (
            b.get("name")
            for b in (brands if isinstance(brands, list) else [])
            if isinstance(b, dict) and isinstance(b.get("name"), str)
        ),
        None,
    )
    description = raw.get("description")
    description = description[:3000] if isinstance(description, str) else None
    images = raw.get("images")
    image_url = None
    if isinstance(images, list):
        for img in images[:15]:
            if isinstance(img, dict):
                image_url = _valid_web_url(img.get("cleaned_url")) or _valid_web_url(img.get("url"))
                if image_url:
                    break
    features = _plain_labels(raw.get("key_features"))
    structured = raw.get("structured_attributes")
    attributes: dict[str, list[str]] = {}
    if isinstance(structured, dict):
        for k, v in list(structured.items())[:40]:
            if isinstance(k, str) and isinstance(v, list):
                attributes[k[:80]] = _plain_labels(v, 20)
    offers: list[CatalogOffer] = []
    for item in (raw.get("offers") if isinstance(raw.get("offers"), list) else [])[:50]:
        if not isinstance(item, dict):
            continue
        offer_url = _valid_web_url(item.get("url"))
        price_obj = item.get("price")
        if offer_url is None or not isinstance(price_obj, dict):
            continue
        offer_currency = price_obj.get("currency")
        if offer_currency != currency:
            continue
        if item.get("availability") != "InStock":
            continue
        try:
            minor = price_to_minor(price_obj.get("price"), currency)
        except ValueError:
            continue
        domain = urlsplit(offer_url).hostname
        if not domain:
            continue
        offers.append(
            CatalogOffer(
                domain=domain,
                url=offer_url,
                availability="InStock",
                currency=currency,
                price_minor=minor,
                price_display=minor_to_display(minor, currency),
            )
        )
    offers.sort(key=lambda offer: (offer.price_minor, offer.domain, offer.url))
    evidence = " ".join(
        [
            title,
            description or "",
            *features,
            *(f"{key} {value}" for key, values in attributes.items() for value in values),
        ]
    )
    # Deliberately exact normalized phrase checks. No claim that text proves performance.
    evidence_key = f" {feature_key(evidence)} "
    missing = [f for f in required_features if f" {feature_key(f)} " not in evidence_key]
    excluded = [f for f in excluded_features if f" {feature_key(f)} " in evidence_key]
    suitability = (
        "blocked" if excluded else "manual_review" if missing or not offers else "candidate"
    )
    return CatalogProduct(
        id=product_id,
        title=title.strip(),
        brand=brand,
        description=description,
        image_url=image_url,
        key_features=features,
        attributes=attributes,
        offers=offers,
        required_features_unverified=missing,
        excluded_features_detected=excluded,
        suitability=suitability,
        checked_at=checked_at or datetime.now(UTC),
    )


class Channel3Client:
    def __init__(self, settings: Settings):
        self.settings = settings

    def _fetch(self, method: str, path: str, *, payload: dict | None = None) -> dict:
        secret = self.settings.channel3_api_key
        if secret is None:
            raise CatalogUnavailable("Channel3 API key is not configured")
        try:
            response = httpx.request(
                method,
                CHANNEL3_URL + path,
                headers={
                    "x-api-key": secret.get_secret_value(),
                    "Accept": "application/json",
                },
                json=payload,
                timeout=httpx.Timeout(self.settings.channel3_timeout_seconds, connect=3.0),
                follow_redirects=False,
            )
            if response.status_code in (401, 403):
                raise CatalogUnavailable("Channel3 credentials were rejected")
            if response.status_code == 429:
                raise CatalogUnavailable("Channel3 rate limit was reached")
            response.raise_for_status()
            content = response.json()
            if not isinstance(content, dict):
                raise CatalogMalformed("Channel3 returned an unexpected JSON type")
            return content
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("channel3_failure", extra={"error_type": type(exc).__name__})
            raise CatalogUnavailable("Channel3 is unavailable; please retry later") from None

    def search(self, asset: str, required: list[str], excluded: list[str]) -> ProductResults:
        query = " ".join([asset, *required]).strip()[:500]
        data = self._fetch(
            "POST",
            "/v1/search",
            payload={
                "query": query,
                "limit": 12,
                "config": {
                    "mode": "default",
                    "country": self.settings.channel3_country,
                    "currency": self.settings.channel3_currency,
                },
            },
        )
        rows = data.get("products")
        if not isinstance(rows, list):
            raise CatalogMalformed("Channel3 search response has no products list")
        checked = datetime.now(UTC)
        products = []
        for product in rows:
            try:
                normalized = normalize_product(
                    product, self.settings.channel3_currency, required, excluded, checked
                )
            except CatalogMalformed:
                continue
            if normalized.offers:
                products.append(normalized)
        return ProductResults(
            query=query,
            country=self.settings.channel3_country,
            currency=self.settings.channel3_currency,
            checked_at=checked,
            products=products,
            next_page_available=bool(data.get("next_page_token")),
        )

    def product(self, product_id: str, required: list[str], excluded: list[str]) -> CatalogProduct:
        # Product ID is not a URL. Quote it so user input cannot change the API path.
        if not product_id.strip() or len(product_id) > 250:
            raise CatalogMalformed("Invalid product ID")
        safe_id = quote(product_id, safe="")
        result = self._fetch(
            "GET",
            f"/v1/products/{safe_id}",
        )
        product = normalize_product(result, self.settings.channel3_currency, required, excluded)
        if product.id != product_id:
            raise CatalogMalformed("Channel3 returned a different product")
        return product
