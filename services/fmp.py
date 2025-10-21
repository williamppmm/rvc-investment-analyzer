"""
Client helper for Financial Modeling Prep API.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Dict, List, Optional

import requests

logger = logging.getLogger("FMPClient")


@dataclass
class FMPConfig:
    api_key: Optional[str]
    base_url: str = "https://financialmodelingprep.com/api/v3"
    timeout: int = 15


class FMPClient:
    """
    Minimal client for FMP endpoints used in the project.
    """

    def __init__(self, api_key: Optional[str] = None):
        key = api_key or os.getenv("FMP_API_KEY")
        if key:
            key = key.strip()
        self.config = FMPConfig(api_key=key)
        self.session = requests.Session()

    @property
    def enabled(self) -> bool:
        return bool(self.config.api_key)

    # -------------------------------
    # Public API helpers
    # -------------------------------

    def get_profile(self, symbol: str) -> Optional[Dict[str, str]]:
        data = self._get(f"profile/{symbol.upper()}")
        return data[0] if isinstance(data, list) and data else None

    def get_quote(self, symbol: str) -> Optional[Dict[str, str]]:
        data = self._get(f"quote/{symbol.upper()}")
        return data[0] if isinstance(data, list) and data else None

    def get_ratios(self, symbol: str) -> Optional[Dict[str, str]]:
        data = self._get(f"ratios-ttm/{symbol.upper()}")
        return data[0] if isinstance(data, list) and data else None

    def get_key_metrics(self, symbol: str) -> Optional[Dict[str, str]]:
        data = self._get(f"key-metrics-ttm/{symbol.upper()}")
        return data[0] if isinstance(data, list) and data else None

    # -------------------------------
    # Internal helpers
    # -------------------------------

    def _get(self, path: str) -> Optional[List[Dict[str, str]]]:
        if not self.enabled:
            return None
        url = f"{self.config.base_url}/{path}"
        params = {"apikey": self.config.api_key}
        try:
            response = self.session.get(url, params=params, timeout=self.config.timeout)
        except requests.RequestException as exc:  # pragma: no cover - network
            logger.warning("FMP request failed: %s", exc)
            return None

        if response.status_code != 200:
            logger.warning("FMP returned status %s for %s", response.status_code, path)
            return None

        try:
            payload = response.json()
        except ValueError:
            logger.warning("FMP invalid JSON for %s", path)
            return None

        if isinstance(payload, dict) and payload.get("Error Message"):
            logger.warning("FMP error for %s: %s", path, payload["Error Message"])
            return None

        return payload

