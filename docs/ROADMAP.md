# Roadmap y Plan de Mejoras - RVC Investment Analyzer

Estado del proyecto, fases completadas y trabajo pendiente.

**Última actualización:** 26 de octubre de 2025
**Versión:** 3.0 — Sistema de Análisis Avanzado

---

## Estado Actual

```
Fase A ✅  Top Opportunities System
Fase B ✅  Modernización UI
Fase C ✅  Calculadora Educativa Avanzada
Fase D ✅  Sistema de Análisis Avanzado (TIER1/TIER2 + sector-relativo)
Fase E 🚀  Deploy a Producción (PRÓXIMA)
Fase F 💰  Monetización y Features Premium (FUTURA)
```

### Métricas del Proyecto (Post Fase D)

| Métrica | Valor |
|---------|-------|
| Líneas de código | ~12,000 (Python, JS, CSS, HTML) |
| Tests unitarios | 30+ (100% passing) |
| Endpoints API | 14 documentados |
| Páginas principales | 5 (Index, Comparador, Calculadora, Ranking, About) |
| Sectores con benchmarks | 11 |
| Métricas en DataAgent | 33+ |
| Carga promedio | < 2 segundos |

---

## Fases Completadas

### ✅ Fase A — Top Opportunities System

- Endpoint `GET /api/top-opportunities` con 6 filtros (sector, score mínimo, ordenamiento, límite)
- Frontend web completo en `/top-opportunities` con tabla dinámica y estados UX
- 9 tests unitarios (100% passing), colección Postman integrada
- Performance: < 500ms con 18 tickers cacheados

### ✅ Fase B — Optimización y Modernización UI

- Sistema de iconografía SVG: 30+ iconos Lucide en sprite centralizado
- Gráficos Plotly modernizados: efecto lollipop, paleta Tailwind, radar charts
- Paleta de colores actualizada (verde esmeralda, ámbar, naranja, rojo)
- Splash screen con video del logo (2–3s, skippable, cooldown 24h)
- Sistema freemium: FREE (20/día) vs PRO ($3/mes)

### ✅ Fase C — Calculadora Educativa Avanzada

- Valores reales deflactados: `valor_real = valor_nominal / (1 + π)^años`
- Tabla anual agregada (mensual → anual)
- Comparación visual: tarjetas nominales (azul) vs reales (verde)
- Tooltips educativos sobre poder adquisitivo
- Contador de visitas SQLite con filtro anti-bots
- 12 tests unitarios (100% passing)

### ✅ Fase D — Sistema de Análisis Avanzado

Cinco mejoras críticas implementadas al motor de scoring:

| # | Mejora | Prioridad | Estado |
|---|--------|-----------|--------|
| 1 | Dispersión entre fuentes (CV) | P0 | ✅ |
| 2 | Normalización TTM/MRQ/MRY | P0 | ✅ |
| 3 | Valoración TIER1: EV/EBIT + FCF Yield | P1 | ✅ |
| 4 | Scores sector-relativos (z-scores, 11 sectores) | P1 | ✅ |
| 6 | Health TIER1: Net Debt/EBITDA + Interest Coverage | P1 | ✅ |

Ver detalles técnicos en [docs/METHODOLOGY.md](METHODOLOGY.md).

---

## Mejoras Pendientes del Sistema de Scoring

| # | Mejora | Prioridad | Complejidad |
|---|--------|-----------|-------------|
| 5 | Estabilidad de calidad (consistencia multi-período) | P2 | Media |
| 7 | Jerarquía de crecimiento (TTM > Forward > 5Y para growth) | P2 | Baja |
| 8 | Winsorización de outliers (limitar métricas extremas) | P2 | Media |
| 9 | Normalización a peers directo (percentil en industria) | P3 | Muy alta |
| 10 | Confidence-aware recommendations (degradar si confidence < 70%) | P2 | Baja |

---

## Fase E — Deploy a Producción (Próxima)

### Infraestructura

| Servicio | Plataforma | Costo |
|----------|------------|-------|
| Servidor web | Railway.app (free tier) | $0–$5/mes |
| Base de datos | Railway PostgreSQL | $0–$5/mes |
| APIs de datos | FMP Starter (a futuro) | $29/mes |

### Tareas para Deploy

- [ ] Configurar `requirements.txt` y `Procfile` para Railway
- [ ] Variables de entorno en Railway (ver [docs/OPERATIONS.md](OPERATIONS.md))
- [ ] PostgreSQL para persistencia de visitas y cache
- [ ] Pruebas de carga básicas
- [ ] Dominio personalizado (opcional)

### Criterios de Éxito Fase E

- App accesible públicamente
- PostgreSQL activo (visitas persistentes entre deploys)
- Logs accesibles vía Railway dashboard
- Uptime > 95%

---

## Fase F — Monetización y Features Premium (Futura)

### Prioridad Alta

- [ ] Página `/planes` con comparativa detallada FREE vs PRO
- [ ] Integración PayPal/Stripe para pagos automáticos
- [ ] Email automático al generar licencia y al vencer

### Prioridad Media

- [ ] Dashboard de administración web (licencias, stats)
- [ ] Plan anual ($30 USD = 2 meses gratis)
- [ ] Sistema de referidos (10% descuento)

### Prioridad Baja

- [ ] Alertas por email (ticker baja de precio objetivo)
- [ ] Exportación de reportes PDF
- [ ] API pública para desarrolladores
- [ ] Buscador de oportunidades por criterios personalizados
- [ ] Contexto de mercado (índices, macro)

---

## Estrategia de Datos

### Ahora (MVP)
Scraping gratuito: Yahoo Finance → Finviz → MarketWatch (cascada)

### Producción (Fase E+)
Migrar a Financial Modeling Prep (FMP):
- **Starter $29/mes:** 15,000 requests/mes (~500/día) — suficiente para inicio
- **Professional $99/mes:** 100,000 requests/mes — para escalar

Ver detalles en [docs/ARCHITECTURE.md — Sección 9](ARCHITECTURE.md#9-plan-de-migración-a-apis-pagadas).

---

## Historial de Commits Clave

| Mejora | Commits |
|--------|---------|
| Mejora #2 Normalización | 1fec754, 4e3c9e3 |
| Mejora #3 TIER1 Valoración | e23fd25, 4abecf7, ed5e3c8 |
| Mejora #4 Sector-relativo | 778fce4, ee91d49 |
| Mejora #6 Health TIER1 | 2e0e158, 8dcd323 |
