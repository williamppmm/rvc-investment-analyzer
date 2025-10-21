"""
Lightweight client for Alpha Vantage REST API.
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from typing import Dict, Optional

import requests

logger = logging.getLogger("AlphaVantageClient")


@dataclass
class AlphaVantageConfig:
    api_key: Optional[str]
    base_url: str = "https://www.alphavantage.co/query"
    timeout: int = 15
    min_interval: float = 12.5  # Respect free tier (≈5 requests/min)


class AlphaVantageClient:
    """
    Minimal Alpha Vantage client with basic throttling and FX caching.
    """

    def __init__(self, api_key: Optional[str] = None):
        key = api_key or os.getenv("ALPHAVANTAGE_API_KEY") or os.getenv("ALPHA_VANTAGE_KEY")
        if key:
            key = key.strip()
        self.config = AlphaVantageConfig(api_key=key)
        self.session = requests.Session()
        self._last_request: float = 0.0
        self._fx_cache: Dict[str, Dict[str, float]] = {}

    @property
    def enabled(self) -> bool:
        return bool(self.config.api_key)

    # -------------------------------
    # Public API helpers
    # -------------------------------

    def get_overview(self, symbol: str) -> Optional[Dict[str, str]]:
        return self._get(function="OVERVIEW", symbol=symbol.upper())

    def get_global_quote(self, symbol: str) -> Optional[Dict[str, str]]:
        data = self._get(function="GLOBAL_QUOTE", symbol=symbol.upper())
        if not data:
            return None
        return data.get("Global Quote") if isinstance(data, dict) else None

    def get_exchange_rate(self, from_currency: str, to_currency: str) -> Optional[float]:
        """
        Returns the latest exchange rate from Alpha Vantage (from_currency -> to_currency).
        Result is cached per currency pair.
        """
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()
        cache_key = f"{from_currency}->{to_currency}"
        cached = self._fx_cache.get(cache_key)
        if cached and time.time() - cached["ts"] < 60 * 60:  # 1 hour cache
            return cached["rate"]

        payload = self._get(
            function="CURRENCY_EXCHANGE_RATE",
            from_currency=from_currency,
            to_currency=to_currency,
        )
        if not payload:
            return None

        rate_str = payload.get("Realtime Currency Exchange Rate", {}).get("5. Exchange Rate")
        if not rate_str:
            return None
        try:
            rate = float(rate_str)
        except (TypeError, ValueError):
            logger.warning("Exchange rate parsing failed for %s", cache_key)
            return None

        self._fx_cache[cache_key] = {"rate": rate, "ts": time.time()}
        return rate

    # -------------------------------
    # Internal helpers
    # -------------------------------

    def _get(self, **params) -> Optional[Dict[str, str]]:
        if not self.enabled:
            return None

        now = time.time()
        elapsed = now - self._last_request
        if elapsed < self.config.min_interval:
            time.sleep(self.config.min_interval - elapsed)

        params["apikey"] = self.config.api_key

        try:
            response = self.session.get(
                self.config.base_url,
                params=params,
                timeout=self.config.timeout,
            )
        except requests.RequestException as exc:  # pragma: no cover - network
            logger.warning("Alpha Vantage request failed: %s", exc)
            return None
        finally:
            self._last_request = time.time()

        if response.status_code != 200:
            logger.warning("Alpha Vantage returned status %s for %s", response.status_code, params)
            return None

        try:
            payload = response.json()
        except ValueError:
            logger.warning("Alpha Vantage invalid JSON for %s", params)
            return None

        if "Note" in payload or "Information" in payload:
            logger.warning("Alpha Vantage notice: %s", payload.get("Note") or payload.get("Information"))
            return None

        if not payload:
            return None
        return payload
