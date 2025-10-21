#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test rápido del nuevo sistema de scoring.
Valida que el InvestmentScorer funciona correctamente con datos de ejemplo.
"""

import sys
import io

# Configurar encoding UTF-8 para Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from scoring_engine import InvestmentScorer


def test_sweet_spot():
    """Empresa con alta calidad y buen precio → SWEET SPOT"""
    scorer = InvestmentScorer()

    # Empresa tipo TSM: Excelente calidad + Precio razonable
    metrics = {
        # Calidad
        "roe": 31.2,
        "roic": 24.5,
        "operating_margin": 42.1,
        "net_margin": 36.8,

        # Valoración
        "pe_ratio": 22.1,
        "peg_ratio": 0.92,
        "price_to_book": 6.8,

        # Salud
        "debt_to_equity": 0.25,
        "current_ratio": 2.5,
        "quick_ratio": 2.0,

        # Crecimiento
        "revenue_growth_5y": 18.5,
        "earnings_growth_this_y": 20.3,

        # Metadata
        "data_completeness": 100,
        "company_name": "Test Company A",
    }

    result = scorer.calculate_all_scores(metrics)

    print("=" * 60)
    print("TEST 1: SWEET SPOT (Alta calidad + Buen precio)")
    print("=" * 60)
    print(f"Calidad:        {result['quality_score']:.2f}/100")
    print(f"Valoración:     {result['valuation_score']:.2f}/100")
    print(f"Salud:          {result['financial_health_score']:.2f}/100")
    print(f"Crecimiento:    {result['growth_score']:.2f}/100")
    print(f"")
    print(f"INVERSIÓN:      {result['investment_score']:.2f}/100 ⭐")
    print(f"Categoría:      {result['category']['emoji']} {result['category']['name']}")
    print(f"Descripción:    {result['category']['desc']}")
    print(f"Recomendación:  {result['recommendation']}")
    print(f"Confianza:      {result['confidence_level']}")
    print("")

    # Validaciones
    assert result['quality_score'] >= 80, "Calidad debería ser alta"
    assert result['valuation_score'] >= 60, "Valoración debería ser buena"
    assert result['investment_score'] >= 70, "Score de inversión debería ser alto"
    assert result['category']['name'] == 'SWEET SPOT', "Debería ser SWEET SPOT"
    print("✅ TEST 1 PASADO\n")


def test_premium_cara():
    """Empresa excelente pero cara → CARA o PREMIUM"""
    scorer = InvestmentScorer()

    # Empresa tipo NVDA: Calidad excepcional pero valoración elevada
    metrics = {
        # Calidad excepcional
        "roe": 109.4,
        "roic": 76.6,
        "operating_margin": 58.1,
        "net_margin": 52.4,

        # Valoración cara
        "pe_ratio": 51.96,
        "peg_ratio": 1.43,
        "price_to_book": 44.39,

        # Salud excelente
        "debt_to_equity": 0.18,
        "current_ratio": 3.5,
        "quick_ratio": 3.2,

        # Crecimiento explosivo
        "revenue_growth_5y": 35.8,
        "earnings_growth_this_y": 45.2,

        # Metadata
        "data_completeness": 100,
        "company_name": "Test Company B",
    }

    result = scorer.calculate_all_scores(metrics)

    print("=" * 60)
    print("TEST 2: EMPRESA CARA (Alta calidad pero precio elevado)")
    print("=" * 60)
    print(f"Calidad:        {result['quality_score']:.2f}/100")
    print(f"Valoración:     {result['valuation_score']:.2f}/100")
    print(f"Salud:          {result['financial_health_score']:.2f}/100")
    print(f"Crecimiento:    {result['growth_score']:.2f}/100")
    print(f"")
    print(f"INVERSIÓN:      {result['investment_score']:.2f}/100 ⭐")
    print(f"Categoría:      {result['category']['emoji']} {result['category']['name']}")
    print(f"Descripción:    {result['category']['desc']}")
    print(f"Recomendación:  {result['recommendation']}")
    print(f"Confianza:      {result['confidence_level']}")
    print("")

    # Validaciones
    assert result['quality_score'] >= 90, "Calidad debería ser excepcional"
    assert result['valuation_score'] < 60, "Valoración debería ser baja (cara)"
    assert result['investment_score'] < 75, "Score de inversión medio (no comprar ahora)"
    assert result['category']['name'] in ['CARA', 'PREMIUM'], "Debería ser CARA o PREMIUM"
    print("✅ TEST 2 PASADO\n")


def test_evitar():
    """Empresa con baja calidad → EVITAR"""
    scorer = InvestmentScorer()

    # Empresa tipo INTC: Calidad deteriorada
    metrics = {
        # Calidad baja
        "roe": -2.3,
        "roic": -1.8,
        "operating_margin": 2.1,
        "net_margin": -5.2,

        # Valoración
        "pe_ratio": -15.2,  # Negativo por pérdidas
        "peg_ratio": None,
        "price_to_book": 1.2,

        # Salud comprometida
        "debt_to_equity": 0.45,
        "current_ratio": 1.8,
        "quick_ratio": 1.5,

        # Crecimiento negativo
        "revenue_growth_5y": -2.5,
        "earnings_growth_this_y": -15.8,

        # Metadata
        "data_completeness": 85,
        "company_name": "Test Company C",
    }

    result = scorer.calculate_all_scores(metrics)

    print("=" * 60)
    print("TEST 3: EVITAR (Baja calidad)")
    print("=" * 60)
    print(f"Calidad:        {result['quality_score']:.2f}/100")
    print(f"Valoración:     {result['valuation_score']:.2f}/100")
    print(f"Salud:          {result['financial_health_score']:.2f}/100")
    print(f"Crecimiento:    {result['growth_score']:.2f}/100")
    print(f"")
    print(f"INVERSIÓN:      {result['investment_score']:.2f}/100 ⭐")
    print(f"Categoría:      {result['category']['emoji']} {result['category']['name']}")
    print(f"Descripción:    {result['category']['desc']}")
    print(f"Recomendación:  {result['recommendation']}")
    print(f"Confianza:      {result['confidence_level']}")
    print("")

    # Validaciones
    assert result['quality_score'] < 40, "Calidad debería ser muy baja"
    assert result['investment_score'] < 50, "Score de inversión bajo"
    assert 'NO COMPRAR' in result['recommendation'] or 'EVITAR' in result['recommendation'], \
        "Debería recomendar NO COMPRAR"
    print("✅ TEST 3 PASADO\n")


def test_valor():
    """Empresa con calidad decente y buen precio → VALOR"""
    scorer = InvestmentScorer()

    # Empresa tipo COST: Calidad sólida + Precio razonable
    metrics = {
        # Calidad sólida pero no excepcional
        "roe": 25.8,
        "roic": 18.2,
        "operating_margin": 4.2,
        "net_margin": 3.1,

        # Valoración atractiva
        "pe_ratio": 28.4,
        "peg_ratio": 2.35,
        "price_to_book": 12.5,

        # Salud buena
        "debt_to_equity": 0.55,
        "current_ratio": 1.1,
        "quick_ratio": 0.8,

        # Crecimiento moderado
        "revenue_growth_5y": 12.3,
        "earnings_growth_this_y": 8.7,

        # Metadata
        "data_completeness": 100,
        "company_name": "Test Company D",
    }

    result = scorer.calculate_all_scores(metrics)

    print("=" * 60)
    print("TEST 4: VALOR (Calidad decente + Precio razonable)")
    print("=" * 60)
    print(f"Calidad:        {result['quality_score']:.2f}/100")
    print(f"Valoración:     {result['valuation_score']:.2f}/100")
    print(f"Salud:          {result['financial_health_score']:.2f}/100")
    print(f"Crecimiento:    {result['growth_score']:.2f}/100")
    print(f"")
    print(f"INVERSIÓN:      {result['investment_score']:.2f}/100 ⭐")
    print(f"Categoría:      {result['category']['emoji']} {result['category']['name']}")
    print(f"Descripción:    {result['category']['desc']}")
    print(f"Recomendación:  {result['recommendation']}")
    print(f"Confianza:      {result['confidence_level']}")
    print("")

    # Validaciones
    assert 60 <= result['quality_score'] < 85, "Calidad debería ser decente"
    assert result['investment_score'] >= 45, "Score de inversión al menos medio"
    print("✅ TEST 4 PASADO\n")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🧪 PRUEBAS DEL SISTEMA DE SCORING")
    print("=" * 60 + "\n")

    try:
        test_sweet_spot()
        test_premium_cara()
        test_evitar()
        test_valor()

        print("=" * 60)
        print("✅ TODAS LAS PRUEBAS PASARON EXITOSAMENTE")
        print("=" * 60)
        print("\nEl sistema de scoring está funcionando correctamente! 🎉")

    except AssertionError as e:
        print(f"\n❌ ERROR: {e}")
        print("Una o más pruebas fallaron.")
    except Exception as e:
        print(f"\n❌ ERROR INESPERADO: {e}")
        import traceback
        traceback.print_exc()
