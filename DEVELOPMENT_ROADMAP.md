# 🗺️ BITÁCORA DE DESARROLLO - RVC Investment Analyzer

## ESTRATEGIA: Escalar MVP en Local → Deploy Gratuito → Monetizar con APIs Pagadas

**Última actualización**: 2025-10-22
**Estado actual**: MVP Funcional - Frontend Unificado ✅

---

## 📋 ÍNDICE DE FASES

1. [Fase 0: Estado Actual y Preparativos](#fase-0)
2. [Fase 1: Optimización del Core Existente](#fase-1)
3. [Fase 2: Top Opportunities (Buscador)](#fase-2)
4. [Fase 3: Contexto de Mercado](#fase-3)
5. [Fase 4: Mejoras de UX y Performance](#fase-4)
6. [Fase 5: Sistema de Alertas](#fase-5)
7. [Fase 6: Preparación para Deploy Gratuito](#fase-6)
8. [Fase 7: Deploy en Hosting Gratuito](#fase-7)
9. [Fase 8: Testing con Usuarios Reales](#fase-8)
10. [Fase 9: Migración a APIs Pagadas](#fase-9)
11. [Fase 10: Monetización](#fase-10)

---

<a name="fase-0"></a>
## 🎯 FASE 0: ESTADO ACTUAL Y PREPARATIVOS
**Duración estimada**: 1 día
**Costo**: $0

### ✅ Estado Actual (Completado):

- [x] Sistema de análisis individual funcional
- [x] Comparador de 2-5 acciones
- [x] Calculadora de inversiones (4 módulos)
- [x] Sistema de caché SQLite (7 días TTL)
- [x] Frontend unificado con diseño consistente
- [x] Sistema de variables CSS centralizado
- [x] Glosario interactivo con 60+ términos
- [x] Tooltips inline para términos técnicos
- [x] Botón flotante de ayuda
- [x] Responsive design móvil/desktop
- [x] 7 fuentes de datos con fallbacks
- [x] 2 sistemas de scoring (Investment + RVC)

### 📦 Estructura Actual:

```
rcv_proyecto/
├── app.py                          # Flask app principal
├── data_agent.py                   # Recolector de datos
├── scoring_engine.py               # Investment Scorer (NUEVO)
├── rvc_calculator.py               # RVC Calculator (LEGACY)
├── investment_calculator.py        # Simulador inversiones
├── asset_classifier.py             # Clasificador de activos
├── etf_analyzer.py                 # Analizador ETFs
├── services/
│   ├── alpha_vantage.py           # API Alpha Vantage
│   ├── twelve_data.py             # API Twelve Data
│   └── fmp.py                     # API FMP
├── data/
│   └── cache.db                    # SQLite cache (88KB)
├── static/
│   ├── style.css                   # CSS global unificado
│   ├── comparador.css             # Estilos comparador
│   ├── calculadora.css            # Estilos calculadora
│   ├── glossary.js                # Glosario interactivo
│   ├── app.js                     # JS index
│   ├── comparador.js              # JS comparador
│   └── calculadora.js             # JS calculadora
├── templates/
│   ├── base.html                  # Layout base
│   ├── index.html                 # Analizador
│   ├── comparador.html            # Comparador
│   └── calculadora.html           # Calculadora
├── DESIGN_SYSTEM.md               # Sistema de diseño
├── DEPLOYMENT_ANALYSIS.md         # Análisis deployment
└── requirements.txt               # Dependencias
```

### 📝 Tareas de Preparación:

#### Tarea 0.1: Crear .gitignore completo
**Archivo**: `.gitignore`
```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Flask
instance/
.webassets-cache

# Environment variables
.env
.env.local
.env.*.local

# Database
*.db
*.sqlite
*.sqlite3
data/cache.db
data/backups/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Logs
*.log
logs/

# Testing
.pytest_cache/
.coverage
htmlcov/

# Temporary files
*.tmp
*.temp
temp/
```

#### Tarea 0.2: Documentar API actual
**Archivo**: `API_DOCUMENTATION.md`
```markdown
# API Documentation

## Endpoints

### POST /analyze
Analiza una acción individual.

**Request:**
```json
{
  "ticker": "NVDA"
}
```

**Response:**
```json
{
  "ticker": "NVDA",
  "company_name": "NVIDIA Corporation",
  "metrics": { ... },
  "investment_scores": { ... },
  "rvc_scores": { ... }
}
```

### POST /api/comparar
Compara 2-5 acciones.

[Documentar el resto de endpoints...]
```

#### Tarea 0.3: Crear backup inicial
```bash
# Crear carpeta de backups
mkdir -p data/backups

# Backup del cache actual
cp data/cache.db data/backups/cache_backup_$(date +%Y%m%d).db

# Crear script de backup
cat > scripts/backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
sqlite3 data/cache.db ".backup 'data/backups/cache_$DATE.db'"
echo "Backup created: cache_$DATE.db"
EOF

chmod +x scripts/backup.sh
```

#### Tarea 0.4: Configurar logging básico
**Archivo**: `app.py` (agregar al inicio)
```python
import logging
from logging.handlers import RotatingFileHandler
import os

# Crear directorio de logs si no existe
if not os.path.exists('logs'):
    os.makedirs('logs')

# Configurar logging
file_handler = RotatingFileHandler(
    'logs/rvc_analyzer.log',
    maxBytes=10240000,  # 10MB
    backupCount=10
)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)

app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
app.logger.info('RVC Analyzer startup')
```

### ✅ Checklist Fase 0:

- [ ] .gitignore configurado
- [ ] API_DOCUMENTATION.md creado
- [ ] Backup inicial del cache
- [ ] Script de backup automático
- [ ] Logging básico configurado
- [ ] Git commit: "Preparativos para escalamiento"

---

<a name="fase-1"></a>
## 🔧 FASE 1: OPTIMIZACIÓN DEL CORE EXISTENTE
**Duración estimada**: 3-4 días
**Costo**: $0

### Objetivo:
Mejorar y optimizar el código existente antes de agregar nuevas funcionalidades.

---

### 📊 Tarea 1.1: Análisis y Refactoring del Comparador

**Problema identificado**: El comparador no hace comparación real, solo ordena por score.

**Solución**: Agregar análisis comparativo relativo.

**Archivo**: `comparative_analyzer.py` (NUEVO)
```python
"""
Módulo de análisis comparativo entre múltiples empresas.
Complementa al comparador básico con insights relativos.
"""

class ComparativeAnalyzer:
    """Analiza múltiples empresas y genera insights comparativos"""

    def __init__(self, companies_data: list):
        """
        Args:
            companies_data: Lista de dicts con {ticker, metrics, scores}
        """
        self.companies = companies_data
        self.metrics_to_compare = [
            'pe_ratio', 'peg_ratio', 'roe', 'roic',
            'debt_to_equity', 'revenue_growth', 'earnings_growth'
        ]

    def analyze(self) -> dict:
        """Genera análisis comparativo completo"""
        return {
            "leaders": self._identify_leaders(),
            "relative_scores": self._calculate_relative_scores(),
            "normalized_for_radar": self._normalize_for_radar(),
            "sector_comparison": self._compare_by_sector(),
            "valuation_spectrum": self._create_valuation_spectrum(),
            "quality_vs_price": self._plot_quality_vs_price(),
            "strengths_weaknesses": self._identify_strengths_weaknesses()
        }

    def _identify_leaders(self) -> dict:
        """Identifica quién lidera en cada dimensión"""
        leaders = {}

        # Mejor valoración (P/E más bajo)
        valid_pe = [(c['ticker'], c['metrics'].get('pe_ratio'))
                    for c in self.companies
                    if c['metrics'].get('pe_ratio')]
        if valid_pe:
            leaders['best_valuation'] = min(valid_pe, key=lambda x: x[1])

        # Mejor calidad (ROE más alto)
        valid_roe = [(c['ticker'], c['metrics'].get('roe'))
                     for c in self.companies
                     if c['metrics'].get('roe')]
        if valid_roe:
            leaders['best_quality'] = max(valid_roe, key=lambda x: x[1])

        # Mejor crecimiento
        valid_growth = [(c['ticker'], c['metrics'].get('revenue_growth'))
                        for c in self.companies
                        if c['metrics'].get('revenue_growth')]
        if valid_growth:
            leaders['best_growth'] = max(valid_growth, key=lambda x: x[1])

        # Mejor salud financiera (D/E más bajo)
        valid_de = [(c['ticker'], c['metrics'].get('debt_to_equity'))
                    for c in self.companies
                    if c['metrics'].get('debt_to_equity')]
        if valid_de:
            leaders['best_health'] = min(valid_de, key=lambda x: x[1])

        return leaders

    def _calculate_relative_scores(self) -> dict:
        """
        Calcula scores relativos (percentiles) entre el grupo.
        Ejemplo: Si NVDA tiene ROE de 45% y es el más alto del grupo,
        su relative_roe_score = 100. El más bajo = 0.
        """
        relative_scores = {}

        for company in self.companies:
            ticker = company['ticker']
            relative_scores[ticker] = {}

            for metric in self.metrics_to_compare:
                values = [c['metrics'].get(metric) for c in self.companies
                         if c['metrics'].get(metric) is not None]

                if not values or len(values) < 2:
                    continue

                company_value = company['metrics'].get(metric)
                if company_value is None:
                    continue

                # Calcular percentil (0-100)
                # Para métricas "lower is better" (P/E, D/E), invertir
                lower_is_better = metric in ['pe_ratio', 'peg_ratio', 'debt_to_equity']

                if lower_is_better:
                    # Invertir: el más bajo obtiene 100
                    max_val = max(values)
                    min_val = min(values)
                    if max_val != min_val:
                        percentile = 100 - ((company_value - min_val) / (max_val - min_val) * 100)
                    else:
                        percentile = 50
                else:
                    # Normal: el más alto obtiene 100
                    max_val = max(values)
                    min_val = min(values)
                    if max_val != min_val:
                        percentile = ((company_value - min_val) / (max_val - min_val) * 100)
                    else:
                        percentile = 50

                relative_scores[ticker][f'{metric}_percentile'] = round(percentile, 1)

        return relative_scores

    def _normalize_for_radar(self) -> dict:
        """
        Normaliza métricas para radar chart (0-100 scale).
        Permite comparar visualmente dimensiones diferentes.
        """
        normalized = {}

        dimensions = {
            'Valoración': ['pe_ratio', 'peg_ratio', 'price_to_book'],
            'Calidad': ['roe', 'roic', 'net_margin'],
            'Salud': ['debt_to_equity', 'current_ratio', 'quick_ratio'],
            'Crecimiento': ['revenue_growth', 'earnings_growth']
        }

        for company in self.companies:
            ticker = company['ticker']
            normalized[ticker] = {}

            for dimension, metrics in dimensions.items():
                scores = []

                for metric in metrics:
                    value = company['metrics'].get(metric)
                    if value is None:
                        continue

                    # Normalizar según rangos típicos de cada métrica
                    normalized_value = self._normalize_metric(metric, value)
                    scores.append(normalized_value)

                # Promedio de la dimensión
                if scores:
                    normalized[ticker][dimension] = round(sum(scores) / len(scores), 1)
                else:
                    normalized[ticker][dimension] = 0

        return normalized

    def _normalize_metric(self, metric: str, value: float) -> float:
        """
        Normaliza una métrica a escala 0-100 según rangos típicos.
        """
        # Definir rangos típicos (mín, ideal, máx)
        ranges = {
            'pe_ratio': (5, 15, 50, 'inverse'),      # Menor es mejor
            'peg_ratio': (0.5, 1, 3, 'inverse'),     # Menor es mejor
            'price_to_book': (0.5, 2, 10, 'inverse'),
            'roe': (0, 15, 50, 'direct'),            # Mayor es mejor
            'roic': (0, 12, 40, 'direct'),
            'net_margin': (0, 10, 40, 'direct'),
            'debt_to_equity': (0, 0.5, 2, 'inverse'),
            'current_ratio': (1, 2, 4, 'direct'),
            'quick_ratio': (0.5, 1.5, 3, 'direct'),
            'revenue_growth': (-10, 10, 100, 'direct'),
            'earnings_growth': (-10, 15, 150, 'direct')
        }

        if metric not in ranges:
            return 50  # Default neutral

        min_val, ideal_val, max_val, direction = ranges[metric]

        if direction == 'inverse':
            # Menor es mejor (P/E, D/E)
            if value <= ideal_val:
                return 100
            elif value >= max_val:
                return 0
            else:
                return 100 - ((value - ideal_val) / (max_val - ideal_val) * 100)
        else:
            # Mayor es mejor (ROE, crecimiento)
            if value >= ideal_val:
                return 100
            elif value <= min_val:
                return 0
            else:
                return (value - min_val) / (ideal_val - min_val) * 100

    def _compare_by_sector(self) -> dict:
        """Compara empresas del mismo sector"""
        sectors = {}

        for company in self.companies:
            sector = company['metrics'].get('sector', 'Unknown')
            if sector not in sectors:
                sectors[sector] = []
            sectors[sector].append(company['ticker'])

        return sectors

    def _create_valuation_spectrum(self) -> list:
        """
        Crea un espectro de valoración (barata → cara)
        basado en P/E ratio.
        """
        spectrum = []

        for company in self.companies:
            pe = company['metrics'].get('pe_ratio')
            if pe:
                spectrum.append({
                    'ticker': company['ticker'],
                    'pe_ratio': pe,
                    'classification': self._classify_valuation(pe)
                })

        spectrum.sort(key=lambda x: x['pe_ratio'])
        return spectrum

    def _classify_valuation(self, pe: float) -> str:
        """Clasifica valoración según P/E"""
        if pe < 10:
            return "Muy Barata"
        elif pe < 15:
            return "Barata"
        elif pe < 25:
            return "Razonable"
        elif pe < 35:
            return "Cara"
        else:
            return "Muy Cara"

    def _plot_quality_vs_price(self) -> dict:
        """
        Datos para scatter plot: Calidad (ROE) vs Precio (P/E)
        Identifica el cuadrante de cada empresa.
        """
        plot_data = []

        for company in self.companies:
            roe = company['metrics'].get('roe')
            pe = company['metrics'].get('pe_ratio')

            if roe and pe:
                # Determinar cuadrante
                high_quality = roe >= 15
                good_price = pe <= 25

                if high_quality and good_price:
                    quadrant = "Sweet Spot"
                    color = "green"
                elif high_quality and not good_price:
                    quadrant = "Premium/Cara"
                    color = "blue"
                elif not high_quality and good_price:
                    quadrant = "Value Trap?"
                    color = "orange"
                else:
                    quadrant = "Evitar"
                    color = "red"

                plot_data.append({
                    'ticker': company['ticker'],
                    'x': pe,           # P/E en eje X
                    'y': roe,          # ROE en eje Y
                    'quadrant': quadrant,
                    'color': color
                })

        return {
            "data": plot_data,
            "axes": {
                "x_label": "P/E Ratio (más bajo = mejor precio)",
                "y_label": "ROE % (más alto = mejor calidad)"
            },
            "quadrants": {
                "top_left": "Sweet Spot (Alta calidad, buen precio)",
                "top_right": "Premium (Alta calidad, cara)",
                "bottom_left": "Boring (Baja calidad, barata)",
                "bottom_right": "Value Trap (Baja calidad, cara)"
            }
        }

    def _identify_strengths_weaknesses(self) -> dict:
        """
        Identifica fortalezas y debilidades de cada empresa
        en relación al grupo.
        """
        analysis = {}

        for company in self.companies:
            ticker = company['ticker']
            strengths = []
            weaknesses = []

            # Obtener percentiles relativos
            relative = self._calculate_relative_scores().get(ticker, {})

            for metric, percentile in relative.items():
                metric_name = metric.replace('_percentile', '')

                if percentile >= 75:
                    strengths.append(f"{metric_name}: Top del grupo ({percentile:.0f}º percentil)")
                elif percentile <= 25:
                    weaknesses.append(f"{metric_name}: Rezagado ({percentile:.0f}º percentil)")

            analysis[ticker] = {
                "strengths": strengths[:3],      # Top 3 fortalezas
                "weaknesses": weaknesses[:3]     # Top 3 debilidades
            }

        return analysis
```

**Integración en app.py**:
```python
from comparative_analyzer import ComparativeAnalyzer

@app.route('/api/comparar', methods=['POST'])
def compare_stocks():
    # ... código existente ...

    # NUEVO: Análisis comparativo avanzado
    comparative = ComparativeAnalyzer(results)
    comparative_analysis = comparative.analyze()

    return jsonify({
        "empresas": results,
        "ranking": [r['ticker'] for r in results],
        "comparative_analysis": comparative_analysis  # NUEVO
    })
```

### ✅ Checklist Tarea 1.1:

- [ ] Crear `comparative_analyzer.py`
- [ ] Integrar en endpoint `/api/comparar`
- [ ] Testing con 3 empresas de sectores diferentes
- [ ] Testing con 5 empresas del mismo sector
- [ ] Validar que percentiles sumen correctamente
- [ ] Git commit: "Agregar análisis comparativo relativo"

---

### 📈 Tarea 1.2: Mejorar Visualización del Comparador

**Objetivo**: Aprovechar el nuevo análisis comparativo en el frontend.

**Archivo**: `static/comparador.js` (actualizar)
```javascript
// NUEVO: Renderizar análisis comparativo

function renderComparativeAnalysis(analysis) {
    const container = document.getElementById('comparative-insights');

    // 1. Líderes por dimensión
    const leaders = analysis.leaders;
    const leadersHTML = `
        <div class="leaders-grid">
            <div class="leader-card">
                <h4>🏆 Mejor Valoración</h4>
                <p class="leader-ticker">${leaders.best_valuation[0]}</p>
                <p class="leader-value">P/E: ${leaders.best_valuation[1].toFixed(2)}</p>
            </div>
            <div class="leader-card">
                <h4>⭐ Mejor Calidad</h4>
                <p class="leader-ticker">${leaders.best_quality[0]}</p>
                <p class="leader-value">ROE: ${leaders.best_quality[1].toFixed(1)}%</p>
            </div>
            <div class="leader-card">
                <h4>🚀 Mejor Crecimiento</h4>
                <p class="leader-ticker">${leaders.best_growth[0]}</p>
                <p class="leader-value">${leaders.best_growth[1].toFixed(1)}%</p>
            </div>
            <div class="leader-card">
                <h4>🏦 Mejor Salud</h4>
                <p class="leader-ticker">${leaders.best_health[0]}</p>
                <p class="leader-value">D/E: ${leaders.best_health[1].toFixed(2)}</p>
            </div>
        </div>
    `;

    // 2. Fortalezas y Debilidades
    const strengthsHTML = Object.entries(analysis.strengths_weaknesses)
        .map(([ticker, data]) => `
            <div class="strength-weakness-card">
                <h4>${ticker}</h4>
                <div class="strengths">
                    <h5>✅ Fortalezas</h5>
                    <ul>
                        ${data.strengths.map(s => `<li>${s}</li>`).join('')}
                    </ul>
                </div>
                <div class="weaknesses">
                    <h5>⚠️ Debilidades</h5>
                    <ul>
                        ${data.weaknesses.map(w => `<li>${w}</li>`).join('')}
                    </ul>
                </div>
            </div>
        `).join('');

    // 3. Scatter Plot Calidad vs Precio
    renderQualityVsPriceScatter(analysis.quality_vs_price);

    container.innerHTML = leadersHTML + strengthsHTML;
}

function renderQualityVsPriceScatter(plotData) {
    const traces = plotData.data.map(point => ({
        x: [point.x],
        y: [point.y],
        mode: 'markers+text',
        type: 'scatter',
        text: [point.ticker],
        textposition: 'top center',
        marker: {
            size: 15,
            color: point.color,
            opacity: 0.7
        },
        name: point.ticker
    }));

    const layout = {
        title: 'Calidad vs Precio',
        xaxis: { title: plotData.axes.x_label },
        yaxis: { title: plotData.axes.y_label },
        annotations: [
            {
                text: plotData.quadrants.top_left,
                xref: 'paper',
                yref: 'paper',
                x: 0.25,
                y: 0.95,
                showarrow: false,
                font: { color: 'green', size: 10 }
            },
            // ... más anotaciones de cuadrantes
        ]
    };

    Plotly.newPlot('quality-price-scatter', traces, layout);
}
```

**Archivo**: `templates/comparador.html` (agregar sección)
```html
<!-- Después de la sección de ranking -->
<section class="comparative-insights-section">
    <h2>Análisis Comparativo Avanzado</h2>
    <div id="comparative-insights"></div>

    <div class="chart-container">
        <div id="quality-price-scatter"></div>
    </div>
</section>
```

### ✅ Checklist Tarea 1.2:

- [ ] Actualizar `comparador.js` con nuevas funciones
- [ ] Agregar sección HTML en `comparador.html`
- [ ] Estilos CSS para leader-cards y strength-weakness-cards
- [ ] Testing visual con datos reales
- [ ] Git commit: "Mejorar visualización comparativa"

---

### 🗃️ Tarea 1.3: Optimizar Sistema de Caché

**Problema**: Caché actual es básico, sin métricas de hit rate.

**Solución**: Agregar estadísticas y limpieza automática.

**Archivo**: `cache_manager.py` (NUEVO)
```python
"""
Gestor avanzado de caché con estadísticas y limpieza automática.
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)

class CacheManager:
    """Gestor de caché SQLite con estadísticas"""

    def __init__(self, db_path: str = 'data/cache.db'):
        self.db_path = db_path
        self.stats = {
            'hits': 0,
            'misses': 0,
            'writes': 0,
            'expirations': 0
        }

    def get(self, ticker: str, max_age_days: int = 7) -> Optional[Dict]:
        """
        Obtiene datos del cache si no están expirados.

        Returns:
            dict con datos o None si no existe/expiró
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        cursor = conn.execute(
            "SELECT data, last_updated FROM financial_cache WHERE ticker = ?",
            (ticker,)
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            self.stats['misses'] += 1
            logger.info(f"Cache MISS: {ticker}")
            return None

        last_updated = datetime.fromisoformat(row['last_updated'])
        age = datetime.now() - last_updated

        if age > timedelta(days=max_age_days):
            self.stats['expirations'] += 1
            logger.info(f"Cache EXPIRED: {ticker} (age: {age.days} days)")
            return None

        self.stats['hits'] += 1
        logger.info(f"Cache HIT: {ticker}")
        return json.loads(row['data'])

    def set(self, ticker: str, data: Dict, source: str = 'multi') -> None:
        """Guarda datos en cache"""
        conn = sqlite3.connect(self.db_path)

        conn.execute(
            """
            INSERT OR REPLACE INTO financial_cache (ticker, data, last_updated, source)
            VALUES (?, ?, ?, ?)
            """,
            (ticker, json.dumps(data), datetime.now().isoformat(), source)
        )

        conn.commit()
        conn.close()

        self.stats['writes'] += 1
        logger.info(f"Cache WRITE: {ticker}")

    def get_stats(self) -> Dict:
        """Estadísticas de uso del cache"""
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0

        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("SELECT COUNT(*) as count FROM financial_cache")
        cache_size = cursor.fetchone()[0]
        conn.close()

        return {
            **self.stats,
            'total_requests': total_requests,
            'hit_rate': round(hit_rate, 2),
            'cache_size': cache_size
        }

    def clean_expired(self, max_age_days: int = 7) -> int:
        """
        Elimina entradas expiradas del cache.

        Returns:
            Número de entradas eliminadas
        """
        cutoff = (datetime.now() - timedelta(days=max_age_days)).isoformat()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "DELETE FROM financial_cache WHERE last_updated < ?",
            (cutoff,)
        )
        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        logger.info(f"Cache cleanup: {deleted} expired entries removed")
        return deleted

    def get_all_tickers(self, max_age_days: int = 7) -> List[str]:
        """
        Obtiene todos los tickers válidos en cache.

        Útil para Top Opportunities.
        """
        cutoff = (datetime.now() - timedelta(days=max_age_days)).isoformat()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            """
            SELECT ticker FROM financial_cache
            WHERE last_updated >= ?
            ORDER BY last_updated DESC
            """,
            (cutoff,)
        )

        tickers = [row[0] for row in cursor.fetchall()]
        conn.close()

        return tickers

    def get_size_bytes(self) -> int:
        """Tamaño del archivo de cache en bytes"""
        import os
        return os.path.getsize(self.db_path)
```

**Integración en app.py**:
```python
from cache_manager import CacheManager

cache_manager = CacheManager()

@app.route('/api/cache/stats', methods=['GET'])
def get_cache_stats():
    """Endpoint para monitorear cache"""
    stats = cache_manager.get_stats()
    size_mb = cache_manager.get_size_bytes() / (1024 * 1024)

    return jsonify({
        **stats,
        'size_mb': round(size_mb, 2)
    })

@app.route('/api/cache/clean', methods=['POST'])
def clean_cache():
    """Limpia cache expirado"""
    deleted = cache_manager.clean_expired(max_age_days=7)
    return jsonify({
        'deleted': deleted,
        'message': f'{deleted} entradas expiradas eliminadas'
    })
```

### ✅ Checklist Tarea 1.3:

- [ ] Crear `cache_manager.py`
- [ ] Integrar en `app.py`
- [ ] Crear endpoint `/api/cache/stats`
- [ ] Crear endpoint `/api/cache/clean`
- [ ] Testing de hit rate
- [ ] Git commit: "Optimizar sistema de cache con estadísticas"

---

### ✅ Checklist Completo Fase 1:

- [ ] Tarea 1.1: Análisis comparativo relativo ✅
- [ ] Tarea 1.2: Visualización avanzada comparador ✅
- [ ] Tarea 1.3: Cache manager con estadísticas ✅
- [ ] Testing integral de todas las mejoras
- [ ] Documentar cambios en CHANGELOG.md
- [ ] Git commit final: "Fase 1 completada: Optimización del core"

**Resultado esperado**: Core más robusto, comparador con insights reales, cache optimizado.

---

<a name="fase-2"></a>
## 🔍 FASE 2: TOP OPPORTUNITIES (BUSCADOR)
**Duración estimada**: 2-3 días
**Costo**: $0

### Objetivo:
Implementar sistema de ranking de mejores oportunidades basado en cache existente.

---

### 📊 Tarea 2.1: Backend del Buscador

**Archivo**: `opportunities_finder.py` (NUEVO)
```python
"""
Buscador de oportunidades de inversión basado en cache.
"""

import sqlite3
import json
from typing import List, Dict, Optional
from datetime import datetime, timedelta

class OpportunitiesFinder:
    """Encuentra las mejores oportunidades en el cache"""

    def __init__(self, db_path: str = 'data/cache.db'):
        self.db_path = db_path

    def find_opportunities(
        self,
        min_score: float = 70,
        sector: Optional[str] = None,
        max_pe: Optional[float] = None,
        min_roe: Optional[float] = None,
        max_age_days: int = 7,
        limit: int = 20
    ) -> List[Dict]:
        """
        Busca oportunidades con filtros opcionales.

        Args:
            min_score: Score mínimo de inversión
            sector: Filtrar por sector (opcional)
            max_pe: P/E máximo (opcional)
            min_roe: ROE mínimo (opcional)
            max_age_days: Edad máxima del cache en días
            limit: Número máximo de resultados

        Returns:
            Lista de oportunidades ordenadas por score
        """
        cutoff_date = (datetime.now() - timedelta(days=max_age_days)).isoformat()

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        # Query base
        query = """
            SELECT
                fc.ticker,
                fc.data,
                fc.last_updated,
                rs.score as investment_score,
                rs.classification,
                rs.breakdown
            FROM financial_cache fc
            INNER JOIN rvc_scores rs ON fc.ticker = rs.ticker
            WHERE
                json_extract(fc.data, '$.asset_type') = 'EQUITY'
                AND json_extract(fc.data, '$.analysis_allowed') = 1
                AND rs.score >= ?
                AND datetime(fc.last_updated) >= datetime(?)
        """

        params = [min_score, cutoff_date]

        # Filtros opcionales
        if sector:
            query += " AND json_extract(fc.data, '$.sector') = ?"
            params.append(sector)

        if max_pe:
            query += " AND CAST(json_extract(fc.data, '$.pe_ratio') AS REAL) <= ?"
            params.append(max_pe)

        if min_roe:
            query += " AND CAST(json_extract(fc.data, '$.roe') AS REAL) >= ?"
            params.append(min_roe)

        query += " ORDER BY rs.score DESC LIMIT ?"
        params.append(limit)

        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        # Procesar resultados
        opportunities = []
        for row in rows:
            data = json.loads(row['data'])
            breakdown = json.loads(row['breakdown'])

            opportunities.append({
                "ticker": row['ticker'],
                "company_name": data.get('company_name'),
                "sector": data.get('sector'),
                "investment_score": row['investment_score'],
                "classification": row['classification'],
                "current_price": data.get('current_price'),
                "market_cap": data.get('market_cap'),
                "pe_ratio": data.get('pe_ratio'),
                "roe": data.get('roe'),
                "revenue_growth": data.get('revenue_growth'),
                "debt_to_equity": data.get('debt_to_equity'),
                "breakdown": breakdown,
                "last_analyzed": row['last_updated'],
                "age_days": (datetime.now() - datetime.fromisoformat(row['last_updated'])).days
            })

        return opportunities

    def get_sectors(self) -> List[str]:
        """Obtiene lista de sectores disponibles en cache"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("""
            SELECT DISTINCT json_extract(data, '$.sector') as sector
            FROM financial_cache
            WHERE json_extract(data, '$.asset_type') = 'EQUITY'
            AND json_extract(data, '$.sector') IS NOT NULL
            ORDER BY sector
        """)

        sectors = [row[0] for row in cursor.fetchall()]
        conn.close()
        return sectors

    def get_summary_stats(self) -> Dict:
        """Estadísticas del cache para el dashboard"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        # Total de empresas analizadas
        cursor = conn.execute("""
            SELECT COUNT(*) as total
            FROM financial_cache
            WHERE json_extract(data, '$.asset_type') = 'EQUITY'
        """)
        total = cursor.fetchone()['total']

        # Distribución por score
        cursor = conn.execute("""
            SELECT
                CASE
                    WHEN score >= 80 THEN 'Excelente (80+)'
                    WHEN score >= 70 THEN 'Muy Bueno (70-79)'
                    WHEN score >= 60 THEN 'Bueno (60-69)'
                    WHEN score >= 50 THEN 'Aceptable (50-59)'
                    ELSE 'Bajo (<50)'
                END as category,
                COUNT(*) as count
            FROM rvc_scores
            GROUP BY category
            ORDER BY MIN(score) DESC
        """)
        distribution = {row['category']: row['count'] for row in cursor.fetchall()}

        # Sectores más representados
        cursor = conn.execute("""
            SELECT json_extract(data, '$.sector') as sector, COUNT(*) as count
            FROM financial_cache
            WHERE json_extract(data, '$.asset_type') = 'EQUITY'
            GROUP BY sector
            ORDER BY count DESC
            LIMIT 5
        """)
        top_sectors = {row['sector']: row['count'] for row in cursor.fetchall()}

        conn.close()

        return {
            'total_analyzed': total,
            'score_distribution': distribution,
            'top_sectors': top_sectors
        }
```

**Integración en app.py**:
```python
from opportunities_finder import OpportunitiesFinder

opportunities_finder = OpportunitiesFinder()

@app.route('/api/opportunities', methods=['GET'])
def get_opportunities():
    """
    Endpoint para buscar oportunidades.

    Query params:
        - min_score: int (default 70)
        - sector: str (optional)
        - max_pe: float (optional)
        - min_roe: float (optional)
        - limit: int (default 20)
    """
    min_score = request.args.get('min_score', 70, type=float)
    sector = request.args.get('sector', None)
    max_pe = request.args.get('max_pe', None, type=float)
    min_roe = request.args.get('min_roe', None, type=float)
    limit = request.args.get('limit', 20, type=int)

    opportunities = opportunities_finder.find_opportunities(
        min_score=min_score,
        sector=sector,
        max_pe=max_pe,
        min_roe=min_roe,
        limit=limit
    )

    sectors = opportunities_finder.get_sectors()
    stats = opportunities_finder.get_summary_stats()

    return jsonify({
        'opportunities': opportunities,
        'count': len(opportunities),
        'filters_applied': {
            'min_score': min_score,
            'sector': sector,
            'max_pe': max_pe,
            'min_roe': min_roe
        },
        'available_sectors': sectors,
        'summary_stats': stats,
        'warning': 'Datos basados en análisis previos (máx 7 días). Presiona "Actualizar" para refrescar.'
    })

@app.route('/api/opportunities/refresh', methods=['POST'])
def refresh_opportunities():
    """
    Actualiza todas las oportunidades del ranking.

    ⚠️ ADVERTENCIA: Consume muchas API calls.
    """
    tickers = request.json.get('tickers', [])

    if len(tickers) > 20:
        return jsonify({'error': 'Máximo 20 tickers por actualización'}), 400

    updated = []
    failed = []

    for ticker in tickers:
        try:
            # Forzar fetch fresh (bypass cache)
            metrics = data_agent.fetch_financial_data(ticker)
            cache_manager.set(ticker, metrics)

            # Recalcular scores
            if metrics.get('asset_type') == 'EQUITY':
                scores = investment_scorer.calculate_all_scores(metrics)
                # Guardar en rvc_scores...

            updated.append(ticker)
        except Exception as e:
            failed.append({'ticker': ticker, 'error': str(e)})

    return jsonify({
        'updated': updated,
        'failed': failed,
        'count_updated': len(updated),
        'count_failed': len(failed),
        'api_calls_used': len(tickers) * 4  # Estimado
    })
```

### ✅ Checklist Tarea 2.1:

- [ ] Crear `opportunities_finder.py`
- [ ] Integrar endpoints en `app.py`
- [ ] Testing con diferentes filtros
- [ ] Validar que query SQL funciona correctamente
- [ ] Git commit: "Backend del buscador de oportunidades"

---

[CONTINÚA EN SIGUIENTE SECCIÓN...]

---

**Contenido restante de la bitácora**:
- Tarea 2.2: Frontend del Buscador
- Tarea 2.3: Sistema de Actualización Selectiva
- Fase 3: Contexto de Mercado (VIX, CAPE, ciclos)
- Fase 4: Mejoras de UX (loading states, error handling)
- Fase 5: Sistema de Alertas (email/notificaciones)
- Fase 6-7: Preparación y Deploy Gratuito
- Fase 8: Testing con usuarios reales
- Fase 9: Migración a APIs pagadas
- Fase 10: Monetización

---

## 📌 CONTROL DE PROGRESO

### Estado Actual:
- [x] Fase 0: Preparativos ✅
- [ ] Fase 1: Optimización del Core (En progreso)
  - [ ] Tarea 1.1: Análisis comparativo
  - [ ] Tarea 1.2: Visualización
  - [ ] Tarea 1.3: Cache manager
- [ ] Fase 2: Top Opportunities
- [ ] Fase 3: Contexto de Mercado
- [ ] Fase 4: Mejoras UX
- [ ] Fase 5: Sistema de Alertas
- [ ] Fase 6: Preparación Deploy
- [ ] Fase 7: Deploy Gratuito
- [ ] Fase 8: Testing Usuarios
- [ ] Fase 9: Migración APIs Pagadas
- [ ] Fase 10: Monetización

### Próxima Sesión:
Continuar con **Fase 1, Tarea 1.1**: Implementar análisis comparativo relativo.

---

**Última actualización**: 2025-10-22
**Próxima revisión**: Después de completar Fase 1
