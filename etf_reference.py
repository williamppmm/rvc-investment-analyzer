"""
Static ETF reference data for profiles not covered by fundamental APIs.
"""

from __future__ import annotations

from typing import Dict, Any

ETF_REFERENCE: Dict[str, Dict[str, Any]] = {
    "IAU": {
        "asset_type": "ETF",
        "fund_name": "iShares Gold Trust",
        "nav": 79.60,
        "expense_ratio": 0.25,
        "description": "Sigue el precio del oro físico y mantiene lingotes en bóveda.",
        "ytd_return": 61.50,
        "category": "Commodity - Precious Metals",
        "data_source": "Snapshot manual 2025-10-20",
        "provider": "BlackRock",
        "analysis_method": "etf_analysis",
        "aum": 32000000000,
        "dividend_yield": 0.00,
        "holdings_count": 1,
        "index": "Precio spot del oro",
    },
    "VOO": {
        "asset_type": "ETF",
        "fund_name": "Vanguard S&P 500 ETF",
        "nav": 617.10,
        "expense_ratio": 0.03,
        "description": "Replica el índice S&P 500 con una estructura de costos muy baja.",
        "ytd_return": 18.40,
        "category": "Large Blend",
        "data_source": "Snapshot manual 2025-10-20",
        "provider": "Vanguard",
        "analysis_method": "etf_analysis",
        "aum": 560000000000,
        "dividend_yield": 1.45,
        "holdings_count": 500,
        "index": "S&P 500",
    },
    "VNQ": {
        "asset_type": "ETF",
        "fund_name": "Vanguard Real Estate ETF",
        "nav": 105.00,
        "expense_ratio": 0.12,
        "description": "Exposición diversificada al sector inmobiliario estadounidense listando REITs.",
        "ytd_return": 9.20,
        "category": "Real Estate",
        "data_source": "Snapshot manual 2025-10-20",
        "provider": "Vanguard",
        "analysis_method": "etf_analysis",
        "aum": 36000000000,
        "dividend_yield": 3.98,
        "holdings_count": 160,
        "index": "MSCI US Investable Market Real Estate",
    },
}
