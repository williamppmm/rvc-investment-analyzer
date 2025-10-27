# Persistencia de Contador de Visitas

## Problema
En plataformas de hosting modernas (Render, Heroku, Railway, etc.), el sistema de archivos es **efímero**: se reinicia con cada deploy. Esto causaba que el contador de visitas se reiniciara a 0.

## Solución Implementada

### Desarrollo Local
- **Base de datos**: SQLite (`data/cache.db`)
- **Persistencia**: Archivo local permanente
- **Sin configuración adicional**

### Producción
- **Base de datos**: PostgreSQL
- **Persistencia**: Base de datos externa permanente
- **Requiere configuración**: Variable `DATABASE_URL`

---

## Configuración para Producción

### 1. Crear Base de Datos PostgreSQL en Railway

#### Railway (Tu Plataforma) - ¡SUPER FÁCIL!
1. En tu proyecto de Railway, haz clic en **"+ New"**
2. Selecciona **"Database"** → **"Add PostgreSQL"**
3. Railway creará automáticamente la base de datos
4. **Importante**: Railway automáticamente añade la variable `DATABASE_URL` a tu servicio
5. ¡Ya está! No necesitas copiar nada manualmente

#### Verificar que está conectada:
1. En Railway, ve a tu servicio web
2. Pestaña **"Variables"**
3. Debes ver `DATABASE_URL` con un valor tipo `postgresql://postgres:...@...railway.app:5432/railway`

#### Otras Opciones (si prefieres externa):
- **Supabase**: [supabase.com](https://supabase.com) - Gratis, 500 MB
- **ElephantSQL**: [elephantsql.com](https://www.elephantsql.com) - Gratis, 20 MB

---

### 2. (Opcional) Conectar Manualmente en Railway

Si NO agregaste la base de datos desde Railway, puedes configurarla manualmente:

1. Ve a tu servicio web en Railway
2. Pestaña **"Variables"** → **"+ New Variable"**
3. Agrega:
   ```
   Variable: DATABASE_URL
   Value: postgresql://user:pass@host:5432/database
   ```
4. Haz redeploy (Railway lo hace automáticamente)

---

### 3. Verificar Funcionamiento

Después del siguiente deploy, verás en los logs:

```
INFO - Modo BD: PostgreSQL (produccion)
INFO - Tablas PostgreSQL inicializadas
```

Si ves esto, **¡está funcionando!** Las visitas ahora persisten entre deploys.

---

## Cómo Funciona

### Detección Automática
El sistema detecta automáticamente el entorno:

```python
# Si existe DATABASE_URL → PostgreSQL (producción)
# Si no existe → SQLite (desarrollo)
IS_PRODUCTION = os.getenv("DATABASE_URL") is not None
```

### Código Transparente
El `DatabaseManager` traduce automáticamente entre SQLite y PostgreSQL:
- **Placeholders**: `?` (SQLite) → `%s` (PostgreSQL)
- **Tipos de datos**: `TEXT` → `TIMESTAMP`, etc.
- **Sintaxis SQL**: Compatible con ambos

---

## Migrar Datos Existentes (Opcional)

Si ya tienes visitas en SQLite local que quieres migrar a PostgreSQL:

```bash
# 1. Exportar datos de SQLite
sqlite3 data/cache.db "SELECT * FROM site_visits;" > visitas.sql

# 2. Conectar a PostgreSQL (reemplaza con tu DATABASE_URL)
psql $DATABASE_URL

# 3. Importar datos
INSERT INTO site_visits (id, total_visits, last_updated)
VALUES (1, [TU_NUMERO], NOW());
```

---

## Monitoreo

### Ver visitas actuales
```bash
# PostgreSQL (producción)
psql $DATABASE_URL -c "SELECT * FROM site_visits;"

# SQLite (desarrollo)
sqlite3 data/cache.db "SELECT * FROM site_visits;"
```

### Resetear contador (si es necesario)
```sql
UPDATE site_visits SET total_visits = 0 WHERE id = 1;
```

---

## Costos

| Plataforma   | Plan Gratuito | Límites                     |
|--------------|---------------|-----------------------------|
| Render       | ✅ Sí         | 1 GB almacenamiento, 90 días inactividad |
| Supabase     | ✅ Sí         | 500 MB almacenamiento, 2 conexiones concurrentes |
| ElephantSQL  | ✅ Sí         | 20 MB almacenamiento        |

**Recomendación**: Render PostgreSQL (más integrado con tu hosting)

---

## Troubleshooting

### Error: "relation site_visits does not exist"
**Causa**: Tablas no inicializadas
**Solución**: Las tablas se crean automáticamente en el primer deploy. Si persiste:
```python
# Forzar reinicialización
db_manager.init_tables()
```

### Error: "could not connect to server"
**Causa**: `DATABASE_URL` incorrecta
**Solución**:
1. Verifica que la URL sea correcta
2. Si empieza con `postgres://`, cámbiala a `postgresql://`
3. Verifica que la base de datos esté activa

### Las visitas siguen reiniciándose
**Causa**: `DATABASE_URL` no está configurada
**Solución**: Verifica los logs, debe decir "PostgreSQL (produccion)"

---

## Referencias
- [Documentación PostgreSQL en Render](https://render.com/docs/databases)
- [Psycopg2 Documentation](https://www.psycopg.org/docs/)
- [SQLite vs PostgreSQL](https://www.sqlite.org/whentouse.html)
