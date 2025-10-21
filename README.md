# RVC Analyzer con Agente IA

Aplicación Flask que realiza análisis fundamental utilizando un agente inteligente con scraping multifuente, caché local y un dashboard interactivo.

## Características
- Descarga métricas desde fuentes públicas (Yahoo Finance, Finviz, MarketWatch) con fallback a datos de ejemplo.
- Caché SQLite (`data/cache.db`) con botón “Limpiar caché” para refrescar selectivamente un ticker o toda la base.
- Calculadora RVC alineada con las dimensiones Valoración / Calidad / Salud / Crecimiento y tolerante a datos parciales (recalcula P/E y PEG, estima ROIC/ROE cuando faltan).
- Panel web que muestra score desglosado, nivel de confianza, advertencias de saneamiento e información de procedencia/fecha por métrica (tooltips).

## Requisitos
- Python 3.11+
- Dependencias listadas en `requirements.txt`

```bash
pip install -r requirements.txt
```

## Estructura
```
rcv_proyecto/
├── app.py
├── data_agent.py
├── rvc_calculator.py
├── requirements.txt
├── data/
│   └── cache.db         # se genera al ejecutar
├── templates/
│   └── index.html
└── static/
    ├── app.js
    └── style.css
```

## Uso
1. Inicia la aplicación: `python app.py`
2. Abre el navegador en `http://localhost:5000` e ingresa un ticker.
3. El agente intentará completar los campos con Yahoo; si falla, continuará con Finviz, MarketWatch y, de último recurso, el fallback de ejemplo.
4. Usa el botón “Limpiar caché” para forzar una nueva obtención (toma el ticker escrito si existe; vacío limpia toda la caché).

## Metodología RVC

| Dimensión | Peso | Métricas principales | Umbrales destacados |
|-----------|------|----------------------|---------------------|
| Valoración | 40% | P/E, PEG, P/B | P/E < 15 → 100 pts, PEG ≈ 1 → 85+, P/B < 3 → 75 |
| Calidad    | 35% | ROE, ROIC, márgenes | ROE > 20% → 85+, ROIC > 15% → 85+, márgenes > 20% → 80 |
| Salud      | 15% | Deuda/Patrimonio, current y quick ratio | D/E < 0.5 → 100, Current > 2 → 100 |
| Crecimiento| 10% | Crecimiento de ingresos y beneficios | +20% en ventas → 85+, +15% en beneficios → 80 |

Clasificación final:
- **🟢 70–100 — Razonable o mejor**
- **🟡 50–69 — Intermedio / Observar**
- **🔴 0–49 — Exigente / Sobrevalorada**

## Personalización
- Extiende `DataAgent` con nuevas fuentes o llaves API (por ejemplo, Macrotrends, Alpha Vantage).
- Ajusta el tiempo de vida de la caché en `app.py` si necesitas refrescos más agresivos.
- Modifica pesos o umbrales del scoring en `rvc_calculator.py`.

## Advertencia
Las métricas provienen de páginas públicas gratuitas y pueden sufrir cambios sin previo aviso. Usa este proyecto con fines educativos y contrasta la información con fuentes oficiales antes de tomar decisiones de inversión.
