"""ETF specific metrics and scoring."""

from __future__ import annotations

from typing import Dict, Any


class ETFAnalyzer:
    """Provide portfolio metrics for ETFs."""

    def analyze(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        nav = metrics.get("nav") or metrics.get("current_price")
        price = metrics.get("current_price")
        premium = self._calculate_premium(price, nav)

        summary = {
            "ticker": metrics.get("ticker"),
            "fund_name": metrics.get("company_name"),
            "asset_type": "ETF",
            "current_price": price,
            "nav": nav,
            "premium_discount": premium,
            "expense_ratio": metrics.get("expense_ratio"),
            "ytd_return": metrics.get("ytd_return"),
            "category": metrics.get("category"),
            "provider": metrics.get("provider"),
            "volume": metrics.get("volume"),
            "assets_under_management": metrics.get("assets_under_management"),
            "dividend_yield": metrics.get("dividend_yield"),
            "holdings_count": metrics.get("holdings_count"),
            "index": metrics.get("index_tracked"),
        }
        score = self.score(summary)
        summary["score"] = score
        return summary

    def score(self, summary: Dict[str, Any]) -> Dict[str, Any]:
        score = 0
        max_score = 0

        expense = summary.get("expense_ratio")
        if expense is not None:
            expense_value = expense
            if expense_value > 0.01:
                expense_value = expense_value / 100
            max_score += 30
            if expense_value < 0.001:
                score += 30
            elif expense_value < 0.0025:
                score += 25
            elif expense_value < 0.005:
                score += 18
            elif expense_value < 0.0075:
                score += 12
            else:
                score += 6

        ytd_return = summary.get("ytd_return")
        if ytd_return is not None:
            ytd_value = ytd_return / 100 if ytd_return > 1 else ytd_return
            max_score += 40
            if ytd_value > 0.20:
                score += 40
            elif ytd_value > 0.10:
                score += 34
            elif ytd_value > 0.05:
                score += 26
            elif ytd_value > 0:
                score += 18
            else:
                score += 8

        premium = summary.get("premium_discount")
        if premium is not None:
            max_score += 20
            if abs(premium) < 0.3:
                score += 20
            elif abs(premium) < 0.75:
                score += 14
            else:
                score += 8

        nav = summary.get("nav")
        if nav:
            max_score += 10
            score += 10

        aum = summary.get("assets_under_management")
        if aum:
            max_score += 10
            if aum >= 100_000_000_000:
                score += 10
            elif aum >= 10_000_000_000:
                score += 8
            elif aum >= 1_000_000_000:
                score += 6
            else:
                score += 3

        final = round((score / max_score) * 100, 1) if max_score else None
        label = self._label(final)
        return {"total_score": final, "label": label}

    def _calculate_premium(self, price, nav) -> float | None:
        if price and nav and nav > 0:
            return ((price - nav) / nav) * 100
        return None

    def _label(self, final: float | None) -> str:
        if final is None:
            return "Sin puntaje"
        if final >= 80:
            return "🟢 Excelente"
        if final >= 65:
            return "🟡 Bueno"
        if final >= 50:
            return "🟠 Aceptable"
        return "🔴 Revisar"
