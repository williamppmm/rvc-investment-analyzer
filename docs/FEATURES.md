# Features del Sistema - RVC Investment Analyzer

Documentación del sistema freemium, licencias PRO y configuración de email.

---

## Tabla de Contenidos

1. [Sistema Freemium](#1-sistema-freemium)
2. [Sistema de Licencias PRO](#2-sistema-de-licencias-pro)
3. [Configuración de Email Automático](#3-configuración-de-email-automático)

---

## 1. Sistema Freemium

### Resumen

| Plan | Consultas diarias | Precio |
|------|-------------------|--------|
| FREE | 10 / día (reset a medianoche) | $0 |
| PRO | Ilimitadas | $3 USD / 30 días |

### Flujo para el Usuario

1. Usa la app normalmente hasta alcanzar el límite diario
2. Aparece el modal automáticamente con comparativa FREE vs PRO
3. Clic en "Contribuir $3 USD" → abre email predefinido a `williamppmm@hotmail.com`
4. Coordina el pago con el administrador (PayPal, transferencia, etc.)
5. Recibe la clave PRO por email
6. Pega la clave en el modal o en `localStorage`
7. Acceso ilimitado por 30 días

### Implementación Técnica

**Archivos principales:**

| Archivo | Líneas | Descripción |
|---------|--------|-------------|
| `usage_limiter.py` | ~450 | Motor de límites y validación de licencias |
| `manage_licenses.py` | ~280 | CLI de administración |
| `static/usage_limit.css` | ~350 | Estilos del modal |
| `static/usage_limit.js` | ~320 | Lógica del modal y verificación |

**Base de datos SQLite — tabla `usage_tracking`:**
```sql
id, identifier (IP), endpoint, timestamp, user_agent, response_status
```

**Base de datos SQLite — tabla `pro_licenses`:**
```sql
id, license_key (UNIQUE), email, plan_type, created_at, expires_at,
is_active (1/0), max_monthly_queries (-1 = ilimitado), notes
```

### Endpoints API

**POST /api/check-limit:**
```json
// Request
{"license_key": "RVC-PRO-XXX"}  // opcional

// Response
{"allowed": true, "remaining": 15, "limit": 20, "plan": "FREE", "reset_in": "8 horas"}
```

**POST /api/validate-license:**
```json
// Request
{"license_key": "RVC-PRO-ABC123"}

// Response
{"valid": true, "plan": "PRO", "expires_at": "24/11/2025", "days_left": 29}
```

**GET /api/usage-stats:**
```json
{"global_stats": {"total_queries": 1250, "unique_metric": 85}}
```

### Proyección de Negocio

| Escenario | Usuarios PRO | Ingresos/mes | Costos API | Ganancia |
|-----------|--------------|--------------|------------|----------|
| Pequeño | 10 | $30 | $10–15 | $15–20 |
| Medio | 30 | $90 | $20–30 | $60–70 |
| Grande | 100 | $300 | $50–80 | $220–250 |

### Seguridad

- Licencias con `secrets.token_hex(8)` (64 bits de entropía)
- Tracking por IP sin requerir login
- Fail-safe: si el sistema de límites falla, se permite el acceso
- SQLite soporta ~100 usuarios concurrentes; para más, migrar a PostgreSQL

---

## 2. Sistema de Licencias PRO

### Comandos CLI (manage_licenses.py)

```bash
# Crear licencia para un cliente
python manage_licenses.py create cliente@email.com
# Output: LICENCIA: RVC-PRO-ABC123XYZ | VÁLIDA HASTA: 24/11/2025

# Listar todas las licencias
python manage_licenses.py list

# Validar una licencia específica
python manage_licenses.py validate RVC-PRO-ABC123XYZ

# Desactivar licencia
python manage_licenses.py deactivate RVC-PRO-ABC123XYZ

# Ver estadísticas de uso
python manage_licenses.py stats
```

### Flujo Completo de Venta (para el Administrador)

```
1. Usuario envía email expresando interés
   ↓
2. Coordinas el pago ($3 USD vía PayPal / transferencia)
   ↓
3. python manage_licenses.py create usuario@gmail.com
   ↓
4. Sistema genera: RVC-PRO-A1B2C3D4E5F6G7H8
   ↓
5. Envías la clave al usuario por email
   ↓
6. Usuario activa en el modal de la app
```

### Formato de Clave

```python
# En usage_limiter.py
import secrets
license_key = f"RVC-PRO-{secrets.token_hex(8).upper()}"
# → RVC-PRO-A1B2C3D4E5F6G7H8  (16 caracteres hexadecimales)
```

### Renovación

Las licencias **no se renuevan automáticamente**. Al vencer, el usuario vuelve a plan FREE y debe contactar nuevamente. Para renovar, usar el mismo flujo de venta con una nueva clave.

### Monitoreo Recomendado

- **Diario:** `python manage_licenses.py stats`
- **Semanal:** Revisar licencias próximas a expirar
- **Mensual:** Analizar tasa de conversión FREE → PRO

---

## 3. Configuración de Email Automático

Al generar una licencia, el sistema puede enviar automáticamente un email profesional al cliente con la clave, fecha de expiración e instrucciones.

### Configuración Rápida

```bash
# Copiar el archivo de ejemplo
cp .env.example .env
# Editar .env con tus credenciales SMTP
```

### Opción 1: Hotmail/Outlook (Recomendado para empezar)

1. Genera una contraseña de aplicación en [account.live.com/proofs/AppPassword](https://account.live.com/proofs/AppPassword)
2. Edita `.env`:
   ```env
   SMTP_SERVER=smtp-mail.outlook.com
   SMTP_PORT=587
   SMTP_EMAIL=williamppmm@hotmail.com
   SMTP_PASSWORD=abcdefghijklmnop   # Sin espacios
   ```

### Opción 2: Gmail

1. Activa la verificación en 2 pasos en tu cuenta de Google
2. Ve a [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords) y genera una contraseña de app
3. Edita `.env`:
   ```env
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SMTP_EMAIL=tu_email@gmail.com
   SMTP_PASSWORD=xxxx xxxx xxxx xxxx   # Contraseña de aplicación de 16 chars
   ```

### Opción 3: Email Profesional (dominio propio)

```env
SMTP_SERVER=mail.tudominio.com
SMTP_PORT=587
SMTP_EMAIL=licencias@tudominio.com
SMTP_PASSWORD=tu_password
```

### Verificar Configuración

```bash
# Probar envío de email de prueba
python manage_licenses.py test-email tu@email.com
```

### Notas Importantes

- El archivo `.env` está en `.gitignore` — nunca subas credenciales al repositorio
- Si el sistema de email falla, la licencia igual se crea correctamente en la base de datos
- Para producción en Railway, configura las variables de entorno directamente en el panel de Railway (no en `.env`)
