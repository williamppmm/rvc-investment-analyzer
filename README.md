# 🎯 RVC Investment Analyzer

**Radar de Valoración y Calidad** — Sistema de análisis fundamental para encontrar empresas de calidad a precio justo.

> 🎓 **Enfoque educativo**: Diseñado para inversores de largo plazo que buscan fundamentos sólidos, no especulación ni trading.

---

## 🌟 ¿Qué es RVC?

RVC es una aplicación web completa que te ayuda a identificar las mejores oportunidades de inversión basándose en:

- ✅ **Calidad del negocio** — ROE, ROIC, márgenes operativos
- 💰 **Valoración justa** — P/E, PEG, P/B
- 🏥 **Salud financiera** — Deuda, liquidez, solvencia
- 📈 **Potencial de crecimiento** — Ingresos, beneficios, expansión

**Para quién**: Inversores de largo plazo (10+ años), personas que invierten mes a mes (DCA), quienes buscan calidad sobre especulación.

---

## ✨ **Características Destacadas (v2.0)**

### 🎨 **Diseño Profesional Modernizado**
- **Iconografía SVG** - 30+ iconos Lucide en sprite centralizado
- **Gráficos Plotly 2.0** - Efecto lollipop, paleta Tailwind moderna
- **Tipografía Inter** - Sistema profesional sans-serif
- **Paleta actualizada** - Verde esmeralda, ámbar, naranja, rojo
- **Responsive total** - Optimizado para móvil, tablet y desktop
- **Splash Screen** - Video de logo RVC en primera carga (2-3s, skippable)

### 💎 **Sistema Freemium**
- **FREE** - 20 consultas diarias, acceso completo
- **PRO** - 200 consultas/día, $3 USD/30 días
- **Licencias** - Sistema con contador de 30 días
- **Modal profesional** - Comparativa visual de planes

---

## 🚀 Características Principales

### 1️⃣ Analizador Individual
Evalúa cualquier acción con un sistema de **4 scores complementarios**:

- **Quality Score** (0-100): ¿Qué tan buena es la empresa?
- **Valuation Score** (0-100): ¿Qué tan caro está el precio?
- **Financial Health Score** (0-100): ¿Qué tan sólida es financieramente?
- **Growth Score** (0-100): ¿Qué tanto está creciendo?
- **Investment Score** (0-100): ¿Vale la pena comprar AHORA?

Clasificación automática en 6 categorías:
- 🏆 **SWEET SPOT** — Alta calidad, precio razonable (el ideal)
- ⭐ **PREMIUM** — Excelente calidad, precio alto justificado
- 💎 **VALOR** — Calidad decente, precio bajo (oportunidad)
- ⚠️ **CARA** — Calidad aceptable, precio muy alto
- 🪤 **TRAMPA** — Baja calidad, precio bajo (peligro)
- � **EVITAR** — Baja calidad, sobrevalorada

**Nuevas características v2.0**:
- ✅ Iconos SVG profesionales en toda la interfaz
- ✅ Glosario interactivo con 60+ términos
- ✅ Tooltips educativos inline
- ✅ Breakdown detallado por pilar

### 2️⃣ Comparador de Acciones **[MODERNIZADO v2.0]**
Compara hasta **5 acciones simultáneamente** lado a lado con gráficos profesionales:

**Gráficos Plotly Modernizados**:
- 📊 **Scatter Plot** - Mapa Calidad vs Valoración con zona ideal
- 📈 **Bar Chart Lollipop** - Ranking visual con efecto stems + heads
- 🎯 **Radar Chart** - Perfil multidimensional (top 3 empresas)

**Características**:
- ✅ Tabla comparativa completa con iconos SVG
- ✅ Ranking automático con medallas coloreadas
- ✅ Paleta Tailwind moderna (verde esmeralda, ámbar, naranja, rojo)
- ✅ Configuración centralizada para consistencia
- ✅ Validación robusta de datos (safeNum, clamp01)
- ✅ Responsive automático en gráficos
- ✅ Breakdown por pilares detallado
- ✅ Conclusiones automáticas (mejor/peor opción)
- ✅ **Guarda scores en BD** para el ranking

### 3️⃣ Calculadora de Inversiones
Simulador DCA (Dollar Cost Averaging) con **4 módulos interactivos**:

**Módulo 1: Plan de Jubilación**
- Proyección con ajuste por inflación
- Aportes mensuales crecientes
- Límite configurable ($1,000,000)
- Tabla anual completa

**Módulo 2: Dollar Cost Averaging**
- 3 escenarios (conservador 7%, moderado 10%, optimista 12%)
- Timing del mercado (normal, crisis -40%, burbuja +40%)
- Visualización del impacto de volatilidad
- Formateo con separadores de miles

**Módulo 3: Lump Sum vs DCA**
- Inversión única vs mensual
- Comparación directa
- Análisis de ventajas
- Gráfico comparativo

**Módulo 4: Interés Compuesto**
- Visualización del poder del interés
- Separación: aportes vs intereses
- Proyección a largo plazo
- Disclaimer educativo visible

### 4️⃣ Ranking RVC (Top Opportunities)
Sistema completo de clasificación de mejores oportunidades:

**Funcionalidades**:
- ✅ Ranking dinámico de tickers analizados
- ✅ **6 filtros interactivos**: Score mín, sector, ordenamiento, límite, búsqueda, fechas
- ✅ Estadísticas en tiempo real (total, promedio, sectores)
- ✅ Medallas SVG coloreadas (oro, plata, bronce)
- ✅ Iconos de categoría profesionales
- ✅ Badge de nivel de confianza
- ✅ Enlace directo al análisis individual
- ✅ Estados UX completos (loading, error, vacío)
- ✅ Conversión automática de monedas

### 5️⃣ Sistema de Datos Inteligente
- **7 fuentes de datos** con fallbacks automáticos:
  - Yahoo Finance, Finviz, MarketWatch
  - Alpha Vantage, Twelve Data, FMP
  - Datos de ejemplo como último recurso
- **Caché SQLite** (7 días TTL) para optimización
- **Clasificación automática** de activos (EQUITY, ETF, REIT, CRYPTO)
- **Soporte multi-moneda** (USD, EUR, GBP, CAD, MXN, etc.)
- **Análisis especializado de ETFs**
- **Health check endpoint** (`/health`) con estado de proveedores

### 6️⃣ UX Educativa y Accesible **[MEJORADO v2.0]**
- **Glosario interactivo** con 60+ términos financieros
- **Tooltips inline** para conceptos técnicos
- **Iconografía SVG** - 30+ iconos Lucide profesionales
- **Disclaimers destacados** - Clase dedicada con fondo de advertencia
- **Texto justificado** - Mejor legibilidad en párrafos
- **Responsive design** optimizado para todos los dispositivos
- **Variables CSS centralizadas** para temas consistentes
- **Tipografía moderna** - Inter system font

---

## 📦 Instalación

### Requisitos
- Python 3.11+
- pip (gestor de paquetes)

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/williamppmm/rvc-investment-analyzer.git
cd rvc-investment-analyzer

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. (Opcional) Configurar APIs premium
# Copiar .env.example a .env y agregar tus claves
cp .env.example .env

# 4. Ejecutar la aplicación
python app.py

# 5. Abrir navegador en http://localhost:5000
```

---

## 🏗️ Estructura del Proyecto

```
rcv_proyecto/
├── app.py                          # Aplicación Flask principal
├── scoring_engine.py               # Motor de 3 scores (Investment)
├── rvc_calculator.py               # Calculadora RVC (Legacy)
├── data_agent.py                   # Agente de recolección de datos
├── investment_calculator.py        # Simulador DCA
├── asset_classifier.py             # Clasificador de activos
├── etf_analyzer.py                 # Análisis especializado ETFs
│
├── services/                       # Integraciones con APIs
│   ├── alpha_vantage.py           # Alpha Vantage API
│   ├── twelve_data.py             # Twelve Data API
│   └── fmp.py                     # Financial Modeling Prep
│
├── data/
│   ├── cache.db                   # Caché SQLite (autogenerado)
│   └── asset_classifications.json # Clasificaciones de activos
│
├── templates/                      # Plantillas HTML
│   ├── base.html                  # Layout base
│   ├── index.html                 # Analizador individual
│   ├── comparador.html            # Comparador de acciones
│   └── calculadora.html           # Calculadora DCA
│
├── static/                         # Assets estáticos
│   ├── style.css                  # CSS global unificado
│   ├── app.js                     # JavaScript index
│   ├── comparador.js              # JavaScript comparador
│   ├── calculadora.js             # JavaScript calculadora
│   ├── glossary.js                # Glosario interactivo
│   └── img/                       # Imágenes y logos
│
├── logs/                           # Logs de aplicación
├── scripts/                        # Scripts de utilidad
│   ├── backup.ps1                 # Backup Windows
│   └── backup.sh                  # Backup Unix/Mac
│
├── README.md                       # Este archivo
├── DEVELOPMENT_ROADMAP.md         # Roadmap de desarrollo
├── API_ENDPOINTS_GUIDE.md         # Guía de endpoints de la API REST
├── TECHNICAL_DOCUMENTATION.md    # Documentación técnica interna
├── LOGGING.md                     # Sistema de logging
└── requirements.txt               # Dependencias Python
```

---

## 📊 Metodología de Scoring

### Investment Score (Principal)
Combina 4 dimensiones con pesos balanceados:

| Dimensión | Peso | Métricas Clave | Rango Objetivo |
|-----------|------|----------------|----------------|
| **Calidad** | 40% | ROE, ROIC, márgenes | ROE > 20%, ROIC > 15% |
| **Valoración** | 35% | P/E, PEG, P/B | P/E < 15, PEG ≈ 1, P/B < 3 |
| **Salud** | 15% | D/E, Current Ratio | D/E < 0.5, Current > 2 |
| **Crecimiento** | 10% | Revenue/Earnings growth | > 15% anual |

### Clasificación Final

#### Por Investment Score:
- 🟢 **85-100**: Compra Fuerte — Excelente oportunidad
- 🟢 **70-84**: Compra — Buena inversión
- 🟡 **55-69**: Mantener — Vigilar de cerca
- 🟠 **40-54**: Precaución — Revisar fundamentos
- 🔴 **0-39**: Evitar — Alto riesgo

#### Por Categoría (Quality + Valuation):
```
                   VALORACIÓN
                Baja    Media    Alta
            ┌────────┬────────┬────────┐
     Alta   │  💎    │  🏆    │  📈   │
CALIDAD     │ Gema   │ Clase  │ Creci-│
            │ Oculta │ Mundial│ miento│
            ├────────┼────────┼────────┤
    Media   │  💰    │  ⚖️    │  ⚠️   │
            │ Valor  │ Equili-│ Sobre- │
            │Razona- │  brado │valuada│
            │  ble   │        │        │
            ├────────┼────────┼────────┤
    Baja    │  ⚠️    │  🤔    │  🚫   │
            │Trampa  │ Dudoso │ Evitar│
            │ Valor  │        │        │
            └────────┴────────┴────────┘
```

---

## 🎯 Casos de Uso

### Para Principiantes
1. Analiza tu primera acción en el **Analizador Individual**
2. Lee los tooltips para entender cada métrica
3. Usa la **Calculadora DCA** para simular tu plan de ahorro
4. Compara 2-3 acciones populares (AAPL, MSFT, GOOGL)

### Para Inversores Intermedios
1. Compara sectores completos con el **Comparador**
2. Filtra por Quality Score > 75 y Valuation Score > 65
3. Simula el impacto de **timing del mercado** con la calculadora
4. Exporta comparaciones para análisis offline

### Para Inversores Avanzados
1. Analiza empresas de pequeña capitalización (small caps)
2. Identifica **gemas ocultas** con alta calidad y baja valoración
3. Combina con análisis técnico externo
4. Usa la API REST para integraciones custom

---

## 🔮 Roadmap (Próximas Funcionalidades)

### 🎯 Fase 2: Buscador de Oportunidades
**Estado**: En planificación
- Ranking de mejores acciones del caché
- Filtros por sector, market cap, scores
- Top 20 Investment Scores
- Alertas de nuevas oportunidades

### 🌍 Fase 3: Contexto de Mercado
**Estado**: En diseño
- Indicadores macro (Fear & Greed Index)
- Valuación histórica (Shiller P/E)
- Ciclo de mercado (Bull/Bear)
- Señales de timing general

### 🔔 Fase 5: Sistema de Alertas
**Estado**: Propuesto
- Alertas de precio objetivo
- Notificaciones de cambios en scores
- Watchlist personalizada
- Email/Telegram integrations

### 🚀 Fase 6-7: Deploy Cloud
**Estado**: Análisis técnico completado
- Hosting gratuito (Render/Railway)
- Base de datos PostgreSQL
- CDN para assets estáticos
- SSL/HTTPS automático

Ver detalles completos en [DEVELOPMENT_ROADMAP.md](DEVELOPMENT_ROADMAP.md)

---

## 🛠️ Uso Avanzado

### API REST Endpoints

```bash
# Analizar una acción
POST /analyze
Body: {"ticker": "AAPL"}

# Comparar múltiples acciones
POST /api/comparar
Body: {"tickers": ["AAPL", "MSFT", "GOOGL"]}

# Calcular inversión DCA
POST /api/calcular-inversion
Body: {
  "monthly_amount": 500,
  "years": 20,
  "scenario": "moderado"
}

# Limpiar caché
POST /cache/clear
Body: {"ticker": "AAPL"}  # Opcional: específico o total
```

Ver documentación completa en [API_ENDPOINTS_GUIDE.md](API_ENDPOINTS_GUIDE.md)

### Variables de Entorno

Crea un archivo `.env` con:

```env
# APIs Premium (Opcional)
ALPHA_VANTAGE_API_KEY=tu_clave_aqui
TWELVE_DATA_API_KEY=tu_clave_aqui
FMP_API_KEY=tu_clave_aqui

# Configuración
LOG_LEVEL=INFO
CACHE_TTL_DAYS=7
RVC_SECRET_KEY=change-me-in-production
```

### Personalización del Scoring

Edita `scoring_engine.py` para ajustar pesos:

```python
self.quality_weights = {
    "roe": 0.40,              # Aumenta si priorizas rentabilidad
    "roic": 0.35,
    "operating_margin": 0.15,
    "net_margin": 0.10,
}
```

---

## 📚 Recursos Adicionales

- **[DEVELOPMENT_ROADMAP.md](DEVELOPMENT_ROADMAP.md)**: Plan de desarrollo detallado por fases
- **[API_ENDPOINTS_GUIDE.md](API_ENDPOINTS_GUIDE.md)**: Guía práctica de endpoints de la API REST
- **[TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md)**: Documentación técnica y arquitectura interna
- **[LOGGING.md](LOGGING.md)**: Sistema de logs y debugging
- **[FREEMIUM_SYSTEM.md](FREEMIUM_SYSTEM.md)**: Documentación completa del modelo freemium
- **[SPLASH_SCREEN.md](SPLASH_SCREEN.md)**: Guía del splash screen con video de logo
- **[Glosario Interactivo](static/glossary.js)**: 60+ términos financieros explicados

---

## ⚠️ Advertencias Importantes

1. **No es asesoría financiera**: Este proyecto es educativo. Consulta con profesionales antes de invertir.
2. **Datos de fuentes públicas**: Pueden contener errores o estar desactualizados.
3. **Limitaciones de APIs gratuitas**: Rate limits pueden afectar la disponibilidad.
4. **Proyecciones != Garantías**: Los retornos históricos no garantizan resultados futuros.
5. **Riesgo de mercado**: Toda inversión conlleva riesgo de pérdida de capital.

**Úsalo como punto de partida para tu análisis, no como única fuente de decisión.**

---

## 🤝 Contribuciones

¿Quieres mejorar RVC? ¡Genial!

1. Fork el proyecto
2. Crea una rama (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -m 'Agrega nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

Ver [CONTRIBUTING.md](CONTRIBUTING.md) para lineamientos detallados.

---

## 📄 Licencia

Este proyecto es de código abierto bajo licencia MIT. Ver [LICENSE](LICENSE) para más detalles.

---

## 👤 Autor

**William Pérez**
- GitHub: [@williamppmm](https://github.com/williamppmm)
- Proyecto: [rvc-investment-analyzer](https://github.com/williamppmm/rvc-investment-analyzer)

---

## 🙏 Agradecimientos

- Datos de Yahoo Finance, Finviz, MarketWatch
- Metodología inspirada en inversores value como Warren Buffett, Peter Lynch
- Comunidad open source de Python y Flask

---

<div align="center">

**⭐ Si te resulta útil, considera darle una estrella al proyecto ⭐**

Made with ❤️ for long-term investors

</div>
