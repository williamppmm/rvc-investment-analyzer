#!/usr/bin/env python3
"""
Tests for the scoring and analysis engine.

Consolidates:
  - test_scoring.py         → InvestmentScorer categories
  - test_tier1_health.py    → TIER1/TIER2 health scoring
  - test_tier1_valuation.py → TIER1/TIER2 valuation scoring
  - test_metric_normalizer.py → MetricNormalizer
  - test_sector_relative.py   → Sector-relative (z-score) scoring
"""

import pytest
from analyzers import EquityAnalyzer
from analyzers.sector_benchmarks import SectorNormalizer
from metric_normalizer import MetricNormalizer
from scoring_engine import InvestmentScorer


# ---------------------------------------------------------------------------
# InvestmentScorer – category classification
# ---------------------------------------------------------------------------

class TestInvestmentScorer:
    def setup_method(self):
        self.scorer = InvestmentScorer()

    def test_sweet_spot(self):
        metrics = {
            "roe": 31.2, "roic": 24.5, "operating_margin": 42.1, "net_margin": 36.8,
            "pe_ratio": 22.1, "peg_ratio": 0.92, "price_to_book": 6.8,
            "debt_to_equity": 0.25, "current_ratio": 2.5, "quick_ratio": 2.0,
            "revenue_growth_5y": 18.5, "earnings_growth_this_y": 20.3,
            "data_completeness": 100, "company_name": "Test Company A",
        }
        result = self.scorer.calculate_all_scores(metrics)

        assert result["quality_score"] >= 80
        assert result["valuation_score"] >= 60
        assert result["investment_score"] >= 70
        assert result["category"]["name"] == "SWEET SPOT"

    def test_premium_cara(self):
        metrics = {
            "roe": 109.4, "roic": 76.6, "operating_margin": 58.1, "net_margin": 52.4,
            "pe_ratio": 51.96, "peg_ratio": 1.43, "price_to_book": 44.39,
            "debt_to_equity": 0.18, "current_ratio": 3.5, "quick_ratio": 3.2,
            "revenue_growth_5y": 35.8, "earnings_growth_this_y": 45.2,
            "data_completeness": 100, "company_name": "Test Company B",
        }
        result = self.scorer.calculate_all_scores(metrics)

        assert result["quality_score"] >= 90
        assert result["valuation_score"] < 60
        assert result["investment_score"] < 75
        assert result["category"]["name"] in ("CARA", "PREMIUM")

    def test_evitar(self):
        metrics = {
            "roe": -2.3, "roic": -1.8, "operating_margin": 2.1, "net_margin": -5.2,
            "pe_ratio": -15.2, "peg_ratio": None, "price_to_book": 1.2,
            "debt_to_equity": 0.45, "current_ratio": 1.8, "quick_ratio": 1.5,
            "revenue_growth_5y": -2.5, "earnings_growth_this_y": -15.8,
            "data_completeness": 85, "company_name": "Test Company C",
        }
        result = self.scorer.calculate_all_scores(metrics)

        assert result["quality_score"] < 40
        assert result["investment_score"] < 50
        assert "NO COMPRAR" in result["recommendation"] or "EVITAR" in result["recommendation"]

    def test_valor(self):
        metrics = {
            "roe": 25.8, "roic": 18.2, "operating_margin": 4.2, "net_margin": 3.1,
            "pe_ratio": 28.4, "peg_ratio": 2.35, "price_to_book": 12.5,
            "debt_to_equity": 0.55, "current_ratio": 1.1, "quick_ratio": 0.8,
            "revenue_growth_5y": 12.3, "earnings_growth_this_y": 8.7,
            "data_completeness": 100, "company_name": "Test Company D",
        }
        result = self.scorer.calculate_all_scores(metrics)

        assert 60 <= result["quality_score"] < 85
        assert result["investment_score"] >= 45


# ---------------------------------------------------------------------------
# TIER1/TIER2 Health scoring
# ---------------------------------------------------------------------------

class TestTier1Health:
    def setup_method(self):
        self.analyzer = EquityAnalyzer()

    def test_tier1_health(self):
        metrics = {
            "net_debt_to_ebitda": 1.2, "interest_coverage": 12.0,
            "total_debt": 500_000_000, "cash_and_equivalents": 200_000_000,
            "ebitda": 250_000_000, "ebit": 180_000_000, "interest_expense": 15_000_000,
        }
        health = self.analyzer.calculate_all_scores(metrics)["breakdown"]["health"]

        assert health["score"] >= 85
        assert health.get("method") == "tier1_health"
        assert health.get("tier") == "TIER1"

    def test_tier2_health_fallback(self):
        metrics = {"debt_to_equity": 0.5, "current_ratio": 2.0, "quick_ratio": 1.5}
        health = self.analyzer.calculate_all_scores(metrics)["breakdown"]["health"]

        assert health.get("method") == "tier2_health"
        assert health.get("tier") == "TIER2"

    def test_net_debt_calculation(self):
        from data_agent import DataAgent
        agent = DataAgent()

        base = {
            "total_debt": 1_000_000_000,
            "cash_and_equivalents": 400_000_000,
            "ebitda": 200_000_000,
        }
        derived = agent._calculate_derived_metrics(base.copy())
        expected = (1_000_000_000 - 400_000_000) / 200_000_000  # 3.0

        assert "net_debt_to_ebitda" in derived
        assert abs(derived["net_debt_to_ebitda"] - expected) < 0.01

    def test_interest_coverage_calculation(self):
        from data_agent import DataAgent
        agent = DataAgent()

        base = {"ebit": 180_000_000, "interest_expense": 15_000_000}
        derived = agent._calculate_derived_metrics(base.copy())
        expected = 180_000_000 / 15_000_000  # 12.0

        assert "interest_coverage" in derived
        assert abs(derived["interest_coverage"] - expected) < 0.01

    def test_net_cash_company(self):
        metrics = {"net_debt_to_ebitda": -0.5, "interest_coverage": 50.0}
        health = self.analyzer.calculate_all_scores(metrics)["breakdown"]["health"]

        assert health["score"] >= 95
        assert health.get("method") == "tier1_health"

    def test_comparison_tier1_vs_tier2(self):
        metrics_full = {
            "net_debt_to_ebitda": 2.5, "interest_coverage": 6.0,
            "debt_to_equity": 1.2, "current_ratio": 1.8, "quick_ratio": 1.3,
        }
        health_t1 = self.analyzer.calculate_all_scores(metrics_full)["breakdown"]["health"]
        assert health_t1.get("method") == "tier1_health"

        metrics_t2 = {"debt_to_equity": 1.2, "current_ratio": 1.8, "quick_ratio": 1.3}
        health_t2 = self.analyzer.calculate_all_scores(metrics_t2)["breakdown"]["health"]
        assert health_t2.get("method") == "tier2_health"

    def test_high_leverage(self):
        metrics = {"net_debt_to_ebitda": 6.5, "interest_coverage": 1.2}
        health = self.analyzer.calculate_all_scores(metrics)["breakdown"]["health"]

        assert health["score"] <= 50

    def test_derived_metrics_integration(self):
        from data_agent import DataAgent
        agent = DataAgent()

        base = {
            "total_debt": 800_000_000, "cash_and_equivalents": 300_000_000,
            "ebitda": 250_000_000, "ebit": 200_000_000, "interest_expense": 20_000_000,
        }
        full = agent._calculate_derived_metrics(base.copy())
        health = self.analyzer.calculate_all_scores(full)["breakdown"]["health"]

        assert "net_debt_to_ebitda" in full
        assert "interest_coverage" in full
        assert health.get("method") == "tier1_health"


# ---------------------------------------------------------------------------
# TIER1/TIER2 Valuation scoring
# ---------------------------------------------------------------------------

class TestTier1Valuation:
    def setup_method(self):
        self.analyzer = EquityAnalyzer()

    def test_tier1_valuation(self):
        metrics = {
            "current_price": 150.0, "market_cap": 2.5e12,
            "ev_to_ebit": 10.5, "fcf_yield": 8.5,
            "free_cash_flow": 2.125e11, "enterprise_value": 2.6e12,
            "ebit": 2.476e11, "pe_ratio": 28.5, "roe": 45.2,
        }
        scores = self.analyzer.calculate_all_scores(metrics)
        breakdown = scores["breakdown"]["valuation"]

        assert breakdown.get("tier") == "TIER1"
        assert breakdown.get("method") == "cash_flow_based"
        assert scores["valuation_score"] > 70

    def test_tier2_valuation_fallback(self):
        metrics = {
            "current_price": 150.0, "market_cap": 2.5e12,
            "pe_ratio": 18.5, "peg_ratio": 1.2, "price_to_book": 8.5, "roe": 45.2,
        }
        scores = self.analyzer.calculate_all_scores(metrics)
        breakdown = scores["breakdown"]["valuation"]

        assert breakdown.get("tier") == "TIER2"
        assert breakdown.get("method") == "traditional_multiples"

    def test_tier1_negative_fcf(self):
        metrics = {
            "current_price": 50.0, "market_cap": 1e12,
            "ev_to_ebit": 25.0, "fcf_yield": -5.2,
            "free_cash_flow": -5.2e10, "enterprise_value": 1.1e12,
            "ebit": 4.4e10, "roe": 12.0,
        }
        scores = self.analyzer.calculate_all_scores(metrics)
        breakdown = scores["breakdown"]["valuation"]

        assert breakdown.get("tier") == "TIER1"
        assert scores["valuation_score"] < 30

    def test_derived_fcf_yield_and_ev_ebit(self):
        from data_agent import DataAgent
        agent = DataAgent()

        base = {
            "ticker": "TEST",
            "free_cash_flow": 1e11, "market_cap": 1e12,
            "enterprise_value": 1.2e12, "ebit": 1.2e11,
        }
        derived = agent._calculate_derived_metrics(base.copy())

        assert "fcf_yield" in derived
        assert abs(derived["fcf_yield"] - 10.0) < 0.01

        assert "ev_to_ebit" in derived
        assert abs(derived["ev_to_ebit"] - 10.0) < 0.01


# ---------------------------------------------------------------------------
# MetricNormalizer
# ---------------------------------------------------------------------------

class TestMetricNormalizer:
    def setup_method(self):
        self.normalizer = MetricNormalizer()

    def test_ttm_priority(self):
        result = self.normalizer.normalize_metric(
            "roe", {"roe_ttm": 22.3, "roe_mry": 21.8, "roe_5y": 19.5}
        )
        assert result["value"] == 22.3
        assert result["period"] == "TTM"

    def test_no_suffix_assumes_ttm(self):
        result = self.normalizer.normalize_metric("roe", {"roe": 20.0})
        assert result["period"] == "TTM (assumed)"

    def test_batch_normalization(self):
        batch_input = {
            "roe_ttm": 22.3,
            "revenue_growth_mrq": 15.2,
            "debt_to_equity_mry": 0.35,
        }
        result = self.normalizer.normalize_metrics_batch(
            batch_input, ["roe", "revenue_growth", "debt_to_equity", "missing_metric"]
        )

        meta = result["_normalization_metadata"]
        assert meta["normalized_count"] == 3
        assert "missing_metric" in meta["failed_metrics"]

    def test_currency_conversion(self):
        result = self.normalizer.normalize_currency(100, "EUR")
        assert result["to_currency"] == "USD"
        assert result["value"] == 108.0

    def test_integration_with_equity_analyzer(self):
        analyzer = EquityAnalyzer()
        metrics = {
            "current_price": 150.0, "market_cap": 2.5e12,
            "pe_ratio_ttm": 28.5, "roe_ttm": 45.2, "roic_ttm": 38.5,
            "operating_margin_ttm": 30.5, "net_margin_ttm": 25.3,
            "debt_to_equity_mry": 1.72, "current_ratio_mry": 1.07,
            "revenue_growth_mrq": 8.5, "earnings_growth_ttm": 12.3,
        }
        scores = analyzer.calculate_all_scores(metrics)
        meta = scores.get("normalization_metadata", {})

        assert "normalization_metadata" in scores
        assert meta.get("normalized_count", 0) > 0


# ---------------------------------------------------------------------------
# Sector-relative (z-score) scoring
# ---------------------------------------------------------------------------

class TestSectorRelative:
    def setup_method(self):
        self.normalizer = SectorNormalizer()
        self.analyzer = EquityAnalyzer()

    def test_z_score_tech(self):
        z = self.normalizer.get_z_score(35.0, "roe", "Technology")
        score = self.normalizer.z_to_score(z)

        assert abs(z - 1.53) < 0.01
        assert score == 85

    def test_z_score_utilities(self):
        z = self.normalizer.get_z_score(12.0, "roe", "Utilities")
        score = self.normalizer.z_to_score(z)

        assert abs(z - 0.78) < 0.01
        assert score == 70

    def test_normalize_metric_metadata(self):
        result = self.normalizer.normalize_metric(35.0, "roe", "Technology")
        assert "sector_mean" in result
        assert "sector_std" in result

    def test_equity_analyzer_uses_sector_relative(self):
        metrics = {
            "sector": "Technology",
            "roe": 35.0, "roic": 28.0, "operating_margin": 35.0, "net_margin": 26.0,
            "current_price": 150.0, "market_cap": 2.5e12,
        }
        scores = self.analyzer.calculate_all_scores(metrics)
        breakdown = scores["breakdown"]["quality"]

        assert breakdown.get("method") == "sector_relative"
        assert breakdown.get("sector") == "Technology"
        assert scores["quality_score"] >= 80

    def test_fallback_to_absolute_without_sector(self):
        metrics = {
            "roe": 35.0, "roic": 28.0, "operating_margin": 35.0, "net_margin": 26.0,
            "current_price": 150.0, "market_cap": 2.5e12,
        }
        breakdown = self.analyzer.calculate_all_scores(metrics)["breakdown"]["quality"]
        assert breakdown.get("method") == "absolute"

    def test_extract_primary_sector(self):
        cases = [
            ("Technology - Semiconductors", "Technology"),
            ("Healthcare - Pharmaceuticals", "Healthcare"),
            ("Consumer Discretionary", "Consumer Discretionary"),
            ("Utilities", "Utilities"),
        ]
        for raw, expected in cases:
            assert self.analyzer._extract_primary_sector(raw) == expected

    def test_sector_relative_vs_absolute(self):
        metrics_util = {
            "sector": "Utilities",
            "roe": 12.0, "roic": 8.0, "operating_margin": 15.0, "net_margin": 10.0,
            "current_price": 50.0, "market_cap": 5e11,
        }
        self.analyzer.use_sector_relative = False
        score_abs = self.analyzer.calculate_all_scores(metrics_util)["quality_score"]

        self.analyzer.use_sector_relative = True
        score_rel = self.analyzer.calculate_all_scores(metrics_util)["quality_score"]

        # Sector-relative should give higher score for a utility with low-but-normal ROE
        assert score_rel > score_abs

    def test_sector_list_count(self):
        sectors = self.normalizer.get_sector_list()
        assert len(sectors) == 11

    def test_normalizer_stats(self):
        self.normalizer.normalize_metric(35.0, "roe", "Technology")
        stats = self.normalizer.get_stats()
        assert stats["total_normalized"] > 0