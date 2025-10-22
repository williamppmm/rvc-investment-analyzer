# Sistema de Logging - RVC Analyzer

**Versión**: 1.0
**Última actualización**: Octubre 2025

---

## RESUMEN

RVC Analyzer implementa un sistema robusto de logging con:
- ✅ Rotación automática de archivos (10 MB máximo)
- ✅ Separación de logs normales y errores
- ✅ Formato detallado con timestamps y líneas de código
- ✅ Configuración flexible por variable de entorno
- ✅ Tracking de performance (tiempo de respuesta)
- ✅ Seguimiento de cache hits/misses
- ✅ Registro de IPs para análisis de uso

---

## ARCHIVOS DE LOG

### Ubicación

Todos los logs se guardan en:
```
rcv_proyecto/
└── logs/
    ├── rvc_app.log         # Log principal (rotación: 5 archivos × 10 MB)
    ├── rvc_app.log.1       # Backup 1
    ├── rvc_app.log.2       # Backup 2
    ├── ...
    ├── errors.log          # Solo errores (rotación: 3 archivos × 10 MB)
    ├── errors.log.1
    └── errors.log.2
```

**NOTA**: La carpeta `logs/` está incluida en `.gitignore` y NO se sube a Git.

---

## NIVELES DE LOGGING

### Configuración

El nivel de logging se controla con la variable de entorno `LOG_LEVEL`:

```bash
# En .env (crear si no existe)
LOG_LEVEL=DEBUG   # Para desarrollo
LOG_LEVEL=INFO    # Para producción (default)
LOG_LEVEL=WARNING # Solo advertencias y errores
LOG_LEVEL=ERROR   # Solo errores críticos
```

### Jerarquía de Niveles

| Nivel | Valor Numérico | Uso | Ejemplo |
|-------|----------------|-----|---------|
| `DEBUG` | 10 | Debugging detallado | Variables, estados internos |
| `INFO` | 20 | **Operaciones normales** (default) | Requests, cache hits, análisis completados |
| `WARNING` | 30 | Situaciones anormales pero manejables | Cache expirado, datos incompletos |
| `ERROR` | 40 | Errores que impiden operación | Falla al obtener datos, excepción en endpoint |
| `CRITICAL` | 50 | Errores que requieren atención inmediata | Falla de DB, crash de aplicación |

---

## FORMATO DE LOGS

### Estructura

```
YYYY-MM-DD HH:MM:SS - logger_name - LEVEL - [file.py:line] - mensaje
```

### Ejemplo Real

```log
2025-10-22 14:32:15 - rvc_app - INFO - [app.py:292] - ==================================================
2025-10-22 14:32:15 - rvc_app - INFO - [app.py:293] - ANALYZE REQUEST - Ticker: AAPL | IP: 127.0.0.1
2025-10-22 14:32:15 - rvc_app - INFO - [app.py:299] - ✓ Cache HIT - Ticker: AAPL | Age: 0:15:23
2025-10-22 14:32:16 - rvc_app - INFO - [app.py:331] - ✓ Analysis completado - Ticker: AAPL | Tiempo: 0.85s | Score: 78.5
2025-10-22 14:32:16 - rvc_app - INFO - [app.py:333] - ==================================================
```

---

## EVENTOS REGISTRADOS

### 1. Inicio de Aplicación

**Logger**: `rvc_app`
**Nivel**: `INFO`

```log
2025-10-22 14:30:00 - rvc_app - INFO - [app.py:85] - ============================================================
2025-10-22 14:30:00 - rvc_app - INFO - [app.py:86] - RVC Analyzer - Iniciando aplicación
2025-10-22 14:30:00 - rvc_app - INFO - [app.py:87] - Directorio base: C:\rcv_proyecto
2025-10-22 14:30:00 - rvc_app - INFO - [app.py:88] - Directorio de datos: C:\rcv_proyecto\data
2025-10-22 14:30:00 - rvc_app - INFO - [app.py:89] - Base de datos: C:\rcv_proyecto\data\cache.db
2025-10-22 14:30:00 - rvc_app - INFO - [app.py:90] - Nivel de logging: INFO
2025-10-22 14:30:00 - rvc_app - INFO - [app.py:91] - ============================================================
```

---

### 2. Análisis de Ticker (`POST /analyze`)

#### Request Exitoso

```log
==================================================
ANALYZE REQUEST - Ticker: NVDA | IP: 192.168.1.100
✓ Cache MISS - Fetching fresh data: NVDA
✓ Fresh data saved to cache: NVDA
✓ Analysis completado - Ticker: NVDA | Tiempo: 3.24s | Score: 85.2
==================================================
```

#### Request con Error

```log
==================================================
ANALYZE REQUEST - Ticker: INVALID | IP: 192.168.1.100
✗ Cache MISS - Fetching fresh data: INVALID
ERROR - No se encontraron datos suficientes - Ticker: INVALID
==================================================
```

#### Cache Hit

```log
==================================================
ANALYZE REQUEST - Ticker: AAPL | IP: 127.0.0.1
✓ Cache HIT - Ticker: AAPL | Age: 0:15:23.456789
✓ Analysis completado - Ticker: AAPL | Tiempo: 0.12s | Score: 78.5
==================================================
```

#### Cache Obsoleto

```log
Cache obsoleto (sin asset_type) - Refrescando: TSLA
```

```log
Cache obsoleto (schema v2 vs v3) - Refrescando: MSFT
```

#### Request Inválido

```log
WARNING - Analyze request sin ticker - IP: 192.168.1.100
```

---

### 3. Comparación de Tickers (`POST /api/comparar`)

#### Comparación Exitosa

```log
==================================================
COMPARE REQUEST - Tickers: AAPL, MSFT, GOOGL | Count: 3 | IP: 127.0.0.1
Using cached metrics for AAPL
Fetching fresh metrics for MSFT
Using cached metrics for GOOGL
✓ Comparison completado - Tickers: AAPL, MSFT, GOOGL | Success: 3/3 | Tiempo: 4.56s
==================================================
```

#### Comparación con Errores

```log
==================================================
COMPARE REQUEST - Tickers: AAPL, INVALID, GOOGL | Count: 3 | IP: 127.0.0.1
Using cached metrics for AAPL
ERROR - Error analyzing INVALID: No se encontraron datos suficientes
Using cached metrics for GOOGL
✓ Comparison completado - Tickers: AAPL, INVALID, GOOGL | Success: 2/3 | Tiempo: 5.21s
WARNING - Comparison errors: No se encontraron datos para INVALID
==================================================
```

#### Requests Inválidos

```log
WARNING - Comparar request con formato inválido - IP: 192.168.1.100
```

```log
WARNING - Comparar request con < 2 tickers - IP: 192.168.1.100
```

```log
WARNING - Comparar request con > 5 tickers (8) - IP: 192.168.1.100
```

---

### 4. DataAgent (Scraping)

**Logger**: `DataAgent`
**Archivo**: `data_agent.py`

```log
INFO - Fetching metrics for AAPL via Yahoo Finance
INFO - Successfully scraped 15 metrics from yahoo for AAPL
WARNING - Failed to fetch from yahoo for INVALID: HTTP 404
INFO - Fallback to finviz for INVALID
ERROR - All sources failed for INVALID
```

---

### 5. Errores de Aplicación

#### Error General en Endpoint

```log
ERROR - ERROR en analyze() - Ticker: AAPL | Tiempo: 2.34s | Error: Database is locked
Traceback (most recent call last):
  File "c:\rcv_proyecto\app.py", line 328, in analyze
    response = prepare_analysis_response(ticker, metrics)
  ...
sqlite3.OperationalError: database is locked
```

**NOTA**: Los errores con traceback completo se escriben tanto en `rvc_app.log` como en `errors.log`.

---

## ROTACIÓN DE ARCHIVOS

### Política de Rotación

- **Tamaño máximo por archivo**: 10 MB
- **Archivos de backup**:
  - `rvc_app.log`: 5 backups (total ~60 MB)
  - `errors.log`: 3 backups (total ~40 MB)
- **Encoding**: UTF-8

### Nomenclatura

```
rvc_app.log       ← Archivo actual (más reciente)
rvc_app.log.1     ← Backup 1 (anterior)
rvc_app.log.2     ← Backup 2
rvc_app.log.3     ← Backup 3
rvc_app.log.4     ← Backup 4
rvc_app.log.5     ← Backup 5 (más antiguo, se elimina cuando rota)
```

### ¿Cuándo Rota?

- Cuando `rvc_app.log` alcanza 10 MB:
  1. Se renombra `rvc_app.log` → `rvc_app.log.1`
  2. Se renombran todos los backups (`.1` → `.2`, `.2` → `.3`, etc.)
  3. Se elimina `.5` si existe
  4. Se crea nuevo `rvc_app.log` vacío

---

## BÚSQUEDA Y ANÁLISIS

### Buscar Requests de un Ticker

```bash
# Linux/Mac/Git Bash
grep "Ticker: AAPL" logs/rvc_app.log

# PowerShell
Select-String -Path logs\rvc_app.log -Pattern "Ticker: AAPL"
```

### Buscar Solo Errores

```bash
# Ver errores del día
grep "ERROR" logs/rvc_app.log

# Ver errores críticos
grep "CRITICAL" logs/errors.log

# Contar errores por tipo
grep -c "No se encontraron datos suficientes" logs/rvc_app.log
```

### Analizar Performance

```bash
# Encontrar requests lentos (>5 segundos)
grep "Tiempo:" logs/rvc_app.log | grep -E "Tiempo: [5-9]\.[0-9]+s|Tiempo: [0-9]{2,}\."

# Promedio de tiempo de análisis (requiere awk)
grep "Analysis completado" logs/rvc_app.log | \
  awk '{print $NF}' | \
  sed 's/s$//' | \
  awk '{sum+=$1; count++} END {print "Promedio:", sum/count, "segundos"}'
```

### Analizar Cache Hit Rate

```bash
# Contar cache hits vs misses
echo "Cache HITs:" $(grep -c "Cache HIT" logs/rvc_app.log)
echo "Cache MISSes:" $(grep -c "Cache MISS" logs/rvc_app.log)

# Calcular hit rate
grep "Cache HIT\|Cache MISS" logs/rvc_app.log | \
  awk '/HIT/{hits++} /MISS/{misses++} END {
    total=hits+misses;
    rate=hits/total*100;
    printf "Hit Rate: %.2f%% (%d hits / %d total)\n", rate, hits, total
  }'
```

### Analizar Uso por IP

```bash
# Top 10 IPs con más requests
grep "IP:" logs/rvc_app.log | \
  awk '{print $(NF)}' | \
  sort | uniq -c | sort -rn | head -10
```

---

## MONITOREO EN PRODUCCIÓN

### Alertas Recomendadas

1. **Error Rate Alto**: >5% de requests con ERROR en última hora
2. **Performance Degradada**: Tiempo promedio de análisis >5 segundos
3. **Cache Hit Rate Bajo**: <50% hit rate en última hora
4. **Archivo de Log Lleno**: `errors.log` rotando más de 1 vez por día

### Comandos de Monitoreo

```bash
# Ver logs en tiempo real
tail -f logs/rvc_app.log

# Ver solo errores en tiempo real
tail -f logs/errors.log

# Ver últimos 100 requests
tail -100 logs/rvc_app.log

# Buscar patrón específico en tiempo real
tail -f logs/rvc_app.log | grep "ERROR"
```

---

## LIMPIEZA DE LOGS

### Manual

```bash
# Eliminar logs antiguos (Linux/Mac/Git Bash)
rm logs/*.log.*

# Truncar log actual
echo "" > logs/rvc_app.log
echo "" > logs/errors.log
```

```powershell
# Eliminar logs antiguos (PowerShell)
Remove-Item logs\*.log.* -Force

# Truncar log actual
Clear-Content logs\rvc_app.log
Clear-Content logs\errors.log
```

### Automática (Futuro)

En Phase 0 de DEVELOPMENT_ROADMAP se planea crear `scripts/db_maintenance.sh` que incluirá limpieza de logs.

---

## VARIABLES DE ENTORNO

### `.env` (Crear si no existe)

```bash
# Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL=INFO

# Secret key de Flask
RVC_SECRET_KEY=change-me-in-production

# Otros (futuro)
# FMP_API_KEY=your_api_key
# DATABASE_URL=sqlite:///data/cache.db
```

---

## DEBUGGING

### Activar Logging Detallado

```bash
# En terminal (Linux/Mac/Git Bash)
export LOG_LEVEL=DEBUG
python app.py

# En terminal (Windows CMD)
set LOG_LEVEL=DEBUG
python app.py

# En terminal (PowerShell)
$env:LOG_LEVEL="DEBUG"
python app.py
```

### Ver Logs de Dependencias

Para ver logs de librerías como Flask, requests, etc.:

```python
# En app.py (temporal, solo para debugging)
logging.getLogger("werkzeug").setLevel(logging.DEBUG)  # Flask
logging.getLogger("urllib3").setLevel(logging.DEBUG)   # Requests
```

---

## MEJORES PRÁCTICAS

### 1. No Loggear Información Sensible

❌ **MAL**:
```python
logger.info(f"API Key: {api_key}")
logger.info(f"Password: {user_password}")
```

✅ **BIEN**:
```python
logger.info(f"API Key configurado: {bool(api_key)}")
logger.info(f"Usuario autenticado: {username}")
```

### 2. Usar Niveles Apropiados

```python
# DEBUG: Solo para desarrollo
logger.debug(f"Variable state: {var}")

# INFO: Operaciones normales
logger.info(f"Request procesado exitosamente: {ticker}")

# WARNING: Situaciones anormales pero manejables
logger.warning(f"Cache expirado para {ticker}, refrescando")

# ERROR: Errores que impiden completar operación
logger.error(f"No se pudo obtener datos para {ticker}", exc_info=True)

# CRITICAL: Errores que requieren atención inmediata
logger.critical(f"Base de datos no disponible", exc_info=True)
```

### 3. Incluir Contexto

❌ **MAL**:
```python
logger.error("Error al analizar")
```

✅ **BIEN**:
```python
logger.error(f"Error al analizar {ticker} - IP: {request.remote_addr}", exc_info=True)
```

### 4. Usar `exc_info=True` para Excepciones

```python
try:
    result = some_operation()
except Exception as e:
    logger.error(f"Error en operación: {e}", exc_info=True)
    # exc_info=True agrega el traceback completo
```

---

## PRÓXIMAS MEJORAS (Roadmap)

Según DEVELOPMENT_ROADMAP.md, futuras mejoras incluirán:

### Phase 1: Cache Manager
- Logging de estadísticas de cache
- Métricas de hit rate por ticker
- Tracking de provenance de datos

### Phase 9: API Usage Tracking
```python
logger.info(f"API Usage - FMP: {fmp_calls}/15000 ({percentage}%)")
logger.warning(f"API Usage - Cerca del límite: {fmp_calls}/15000")
```

### Phase 10: Métricas de Usuario
```python
logger.info(f"User Metrics - MAU: {mau} | DAU: {dau} | Conversión: {conversion_rate}%")
```

---

## TROUBLESHOOTING

### Log File Locked

**Síntoma**: `PermissionError: [Errno 13] Permission denied: 'logs/rvc_app.log'`

**Solución**:
1. Cerrar todas las instancias de la aplicación
2. Verificar que ningún editor tenga el archivo abierto
3. En Windows: Reiniciar proceso o cambiar permisos

### Logs No Aparecen

**Verificar**:
1. Directorio `logs/` existe: `ls logs/` o `dir logs\`
2. Nivel de logging: `echo $LOG_LEVEL` o revisar `.env`
3. Permisos de escritura: `ls -la logs/`

### Logs Demasiado Grandes

**Si los logs crecen muy rápido**:
1. Aumentar `LOG_LEVEL` a `WARNING` en producción
2. Reducir `backupCount` si el espacio es crítico
3. Implementar limpieza automática en backups scripts

---

**Fin de Documentación de Logging v1.0**
