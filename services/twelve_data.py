"""
Client helper for Twelve Data REST API.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Dict, Optional

import requests

logger = logging.getLogger("TwelveDataClient")


@dataclass
class TwelveDataConfig:
    api_key: Optional[str]
    base_url: str = "https://api.twelvedata.com"
    timeout: int = 15


class TwelveDataClient:
    """
    Minimal client for Twelve Data quote endpoint.
    """

    def __init__(self, api_key: Optional[str] = None):
        key = api_key or os.getenv("TWELVEDATA_API_KEY") or os.getenv("TWELVE_DATA_API_KEY")
        if key:
            key = key.strip()
        self.config = TwelveDataConfig(api_key=key)
        self.session = requests.Session()

    @property
    def enabled(self) -> bool:
        return bool(self.config.api_key)

    def get_quote(self, symbol: str) -> Optional[Dict[str, str]]:
        if not self.enabled:
            return None
        params = {
            "symbol": symbol.upper(),
            "apikey": self.config.api_key,
        }
        url = f"{self.config.base_url}/quote"
        try:
            response = self.session.get(url, params=params, timeout=self.config.timeout)
        except requests.RequestException as exc:  # pragma: no cover - network
            logger.warning("Twelve Data request failed: %s", exc)
            return None

        if response.status_code != 200:
            logger.warning("Twelve Data returned status %s for %s", response.status_code, symbol)
            return None

        try:
            payload = response.json()
        except ValueError:
            logger.warning("Twelve Data invalid JSON for %s", symbol)
            return None

        if isinstance(payload, dict) and payload.get("status") == "error":
            logger.warning("Twelve Data error for %s: %s", symbol, payload.get("message"))
            return None

        return payload if isinstance(payload, dict) else None

