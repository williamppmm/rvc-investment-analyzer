# Operaciones y Configuración - RVC Investment Analyzer

Guía de configuración del servidor: logging, persistencia de datos, splash screen y despliegue.

---

## Tabla de Contenidos

1. [Sistema de Logging](#1-sistema-de-logging)
2. [Persistencia de Visitas (SQLite vs PostgreSQL)](#2-persistencia-de-visitas-sqlite-vs-postgresql)
3. [Splash Screen con Logo](#3-splash-screen-con-logo)
4. [Variables de Entorno](#4-variables-de-entorno)

---

## 1. Sistema de Logging

### Archivos de Log

```
logs/
├── rvc_app.log      # Log principal (rotación: 5 archivos × 10 MB)
├── rvc_app.log.1    # Backup 1
├── errors.log       # Solo errores (rotación: 3 archivos × 10 MB)
└── errors.log.1
```

La carpeta `logs/` está en `.gitignore` — no se sube al repositorio.

### Niveles de Log

Controla el nivel con la variable de entorno `LOG_LEVEL`:

```bash
LOG_LEVEL=DEBUG    # Desarrollo — todo el detalle
LOG_LEVEL=INFO     # Producción — (default)
LOG_LEVEL=WARNING  # Solo advertencias y errores
LOG_LEVEL=ERROR    # Solo errores críticos
```

| Nivel | Uso |
|-------|-----|
| DEBUG | Variables internas, estados de scraping |
| INFO | Requests, análisis completados, cache hits |
| WARNING | Fuentes de datos fallidas, coberturas bajas |
| ERROR | Excepciones no manejadas, fallos críticos |

### Qué se Registra

- **Performance:** tiempo de respuesta por endpoint
- **Cache:** hits/misses con TTL restante
- **Provenance:** qué fuente entregó cada métrica
- **IPs:** para análisis de uso (anonimizadas en producción)
- **Errores de scraping:** fuentes que fallaron y fallback usado

---

## 2. Persistencia de Visitas (SQLite vs PostgreSQL)

### Problema

En plataformas modernas (Railway, Render, Heroku), el sistema de archivos es **efímero**: se reinicia en cada deploy. Sin configuración adicional, el contador de visitas volvería a 0.

### Solución: Detección Automática de Entorno

```python
# Si existe DATABASE_URL → PostgreSQL (producción)
# Si no existe          → SQLite (desarrollo)
IS_PRODUCTION = os.getenv("DATABASE_URL") is not None
```

| Entorno | Base de Datos | Configuración |
|---------|---------------|---------------|
| Desarrollo local | SQLite (`data/cache.db`) | Automático, sin configuración |
| Producción (Railway, Render, etc.) | PostgreSQL | Variable `DATABASE_URL` |

### Configurar PostgreSQL en Railway

1. En tu proyecto de Railway → **"+ New"** → **"Database"** → **"Add PostgreSQL"**
2. Railway agrega automáticamente `DATABASE_URL` a las variables de entorno
3. En el próximo deploy verás en los logs: `INFO - Modo BD: PostgreSQL (produccion)`

Si no usas Railway, agrega manualmente:
```
Variable: DATABASE_URL
Value:    postgresql://user:pass@host:5432/database
```

### Opciones de PostgreSQL Gratuito

| Plataforma | Plan Gratuito | Límite |
|------------|---------------|--------|
| Railway | ✅ | 1 GB |
| Supabase | ✅ | 500 MB |
| ElephantSQL | ✅ | 20 MB |

### Migrar Datos Existentes (opcional)

```bash
# 1. Exportar de SQLite local
sqlite3 data/cache.db "SELECT * FROM site_visits;" > visitas.sql

# 2. Conectar a PostgreSQL
psql $DATABASE_URL

# 3. Importar
INSERT INTO site_visits (id, total_visits, last_updated) VALUES (1, [TU_NUMERO], NOW());
```

### Monitoreo

```bash
# PostgreSQL (producción)
psql $DATABASE_URL -c "SELECT * FROM site_visits;"

# SQLite (desarrollo)
sqlite3 data/cache.db "SELECT * FROM site_visits;"

# Resetear contador si es necesario
UPDATE site_visits SET total_visits = 0 WHERE id = 1;
```

### Troubleshooting

| Error | Causa | Solución |
|-------|-------|----------|
| `relation site_visits does not exist` | Tablas no inicializadas | Las tablas se crean automáticamente en el primer deploy. Forzar con `db_manager.init_tables()` |
| `could not connect to server` | `DATABASE_URL` incorrecta | Verificar URL; si empieza con `postgres://`, cambiar a `postgresql://` |
| Visitas siguen reiniciándose | `DATABASE_URL` no configurada | Verificar en los logs: debe decir "PostgreSQL (produccion)" |

---

## 3. Splash Screen con Logo

### Comportamiento

- Se muestra solo en la primera visita del día
- Se vuelve a mostrar cada 24 horas
- Se puede saltar con clic o tecla ESC
- Se oculta automáticamente al terminar el video (2–3 segundos)
- Timeout de seguridad si el video no carga

### Archivo de Video Requerido

**Nombre:** `static/video/rvc-logo-intro.mp4`

| Especificación | Valor |
|----------------|-------|
| Duración | 2–3 segundos máximo |
| Resolución | 1280×720 (HD) recomendado |
| Formato | MP4 (H.264 codec) |
| Tamaño | < 500 KB |
| Audio | No requerido (se reproduce muted) |

### Optimización con FFmpeg

```bash
# Optimizar video existente
ffmpeg -i original.mp4 \
  -vcodec libx264 -crf 28 -preset fast \
  -vf "scale=1280:720" -an -movflags +faststart \
  static/video/rvc-logo-intro.mp4

# Crear fallback WebM (mejor compresión)
ffmpeg -i original.mp4 \
  -c:v libvpx-vp9 -crf 30 -b:v 0 \
  -vf "scale=1280:720" -an \
  static/video/rvc-logo-intro.webm

# Desde MOV, AVI o GIF animado
ffmpeg -i logo.mov -vcodec libx264 -crf 23 -preset medium -an static/video/rvc-logo-intro.mp4
ffmpeg -i logo.gif -movflags faststart -pix_fmt yuv420p -vf "scale=1280:720" static/video/rvc-logo-intro.mp4
```

### Control desde Consola (Debugging)

```javascript
RVCSplash.reset();    // Resetear cooldown (se mostrará en próxima carga)
location.reload();    // Recargar para mostrar inmediatamente
RVCSplash.show();     // Mostrar manualmente
```

### Configuración en Código

```javascript
// En static/splash.js
this.COOLDOWN_HOURS = 24;    // Cambiar frecuencia de aparición
this.SPLASH_DURATION = 2500; // Duración en ms (2.5 segundos)

// Desactivar completamente (desarrollo)
shouldShow() { return false; }

// Mostrar siempre (testing)
shouldShow() { return true; }
```

### Troubleshooting

| Problema | Causa | Solución |
|----------|-------|----------|
| Video no se reproduce | Archivo no existe o formato incorrecto | Verificar `static/video/rvc-logo-intro.mp4` y revisar F12 |
| Splash no aparece | Cooldown activo | Ejecutar `RVCSplash.reset()` en consola |
| Video muy pesado | Sin optimizar | Re-optimizar con FFmpeg (`-crf 30`, resolución 720p) |

---

## 4. Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto (está en `.gitignore`):

```bash
# Base de datos
DATABASE_URL=sqlite:///data/cache.db   # Local (automático)
# DATABASE_URL=postgresql://...        # Producción

# Flask
FLASK_ENV=production
SECRET_KEY=tu_clave_secreta_aqui

# Logging
LOG_LEVEL=INFO   # DEBUG en desarrollo, INFO en producción

# Email (para envío automático de licencias)
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_EMAIL=tu@email.com
SMTP_PASSWORD=tu_password_de_aplicacion

# APIs (cuando se implemente Fase 9)
FMP_API_KEY=
ALPHA_VANTAGE_KEY=
TWELVE_DATA_KEY=
```

**En Railway:** configura las variables directamente en el panel → Settings → Variables (no uses `.env` en producción).
