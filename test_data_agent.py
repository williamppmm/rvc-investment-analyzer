#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test rápido del data_agent para verificar que obtiene current_price y market_cap.
"""

import sys
import io

# Configurar encoding UTF-8 para Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from data_agent import DataAgent

def test_data_agent():
    agent = DataAgent()

    # Probar con varios tickers
    tickers = ["AMD", "NVDA", "TSM", "AAPL", "INTC"]

    print("=" * 60)
    print("🧪 TEST: Data Agent - Current Price & Market Cap")
    print("=" * 60)
    print("")

    for ticker in tickers:
        print(f"📊 Ticker: {ticker}")
        print("-" * 60)

        metrics = agent.fetch_financial_data(ticker)

        if metrics:
            print(f"✅ Datos obtenidos")
            print(f"   Company Name:   {metrics.get('company_name', 'N/A')}")
            print(f"   Sector:         {metrics.get('sector', 'N/A')}")
            print(f"   Current Price:  ${metrics.get('current_price', 'N/A')}")
            print(f"   Market Cap:     ${metrics.get('market_cap', 'N/A'):,.0f}" if metrics.get('market_cap') else "   Market Cap:     N/A")
            print(f"   P/E Ratio:      {metrics.get('pe_ratio', 'N/A')}")
            print(f"   ROE:            {metrics.get('roe', 'N/A')}%")
            print(f"   Source:         {metrics.get('primary_source', 'N/A')}")
            print(f"   Completeness:   {metrics.get('data_completeness', 0)}%")
        else:
            print(f"❌ No se obtuvieron datos")

        print("")

    print("=" * 60)
    print("✅ TEST COMPLETADO")
    print("=" * 60)

if __name__ == "__main__":
    test_data_agent()
