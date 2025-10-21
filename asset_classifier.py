"""Simple heuristics to classify asset types using available metadata."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class AssetClassification:
    ticker: str
    asset_type: str
    raw_type: Optional[str]
    type_label: str
    is_analyzable: bool
    needs_special_metrics: bool
    source: str


class AssetClassifier:
    """Classify tickers into broad asset classes using heuristics."""

    ASSET_NAMES: Dict[str, str] = {
        "EQUITY": "Acción",
        "ETF": "ETF",
        "REIT": "REIT",
        "BOND": "Bono",
        "MUTUALFUND": "Fondo mutuo",
        "INDEX": "Índice",
        "CURRENCY": "Divisa",
        "CRYPTO": "Criptomoneda",
        "COMMODITY": "Commodity",
        "UNKNOWN": "Desconocido",
    }

    ANALYZABLE = {"EQUITY"}
    SPECIAL_METRICS = {"ETF", "REIT", "BOND", "MUTUALFUND"}

    MANUAL_OVERRIDES = {
        "IAU": "ETF",
        "VOO": "ETF",
        "VNQ": "ETF",
        "SPY": "ETF",
        "QQQ": "ETF",
        "DJI": "INDEX",
        "DJIA": "INDEX",
        "^DJI": "INDEX",
        "DIA": "ETF",
        "GLD": "ETF",
        "ADA": "CRYPTO",
    }

    def classify(self, metadata: Dict[str, str]) -> AssetClassification:
        ticker = (metadata.get("ticker", "?") or "?").upper()
        raw_type = (metadata.get("quoteType") or metadata.get("type") or "").upper() or None
        long_name = (metadata.get("company_name") or metadata.get("longName") or "").upper()
        category = (metadata.get("category") or metadata.get("sector") or "").upper()

        if ticker in self.MANUAL_OVERRIDES:
            asset_type = self.MANUAL_OVERRIDES[ticker]
        else:
            asset_type = self._refine(raw_type, long_name, category)
        type_label = self.ASSET_NAMES.get(asset_type, asset_type)
        is_analyzable = asset_type in self.ANALYZABLE
        needs_special = asset_type in self.SPECIAL_METRICS

        return AssetClassification(
            ticker=ticker,
            asset_type=asset_type,
            raw_type=raw_type,
            type_label=type_label,
            is_analyzable=is_analyzable,
            needs_special_metrics=needs_special,
            source=metadata.get("primary_source", "unknown"),
        )

    def _refine(self, raw_type: Optional[str], name: str, category: str) -> str:
        if not raw_type:
            raw_type = "UNKNOWN"

        if "ETF" in name:
            return "ETF"

        if raw_type == "EQUITY":
            if "REIT" in name or "REIT" in category:
                return "REIT"
        if raw_type == "ETF":
            if any(word in category for word in ["BOND", "FIXED INCOME"]):
                return "BOND"
            if "ETF" in name:
                return "ETF"
            if any(word in name for word in ["GOLD", "SILVER", "OIL", "COMMODITY"]):
                return "ETF"
        if raw_type == "MUTUALFUND":
            return "MUTUALFUND"
        if raw_type == "INDEX":
            return "INDEX"
        if raw_type == "CURRENCY":
            return "CURRENCY"
        if raw_type == "CRYPTOCURRENCY":
            return "CRYPTO"
        return raw_type
