#!/usr/bin/env python3
"""
RVC Analyzer - Flask application orchestrating the IA agent and RVC calculator.
"""

from __future__ import annotations

import json
import logging
import os
import re
import sqlite3
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from flask import Flask, jsonify, render_template, request, session
from dotenv import load_dotenv
import requests

from data_agent import DataAgent, METRIC_SCHEMA_VERSION
from analyzers import EquityAnalyzer, ETFAnalyzer  # Modular architecture
from investment_calculator import InvestmentCalculator
from usage_limiter import get_limiter
from db_manager import get_db_manager

# Alias para compatibilidad con código existente
InvestmentScorer = EquityAnalyzer


load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "cache.db"
LOG_DIR = BASE_DIR / "logs"
CACHE_EXPIRATION_HOURS = int(os.getenv("CACHE_EXPIRATION_HOURS", "24"))

# Crear directorio de logs si no existe
LOG_DIR.mkdir(exist_ok=True)


app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("RVC_SECRET_KEY", "change-me")

# ============================================
# CONFIGURACIÓN DE LOGGING
# ============================================

# Nivel de logging desde variable de entorno (default: INFO)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# Formato detallado para logs
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Configurar logger raíz
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format=LOG_FORMAT,
    datefmt=DATE_FORMAT,
    handlers=[
        # Handler 1: Console output (solo INFO y superiores)
        logging.StreamHandler(),
        # Handler 2: File output con rotación (10 MB max, 5 archivos)
        RotatingFileHandler(
            LOG_DIR / "rvc_app.log",
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8"
        )
    ]
)

# Logger principal de la aplicación
logger = logging.getLogger("rvc_app")

# Logger separado para errores críticos
error_handler = RotatingFileHandler(
    LOG_DIR / "errors.log",
    maxBytes=10 * 1024 * 1024,
    backupCount=3,
    encoding="utf-8"
)
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
logger.addHandler(error_handler)

# Log de inicio de aplicación
logger.info("=" * 60)
logger.info("RVC Analyzer - Iniciando aplicación")
logger.info(f"Directorio base: {BASE_DIR}")
logger.info(f"Directorio de datos: {DATA_DIR}")
logger.info(f"Base de datos: {DB_PATH}")
logger.info(f"Nivel de logging: {LOG_LEVEL}")
logger.info("=" * 60)

data_agent = DataAgent()
investment_scorer = InvestmentScorer()
etf_analyzer = ETFAnalyzer()
investment_calculator = InvestmentCalculator()

# Inicializar gestor de base de datos (SQLite en dev, PostgreSQL en prod)
db_manager = get_db_manager(DB_PATH)
logger.info(f"Modo BD: {'PostgreSQL (produccion)' if db_manager.is_production else 'SQLite (desarrollo)'}")

# ============================================
# CONTADOR DE VISITAS - FILTRO ANTI-BOTS
# ============================================

# Patrón regex para detectar bots (case-insensitive)
BOT_PATTERN = re.compile(
    r'bot|crawler|spider|slurp|facebook|twitter|discord|'
    r'curl|wget|requests|python|java|okhttp|axios|'
    r'headless|phantom|selenium|scraper|preview|postman',
    re.IGNORECASE
)


def is_bot_request() -> bool:
    """
    Detecta si el request viene de un bot.
    Retorna True si es bot, False si es humano.
    """
    user_agent = request.headers.get('User-Agent', '')
    
    # Sin User-Agent = probablemente bot
    if not user_agent:
        return True
    
    # Coincide con patrón de bot
    if BOT_PATTERN.search(user_agent):
        return True
    
    return False


def init_visits_counter() -> None:
    """Inicializa la tabla de contador de visitas."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS site_visits (
                id INTEGER PRIMARY KEY,
                total_visits INTEGER DEFAULT 0,
                last_updated TEXT
            )
        ''')
        
        # Inicializar contador si no existe
        cursor.execute('SELECT COUNT(*) FROM site_visits')
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO site_visits (id, total_visits, last_updated) 
                VALUES (1, 0, ?)
            ''', (datetime.now().isoformat(),))
        
        # Tabla para visitas diarias (opcional)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_visits (
                date TEXT PRIMARY KEY,
                visits INTEGER DEFAULT 0
            )
        ''')
        
        conn.commit()


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
    
    # Inicializar contador de visitas
    init_visits_counter()


# Asegurar el esquema de la base de datos al importar el módulo (modo WSGI)
try:
    init_database()
    purged_entries = purge_expired_cache()
    if purged_entries:
        logger.info(
            "Limpieza inicial de cache: %s entradas eliminadas (>%s horas).",
            purged_entries,
            CACHE_EXPIRATION_HOURS,
        )
    logger.info("Base de datos inicializada (tablas aseguradas)")
    logger.info("Contador de visitas inicializado")
except Exception as e:
    logger.error("Error inicializando base de datos al importar: %s", e, exc_info=True)


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
    cache_entry = {"data": row[0], "last_updated": row[1], "source": row[2]}
    if cache_expired(cache_entry["last_updated"]):
        logger.info(
            "Cache expirado para %s (>%s horas); eliminando entrada.",
            ticker,
            CACHE_EXPIRATION_HOURS,
        )
        delete_cache_entry(ticker)
        return None
    return cache_entry


def cache_expired(last_updated: str, max_age_hours: int = CACHE_EXPIRATION_HOURS) -> bool:
    dt = datetime.fromisoformat(last_updated)
    return datetime.now() - dt > timedelta(hours=max_age_hours)


def delete_cache_entry(ticker: str) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM financial_cache WHERE ticker = ?",
            (ticker,),
        )
        conn.commit()


def purge_expired_cache() -> int:
    cutoff = datetime.now() - timedelta(hours=CACHE_EXPIRATION_HOURS)
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            DELETE FROM financial_cache
            WHERE last_updated < ?
            """,
            (cutoff.isoformat(timespec="seconds"),),
        )
        removed = cursor.rowcount
        conn.commit()
    return removed


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
        # Simplificar breakdown a solo scores para SQLite
        simplified_breakdown = {
            key: value["score"] if isinstance(value, dict) and "score" in value else value
            for key, value in score["breakdown"].items()
        }
        cursor.execute(
            """
            INSERT OR REPLACE INTO rvc_scores (ticker, score, classification, breakdown, last_calculated)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                ticker,
                score["total_score"],
                score["classification"],
                json.dumps(simplified_breakdown),
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
        # Adaptar formato de investment_scores a rvc_score para compatibilidad
        category_info = investment_scores.get("category", {})
        rvc_score = {
            "total_score": investment_scores.get("investment_score"),
            "classification": category_info.get("name", "No evaluado") if isinstance(category_info, dict) else category_info,
            "recommendation": investment_scores.get("recommendation"),
            "breakdown": {
                "calidad": investment_scores["breakdown"]["quality"],
                "valoracion": investment_scores["breakdown"]["valuation"],
                "salud": investment_scores["breakdown"]["health"],
                "crecimiento": investment_scores["breakdown"]["growth"],
            },
            "data_completeness": investment_scores.get("data_completeness", 0),
            "confidence_level": investment_scores.get("confidence_level", "Media"),
            "confidence_factors": investment_scores.get("confidence_factors", {}),
        }
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


# ============================================
# MIDDLEWARE - CONTADOR DE VISITAS
# ============================================

@app.before_request
def count_visit():
    """
    Cuenta visitas reales (humanos) en la página principal.
    - Solo cuenta en GET /
    - Filtra bots por User-Agent
    - Una visita por sesión (cookie)
    """
    if request.path == '/' and request.method == 'GET':
        # Ignorar bots
        if is_bot_request():
            logger.debug("Bot detectado, visita no contada")
            return
        
        # Solo contar una vez por sesión
        if session.get('visited'):
            return
        
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()

            # Incrementar contador total
            query = '''
                UPDATE site_visits
                SET total_visits = total_visits + 1,
                    last_updated = ?
                WHERE id = 1
            '''
            if db_manager.is_production:
                query = query.replace('?', '%s')
            cursor.execute(query, (datetime.now().isoformat(),))

            # Incrementar contador del día
            today = datetime.now().strftime('%Y-%m-%d')
            if db_manager.is_production:
                # PostgreSQL requiere EXCLUDED para valores en conflicto
                query = '''
                    INSERT INTO daily_visits (date, visits) VALUES (%s, 1)
                    ON CONFLICT(date) DO UPDATE SET visits = daily_visits.visits + 1
                '''
            else:
                # SQLite usa sintaxis estándar
                query = '''
                    INSERT INTO daily_visits (date, visits) VALUES (?, 1)
                    ON CONFLICT(date) DO UPDATE SET visits = visits + 1
                '''
            cursor.execute(query, (today,))

            conn.commit()
            conn.close()

            # Marcar sesión como visitada
            session['visited'] = True
            session.permanent = False  # Expira con el navegador

            logger.info("✓ Visita contada (sesión única)")
            
        except Exception as e:
            logger.error(f"Error counting visit: {e}")


# ============================================
# RUTAS PRINCIPALES
# ============================================

@app.route("/")
def index():
    return render_template("index.html", active_page="home")


@app.route("/health")
def health():
    """Endpoint de salud simple para verificaciones de plataforma."""
    # Estado de proveedores externos (sin exponer secretos)
    try:
        providers = {
            "alpha_vantage": {
                "enabled": getattr(data_agent, "alpha_client", None).enabled if hasattr(data_agent, "alpha_client") else False,
                "env": (
                    "ALPHA_VANTAGE_KEY" if os.getenv("ALPHA_VANTAGE_KEY") else (
                        "ALPHAVANTAGE_API_KEY" if os.getenv("ALPHAVANTAGE_API_KEY") else None
                    )
                ),
                "env_candidates": {
                    "ALPHA_VANTAGE_KEY": bool(os.getenv("ALPHA_VANTAGE_KEY")),
                    "ALPHAVANTAGE_API_KEY": bool(os.getenv("ALPHAVANTAGE_API_KEY")),
                },
            },
            "twelve_data": {
                "enabled": getattr(data_agent, "twelve_client", None).enabled if hasattr(data_agent, "twelve_client") else False,
                "env": (
                    "TWELVEDATA_API_KEY" if os.getenv("TWELVEDATA_API_KEY") else (
                        "TWELVE_DATA_API_KEY" if os.getenv("TWELVE_DATA_API_KEY") else None
                    )
                ),
                "env_candidates": {
                    "TWELVEDATA_API_KEY": bool(os.getenv("TWELVEDATA_API_KEY")),
                    "TWELVE_DATA_API_KEY": bool(os.getenv("TWELVE_DATA_API_KEY")),
                },
            },
            "fmp": {
                "enabled": getattr(data_agent, "fmp_client", None).enabled if hasattr(data_agent, "fmp_client") else False,
                "env": ("FMP_API_KEY" if os.getenv("FMP_API_KEY") else None),
                "env_candidates": {"FMP_API_KEY": bool(os.getenv("FMP_API_KEY"))},
            },
        }
    except Exception:
        providers = {"alpha_vantage": {"enabled": False}, "twelve_data": {"enabled": False}, "fmp": {"enabled": False}}

    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "providers": providers,
    })


# ============================================
# API: Exchange Rate (USD -> EUR), con cache simple
# ============================================

_EXCHANGE_CACHE: Dict[str, Dict[str, Any]] = {}


def _get_cached_rate_key(base: str, target: str) -> str:
    return f"{base}->{target}".upper()


def get_exchange_rate(base: str = "USD", target: str = "EUR") -> Dict[str, Any]:
    base = (base or "USD").upper()
    target = (target or "EUR").upper()
    key = _get_cached_rate_key(base, target)

    # 12 horas de cache
    cached = _EXCHANGE_CACHE.get(key)
    if cached and cached.get("expires_at") and cached["expires_at"] > datetime.utcnow():
        return {"base": base, "target": target, "rate": cached.get("rate"), "cached": True}

    rate = 1.0
    try:
        # Usar exchangerate.host (sin API key)
        url = f"https://api.exchangerate.host/latest?base={base}&symbols={target}"
        resp = requests.get(url, timeout=5)
        if resp.ok:
            data = resp.json()
            rate = float(data.get("rates", {}).get(target, 1.0))
    except Exception as ex:
        logger.warning("Fallo obteniendo tasa de cambio %s->%s: %s", base, target, ex)

    _EXCHANGE_CACHE[key] = {
        "rate": rate,
        "expires_at": datetime.utcnow() + timedelta(hours=12),
    }
    return {"base": base, "target": target, "rate": rate, "cached": False}


@app.get("/api/exchange-rate")
def exchange_rate():
    base = request.args.get("base", "USD")
    target = request.args.get("target", "EUR")
    data = get_exchange_rate(base, target)
    return jsonify(data)


@app.route('/api/visit-count')
def get_visit_count():
    """
    Retorna el contador de visitas para mostrar en el footer.
    Incluye visitas totales y del día actual.
    """
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()

        # Total visitas
        cursor.execute('SELECT total_visits FROM site_visits WHERE id = 1')
        result = cursor.fetchone()
        total = result[0] if result else 0

        # Visitas del día
        today = datetime.now().strftime('%Y-%m-%d')
        query = 'SELECT visits FROM daily_visits WHERE date = ?'
        if db_manager.is_production:
            query = query.replace('?', '%s')
        cursor.execute(query, (today,))
        result = cursor.fetchone()
        daily = result[0] if result else 0

        conn.close()

        return jsonify({
            'visits': total,
            'today': daily
        })
    except Exception as e:
        logger.error(f"Error getting visit count: {e}")
        return jsonify({'visits': 0, 'today': 0})


@app.route("/analyze", methods=["POST"])
def analyze():
    """Endpoint principal para análisis de ticker individual."""
    start_time = datetime.now()

    payload = request.get_json(silent=True) or {}
    ticker = (payload.get("ticker") or "").strip().upper()
    license_key = payload.get("license_key")  # Usuario puede enviar su licencia

    if not ticker:
        logger.warning("Analyze request sin ticker - IP: %s", request.remote_addr)
        return jsonify({"error": "Por favor ingrese un ticker"}), 400

    # ===== VERIFICAR LÍMITE DE USO =====
    try:
        limiter = get_limiter()
        user_id = request.remote_addr
        limit_check = limiter.check_limit(user_id, license_key)
        
        if not limit_check["allowed"]:
            logger.warning(f"⛔ Límite alcanzado - IP: {user_id} | Usado: {limit_check['limit']}")
            return jsonify({
                "error": "Límite de consultas alcanzado",
                "limit_info": limit_check
            }), 429  # Too Many Requests
        
        # Registrar uso
        limiter.track_usage(user_id, "/analyze", request.headers.get("User-Agent"))
        
    except Exception as e:
        logger.error(f"Error en verificación de límite: {e}")
        # Continuar sin bloquear si hay error en el limiter
    # ===================================

    logger.info("=" * 50)
    logger.info("ANALYZE REQUEST - Ticker: %s | IP: %s | Plan: %s", 
                ticker, request.remote_addr, limit_check.get("plan", "FREE"))

    try:
        cached = get_cached_data(ticker)
        metrics: Optional[Dict[str, Any]] = None

        if cached and not cache_expired(cached["last_updated"]):
            logger.info("✓ Cache HIT - Ticker: %s | Age: %s",
                       ticker,
                       datetime.now() - datetime.fromisoformat(cached["last_updated"]))
            metrics = json.loads(cached["data"])

            # Verificar si necesita actualización
            if metrics and not metrics.get("asset_type"):
                logger.warning("Cache obsoleto (sin asset_type) - Refrescando: %s", ticker)
                metrics = data_agent.fetch_financial_data(ticker)
                if metrics:
                    save_cache(ticker, metrics)
            elif metrics and metrics.get("schema_version") != METRIC_SCHEMA_VERSION:
                logger.warning("Cache obsoleto (schema v%s vs v%s) - Refrescando: %s",
                             metrics.get("schema_version"), METRIC_SCHEMA_VERSION, ticker)
                metrics = data_agent.fetch_financial_data(ticker)
                if metrics:
                    save_cache(ticker, metrics)
        else:
            cache_status = "EXPIRED" if cached else "MISS"
            logger.info("✗ Cache %s - Fetching fresh data: %s", cache_status, ticker)
            metrics = data_agent.fetch_financial_data(ticker)
            if metrics:
                save_cache(ticker, metrics)
                logger.info("✓ Fresh data saved to cache: %s", ticker)

        if not metrics:
            logger.error("No se encontraron datos suficientes - Ticker: %s", ticker)
            return jsonify({"error": f"No se encontraron datos suficientes para {ticker}"}), 404

        response = prepare_analysis_response(ticker, metrics)

        elapsed = (datetime.now() - start_time).total_seconds()
        # Log de score con la nueva estructura (rvc_score.total_score)
        try:
            logged_score = response.get("rvc_score", {}).get("total_score")
            if logged_score is None:
                logged_score = 0.0
        except Exception:
            logged_score = 0.0
        logger.info("✓ Analysis completado - Ticker: %s | Tiempo: %.2fs | Score: %.1f",
                   ticker, elapsed, logged_score)
        logger.info("=" * 50)

        return jsonify(response)

    except Exception as e:
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.error("ERROR en analyze() - Ticker: %s | Tiempo: %.2fs | Error: %s",
                    ticker, elapsed, str(e), exc_info=True)
        return jsonify({"error": f"Error interno al analizar {ticker}"}), 500


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


@app.route("/api/top-opportunities")
def top_opportunities():
    """
    Endpoint que retorna ranking de mejores oportunidades de inversión
    basado en RVC scores y métricas financieras.
    
    Query parameters:
    - min_score: Score mínimo RVC (default: 50.0)
    - sector: Filtrar por sector específico
    - sort_by: Campo de ordenamiento (rvc_score, market_cap, pe_ratio)
    - limit: Máximo número de resultados (default: 50)
    """
    try:
        # Obtener parámetros de consulta
        min_score = float(request.args.get('min_score', 50.0))
        sector_filter = request.args.get('sector', '').strip()
        sort_by = request.args.get('sort_by', 'rvc_score').lower()
        target_currency = (request.args.get('currency', 'USD') or 'USD').upper()
        limit = min(int(request.args.get('limit', 50)), 100)  # Max 100 resultados
        
        # Validar parámetros
        valid_sort_fields = ['rvc_score', 'market_cap', 'pe_ratio', 'ticker']
        if sort_by not in valid_sort_fields:
            sort_by = 'rvc_score'
        
        # Consulta base para obtener tickers con RVC scores
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # Query para obtener tickers con scores y sus datos financieros
            cursor.execute("""
                SELECT 
                    r.ticker,
                    r.score as rvc_score,
                    r.classification,
                    r.breakdown,
                    r.last_calculated,
                    f.data as financial_data
                FROM rvc_scores r
                LEFT JOIN financial_cache f ON r.ticker = f.ticker
                WHERE r.score >= ?
                ORDER BY r.score DESC
            """, (min_score,))
            
            rows = cursor.fetchall()
        
        # Preparar tipo de cambio si se solicitó otra moneda
        fx_rate = None
        if target_currency and target_currency != 'USD':
            try:
                rate_info = get_exchange_rate('USD', target_currency)
                fx_rate = float(rate_info.get('rate', 1.0)) if isinstance(rate_info, dict) else float(rate_info)
            except Exception:
                fx_rate = None

        # Procesar resultados
        opportunities = []
        sectors_found = set()
        
        for row in rows:
            ticker, rvc_score, classification, breakdown_json, last_calc, financial_data = row
            
            # Parse financial data si existe
            financial_metrics = {}
            if financial_data:
                try:
                    financial_metrics = json.loads(financial_data)
                except (json.JSONDecodeError, TypeError):
                    financial_metrics = {}
            
            # Parse breakdown
            try:
                breakdown = json.loads(breakdown_json) if breakdown_json else {}
            except (json.JSONDecodeError, TypeError):
                breakdown = {}
            
            # Extraer métricas relevantes
            market_cap = financial_metrics.get('market_cap') or financial_metrics.get('Market_Cap')
            pe_ratio = financial_metrics.get('pe_ratio') or financial_metrics.get('P/E_Ratio')
            sector = financial_metrics.get('sector') or financial_metrics.get('Sector', 'Unknown')
            company_name = financial_metrics.get('company_name') or financial_metrics.get('Name', ticker)
            current_price = financial_metrics.get('current_price') or financial_metrics.get('Price')
            
            # Aplicar filtro de sector si se especificó
            if sector_filter and sector.lower() != sector_filter.lower():
                continue
            
            sectors_found.add(sector)
            
            # Conversiones a moneda objetivo (si hay tasa)
            price_converted = None
            market_cap_converted = None
            if fx_rate is not None and fx_rate > 0:
                try:
                    if isinstance(current_price, (int, float)):
                        price_converted = {target_currency: round(float(current_price) * fx_rate, 6)}
                    else:
                        cp = float(current_price)
                        price_converted = {target_currency: round(cp * fx_rate, 6)}
                except (TypeError, ValueError):
                    price_converted = None
                try:
                    if isinstance(market_cap, (int, float)):
                        market_cap_converted = {target_currency: round(float(market_cap) * fx_rate, 2)}
                    else:
                        mc = float(market_cap)
                        market_cap_converted = {target_currency: round(mc * fx_rate, 2)}
                except (TypeError, ValueError):
                    market_cap_converted = None

            opportunity = {
                'ticker': ticker,
                'company_name': company_name,
                'rvc_score': round(rvc_score, 2),
                'classification': classification,
                'sector': sector,
                'market_cap': market_cap,
                'pe_ratio': pe_ratio,
                'current_price': current_price,
                'last_updated': last_calc,
                'breakdown': breakdown,
                'price_currency': 'USD',
                'price_converted': price_converted,
                'market_cap_converted': market_cap_converted
            }
            
            opportunities.append(opportunity)
        
        # Aplicar ordenamiento personalizado
        if sort_by == 'rvc_score':
            opportunities.sort(key=lambda x: x['rvc_score'] or 0, reverse=True)
        elif sort_by == 'market_cap':
            opportunities.sort(key=lambda x: x['market_cap'] or 0, reverse=True)
        elif sort_by == 'pe_ratio':
            opportunities.sort(key=lambda x: x['pe_ratio'] or float('inf'))
        elif sort_by == 'ticker':
            opportunities.sort(key=lambda x: x['ticker'])
        
        # Aplicar límite
        opportunities = opportunities[:limit]
        
        # Calcular estadísticas
        total_count = len(opportunities)
        avg_score = sum(op['rvc_score'] for op in opportunities) / total_count if total_count > 0 else 0
        
        # Preparar respuesta
        response = {
            'status': 'success',
            'data': {
                'opportunities': opportunities,
                'metadata': {
                    'total_count': total_count,
                    'average_score': round(avg_score, 2),
                    'sectors_available': sorted(list(sectors_found)),
                    'filters_applied': {
                        'min_score': min_score,
                        'sector': sector_filter or None,
                        'sort_by': sort_by,
                        'limit': limit
                    },
                    'generated_at': datetime.now().isoformat(timespec='seconds'),
                    'currency': target_currency,
                    'fx_rate': (float(fx_rate) if isinstance(fx_rate, (int, float)) else None)
                }
            }
        }
        
        logger.info("Top opportunities request processed: %d results, avg_score=%.2f", 
                   total_count, avg_score)
        
        return jsonify(response)
        
    except ValueError as e:
        return jsonify({
            'status': 'error',
            'error': 'Invalid parameter format',
            'message': str(e)
        }), 400
    except Exception as e:
        logger.error("Error in top_opportunities endpoint: %s", str(e))
        return jsonify({
            'status': 'error',
            'error': 'Internal server error',
            'message': 'An error occurred while fetching opportunities'
        }), 500


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


@app.route("/top-opportunities")
def top_opportunities_page():
    """Página de Top Opportunities - mejores oportunidades de inversión."""
    return render_template("top_opportunities.html", active_page="opportunities")


@app.route("/about")
def about():
    """Página Acerca de - misión, filosofía y creador del proyecto."""
    return render_template("about.html", active_page="about")


@app.route("/api/comparar", methods=["POST"])
def comparar():
    """
    Compara múltiples tickers (2-5) y devuelve análisis comparativo.

    Payload:
        {
            "tickers": ["NVDA", "AMD", "TSM"],
            "license_key": "RVC-PRO-XXX" (opcional)
        }

    Returns:
        {
            "companies": [...],  // Datos completos de cada empresa
            "ranking": [...],    // Ordenado por investment_score
            "timestamp": "..."
        }
    """
    start_time = datetime.now()

    payload = request.get_json(silent=True) or {}
    tickers_input = payload.get("tickers", [])
    license_key = payload.get("license_key")

    if not isinstance(tickers_input, list):
        logger.warning("Comparar request con formato inválido - IP: %s", request.remote_addr)
        return jsonify({"error": "El campo 'tickers' debe ser una lista"}), 400

    # Filtrar y normalizar tickers
    tickers = [t.strip().upper() for t in tickers_input if t and isinstance(t, str)]
    tickers = list(dict.fromkeys(tickers))  # Eliminar duplicados

    if len(tickers) < 2:
        logger.warning("Comparar request con < 2 tickers - IP: %s", request.remote_addr)
        return jsonify({"error": "Debe proporcionar al menos 2 tickers"}), 400
    
    # ===== VERIFICAR LÍMITE DE USO =====
    try:
        limiter = get_limiter()
        user_id = request.remote_addr
        limit_check = limiter.check_limit(user_id, license_key)
        
        if not limit_check["allowed"]:
            logger.warning(f"⛔ Límite alcanzado (comparar) - IP: {user_id}")
            return jsonify({
                "error": "Límite de consultas alcanzado",
                "limit_info": limit_check
            }), 429
        
        # Registrar uso
        limiter.track_usage(user_id, "/api/comparar", request.headers.get("User-Agent"))
        
    except Exception as e:
        logger.error(f"Error en verificación de límite: {e}")
    # ===================================

    if len(tickers) > 5:
        logger.warning("Comparar request con > 5 tickers (%d) - IP: %s", len(tickers), request.remote_addr)
        return jsonify({"error": "Máximo 5 tickers permitidos"}), 400

    logger.info("=" * 50)
    logger.info("COMPARE REQUEST - Tickers: %s | Count: %d | IP: %s",
               ", ".join(tickers), len(tickers), request.remote_addr)

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
            
            # 2.1 Guardar scores en BD para que aparezcan en el Ranking
            try:
                score_data = {
                    "total_score": scores["investment_score"],
                    "classification": scores["category"]["name"],
                    "breakdown": {
                        "quality": scores["quality_score"],
                        "valuation": scores["valuation_score"],
                        "health": scores["financial_health_score"],
                        "growth": scores["growth_score"]
                    }
                }
                save_score(ticker, score_data)
                logger.info("✓ Scores guardados en BD para %s (desde comparador)", ticker)
            except Exception as save_err:
                logger.warning("No se pudieron guardar scores para %s: %s", ticker, save_err)

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

    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info("✓ Comparison completado - Tickers: %s | Success: %d/%d | Tiempo: %.2fs",
               ", ".join(tickers), len(companies_data), len(tickers), elapsed)
    if errors:
        logger.warning("Comparison errors: %s", "; ".join(errors))
    logger.info("=" * 50)

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
            index_contributions = payload.get("index_contributions_annually", True)

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
                annual_inflation=annual_inflation if index_contributions else 0.0,
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
            mode = payload.get("mode", "deterministic")  # "deterministic" o "simulation"
            num_paths = int(payload.get("num_paths", 5))  # Número de simulaciones

            if initial_amount < 0 or monthly_contribution < 0:
                return jsonify({"error": "Los montos no pueden ser negativos"}), 400

            if years <= 0 or years > 50:
                return jsonify({"error": "Los años deben estar entre 1 y 50"}), 400

            annual_return = investment_calculator.HISTORICAL_RETURNS.get(scenario, 0.10)

            if mode == "simulation":
                result = investment_calculator.calculate_compound_interest_simulation(
                    initial_amount=initial_amount,
                    monthly_contribution=monthly_contribution,
                    years=years,
                    annual_return=annual_return,
                    scenario=scenario,
                    use_stochastic=True,
                    num_paths=min(max(num_paths, 3), 10)  # Entre 3 y 10 caminos
                )
            else:
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
            index_contributions = payload.get("index_contributions_annually", True)

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
                annual_inflation=annual_inflation if index_contributions else 0.0,
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


# ============================================
# ENDPOINTS DE SISTEMA DE LÍMITES (FREEMIUM)
# ============================================

@app.route("/api/check-limit", methods=["POST"])
def check_usage_limit():
    """
    Verificar límite de uso del usuario.
    
    Request:
        {
            "license_key": "RVC-PRO-XXXX" (opcional)
        }
    
    Response:
        {
            "allowed": bool,
            "remaining": int,
            "limit": int,
            "plan": "FREE" | "PRO",
            "reset_in": str
        }
    """
    try:
        data = request.get_json() or {}
        license_key = data.get("license_key")
        
        # Obtener identificador del usuario (IP)
        user_id = request.remote_addr
        
        # Verificar límite
        limiter = get_limiter()
        limit_info = limiter.check_limit(user_id, license_key)
        
        return jsonify(limit_info)
        
    except Exception as e:
        logger.error(f"Error checking limit: {e}")
        return jsonify({"allowed": True}), 200  # Fail open


@app.route("/api/validate-license", methods=["POST"])
def validate_license():
    """
    Validar una licencia PRO.
    
    Request:
        {
            "license_key": "RVC-PRO-XXXX"
        }
    
    Response:
        {
            "valid": bool,
            "plan": str,
            "expires_at": str,
            "email": str
        }
    """
    try:
        data = request.get_json()
        license_key = data.get("license_key")
        
        if not license_key:
            return jsonify({"valid": False, "reason": "No se proporcionó licencia"}), 400
        
        limiter = get_limiter()
        validation = limiter.validate_license(license_key)
        
        return jsonify(validation)
        
    except Exception as e:
        logger.error(f"Error validating license: {e}")
        return jsonify({"valid": False, "reason": "Error de validación"}), 500


@app.route("/api/usage-stats", methods=["GET"])
def get_usage_stats():
    """
    Obtener estadísticas de uso.
    Requiere autenticación admin (por implementar).
    """
    try:
        limiter = get_limiter()
        
        # Stats globales
        stats = limiter.get_usage_stats()
        
        return jsonify({
            "global_stats": stats,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    init_database()
    app.run(debug=True, port=int(os.getenv("PORT", 5000)))
