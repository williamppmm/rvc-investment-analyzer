#!/usr/bin/env python3
"""
RVC Analyzer - Flask application orchestrating the IA agent and RVC calculator.
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv

from data_agent import DataAgent, METRIC_SCHEMA_VERSION
from etf_analyzer import ETFAnalyzer
from rvc_calculator import RVCCalculator
from scoring_engine import InvestmentScorer
from investment_calculator import InvestmentCalculator


load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "cache.db"


app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("RVC_SECRET_KEY", "change-me")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("rvc_app")

data_agent = DataAgent()
rvc_calculator = RVCCalculator()
investment_scorer = InvestmentScorer()
etf_analyzer = ETFAnalyzer()
investment_calculator = InvestmentCalculator()


def pick_metric(metrics: Dict[str, Any], keys: Iterable[str], default: Optional[float] = None):
    """Return the first non-None metric value following the provided priority order."""
    for key in keys:
        value = metrics.get(key)
        if value is not None:
            return value
    return default


def init_database() -> None:
    """Ensure sqlite cache schema exists."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS financial_cache (
                ticker TEXT PRIMARY KEY,
                data TEXT,
                last_updated TEXT,
                source TEXT
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS rvc_scores (
                ticker TEXT PRIMARY KEY,
                score REAL,
                classification TEXT,
                breakdown TEXT,
                last_calculated TEXT
            )
            """
        )
        conn.commit()


def get_cached_data(ticker: str) -> Optional[Dict[str, Any]]:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT data, last_updated, source
            FROM financial_cache
            WHERE ticker = ?
            """,
            (ticker,),
        )
        row = cursor.fetchone()
    if not row:
        return None
    return {"data": row[0], "last_updated": row[1], "source": row[2]}


def cache_expired(last_updated: str, days: int = 7) -> bool:
    dt = datetime.fromisoformat(last_updated)
    return datetime.now() - dt > timedelta(days=days)


def save_cache(ticker: str, metrics: Dict[str, Any]) -> None:
    payload = json.dumps(metrics)
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO financial_cache (ticker, data, last_updated, source)
            VALUES (?, ?, ?, ?)
            """,
            (
                ticker,
                payload,
                datetime.now().isoformat(timespec="seconds"),
                metrics.get("source", "web"),
            ),
        )
        conn.commit()


def save_score(ticker: str, score: Dict[str, Any]) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO rvc_scores (ticker, score, classification, breakdown, last_calculated)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                ticker,
                score["total_score"],
                score["classification"],
                json.dumps(score["breakdown"]),
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        conn.commit()


def prepare_analysis_response(
    ticker: str,
    metrics: Dict[str, Any],
    save_scores_flag: bool = True,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    asset_type = metrics.get("asset_type")
    analysis_allowed = metrics.get("analysis_allowed", False)
    etf_summary: Optional[Dict[str, Any]] = None

    if asset_type == "EQUITY" and analysis_allowed:
        investment_scores = investment_scorer.calculate_all_scores(metrics)
        rvc_score = rvc_calculator.calculate_score(metrics)
    elif asset_type == "ETF":
        investment_scores = None
        etf_summary = etf_analyzer.analyze(metrics)
        breakdown_stub = {
            "valoracion": {"score": None, "metrics_used": []},
            "calidad": {"score": None, "metrics_used": []},
            "salud": {"score": None, "metrics_used": []},
            "crecimiento": {"score": None, "metrics_used": []},
        }
        rvc_score = {
            "total_score": None,
            "classification": "ETF (informativo)",
            "recommendation": metrics.get("analysis_note")
            or "Instrumento ETF: revise métricas específicas del fondo.",
            "breakdown": breakdown_stub,
            "data_completeness": metrics.get("data_completeness", 0),
            "confidence_level": "Media",
        }
    else:
        investment_scores = None
        breakdown_stub = {
            "valoracion": {"score": None, "metrics_used": []},
            "calidad": {"score": None, "metrics_used": []},
            "salud": {"score": None, "metrics_used": []},
            "crecimiento": {"score": None, "metrics_used": []},
        }
        rvc_score = {
            "total_score": None,
            "classification": metrics.get("asset_type_label", "No evaluado"),
            "recommendation": metrics.get("analysis_note")
            or "Actualmente solo se evalúan acciones individuales.",
            "breakdown": breakdown_stub,
            "data_completeness": metrics.get("data_completeness", 0),
            "confidence_level": "Baja",
        }

    if analysis_allowed and save_scores_flag:
        save_score(ticker, rvc_score)

    response = {
        "ticker": ticker,
        "company_name": metrics.get("company_name", "N/A"),
        "sector": metrics.get("sector", "Desconocido"),
        "currency": metrics.get("currency"),
        "price_currency": metrics.get("price_currency"),
        "price_converted": metrics.get("price_converted"),
        "market_cap_converted": metrics.get("market_cap_converted"),
        "exchange_rates": metrics.get("exchange_rates"),
        "asset_type": asset_type,
        "asset_type_label": metrics.get("asset_type_label"),
        "analysis_allowed": analysis_allowed,
        "analysis_note": metrics.get("analysis_note"),
        "metrics": metrics,
        "rvc_score": rvc_score,
        "investment_scores": investment_scores,
        "etf_summary": etf_summary,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }
    if extra:
        response.update(extra)
    return response


@app.route("/")
def index():
    return render_template("index.html", active_page="home")


@app.route("/analyze", methods=["POST"])
def analyze():
    payload = request.get_json(silent=True) or {}
    ticker = (payload.get("ticker") or "").strip().upper()
    if not ticker:
        return jsonify({"error": "Por favor ingrese un ticker"}), 400

    logger.info("Analyzing ticker %s", ticker)
    cached = get_cached_data(ticker)
    metrics: Optional[Dict[str, Any]] = None
    if cached and not cache_expired(cached["last_updated"]):
        logger.info("Using cached metrics for %s", ticker)
        metrics = json.loads(cached["data"])
        if metrics and not metrics.get("asset_type"):
            logger.info("Cached metrics desactualizados para %s, recargando", ticker)
            metrics = data_agent.fetch_financial_data(ticker)
            if metrics:
                save_cache(ticker, metrics)
        elif metrics and metrics.get("schema_version") != METRIC_SCHEMA_VERSION:
            logger.info("Actualizando métricas a esquema vigente para %s", ticker)
            metrics = data_agent.fetch_financial_data(ticker)
            if metrics:
                save_cache(ticker, metrics)
    else:
        logger.info("Fetching fresh metrics for %s", ticker)
        metrics = data_agent.fetch_financial_data(ticker)
        if metrics:
            save_cache(ticker, metrics)

    if not metrics:
        return jsonify({"error": f"No se encontraron datos suficientes para {ticker}"}), 404

    response = prepare_analysis_response(ticker, metrics)
    return jsonify(response)


@app.route("/api/manual-metrics", methods=["POST"])
def manual_metrics():
    payload = request.get_json(silent=True) or {}
    ticker = (payload.get("ticker") or "").strip().upper()
    overrides = payload.get("overrides") or {}

    if not ticker:
        return jsonify({"error": "Debe proporcionar un ticker"}), 400
    if not isinstance(overrides, dict) or not overrides:
        return jsonify({"error": "Debe proporcionar al menos una métrica a ajustar"}), 400

    logger.info("Manual override request for %s", ticker)
    cached = get_cached_data(ticker)
    metrics: Optional[Dict[str, Any]] = None
    if cached:
        try:
            metrics = json.loads(cached["data"])
        except (TypeError, json.JSONDecodeError):
            metrics = None

    if not metrics:
        logger.info("No cached metrics for %s, attempting fresh fetch before manual overrides", ticker)
        metrics = data_agent.fetch_financial_data(ticker)
        if not metrics:
            metrics = {"ticker": ticker, "warnings": [], "provenance": {}}

    updated_metrics, applied, invalid = data_agent.apply_manual_overrides(metrics, overrides)
    if not applied and invalid:
        return jsonify(
            {
                "error": "Algunos valores manuales no pudieron interpretarse.",
                "invalid_fields": invalid,
            }
        ), 400
    if not applied and not invalid:
        return jsonify({"error": "No se aplicaron ajustes manuales válidos."}), 400

    save_cache(ticker, updated_metrics)
    response = prepare_analysis_response(
        ticker,
        updated_metrics,
        save_scores_flag=True,
        extra={"manual_overrides": {"applied": applied, "invalid": invalid}},
    )
    return jsonify(response)


@app.route("/history/<ticker>")
def history(ticker: str):
    ticker = ticker.upper()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT score, classification, breakdown, last_calculated
            FROM rvc_scores
            WHERE ticker = ?
            ORDER BY last_calculated DESC
            LIMIT 10
            """,
            (ticker,),
        )
        rows = cursor.fetchall()

    history_payload = [
        {
            "score": row[0],
            "classification": row[1],
            "breakdown": json.loads(row[2]),
            "date": row[3],
        }
        for row in rows
    ]
    return jsonify({"ticker": ticker, "history": history_payload})


@app.route("/cache/clear", methods=["POST"])
def clear_cache():
    payload = request.get_json(silent=True) or {}
    ticker = payload.get("ticker")
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            if ticker:
                symbol = ticker.upper()
                cursor.execute("DELETE FROM financial_cache WHERE ticker = ?", (symbol,))
                cursor.execute("DELETE FROM rvc_scores WHERE ticker = ?", (symbol,))
                conn.commit()
                cleared = "ticker"
            else:
                cursor.execute("DELETE FROM financial_cache")
                cursor.execute("DELETE FROM rvc_scores")
                conn.commit()
                cleared = "all"
    except sqlite3.Error as exc:
        logger.error("Error clearing cache: %s", exc)
        return jsonify({"error": "No se pudo limpiar la cache"}), 500
    return jsonify({"status": "ok", "cleared": cleared})


@app.route("/comparador")
def comparador():
    """Página del comparador de acciones."""
    return render_template("comparador.html", active_page="compare")


@app.route("/calculadora")
def calculadora():
    """Página de la calculadora de inversión."""
    return render_template("calculadora.html", active_page="calculator")


@app.route("/api/comparar", methods=["POST"])
def comparar():
    """
    Compara múltiples tickers (2-5) y devuelve análisis comparativo.

    Payload:
        {
            "tickers": ["NVDA", "AMD", "TSM"]
        }

    Returns:
        {
            "companies": [...],  // Datos completos de cada empresa
            "ranking": [...],    // Ordenado por investment_score
            "timestamp": "..."
        }
    """
    payload = request.get_json(silent=True) or {}
    tickers_input = payload.get("tickers", [])

    if not isinstance(tickers_input, list):
        return jsonify({"error": "El campo 'tickers' debe ser una lista"}), 400

    # Filtrar y normalizar tickers
    tickers = [t.strip().upper() for t in tickers_input if t and isinstance(t, str)]
    tickers = list(dict.fromkeys(tickers))  # Eliminar duplicados

    if len(tickers) < 2:
        return jsonify({"error": "Debe proporcionar al menos 2 tickers"}), 400

    if len(tickers) > 5:
        return jsonify({"error": "Máximo 5 tickers permitidos"}), 400

    logger.info("Comparing tickers: %s", tickers)

    companies_data = []
    errors = []

    for ticker in tickers:
        try:
            # 1. Obtener métricas (usar caché si disponible)
            cached = get_cached_data(ticker)
            metrics: Optional[Dict[str, Any]] = None

            if cached and not cache_expired(cached["last_updated"]):
                logger.info("Using cached metrics for %s", ticker)
                metrics = json.loads(cached["data"])
                if metrics and not metrics.get("asset_type"):
                    logger.info("Cached metrics desactualizados para %s, recargando", ticker)
                    metrics = data_agent.fetch_financial_data(ticker)
                    if metrics:
                        save_cache(ticker, metrics)
                elif metrics and metrics.get("schema_version") != METRIC_SCHEMA_VERSION:
                    logger.info("Actualizando métricas a esquema vigente para %s", ticker)
                    metrics = data_agent.fetch_financial_data(ticker)
                    if metrics:
                        save_cache(ticker, metrics)
            else:
                logger.info("Fetching fresh metrics for %s", ticker)
                metrics = data_agent.fetch_financial_data(ticker)
                if metrics:
                    save_cache(ticker, metrics)

            if not metrics:
                errors.append(f"No se encontraron datos para {ticker}")
                continue

            if metrics.get("asset_type") != "EQUITY" or not metrics.get("analysis_allowed", False):
                label = metrics.get("asset_type_label") or metrics.get("asset_type") or "activo"
                errors.append(
                    f"{ticker} es un tipo {label}. El comparador actual solo analiza acciones individuales."
                )
                continue

            # 2. Calcular scores con el nuevo motor
            scores = investment_scorer.calculate_all_scores(metrics)

            # 3. Compilar datos
            company_data = {
                "ticker": ticker,
                "company_name": metrics.get("company_name", "N/A"),
                "sector": metrics.get("sector", "Desconocido"),
                "current_price": metrics.get("current_price"),
                "market_cap": metrics.get("market_cap"),
                "currency": metrics.get("currency"),
                "price_currency": metrics.get("price_currency"),
                "price_converted": metrics.get("price_converted"),
                "market_cap_converted": metrics.get("market_cap_converted"),
                "exchange_rates": metrics.get("exchange_rates"),
                "primary_source": metrics.get("primary_source"),

                # Scores principales
                "quality_score": scores["quality_score"],
                "valuation_score": scores["valuation_score"],
                "financial_health_score": scores["financial_health_score"],
                "growth_score": scores["growth_score"],
                "investment_score": scores["investment_score"],

                # Categorización y recomendación
                "category": scores["category"],
                "recommendation": scores["recommendation"],
                "confidence_level": scores["confidence_level"],

                # Métricas clave para la tabla
                "metrics": {
                    "pe_ratio": metrics.get("pe_ratio"),
                    "peg_ratio": metrics.get("peg_ratio"),
                    "price_to_book": metrics.get("price_to_book"),
                    "roe": metrics.get("roe"),
                    "roic": metrics.get("roic"),
                    "operating_margin": metrics.get("operating_margin"),
                    "net_margin": metrics.get("net_margin"),
                    "debt_to_equity": metrics.get("debt_to_equity"),
                    "current_ratio": metrics.get("current_ratio"),
                    "quick_ratio": metrics.get("quick_ratio"),
                    "revenue_growth": pick_metric(
                        metrics,
                        (
                            "revenue_growth_5y",
                            "revenue_growth",
                            "revenue_growth_qoq",
                        ),
                    ),
                    "earnings_growth": pick_metric(
                        metrics,
                        (
                            "earnings_growth_this_y",
                            "earnings_growth_next_y",
                            "earnings_growth_next_5y",
                            "earnings_growth_qoq",
                            "earnings_growth",
                        ),
                    ),
                },

                # Breakdown detallado
                "breakdown": scores["breakdown"],
            }

            companies_data.append(company_data)

        except Exception as e:
            logger.error(f"Error analyzing {ticker}: {e}")
            errors.append(f"Error al analizar {ticker}: {str(e)}")

    if not companies_data:
        return jsonify({
            "error": "No se pudieron obtener datos para ningún ticker",
            "details": errors
        }), 404

    # Ordenar por investment_score (descendente)
    companies_data.sort(key=lambda x: x["investment_score"], reverse=True)

    # Crear ranking
    ranking = [
        {
            "position": idx + 1,
            "ticker": company["ticker"],
            "investment_score": company["investment_score"],
            "category": company["category"],
            "recommendation": company["recommendation"],
        }
        for idx, company in enumerate(companies_data)
    ]

    response = {
        "companies": companies_data,
        "ranking": ranking,
        "count": len(companies_data),
        "errors": errors if errors else None,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }

    return jsonify(response)


@app.route("/api/calcular-inversion", methods=["POST"])
def calcular_inversion():
    """
    Calcula proyecciones de inversión con diferentes estrategias.

    Payload:
        {
            "calculation_type": "dca" | "lump_sum_vs_dca" | "compound_interest" | "retirement_plan",
            "monthly_amount": 500,
            "years": 10,
            "scenario": "conservador" | "moderado" | "optimista",
            "market_timing": "crisis" | "normal" | "burbuja",
            "initial_amount": 10000,     // Para compound_interest y retirement_plan
            "total_amount": 50000,       // Para lump_sum_vs_dca
            "current_age": 35,           // Para retirement_plan
            "retirement_age": 65,        // Para retirement_plan
            "annual_inflation": 0.03     // Para retirement_plan (opcional, default 3%)
        }

    Returns:
        Resultados de la simulación según el tipo de cálculo
    """
    payload = request.get_json(silent=True) or {}
    calc_type = payload.get("calculation_type", "dca")

    try:
        if calc_type == "dca":
            monthly_amount = float(payload.get("monthly_amount", 0))
            years = int(payload.get("years", 10))
            scenario = payload.get("scenario", "moderado")
            market_timing = payload.get("market_timing", "normal")
            initial_amount = float(payload.get("initial_amount", 0))
            annual_inflation = float(payload.get("annual_inflation", 0.0))

            if monthly_amount < 0:
                return jsonify({"error": "El aporte mensual no puede ser negativo"}), 400

            if initial_amount < 0:
                return jsonify({"error": "El capital inicial no puede ser negativo"}), 400

            if monthly_amount == 0 and initial_amount == 0:
                return jsonify({"error": "Ingresa al menos un capital inicial o un aporte mensual"}), 400

            if years <= 0 or years > 50:
                return jsonify({"error": "Los anos deben estar entre 1 y 50"}), 400

            if annual_inflation < 0 or annual_inflation > 0.15:
                return jsonify({"error": "La inflacion anual debe estar entre 0% y 15%"}), 400

            result = investment_calculator.calculate_dca(
                monthly_amount=monthly_amount,
                years=years,
                scenario=scenario,
                market_timing=market_timing,
                include_simulation=True,
                initial_amount=initial_amount,
                annual_inflation=annual_inflation,
                max_portfolio_value=investment_calculator.MAX_PORTFOLIO_VALUE
            )

            return jsonify({
                "calculation_type": "dca",
                "result": result,
                "timestamp": datetime.now().isoformat(timespec="seconds")
            })

        elif calc_type == "lump_sum_vs_dca":
            total_amount = float(payload.get("total_amount", 0))
            years = int(payload.get("years", 10))
            scenario = payload.get("scenario", "moderado")

            if total_amount <= 0:
                return jsonify({"error": "El monto total debe ser mayor a 0"}), 400

            if years <= 0 or years > 50:
                return jsonify({"error": "Los años deben estar entre 1 y 50"}), 400

            result = investment_calculator.compare_lump_sum_vs_dca(
                total_amount=total_amount,
                years=years,
                scenario=scenario
            )

            return jsonify({
                "calculation_type": "lump_sum_vs_dca",
                "result": result,
                "timestamp": datetime.now().isoformat(timespec="seconds")
            })

        elif calc_type == "compound_interest":
            initial_amount = float(payload.get("initial_amount", 0))
            monthly_contribution = float(payload.get("monthly_amount", 0))
            years = int(payload.get("years", 10))
            scenario = payload.get("scenario", "moderado")

            if initial_amount < 0 or monthly_contribution < 0:
                return jsonify({"error": "Los montos no pueden ser negativos"}), 400

            if years <= 0 or years > 50:
                return jsonify({"error": "Los años deben estar entre 1 y 50"}), 400

            annual_return = investment_calculator.HISTORICAL_RETURNS.get(scenario, 0.10)

            result = investment_calculator.calculate_compound_interest_impact(
                initial_amount=initial_amount,
                monthly_contribution=monthly_contribution,
                years=years,
                annual_return=annual_return
            )

            return jsonify({
                "calculation_type": "compound_interest",
                "result": result,
                "timestamp": datetime.now().isoformat(timespec="seconds")
            })

        elif calc_type == "retirement_plan":
            current_age = int(payload.get("current_age", 0))
            retirement_age = int(payload.get("retirement_age", 0))
            initial_amount = float(payload.get("initial_amount", 0))
            monthly_contribution = float(payload.get("monthly_amount", 0))
            scenario = payload.get("scenario", "moderado")
            annual_inflation = float(payload.get("annual_inflation", 0.03))
            annual_return_override = payload.get("annual_return_override")

            if current_age < 18 or current_age > 75:
                return jsonify({"error": "La edad actual debe estar entre 18 y 75 años"}), 400

            if retirement_age <= current_age or retirement_age > 75:
                return jsonify({"error": "La edad de jubilación debe ser mayor a la edad actual y máximo 75 años"}), 400

            if initial_amount < 0 or monthly_contribution < 0:
                return jsonify({"error": "Los montos no pueden ser negativos"}), 400

            if annual_return_override is not None:
                annual_return = float(annual_return_override)
                if annual_return < -0.10 or annual_return > 0.20:
                    return jsonify({"error": "El rendimiento anual debe estar entre -10% y 20%"}), 400
            else:
                annual_return = investment_calculator.HISTORICAL_RETURNS.get(scenario, 0.10)

            result = investment_calculator.calculate_retirement_plan(
                current_age=current_age,
                retirement_age=retirement_age,
                initial_amount=initial_amount,
                monthly_contribution=monthly_contribution,
                annual_return=annual_return,
                annual_inflation=annual_inflation,
                include_yearly_detail=True,
                max_portfolio_value=investment_calculator.MAX_PORTFOLIO_VALUE
            )

            return jsonify({
                "calculation_type": "retirement_plan",
                "result": result,
                "timestamp": datetime.now().isoformat(timespec="seconds")
            })

        else:
            return jsonify({
                "error": f"Tipo de cálculo '{calc_type}' no soportado",
                "supported_types": ["dca", "lump_sum_vs_dca", "compound_interest", "retirement_plan"]
            }), 400

    except ValueError as e:
        return jsonify({"error": f"Error en los valores proporcionados: {str(e)}"}), 400
    except Exception as e:
        logger.error(f"Error calculating investment: {e}")
        return jsonify({"error": f"Error en el cálculo: {str(e)}"}), 500


if __name__ == "__main__":
    init_database()
    app.run(debug=True, port=int(os.getenv("PORT", 5000)))
