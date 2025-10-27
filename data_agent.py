"""
DataAgent responsible for gathering financial metrics through web scraping and fallbacks.
"""

from __future__ import annotations

import json
import logging
import re
import time
from copy import deepcopy
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup

from services import AlphaVantageClient, FMPClient, TwelveDataClient
from etf_reference import ETF_REFERENCE
from asset_classifier import AssetClassifier, AssetClassification

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
METRIC_SCHEMA_VERSION = 3
logger = logging.getLogger("DataAgent")
logger.setLevel(logging.INFO)


@dataclass
class SourceResult:
    data: Dict[str, float]
    source: str
    coverage: int = 0


class DataAgent:
    """
    Aggregator that fetches public metrics from multiple sources (Yahoo, Finviz,
    MarketWatch) with fallbacks and provenance tracking.
    """

    MANUAL_EDITABLE_FIELDS: Dict[str, str] = {
        "current_price": "number",
        "market_cap": "number",
        "pe_ratio": "number",
        "peg_ratio": "number",
        "price_to_book": "number",
        "price_to_sales": "number",
        "ev_to_ebitda": "number",
        "roe": "percent",
        "roic": "percent",
        "roa": "percent",
        "gross_margin": "percent",
        "operating_margin": "percent",
        "net_margin": "percent",
        "debt_to_equity": "number",
        "current_ratio": "number",
        "quick_ratio": "number",
        "revenue_growth": "percent",
        "revenue_growth_qoq": "percent",
        "revenue_growth_5y": "percent",
        "earnings_growth": "percent",
        "earnings_growth_this_y": "percent",
        "earnings_growth_next_y": "percent",
        "earnings_growth_next_5y": "percent",
        "earnings_growth_qoq": "percent",
        # Mejora #6: Métricas de salud financiera avanzada
        "net_debt_to_ebitda": "number",
        "interest_coverage": "number",
        "total_debt": "number",
        "cash_and_equivalents": "number",
        "ebitda": "number",
        "interest_expense": "number",
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
                ),
                "Accept-Language": "es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7",
                "Cache-Control": "no-cache",
            }
        )
        self.provenance: Dict[str, str] = {}
        self.metric_aliases = {
            "current_price": {"Price", "Current Price"},
            "market_cap": {"Market Cap", "Market Capitalization"},
            "pe_ratio": {"P/E", "PE Ratio (TTM)", "Trailing P/E", "P/E TTM"},
            "forward_pe": {"Forward P/E"},
            "peg_ratio": {"PEG", "PEG ratio", "PEG Ratio"},
            "price_to_book": {"P/B", "Price/Book"},
            "price_to_sales": {"P/S"},
            "ev_to_ebitda": {"EV/EBITDA"},
            "roe": {"ROE", "Return on Equity"},
            "roic": {"ROI", "ROIC", "Return on Invested Capital"},
            "roa": {"ROA", "Return on Assets"},
            "operating_margin": {"Operating Margin", "Oper. Margin"},
            "net_margin": {"Profit Margin", "Net Profit Margin", "Net Margin"},
            "gross_margin": {"Gross Margin"},
            "debt_to_equity": {"Debt/Eq", "Debt to Equity"},
            "current_ratio": {"Current Ratio"},
            "quick_ratio": {"Quick Ratio"},
            "eps_ttm": {"EPS (ttm)"},
            "revenue_growth": {
                "Revenue Growth",
                "Sales growth TTM",
                "Quarterly Revenue Growth (yoy)",
            },
            "revenue_growth_qoq": {"Sales Q/Q"},
            "revenue_growth_5y": {"Sales past 5Y"},
            "earnings_growth": {"EPS growth TTM"},
            "earnings_growth_this_y": {"EPS this Y"},
            "earnings_growth_next_y": {"EPS next Y"},
            "earnings_growth_next_5y": {"EPS next 5Y"},
            "earnings_growth_qoq": {"EPS Q/Q"},
            # Mejora #3: Métricas de valoración basadas en caja
            "ev_to_ebit": {"EV/EBIT"},
            "fcf_yield": {"FCF Yield", "Free Cash Flow Yield"},
            "enterprise_value": {"Enterprise Value", "EV"},
            "free_cash_flow": {"Free Cash Flow", "FCF", "Free CF"},
            "ebit": {"EBIT", "Operating Income"},
            # Mejora #6: Métricas de salud financiera avanzada
            "net_debt_to_ebitda": {"Net Debt/EBITDA", "Net Debt to EBITDA"},
            "interest_coverage": {"Interest Coverage", "Times Interest Earned"},
            "total_debt": {"Total Debt", "Total Liabilities"},
            "cash_and_equivalents": {"Cash and Equivalents", "Cash", "Cash & ST Investments"},
            "ebitda": {"EBITDA"},
            "interest_expense": {"Interest Expense"},
        }
        self.metric_priority = {
            "current_price": [
                "manual_override",
                # Prefer structured API sources over scraped HTML to avoid mis-parsing/scaling issues
                "twelvedata",
                "fmp",
                "alpha_vantage",
                "yahoo",
                "finviz",
                "marketwatch",
                "fallback_example",
            ],
            "market_cap": [
                "manual_override",
                # Prefer structured API sources over scraped HTML to avoid mis-parsing/scaling issues
                "twelvedata",
                "fmp",
                "alpha_vantage",
                "yahoo",
                "finviz",
                "marketwatch",
                "fallback_example",
            ],
        }
        self.percent_metrics = {
            "roe",
            "roic",
            "roa",
            "operating_margin",
            "net_margin",
            "gross_margin",
            "revenue_growth",
            "revenue_growth_qoq",
            "revenue_growth_5y",
            "earnings_growth",
            "earnings_growth_this_y",
            "earnings_growth_next_y",
            "earnings_growth_next_5y",
            "earnings_growth_qoq",
        }
        self.critical_metrics = [
            "pe_ratio",
            "peg_ratio",
            "price_to_book",
            "roe",
            "roic",
            "operating_margin",
            "net_margin",
            # Mejora #3: Métricas basadas en caja (TIER1 valuation)
            "ev_to_ebit",
            "fcf_yield",
            "enterprise_value",
            "free_cash_flow",
            "ebit",
            # Mejora #6: Métricas de salud financiera (TIER1 health)
            "net_debt_to_ebitda",
            "interest_coverage",
            "total_debt",
            "cash_and_equivalents",
            "ebitda",
            "interest_expense",
        ]
        self.alpha_client = AlphaVantageClient()
        self.twelve_client = TwelveDataClient()
        self.fmp_client = FMPClient()
        # Log de disponibilidad de proveedores (sin exponer secretos)
        try:
            av_env = "ALPHA_VANTAGE_KEY" if os.getenv("ALPHA_VANTAGE_KEY") else ("ALPHAVANTAGE_API_KEY" if os.getenv("ALPHAVANTAGE_API_KEY") else "none")
            td_env = "TWELVEDATA_API_KEY" if os.getenv("TWELVEDATA_API_KEY") else ("TWELVE_DATA_API_KEY" if os.getenv("TWELVE_DATA_API_KEY") else "none")
            fmp_env = "FMP_API_KEY" if os.getenv("FMP_API_KEY") else "none"
            logger.info(
                "Providers enabled -> AlphaVantage=%s (env=%s), TwelveData=%s (env=%s), FMP=%s (env=%s)",
                self.alpha_client.enabled, av_env, self.twelve_client.enabled, td_env, self.fmp_client.enabled, fmp_env
            )
        except Exception:
            # Evitar que un error de logging afecte la inicialización
            pass
        self.classifier = AssetClassifier()
        self.classification_path = DATA_DIR / "asset_classifications.json"
        self.classification_cache = self._load_classification_cache()
        for symbol, asset_type in self.classifier.MANUAL_OVERRIDES.items():
            self.classification_cache[symbol] = {
                "asset_type": asset_type,
                "type_label": AssetClassifier.ASSET_NAMES.get(asset_type, asset_type),
                "raw_type": asset_type,
                "needs_special_metrics": asset_type in AssetClassifier.SPECIAL_METRICS,
                "is_analyzable": asset_type == "EQUITY",
                "source": "manual_override",
            }
        self._save_classification_cache()

    def _get(self, url: str, timeout: int = 12, tries: int = 3, sleep: float = 1.2) -> Optional[requests.Response]:
        for attempt in range(tries):
            try:
                resp = self.session.get(url, timeout=timeout)
            except requests.RequestException as exc:  # pragma: no cover - defensive
                logger.debug("Request error %s for %s", exc, url)
                resp = None
            if resp and resp.status_code == 200 and resp.text:
                return resp
            time.sleep(sleep * (attempt + 1))
        return None

    def fetch_financial_data(self, ticker: str) -> Optional[Dict]:
        # Asegurar que, si el agente fue construido antes de que la plataforma
        # inyectara variables, volvamos a resolver claves desde el entorno.
        # Esto es idempotente y barato.
        if not (self.alpha_client.enabled and self.twelve_client.enabled and self.fmp_client.enabled):
            prev = (self.alpha_client.enabled, self.twelve_client.enabled, self.fmp_client.enabled)
            # Reconstruir clientes desde el entorno actual
            self.alpha_client = AlphaVantageClient()
            self.twelve_client = TwelveDataClient()
            self.fmp_client = FMPClient()
            curr = (self.alpha_client.enabled, self.twelve_client.enabled, self.fmp_client.enabled)
            if prev != curr:
                try:
                    av_env = "ALPHA_VANTAGE_KEY" if os.getenv("ALPHA_VANTAGE_KEY") else ("ALPHAVANTAGE_API_KEY" if os.getenv("ALPHAVANTAGE_API_KEY") else "none")
                    td_env = "TWELVEDATA_API_KEY" if os.getenv("TWELVEDATA_API_KEY") else ("TWELVE_DATA_API_KEY" if os.getenv("TWELVE_DATA_API_KEY") else "none")
                    fmp_env = "FMP_API_KEY" if os.getenv("FMP_API_KEY") else "none"
                    logger.info(
                        "Providers refreshed -> AlphaVantage=%s (env=%s), TwelveData=%s (env=%s), FMP=%s (env=%s)",
                        self.alpha_client.enabled, av_env, self.twelve_client.enabled, td_env, self.fmp_client.enabled, fmp_env
                    )
                except Exception:
                    pass

        ticker = ticker.upper()
        self.provenance = {}
        metrics: Dict[str, Optional[float]] = {
            "ticker": ticker,
            "source": "web",
            "warnings": [],
        }

        sources = [
            self._fetch_alpha_vantage,
            self._fetch_twelve_data,
            self._fetch_fmp,
            self._fetch_yahoo,
            self._fetch_finviz,
            self._fetch_marketwatch,
            self._fetch_example_data,
        ]

        # Almacenar resultados para calcular dispersión
        source_results = []

        for source in sources:
            logger.info("Consultando %s para %s", source.__name__, ticker)
            result = None
            try:
                result = source(ticker)
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Source %s failed for %s: %s", source.__name__, ticker, exc)
            if not result:
                logger.info("%s no aportó datos para %s", source.__name__, ticker)
                continue

            # Guardar resultado para análisis de dispersión
            source_results.append(result)

            for key, value in result.data.items():
                if key in self.metric_priority:
                    self._update_metric(metrics, key, value, result.source)
                    continue
                if value is None:
                    continue
                if metrics.get(key) is None:
                    metrics[key] = value
                    self.provenance[key] = self._resolve_provenance_label(key, source)
            metrics["primary_source"] = metrics.get("primary_source") or result.source
            logger.info(
                "%s aportó %s campos para %s (origen %s)",
                source.__name__,
                len(result.data),
                ticker,
                result.source,
            )

            if self._calculate_completeness(metrics) >= 80:
                break
            time.sleep(0.6)

        # Calcular dispersión para métricas críticas (solo si tenemos múltiples fuentes)
        dispersion_data = {}
        if len(source_results) >= 2:
            for critical_metric in self.critical_metrics:
                disp_result = self._calculate_dispersion(critical_metric, source_results)
                if disp_result:
                    # Usar valor consolidado (mediana) en vez de primera fuente
                    metrics[critical_metric] = disp_result["value"]
                    dispersion_data[critical_metric] = {
                        "sources": disp_result["sources"],
                        "cv": disp_result["dispersion"],
                        "confidence_adj": disp_result["confidence_adj"],
                        "quality": disp_result["quality"]
                    }
                    logger.info(
                        "Dispersión para %s: CV=%.2f%%, confianza=%.2f, calidad=%s (fuentes: %s)",
                        critical_metric,
                        disp_result["dispersion"],
                        disp_result["confidence_adj"],
                        disp_result["quality"],
                        ", ".join(disp_result["sources"])
                    )

        # Calcular métricas derivadas (FCF Yield, EV/EBIT, etc.) - Mejora #3
        metrics = self._calculate_derived_metrics(metrics)
        
        metrics = self._finalize_metrics(metrics)
        
        # Adjuntar información de dispersión
        if dispersion_data:
            metrics["dispersion"] = dispersion_data
        
        # Adjuntar trazabilidad de origen por métrica para depuración/auditoría.
        # Esto permite verificar rápidamente qué fuente aportó cada valor
        # (p. ej., alpha_vantage, fmp, twelvedata, scraping, override manual, etc.).
        if self.provenance:
            try:
                # deepcopy por seguridad (no mutar el estado interno en cachés posteriores)
                metrics["provenance"] = deepcopy(self.provenance)
            except Exception:
                # Falla silenciosa: la falta de provenance no debe impedir devolver métricas
                pass
        return metrics if len(metrics) > 2 else None

    def _priority_rank(self, key: str, source: Optional[str]) -> int:
        order = self.metric_priority.get(key, [])
        if not order:
            return 0
        if source is None:
            return len(order)
        normalized = source.split(":", 1)[0]
        try:
            return order.index(normalized)
        except ValueError:
            return len(order)

    def _resolve_provenance_label(self, key: str, source: str) -> str:
        existing = self.provenance.get(key)
        if existing and existing.split(":", 1)[0] == source:
            return existing
        return source

    def _update_metric(self, metrics: Dict, key: str, value: Any, source: str) -> None:
        if value is None:
            return
        current = metrics.get(key)
        if current is None:
            metrics[key] = value
            self.provenance[key] = self._resolve_provenance_label(key, source)
            return

        priority_order = self.metric_priority.get(key)
        if not priority_order:
            return

        current_source = self.provenance.get(key)
        current_rank = self._priority_rank(key, current_source)
        new_rank = self._priority_rank(key, source)

        if new_rank < current_rank:
            metrics[key] = value
            self.provenance[key] = self._resolve_provenance_label(key, source)
            return

        if (
            new_rank == current_rank
            and isinstance(current, (int, float))
            and isinstance(value, (int, float))
        ):
            baseline = max(abs(current), 1e-6)
            if abs(value - current) / baseline >= 0.25:
                metrics[key] = value
                self.provenance[key] = self._resolve_provenance_label(key, source)

    def _merge_provenance(self, prov: Dict[str, str]) -> None:
        for key, value in prov.items():
            self.provenance.setdefault(key, value)

    def _load_classification_cache(self) -> Dict[str, Dict[str, str]]:
        if not self.classification_path.exists():
            return {}
        try:
            with self.classification_path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
                if isinstance(data, dict):
                    return data
        except json.JSONDecodeError:
            logging.warning("Corrupted classification cache; rebuilding")
        return {}

    def _save_classification_cache(self) -> None:
        try:
            with self.classification_path.open("w", encoding="utf-8") as fh:
                json.dump(self.classification_cache, fh, indent=2, sort_keys=True)
        except OSError as exc:
            logging.warning("No se pudo guardar la clasificacion de activos: %s", exc)

    def _cache_classification(self, classification: AssetClassification) -> None:
        self.classification_cache[classification.ticker] = {
            "asset_type": classification.asset_type,
            "type_label": classification.type_label,
            "raw_type": classification.raw_type,
            "needs_special_metrics": classification.needs_special_metrics,
            "is_analyzable": classification.is_analyzable,
            "source": classification.source,
        }
        self._save_classification_cache()

    def _fetch_alpha_vantage(self, ticker: str) -> Optional[SourceResult]:
        if not self.alpha_client.enabled:
            logger.info("Alpha Vantage deshabilitado (API key ausente)")
            return None

        overview = self.alpha_client.get_overview(ticker)
        if not overview:
            return None

        data: Dict[str, Optional[float]] = {}
        prov: Dict[str, str] = {}

        def set_value(field: str, value: Optional[str], parser=None) -> None:
            if value in (None, "", "None"):
                return
            parsed = parser(value) if parser else self._parse_number(value)
            if parsed is None:
                return
            data.setdefault(field, parsed)
            prov[field] = "alpha_vantage"

        def set_percentage(field: str, value: Optional[str]) -> None:
            parsed = self._to_percentage(value)
            if parsed is None:
                return
            data.setdefault(field, parsed)
            prov[field] = "alpha_vantage"

        text_mappings = {
            "company_name": overview.get("Name"),
            "sector": overview.get("Sector"),
            "industry": overview.get("Industry"),
            "currency": overview.get("Currency"),
        }
        for field, value in text_mappings.items():
            if value:
                data.setdefault(field, value.strip())
                prov[field] = "alpha_vantage"

        set_value("market_cap", overview.get("MarketCapitalization"))
        set_value("pe_ratio", overview.get("PERatio"))
        set_value("peg_ratio", overview.get("PEGRatio"))
        set_value("price_to_book", overview.get("PriceToBookRatio"))
        set_value("debt_to_equity", overview.get("DebtToEquityRatio"))
        set_value("current_ratio", overview.get("CurrentRatio"))
        set_value("quick_ratio", overview.get("QuickRatio"))

        set_percentage("roe", overview.get("ReturnOnEquityTTM"))
        set_percentage("roa", overview.get("ReturnOnAssetsTTM"))
        set_percentage("operating_margin", overview.get("OperatingMarginTTM"))
        set_percentage("net_margin", overview.get("ProfitMarginTTM") or overview.get("NetProfitMarginTTM"))
        set_percentage("gross_margin", overview.get("GrossMarginTTM"))
        set_percentage("revenue_growth", overview.get("QuarterlyRevenueGrowthYOY"))
        set_percentage("earnings_growth", overview.get("QuarterlyEarningsGrowthYOY"))

        if not data:
            return None

        if "current_price" not in data or data["current_price"] is None:
            quote = self.alpha_client.get_global_quote(ticker)
            if quote:
                price_str = quote.get("05. price") or quote.get("05.price")
                if price_str:
                    price_val = self._parse_number(price_str)
                    if price_val is not None:
                        data.setdefault("current_price", price_val)
                        prov["current_price"] = "alpha_vantage:quote"

                currency = data.get("currency")
                if not currency:
                    data["currency"] = "USD"
                    prov["currency"] = "alpha_vantage:quote"

        # Alpha Vantage overview does not include live price reliably.
        # Only fetch when we still miss current_price to avoid extra calls.
        if data.get("currency") and data.get("market_cap") and data.get("market_cap") < 1e6:
            # Sometimes AV returns values scaled wrongly; drop unrealistic cap.
            data.pop("market_cap", None)

        if data.get("currency"):
            data.setdefault("price_currency", data["currency"])

        self._merge_provenance(prov)
        return SourceResult(data=data, source="alpha_vantage", coverage=len(data))

    def _fetch_twelve_data(self, ticker: str) -> Optional[SourceResult]:
        if not self.twelve_client.enabled:
            logger.info("Twelve Data deshabilitado (API key ausente)")
            return None

        payload = self.twelve_client.get_quote(ticker)
        if not payload:
            return None

        data: Dict[str, Optional[float]] = {}
        prov: Dict[str, str] = {}

        price = payload.get("close") or payload.get("last") or payload.get("price")
        if price:
            parsed_price = self._parse_number(str(price))
            if parsed_price is not None:
                data["current_price"] = parsed_price
                prov["current_price"] = "twelvedata:quote"

        currency = payload.get("currency")
        if currency:
            data.setdefault("currency", currency.upper())
            data.setdefault("price_currency", currency.upper())
            prov["currency"] = "twelvedata:quote"

        name = payload.get("name")
        if name:
            data.setdefault("company_name", name.strip())
            prov["company_name"] = "twelvedata:quote"

        exchange = payload.get("exchange")
        if exchange:
            data.setdefault("exchange", exchange)

        market_cap = payload.get("market_cap")
        if market_cap:
            parsed_cap = self._parse_number(str(market_cap))
            if parsed_cap is not None:
                data.setdefault("market_cap", parsed_cap)
                prov["market_cap"] = "twelvedata:quote"

        volume = payload.get("volume")
        if volume:
            parsed_volume = self._parse_number(str(volume))
            if parsed_volume is not None:
                data.setdefault("volume", parsed_volume)
                prov["volume"] = "twelvedata:quote"

        if not data:
            return None

        self._merge_provenance(prov)
        return SourceResult(data=data, source="twelvedata", coverage=len(data))

    def _fetch_fmp(self, ticker: str) -> Optional[SourceResult]:
        if not self.fmp_client.enabled:
            logger.info("FMP deshabilitado (API key ausente)")
            return None

        data: Dict[str, Optional[float]] = {}
        prov: Dict[str, str] = {}

        profile = self.fmp_client.get_profile(ticker)
        if profile:
            text_fields = {
                "company_name": profile.get("companyName"),
                "sector": profile.get("sector"),
                "industry": profile.get("industry"),
                "currency": profile.get("currency"),
            }
            for field, value in text_fields.items():
                if value:
                    data.setdefault(field, value.strip())
                    prov[field] = "fmp:profile"

            set_price = profile.get("price")
            if set_price is not None:
                parsed_price = self._parse_number(str(set_price))
                if parsed_price is not None:
                    data.setdefault("current_price", parsed_price)
                    prov["current_price"] = "fmp:profile"

            market_cap = profile.get("mktCap") or profile.get("marketCap")
            if market_cap is not None:
                parsed_cap = self._parse_number(str(market_cap))
                if parsed_cap is not None:
                    data.setdefault("market_cap", parsed_cap)
                    prov["market_cap"] = "fmp:profile"

        quote = self.fmp_client.get_quote(ticker)
        if quote:
            price = quote.get("price") or quote.get("previousClose")
            if price is not None:
                parsed_price = self._parse_number(str(price))
                if parsed_price is not None:
                    data.setdefault("current_price", parsed_price)
                    prov["current_price"] = "fmp:quote"
            market_cap = quote.get("marketCap")
            if market_cap is not None:
                parsed_cap = self._parse_number(str(market_cap))
                if parsed_cap is not None:
                    data.setdefault("market_cap", parsed_cap)
                    prov["market_cap"] = "fmp:quote"

        ratios = self.fmp_client.get_ratios(ticker)
        if ratios:
            ratio_map = {
                "roe": ratios.get("returnOnEquityTTM"),
                "roic": ratios.get("returnOnCapitalEmployedTTM"),
                "operating_margin": ratios.get("operatingProfitMarginTTM"),
                "net_margin": ratios.get("netProfitMarginTTM"),
                "current_ratio": ratios.get("currentRatioTTM"),
                "quick_ratio": ratios.get("quickRatioTTM"),
                "debt_to_equity": ratios.get("debtEquityRatioTTM"),
            }
            for field, value in ratio_map.items():
                if value is None:
                    continue
                if field in {"roe", "roic", "operating_margin", "net_margin"}:
                    parsed = self._to_percentage(value)
                else:
                    parsed = self._parse_number(str(value))
                if parsed is None:
                    continue
                data.setdefault(field, parsed)
                prov[field] = "fmp:ratios"

        key_metrics = self.fmp_client.get_key_metrics(ticker)
        if key_metrics:
            km_map = {
                "peg_ratio": key_metrics.get("pegRatioTTM") or key_metrics.get("pegRatio"),
                "price_to_book": key_metrics.get("priceToBookRatioTTM") or key_metrics.get("priceToBookRatio"),
                "revenue_growth": key_metrics.get("revenueGrowthYoy"),
                "earnings_growth": key_metrics.get("netIncomeGrowth"),
            }
            for field, value in km_map.items():
                if value is None:
                    continue
                parsed = self._to_percentage(value) if "growth" in field else self._parse_number(str(value))
                if parsed is None:
                    continue
                data.setdefault(field, parsed)
                prov[field] = "fmp:key-metrics"

        if not data:
            return None

        if data.get("currency"):
            data.setdefault("price_currency", data["currency"])

        self._merge_provenance(prov)
        return SourceResult(data=data, source="fmp", coverage=len(data))

    def _fetch_yahoo(self, ticker: str) -> Optional[SourceResult]:
        data: Dict[str, float] = {}
        prov: Dict[str, str] = {}

        url_stats = f"https://finance.yahoo.com/quote/{ticker}/key-statistics"
        resp = self._get(url_stats)
        if resp:
            soup = BeautifulSoup(resp.text, "lxml")
            for row in soup.select("section table tr"):
                cells = row.find_all("td")
                if len(cells) != 2:
                    continue
                label = cells[0].get_text(strip=True)
                value = cells[1].get_text(strip=True)

                def set_pct(field: str):
                    parsed = self._parse_percentage(value)
                    if parsed is not None:
                        data.setdefault(field, parsed)
                        prov[field] = "yahoo:key-statistics"

                def set_num(field: str):
                    parsed = self._parse_number(value)
                    if parsed is not None:
                        data.setdefault(field, parsed)
                        prov[field] = "yahoo:key-statistics"

                if "Return on Equity" in label:
                    set_pct("roe")
                elif "Return on Assets" in label:
                    set_pct("roa")
                elif "Operating Margin" in label:
                    set_pct("operating_margin")
                elif "Profit Margin" in label:
                    set_pct("net_margin")
                elif "Gross Margin" in label:
                    set_pct("gross_margin")
                elif "Current Ratio" in label:
                    set_num("current_ratio")
                elif "Quick Ratio" in label:
                    set_num("quick_ratio")
                elif "Trailing P/E" in label or "PE Ratio" in label:
                    set_num("pe_ratio")
                elif "Price/Book" in label:
                    set_num("price_to_book")
                elif "PEG Ratio" in label:
                    set_num("peg_ratio")
                elif "Revenue Growth" in label:
                    set_pct("revenue_growth")
                elif "Gross Profit" in label and "TTM" in label:
                    set_num("gross_profit")

        url_quote = f"https://finance.yahoo.com/quote/{ticker}"
        resp_quote = self._get(url_quote)
        if resp_quote:
            soup = BeautifulSoup(resp_quote.text, "lxml")

            # Extraer precio actual
            price_tag = soup.select_one("fin-streamer[data-field='regularMarketPrice']")
            if price_tag:
                raw_price = price_tag.get("value") or price_tag.text
                price_val = self._parse_number(raw_price)
                if price_val is not None:
                    data.setdefault("current_price", price_val)
                    prov["current_price"] = "yahoo:quote"

            # Extraer market cap
            market_cap_tag = soup.select_one("fin-streamer[data-field='marketCap']")
            if market_cap_tag and market_cap_tag.get("value"):
                try:
                    market_cap_val = float(market_cap_tag.get("value"))
                    data.setdefault("market_cap", market_cap_val)
                    prov["market_cap"] = "yahoo:quote"
                except (ValueError, TypeError):
                    pass

            # Extraer company name y sector (de los meta tags)
            company_name_tag = soup.select_one("h1")
            if company_name_tag:
                company_name_text = company_name_tag.get_text(strip=True)
                # Remover el ticker si está entre paréntesis
                if "(" in company_name_text:
                    company_name_text = company_name_text.split("(")[0].strip()
                if not self._is_suspicious_company_name(company_name_text):
                    data.setdefault("company_name", company_name_text)
                    prov["company_name"] = "yahoo:quote"
                else:
                    logger.warning(
                        "Descartando nombre sospechoso desde Yahoo para %s: %s",
                        ticker,
                        company_name_text,
                    )

        if not data:
            return None

        self._merge_provenance(prov)
        return SourceResult(data=data, source="yahoo", coverage=len(data))

    def _fetch_finviz(self, ticker: str) -> Optional[SourceResult]:
        url = f"https://finviz.com/quote.ashx?t={ticker}"
        resp = self._get(url)
        if resp is None:
            return None
        soup = BeautifulSoup(resp.text, "lxml")
        tables = soup.find_all("table", class_="snapshot-table2")
        if not tables:
            return None
        data: Dict[str, Optional[float]] = {}
        for table in tables:
            cells = table.find_all("td")
            for idx in range(0, len(cells), 2):
                if idx + 1 >= len(cells):
                    continue
                key = cells[idx].get_text(strip=True)
                value = cells[idx + 1].get_text(strip=True)
                mapped = self._map_finviz_metric(key, value)
                if mapped:
                    for field, val in mapped.items():
                        data.setdefault(field, val)
                        self._merge_provenance({field: "finviz"})

        name_tag = soup.select_one(".fullview-title .fullview-title-name")
        if name_tag:
            data.setdefault("company_name", name_tag.get_text(strip=True))
        meta_rows = soup.select(".fullview-title .fullview-title-data span")
        for span in meta_rows:
            text = span.get_text(strip=True)
            if text.startswith("Sector:"):
                data.setdefault("sector", text.replace("Sector:", "").strip())
            if text.startswith("Industry:"):
                data.setdefault("industry", text.replace("Industry:", "").strip())

        return SourceResult(data=data, source="finviz", coverage=len(data)) if data else None

    def _map_finviz_metric(self, key: str, value: str) -> Optional[Dict[str, float]]:
        mapping = {
            "P/E": "pe_ratio",
            "P/E TTM": "pe_ratio",
            "PEG": "peg_ratio",
            "P/B": "price_to_book",
            "Price/Book": "price_to_book",
            "P/S": "price_to_sales",
            "EV/EBITDA": "ev_to_ebitda",
            "ROE": "roe",
            "ROA": "roa",
            "ROI": "roic",
            "Operating Margin": "operating_margin",
            "Oper. Margin": "operating_margin",
            "Profit Margin": "net_margin",
            "Net Profit Margin": "net_margin",
            "Gross Margin": "gross_margin",
            "Debt/Eq": "debt_to_equity",
            "Current Ratio": "current_ratio",
            "Quick Ratio": "quick_ratio",
            "EPS (ttm)": "eps_ttm",
            "EPS this Y": "earnings_growth_this_y",
            "EPS next Y": "earnings_growth_next_y",
            "EPS next 5Y": "earnings_growth_next_5y",
            "Sales Q/Q": "revenue_growth_qoq",
            "Sales past 5Y": "revenue_growth_5y",
            "Market Cap": "market_cap",
        }
        field = mapping.get(key)
        if not field:
            return None

        if field in self.percent_metrics:
            parsed = self._parse_percentage(value)
        else:
            parsed = self._parse_number(value)
        if parsed is None:
            return None
        return {field: parsed}

    def _fetch_marketwatch(self, ticker: str) -> Optional[SourceResult]:
        url = f"https://www.marketwatch.com/investing/stock/{ticker.lower()}/company-profile"
        resp = self._get(url)
        if resp is None:
            return None
        soup = BeautifulSoup(resp.text, "lxml")
        data: Dict[str, Optional[float]] = {}
        for row in soup.select("tbody tr"):
            cells = row.find_all("td")
            if len(cells) != 2:
                continue
            key = cells[0].get_text(strip=True)
            value = cells[1].get_text(strip=True)
            lower = key.lower()
            if "p/e" in lower:
                parsed = self._parse_number(value)
                if parsed:
                    data.setdefault("pe_ratio", parsed)
                    self._merge_provenance({"pe_ratio": "marketwatch"})
            elif "profit margin" in lower and "net" in lower:
                parsed = self._parse_percentage(value)
                if parsed is not None:
                    data.setdefault("net_margin", parsed)
                    self._merge_provenance({"net_margin": "marketwatch"})
            elif "gross margin" in lower:
                parsed = self._parse_percentage(value)
                if parsed is not None:
                    data.setdefault("gross_margin", parsed)
                    self._merge_provenance({"gross_margin": "marketwatch"})
            elif "operating margin" in lower:
                parsed = self._parse_percentage(value)
                if parsed is not None:
                    data.setdefault("operating_margin", parsed)
                    self._merge_provenance({"operating_margin": "marketwatch"})
            elif "return on equity" in lower:
                parsed = self._parse_percentage(value)
                if parsed is not None:
                    data.setdefault("roe", parsed)
                    self._merge_provenance({"roe": "marketwatch"})
            elif "return on assets" in lower:
                parsed = self._parse_percentage(value)
                if parsed is not None:
                    data.setdefault("roa", parsed)
                    self._merge_provenance({"roa": "marketwatch"})

        description = soup.find("div", class_="description__text")
        if description and "Sector" in description.text:
            match = re.search(r"Sector\s+(.+?)\s+Industry", description.text)
            if match:
                data.setdefault("sector", match.group(1).strip())

        return SourceResult(data=data, source="marketwatch", coverage=len(data)) if data else None

    def _fetch_example_data(self, ticker: str) -> SourceResult:
        examples = {
            "AAPL": {
                "company_name": "Apple Inc.",
                "sector": "Technology",
                "current_price": 230.45,
                "market_cap": 3.5e12,  # $3.5T
                "pe_ratio": 28.5,
                "peg_ratio": 2.3,
                "price_to_book": 46.5,
                "roe": 147.5,
                "roic": 28.1,
                "operating_margin": 29.8,
                "net_margin": 25.3,
                "debt_to_equity": 1.95,
                "current_ratio": 0.98,
                "quick_ratio": 0.87,
                "revenue_growth": 8.1,
                "earnings_growth": 7.4,
            },
            "MSFT": {
                "company_name": "Microsoft Corporation",
                "sector": "Technology",
                "current_price": 425.30,
                "market_cap": 3.1e12,  # $3.1T
                "pe_ratio": 35.2,
                "peg_ratio": 2.1,
                "price_to_book": 14.2,
                "roe": 39.2,
                "roic": 23.5,
                "operating_margin": 42.1,
                "net_margin": 34.1,
                "debt_to_equity": 0.69,
                "current_ratio": 1.82,
                "quick_ratio": 1.6,
                "revenue_growth": 12.5,
                "earnings_growth": 14.0,
            },
            "AMD": {
                "company_name": "Advanced Micro Devices, Inc.",
                "sector": "Technology - Semiconductors",
                "current_price": 169.50,
                "market_cap": 273e9,  # $273B
                "pe_ratio": 55.0,
                "peg_ratio": 1.8,
                "price_to_book": 6.5,
                "roe": 12.0,
                "roic": 9.0,
                "operating_margin": 18.0,
                "net_margin": 15.5,
                "debt_to_equity": 0.07,
                "current_ratio": 2.5,
                "quick_ratio": 1.9,
                "revenue_growth": 30.0,
                "earnings_growth": 25.0,
            },
            "NVDA": {
                "company_name": "NVIDIA Corporation",
                "sector": "Technology - Semiconductors",
                "current_price": 880.25,
                "market_cap": 2.2e12,  # $2.2T
                "pe_ratio": 52.0,
                "peg_ratio": 1.43,
                "price_to_book": 44.4,
                "roe": 109.4,
                "roic": 76.6,
                "operating_margin": 58.1,
                "net_margin": 52.4,
                "debt_to_equity": 0.18,
                "current_ratio": 3.5,
                "quick_ratio": 3.2,
                "revenue_growth": 55.6,
                "earnings_growth": 51.2,
            },
            "TSM": {
                "company_name": "Taiwan Semiconductor Manufacturing",
                "sector": "Technology - Semiconductors",
                "current_price": 150.80,
                "market_cap": 780e9,  # $780B
                "pe_ratio": 30.5,
                "peg_ratio": 1.02,
                "price_to_book": 9.85,
                "roe": 34.9,
                "roic": 24.4,
                "operating_margin": 49.5,
                "net_margin": 43.7,
                "debt_to_equity": 0.19,
                "current_ratio": 2.69,
                "quick_ratio": 2.47,
                "revenue_growth": 40.7,
                "earnings_growth": 50.8,
            },
            "INTC": {
                "company_name": "Intel Corporation",
                "sector": "Technology - Semiconductors",
                "current_price": 25.30,
                "market_cap": 103e9,  # $103B
                "pe_ratio": -15.2,  # Negativo por pérdidas
                "peg_ratio": None,
                "price_to_book": 1.2,
                "roe": -2.3,
                "roic": -1.8,
                "operating_margin": 2.1,
                "net_margin": -5.2,
                "debt_to_equity": 0.45,
                "current_ratio": 1.8,
                "quick_ratio": 1.5,
                "revenue_growth": -2.5,
                "earnings_growth": -15.8,
            },
            "IAU": {
                "company_name": "iShares Gold Trust",
                "sector": "Commodity ETF",
                "current_price": 82.5,
                "nav": 79.6,
                "expense_ratio": 0.25,
                "ytd_return": 61.5,
                "category": "Commodity - Precious Metals",
                "provider": "BlackRock",
                "assets_under_management": 32000000000,
                "dividend_yield": 0.0,
                "holdings_count": 1,
                "index_tracked": "Precio spot del oro",
            },
            "VOO": {
                "company_name": "Vanguard S&P 500 ETF",
                "sector": "Large Blend ETF",
                "current_price": 617.2,
                "nav": 617.1,
                "expense_ratio": 0.03,
                "ytd_return": 18.4,
                "category": "Large Blend",
                "provider": "Vanguard",
                "assets_under_management": 560000000000,
                "dividend_yield": 1.45,
                "holdings_count": 500,
                "index_tracked": "S&P 500",
            },
            "VNQ": {
                "company_name": "Vanguard Real Estate ETF",
                "sector": "Real Estate ETF",
                "current_price": 105.4,
                "nav": 105.0,
                "expense_ratio": 0.12,
                "ytd_return": 9.2,
                "category": "Real Estate",
                "provider": "Vanguard",
                "assets_under_management": 36000000000,
                "dividend_yield": 3.98,
                "holdings_count": 160,
                "index_tracked": "MSCI US Investable Market Real Estate",
            },
            "QCOM": {
                "company_name": "QUALCOMM Incorporated",
                "sector": "Technology - Semiconductors",
                "current_price": 175.60,
                "market_cap": 195e9,  # $195B
                "pe_ratio": 19.5,
                "peg_ratio": 1.15,
                "price_to_book": 7.2,
                "roe": 38.5,
                "roic": 28.2,
                "operating_margin": 31.5,
                "net_margin": 26.8,
                "debt_to_equity": 0.82,
                "current_ratio": 1.95,
                "quick_ratio": 1.65,
                "revenue_growth": 15.3,
                "earnings_growth": 18.7,
            },
        }
        default = {
            "company_name": f"{ticker} Corporation",
            "sector": "Unknown",
            "current_price": 100.0,
            "market_cap": 50e9,  # $50B default
            "pe_ratio": 20.0,
            "peg_ratio": 1.5,
            "price_to_book": 3.0,
            "roe": 15.0,
            "roic": 10.0,
            "operating_margin": 15.0,
            "net_margin": 12.0,
            "debt_to_equity": 1.0,
            "current_ratio": 1.5,
            "quick_ratio": 1.2,
            "revenue_growth": 5.0,
            "earnings_growth": 4.0,
        }
        data = examples.get(ticker, default)
        logger.warning("Using fallback example data for %s", ticker)
        self._merge_provenance({key: "fallback_example" for key in data})
        return SourceResult(data=data, source="fallback_example", coverage=len(data))

    def _to_percentage(self, value) -> Optional[float]:
        if value is None:
            return None
        if isinstance(value, str):
            value = value.strip()
            if not value or value in {"-", "N/A", "None"}:
                return None
            parsed = self._parse_number(value)
        elif isinstance(value, (int, float)):
            parsed = float(value)
        else:
            return None
        if parsed is None:
            return None
        if -1.5 <= parsed <= 1.5:
            parsed *= 100
        return parsed

    def _parse_number(self, value: str) -> Optional[float]:
        if not value or value in {"-", "N/A", "None"}:
            return None
        cleaned = (
            value.replace("\xa0", "")
            .replace("$", "")
            .replace("€", "")
            .replace("£", "")
            .replace("¥", "")
            .strip()
        )
        multipliers = {"K": 1e3, "M": 1e6, "B": 1e9, "T": 1e12}
        suffix = cleaned[-1].upper()
        multiplier = multipliers.get(suffix)
        if multiplier:
            cleaned = cleaned[:-1]

        cleaned = cleaned.strip()

        if "," in cleaned:
            if "." in cleaned:
                if cleaned.rfind(",") > cleaned.rfind("."):
                    cleaned = cleaned.replace(".", "").replace(",", ".")
                else:
                    cleaned = cleaned.replace(",", "")
            else:
                parts = cleaned.split(",")
                if len(parts) == 2 and len(parts[1]) <= 2:
                    cleaned = parts[0].replace(".", "") + "." + parts[1]
                else:
                    cleaned = cleaned.replace(",", "")
        else:
            cleaned = cleaned.replace(",", "")

        try:
            numeric = float(cleaned)
            return numeric * multiplier if multiplier else numeric
        except ValueError:
            return None

    def _parse_percentage(self, value: str) -> Optional[float]:
        if isinstance(value, str) and value.endswith("%"):
            value = value[:-1]
        return self._parse_number(value)

    def _clean_metrics(self, metrics: Dict) -> Dict:
        cleaned: Dict[str, Optional[float]] = {}
        warnings_buffer = list(metrics.get("warnings", []))
        for key, value in metrics.items():
            if isinstance(value, (int, float)):
                if key == "pe_ratio" and (value <= 0 or value > 1000):
                    continue
                if key == "peg_ratio" and (value <= 0 or value > 10):
                    continue
                if key in {"roe", "roic", "roa", "gross_margin", "operating_margin", "net_margin"}:
                    if not (-50 <= value <= 200):
                        continue
                if key == "debt_to_equity" and value < 0:
                    continue
                if key in {"current_ratio", "quick_ratio"} and value < 0:
                    continue
                if "growth" in key and not (-100 <= value <= 300):
                    continue
            cleaned[key] = value
        cleaned["warnings"] = warnings_buffer
        return cleaned

    def _maybe_recalc_peg(self, metrics: Dict) -> None:
        pe = metrics.get("pe_ratio")
        growth_sources = [
            metrics.get("earnings_growth_this_y"),
            metrics.get("earnings_growth_next_y"),
            metrics.get("earnings_growth_next_5y"),
            metrics.get("earnings_growth"),
        ]
        growth = next((g for g in growth_sources if g), None)
        if metrics.get("peg_ratio") is None and pe and growth and growth > 0:
            growth_decimal = growth / 100 if growth > 1 else growth
            if growth_decimal > 0:
                metrics["peg_ratio"] = round(pe / (growth_decimal * 100) if growth > 1 else pe / growth_decimal, 2)
                metrics.setdefault("warnings", []).append("PEG recalculado a partir de P/E y crecimiento de utilidades.")

    def _finalize_metrics(self, metrics: Dict) -> Dict:
        metrics = self._clean_metrics(metrics)
        self._apply_sanity_checks(metrics)
        self._maybe_recalc_peg(metrics)

        classification = self._classify_asset(metrics)
        metrics["asset_type"] = classification.asset_type
        metrics["asset_type_label"] = classification.type_label
        metrics["asset_classification"] = {
            "raw_type": classification.raw_type,
            "source": classification.source,
            "needs_special_metrics": classification.needs_special_metrics,
            "is_analyzable": classification.is_analyzable,
        }
        metrics["analysis_allowed"] = classification.asset_type == "EQUITY"

        metrics["data_completeness"] = self._calculate_completeness(metrics)
        metrics["metrics_collected"] = self._metrics_collected(metrics)
        self._flag_missing_critical(metrics)
        self._apply_asset_special_cases(metrics, classification)
        self._attach_currency_metadata(metrics)
        metrics["schema_version"] = METRIC_SCHEMA_VERSION
        metrics["provenance"] = self.provenance
        metrics["scraped_at"] = datetime.utcnow().isoformat(timespec="seconds")
        return metrics

    def _parse_manual_override_value(self, field: str, value) -> Optional[float]:
        if value is None:
            return None
        if isinstance(value, str):
            normalized = value.strip()
            if not normalized:
                return None
            if normalized.lower() in {"na", "n/a", "none"}:
                return None
            if self.MANUAL_EDITABLE_FIELDS.get(field) == "percent":
                parsed = self._parse_percentage(normalized)
            else:
                parsed = self._parse_number(normalized)
        elif isinstance(value, (int, float)):
            parsed = float(value)
        else:
            raise ValueError("Tipo de dato no soportado para override manual.")
        if parsed is None:
            raise ValueError(f"Valor no válido para {field}.")
        return parsed

    def apply_manual_overrides(
        self, metrics: Dict, overrides: Dict[str, Optional[Any]]
    ) -> Tuple[Dict, List[str], Dict[str, str]]:
        if not overrides:
            return metrics, [], {}

        updated = deepcopy(metrics) if metrics else {"warnings": [], "provenance": {}}
        if "ticker" not in updated and overrides.get("ticker"):
            updated["ticker"] = overrides.get("ticker")
        updated.setdefault("warnings", [])
        updated.setdefault("provenance", {})

        provenance = dict(updated.get("provenance") or {})
        self.provenance = provenance

        warnings = updated.setdefault("warnings", [])
        cleaned_warnings = []
        for warning in warnings:
            if isinstance(warning, str):
                lowered = warning.lower()
                if "datos de ejemplo" in lowered or "las apis no devolvieron" in lowered:
                    continue
            cleaned_warnings.append(warning)
        warnings[:] = cleaned_warnings

        applied: List[str] = []
        invalid: Dict[str, str] = {}

        for field, raw_value in overrides.items():
            if field not in self.MANUAL_EDITABLE_FIELDS:
                invalid[field] = "Campo no editable manualmente."
                continue
            try:
                parsed = self._parse_manual_override_value(field, raw_value)
            except ValueError as exc:
                invalid[field] = str(exc)
                continue
            updated[field] = parsed
            provenance[field] = "manual_override"
            applied.append(field)

        if not applied:
            updated["warnings"] = warnings
            updated["manual_input_recommended"] = updated.get("manual_input_recommended", True)
            return updated, applied, invalid

        summary = "Metricas actualizadas manualmente: " + ", ".join(applied)
        warnings[:] = [w for w in warnings if "Metricas actualizadas manualmente" not in w]
        warnings.append(summary)

        updated["source"] = "manual_override"
        updated["primary_source"] = "manual_override"
        updated["manual_input_recommended"] = False

        finalized = self._finalize_metrics(updated)
        finalized["manual_overrides"] = applied
        logger.info("Overrides manuales aplicados para %s: %s", finalized.get("ticker"), ", ".join(applied))
        return finalized, applied, invalid

    def _calculate_completeness(self, metrics: Dict) -> float:
        required = [
            "pe_ratio",
            "peg_ratio",
            "price_to_book",
            "roe",
            "roic",
            "operating_margin",
            "net_margin",
            "debt_to_equity",
            "current_ratio",
            "quick_ratio",
            "revenue_growth",
            "earnings_growth",
        ]
        alternatives = {
            "revenue_growth": ["revenue_growth_5y", "revenue_growth_qoq"],
            "earnings_growth": [
                "earnings_growth_this_y",
                "earnings_growth_next_y",
                "earnings_growth_next_5y",
                "earnings_growth_qoq",
            ],
        }
        available = []
        for field in required:
            if metrics.get(field) is not None:
                available.append(field)
                continue
            alt_fields = alternatives.get(field, [])
            if any(metrics.get(alias) is not None for alias in alt_fields):
                available.append(field)
        return round((len(available) / len(required)) * 100, 1)

    def _metrics_collected(self, metrics: Dict) -> Dict[str, bool]:
        tracked = [
            "pe_ratio",
            "peg_ratio",
            "price_to_book",
            "roe",
            "roic",
            "roa",
            "operating_margin",
            "net_margin",
            "debt_to_equity",
            "current_ratio",
            "quick_ratio",
            "revenue_growth",
            "revenue_growth_qoq",
            "revenue_growth_5y",
            "earnings_growth",
            "earnings_growth_this_y",
            "earnings_growth_next_y",
            "earnings_growth_next_5y",
            "price",
            "eps_ttm",
        ]
        return {field: metrics.get(field) is not None for field in tracked}

    def _apply_sanity_checks(self, metrics: Dict) -> None:
        warnings = metrics.setdefault("warnings", [])
        ignored = []
        pe = metrics.get("pe_ratio")
        if pe is not None:
            if pe <= 0 or pe > 1000:
                ignored.append(f"P/E ({pe:.2f})")
                metrics["pe_ratio"] = None
            elif pe > 80:
                warnings.append(f"P/E elevado ({pe:.2f}). Revisar expectativas de crecimiento.")
        peg = metrics.get("peg_ratio")
        if peg is not None:
            if peg <= 0 or peg > 50:
                ignored.append(f"PEG ({peg:.2f})")
                metrics["peg_ratio"] = None
            elif peg > 8:
                warnings.append(f"PEG elevado ({peg:.2f}).")

        roe = metrics.get("roe")
        if roe is not None:
            if roe < 0:
                ignored.append(f"ROE ({roe:.1f}%)")
                metrics["roe"] = None
            elif roe > 150:
                ignored.append(f"ROE ({roe:.1f}%)")
                metrics["roe"] = None
            elif roe > 80:
                warnings.append(f"ROE extraordinario ({roe:.1f}%). Verificar base de capital.")

        op_margin = metrics.get("operating_margin")
        if op_margin is not None and op_margin < 0:
            ignored.append(f"Margen operativo ({op_margin:.1f}%)")
            metrics["operating_margin"] = None

        if metrics.get("earnings_growth") and metrics.get("operating_margin") and metrics["operating_margin"] < 10:
            if metrics["earnings_growth"] > 25:
                metrics["operating_margin"] = min(metrics["operating_margin"] * 1.5, 18)
                warnings.append("Margen operativo ajustado por fuerte crecimiento (>25%).")

        if metrics.get("earnings_growth") and metrics.get("roe") is None and metrics.get("roa"):
            metrics["roe"] = metrics["roa"] * 1.2
            warnings.append("ROE estimado a partir de ROA.")

        if metrics.get("roic") is None and metrics.get("roe"):
            metrics["roic"] = min(metrics["roe"] * 0.7, 120)
            warnings.append("ROIC estimado a partir de ROE.")

        if metrics.get("source") == "fallback_example":
            metrics["manual_input_recommended"] = True
            warnings.append(
                "Datos de ejemplo utilizados: referencias aproximadas, no reales. "
                "Reemplaza los valores con informacion actualizada antes de tomar decisiones."
            )

        if ignored:
            warnings.append("Ignorados por rango: " + ", ".join(ignored) + ".")

    def _flag_missing_critical(self, metrics: Dict) -> None:
        warnings = metrics.setdefault("warnings", [])
        alt_map = {
            "roe": ["roa"],
            "roic": ["roe"],
            "operating_margin": ["gross_margin"],
            "net_margin": ["operating_margin"],
        }
        missing = []
        for field in self.critical_metrics:
            if metrics.get(field) is not None:
                continue
            alt_fields = alt_map.get(field, [])
            if any(metrics.get(alias) is not None for alias in alt_fields):
                continue
            missing.append(field)
        if missing:
            warnings.append(
                "Las APIs no devolvieron metricas criticas: "
                + ", ".join(missing)
                + ". Ingresa estos valores de forma manual si los tienes y vuelve a ejecutar."
            )
            metrics["manual_input_recommended"] = True

    def _classify_asset(self, metrics: Dict) -> AssetClassification:
        payload = {
            "ticker": metrics.get("ticker"),
            "quoteType": metrics.get("quoteType"),
            "type": metrics.get("type") or metrics.get("asset_type"),
            "company_name": metrics.get("company_name"),
            "sector": metrics.get("sector"),
            "category": metrics.get("category"),
            "primary_source": metrics.get("primary_source"),
        }
        cached = self.classification_cache.get(payload["ticker"])
        if cached:
            classification = AssetClassification(
                ticker=payload["ticker"],
                asset_type=cached.get("asset_type", "UNKNOWN"),
                raw_type=cached.get("raw_type"),
                type_label=cached.get("type_label", cached.get("asset_type", "Desconocido")),
                is_analyzable=cached.get("is_analyzable", False),
                needs_special_metrics=cached.get("needs_special_metrics", False),
                source=cached.get("source", payload.get("primary_source", "unknown")),
            )
        else:
            classification = self.classifier.classify(payload)
        ticker = payload["ticker"] or ""
        if ticker in ETF_REFERENCE and classification.asset_type != "ETF":
            classification.asset_type = "ETF"
            classification.type_label = "ETF"
            classification.needs_special_metrics = True
            classification.is_analyzable = False
        if classification.asset_type in {None, "", "UNKNOWN"}:
            if ticker and ticker.replace("^", "").isalpha() and len(ticker) <= 5:
                classification.asset_type = "EQUITY"
                classification.type_label = AssetClassifier.ASSET_NAMES.get("EQUITY", "Acción")
                classification.is_analyzable = True
                classification.needs_special_metrics = False
            else:
                classification.asset_type = "UNKNOWN"
                classification.type_label = "Desconocido"
                classification.is_analyzable = False
                classification.needs_special_metrics = False
        classification.is_analyzable = classification.asset_type == "EQUITY"
        classification.needs_special_metrics = classification.asset_type in AssetClassifier.SPECIAL_METRICS
        self._cache_classification(classification)
        return classification

    def _apply_asset_special_cases(self, metrics: Dict, classification) -> None:
        ticker = metrics.get("ticker", "")
        metrics.pop("analysis_note", None)
        fundamental_fields = [
            "pe_ratio",
            "peg_ratio",
            "price_to_book",
            "roe",
            "roic",
            "roa",
            "operating_margin",
            "net_margin",
            "gross_margin",
            "debt_to_equity",
            "current_ratio",
            "quick_ratio",
            "revenue_growth",
            "revenue_growth_qoq",
            "revenue_growth_5y",
            "earnings_growth",
            "earnings_growth_this_y",
            "earnings_growth_next_y",
            "earnings_growth_next_5y",
            "earnings_growth_qoq",
        ]

        if classification.asset_type == "ETF":
            profile = ETF_REFERENCE.get(ticker, {})
            metrics["is_etf"] = True

            metrics.setdefault("company_name", profile.get("fund_name", metrics.get("company_name")))
            metrics.setdefault("nav", profile.get("nav") or metrics.get("current_price"))
            metrics.setdefault("expense_ratio", profile.get("expense_ratio"))
            metrics.setdefault("ytd_return", profile.get("ytd_return"))
            metrics.setdefault("description", profile.get("description"))
            metrics.setdefault("category", profile.get("category"))
            metrics.setdefault("provider", profile.get("provider"))
            metrics.setdefault("index_tracked", profile.get("index"))
            metrics.setdefault("assets_under_management", profile.get("aum"))
            metrics.setdefault("dividend_yield", profile.get("dividend_yield"))
            metrics.setdefault("holdings_count", profile.get("holdings_count"))
            metrics.setdefault("analysis_method", profile.get("analysis_method", "etf_analysis"))

            metrics.setdefault("nav_currency", metrics.get("price_currency") or metrics.get("currency") or "USD")

            metrics["etf_profile"] = {
                "ticker": ticker,
                "nav_currency": metrics.get("nav_currency"),
                "category": metrics.get("category"),
                "provider": metrics.get("provider"),
                "description": metrics.get("description"),
                "data_source": profile.get("data_source", metrics.get("primary_source", "desconocida")),
                "index": profile.get("index"),
            }

            nav = metrics.get("nav")
            price = metrics.get("current_price")
            if nav and price:
                try:
                    premium = ((price - nav) / nav) * 100
                    metrics["premium_discount"] = round(premium, 2)
                except ZeroDivisionError:
                    metrics["premium_discount"] = None

            removed = []
            for field in fundamental_fields:
                if metrics.get(field) is not None:
                    metrics[field] = None
                    removed.append(field)

            warnings = metrics.setdefault("warnings", [])
            cleanup_terms = [
                "P/E",
                "PEG",
                "ROE",
                "ROIC",
                "Margen",
                "ROA",
                "Faltan métricas críticas",
            ]
            warnings[:] = [w for w in warnings if not any(term in w for term in cleanup_terms)]
            if removed:
                warnings.append(
                    "ETF detectado: métricas fundamentales tradicionales omitidas (" + ", ".join(removed) + ")."
                )
            else:
                warnings.append("ETF detectado: revise métricas de costos y rendimiento.")

            note = "ETF detectado: se muestra información informativa sin calificación RVC."
            metrics["analysis_note"] = note
            if note not in warnings:
                warnings.append(note)
            metrics["analysis_allowed"] = False
            return

        if classification.asset_type == "EQUITY":
            return

        warnings = metrics.setdefault("warnings", [])
        for field in fundamental_fields:
            if metrics.get(field) is not None:
                metrics[field] = None

        note = f"Tipo de activo detectado: {classification.type_label}. Actualmente solo se evalúan acciones individuales."
        metrics["analysis_note"] = note
        if note not in warnings:
            warnings.append(note)
        metrics["analysis_allowed"] = False

    def _attach_currency_metadata(self, metrics: Dict) -> None:
        warnings = metrics.setdefault("warnings", [])
        currency = metrics.get("price_currency") or metrics.get("currency")
        price = metrics.get("current_price")
        market_cap = metrics.get("market_cap")

        if not currency:
            if price is not None or market_cap is not None:
                warnings.append("Moneda no identificada; se asume USD para precios y market cap.")
            currency = "USD"

        currency = currency.upper()
        metrics["currency"] = currency
        metrics["price_currency"] = currency

        price_converted = {}
        market_cap_converted = {}
        exchange_rates = {}

        if price is not None:
            price_converted[currency] = round(float(price), 4)
        if market_cap is not None:
            market_cap_converted[currency] = float(market_cap)

        targets = ["USD", "EUR"]
        for target in targets:
            if currency == target:
                continue
            if not self.alpha_client.enabled:
                continue
            rate = self.alpha_client.get_exchange_rate(currency, target)
            if rate is None:
                continue
            exchange_rates[f"{currency}->{target}"] = rate
            if price is not None:
                price_converted[target] = round(float(price) * rate, 4)
            if market_cap is not None:
                market_cap_converted[target] = float(market_cap) * rate

        if not exchange_rates and currency not in {"USD", "EUR"} and self.alpha_client.enabled:
            warnings.append(f"No se pudo obtener tipo de cambio para {currency}.")

        if price_converted:
            metrics["price_converted"] = price_converted
        if market_cap_converted:
            metrics["market_cap_converted"] = market_cap_converted
        if exchange_rates:
            metrics["exchange_rates"] = exchange_rates

    def _is_suspicious_company_name(self, name: str) -> bool:
        normalized = name.strip().lower()
        if not normalized:
            return True
        suspicious_keywords = [
            "yahoo finance",
            "finance.yahoo.com",
            "captcha",
            "temporarily unavailable",
            "will be right back",
            "service unavailable",
        ]
        return any(keyword in normalized for keyword in suspicious_keywords)
    
    def _calculate_derived_metrics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calcula métricas derivadas a partir de métricas base.
        
        Mejora #3 (IMPROVEMENT_PLAN.md):
        - FCF Yield = Free Cash Flow / Market Cap * 100
        - EV/EBIT = Enterprise Value / EBIT (si no viene directamente)
        
        Args:
            metrics: Dict con métricas base
        
        Returns:
            Dict con métricas actualizadas (incluyendo derivadas)
        """
        # FCF Yield = FCF / Market Cap
        # Métrica clave para valoración TIER1 (mide retorno de caja por dólar invertido)
        if "free_cash_flow" in metrics and "market_cap" in metrics:
            fcf = metrics.get("free_cash_flow")
            mcap = metrics.get("market_cap")
            
            if fcf is not None and mcap is not None and mcap > 0:
                fcf_yield = (fcf / mcap) * 100
                metrics["fcf_yield"] = fcf_yield
                self.provenance["fcf_yield"] = "calculated:fcf/mcap"
                logger.debug(
                    "Métrica derivada: FCF Yield = %.2f%% (FCF: %s, MCap: %s)",
                    fcf_yield,
                    fcf,
                    mcap
                )
        
        # EV/EBIT = Enterprise Value / EBIT
        # Múltiplo preferido vs EV/EBITDA (no incluye D&A que puede distorsionar)
        if "enterprise_value" in metrics and "ebit" in metrics:
            ev = metrics.get("enterprise_value")
            ebit = metrics.get("ebit")
            
            if ev is not None and ebit is not None and abs(ebit) > 1e-6:
                ev_to_ebit = ev / ebit
                metrics["ev_to_ebit"] = ev_to_ebit
                self.provenance["ev_to_ebit"] = "calculated:ev/ebit"
                logger.debug(
                    "Métrica derivada: EV/EBIT = %.2f (EV: %s, EBIT: %s)",
                    ev_to_ebit,
                    ev,
                    ebit
                )
        
        # Mejora #6: Net Debt/EBITDA = (Total Debt - Cash) / EBITDA
        # Métrica clave para health TIER1 (mide apalancamiento real vs generación de caja)
        if "total_debt" in metrics and "cash_and_equivalents" in metrics and "ebitda" in metrics:
            total_debt = metrics.get("total_debt")
            cash = metrics.get("cash_and_equivalents")
            ebitda = metrics.get("ebitda")
            
            if total_debt is not None and cash is not None and ebitda is not None:
                net_debt = total_debt - cash
                
                if abs(ebitda) > 1e-6:  # Evitar división por 0
                    net_debt_to_ebitda = net_debt / ebitda
                    metrics["net_debt_to_ebitda"] = net_debt_to_ebitda
                    self.provenance["net_debt_to_ebitda"] = "calculated:(debt-cash)/ebitda"
                    logger.debug(
                        "Métrica derivada: Net Debt/EBITDA = %.2f (Debt: %s, Cash: %s, EBITDA: %s)",
                        net_debt_to_ebitda,
                        total_debt,
                        cash,
                        ebitda
                    )
        
        # Mejora #6: Interest Coverage = EBIT / Interest Expense
        # Métrica clave para health TIER1 (mide capacidad de pagar intereses)
        if "ebit" in metrics and "interest_expense" in metrics:
            ebit = metrics.get("ebit")
            interest = metrics.get("interest_expense")
            
            if ebit is not None and interest is not None and abs(interest) > 1e-6:
                interest_coverage = ebit / interest
                metrics["interest_coverage"] = interest_coverage
                self.provenance["interest_coverage"] = "calculated:ebit/interest"
                logger.debug(
                    "Métrica derivada: Interest Coverage = %.2fx (EBIT: %s, Interest: %s)",
                    interest_coverage,
                    ebit,
                    interest
                )
        
        return metrics

    def _calculate_dispersion(self, metric_name: str, source_results: List[SourceResult]) -> Optional[Dict[str, Any]]:
        """
        Calcula dispersión de una métrica entre múltiples fuentes.
        
        ESTRATEGIA:
        - Prioriza fuentes premium (AlphaVantage + TwelveData) si ambas proveen el dato
        - Calcula Coefficient of Variation (CV) para medir concordancia
        - Usa mediana como valor consolidado (robusto a outliers)
        - Ajusta confidence según dispersión (CV bajo = alta confianza)
        
        Args:
            metric_name: Nombre de la métrica (ej: "pe_ratio")
            source_results: Lista de resultados de todas las fuentes consultadas
        
        Returns:
            Dict con:
                - value: Valor consolidado (mediana)
                - sources: Lista de fuentes que proveyeron el dato
                - dispersion: Coefficient of Variation (0-100)
                - confidence_adj: Factor de ajuste de confianza (0.5-1.0)
                - quality: "PREMIUM_SOURCES", "MIXED_SOURCES", o "SINGLE_SOURCE"
            None si ninguna fuente tiene el dato
        """
        import numpy as np
        
        # Recolectar valores de todas las fuentes
        values = []
        sources = []
        
        for result in source_results:
            if metric_name in result.data and result.data[metric_name] is not None:
                values.append(result.data[metric_name])
                sources.append(result.source)
        
        # Sin datos
        if len(values) == 0:
            return None
        
        # Una sola fuente: sin dispersión calculable
        if len(values) == 1:
            return {
                "value": values[0],
                "sources": sources,
                "dispersion": 0.0,
                "confidence_adj": 1.0,
                "quality": "SINGLE_SOURCE"
            }
        
        # PRIORIZACIÓN: Si tenemos AlphaVantage + TwelveData, usar SOLO esas (ignorar Yahoo/scraping)
        premium_sources = ["alpha_vantage", "twelvedata"]
        premium_values = []
        premium_source_names = []
        
        for i, source in enumerate(sources):
            if source in premium_sources:
                premium_values.append(values[i])
                premium_source_names.append(source)
        
        # Si tenemos 2+ fuentes premium, usar solo esas (mejor calidad)
        if len(premium_values) >= 2:
            values = premium_values
            sources = premium_source_names
            quality = "PREMIUM_SOURCES"
        else:
            quality = "MIXED_SOURCES"
        
        # Valor consolidado: mediana (robusto a outliers)
        consolidated_value = float(np.median(values))
        
        # Dispersión: Coefficient of Variation (CV = std/mean * 100)
        mean_val = np.mean(values)
        std_val = np.std(values)
        
        # Evitar división por cero
        if abs(mean_val) < 1e-9:
            cv = 0.0
        else:
            cv = (std_val / abs(mean_val)) * 100
        
        # Ajuste de confidence según dispersión
        # CV bajo = fuentes concuerdan → alta confianza
        # CV alto = fuentes discrepan → baja confianza
        if cv < 5.0:
            confidence_adj = 1.0     # Concordancia perfecta (AlphaVantage ≈ TwelveData)
        elif cv < 10.0:
            confidence_adj = 0.95    # Muy buena concordancia
        elif cv < 20.0:
            confidence_adj = 0.85    # Aceptable
        elif cv < 40.0:
            confidence_adj = 0.70    # Discrepante (posible problema con una fuente)
        else:
            confidence_adj = 0.50    # Muy discrepante (datos sospechosos)
        
        return {
            "value": consolidated_value,
            "sources": sources,
            "dispersion": float(cv),
            "confidence_adj": float(confidence_adj),
            "quality": quality
        }
