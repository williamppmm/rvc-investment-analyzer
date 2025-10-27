# 🔐 GUÍA COMPLETA DEL SISTEMA DE LICENCIAS

**Fecha**: 26 de octubre de 2025  
**Versión**: 2.0 (con sistema de renovación)  
**Sistema**: RVC Analyzer - Modelo Freemium  
**Autor**: William Pérez

---

## 📋 ÍNDICE

1. [Resumen del Sistema](#resumen)
2. [Cómo Funciona (Técnicamente)](#funcionamiento)
3. [Generación de Licencias](#generacion)
   - 3.1. CLI - Línea de Comandos
   - 3.2. API REST
   - 3.3. Formato de Licencia
   - 3.4. ♻️ **Renovación de Licencias** (NUEVO v2.0)
4. [Flujo Completo de Venta](#flujo-venta)
5. [Seguridad](#seguridad)
6. [FAQ - Preguntas Frecuentes](#faq)

---

## <a name="resumen"></a>🎯 1. RESUMEN DEL SISTEMA

### ¿Dónde se Gestiona?

✅ **TODO está en este mismo proyecto** - No necesitas un proyecto separado.

### Componentes Principales

```
rcv_proyecto/
├── usage_limiter.py        # Motor del sistema (validación, creación, tracking)
├── manage_licenses.py      # CLI para administrar licencias (tú lo usas)
├── app.py                  # Endpoints API (/api/check-limit, /api/validate-license)
├── static/usage_limit.js   # Modal frontend (usuario final)
└── data/
    └── rvc_database.db     # SQLite con tabla pro_licenses
```

### ¿Cómo Funciona en 3 Pasos?

```
1. Usuario paga $3 USD (PayPal/Transferencia/etc.)
   ↓
2. Tú ejecutas: python manage_licenses.py create usuario@gmail.com
   ↓
3. Sistema genera: RVC-PRO-A1B2C3D4E5F6G7H8
   ↓
4. Envías la clave al usuario por email
   ↓
5. Usuario pega la clave en el modal o localStorage
   ↓
6. Sistema valida y desbloquea 30 días de acceso PRO
```

---

## <a name="funcionamiento"></a>⚙️ 2. CÓMO FUNCIONA (TÉCNICAMENTE)

### 2.1. Generación de Claves

**Tipo de Hash**: NO es un hash tradicional (SHA256, bcrypt), es un **token aleatorio criptográficamente seguro**.

```python
# Código real de usage_limiter.py línea 286
import secrets

license_key = f"RVC-PRO-{secrets.token_hex(8).upper()}"
# Resultado: RVC-PRO-A1B2C3D4E5F6G7H8
#                    ^^^^^^^^^^^^^^^^
#                    16 caracteres hexadecimales (64 bits de entropía)
```

**¿Por qué `secrets.token_hex(8)`?**
- `secrets` = módulo criptográficamente seguro de Python
- `token_hex(8)` = genera 8 bytes (64 bits) en formato hexadecimal = 16 caracteres
- Resultado: `A1B2C3D4E5F6G7H8` (mayúsculas para mejor legibilidad)

**Nivel de Seguridad**:
- 16^16 = 18,446,744,073,709,551,616 combinaciones posibles
- Imposible de adivinar por fuerza bruta
- Único garantizado (probabilidad de colisión ~0%)

### 2.2. Almacenamiento en Base de Datos

**Tabla `pro_licenses` en SQLite**:

```sql
CREATE TABLE pro_licenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    license_key TEXT UNIQUE NOT NULL,        -- RVC-PRO-XXX (SIN hashear)
    email TEXT,                              -- Email del comprador
    plan_type TEXT DEFAULT 'PRO',           -- PRO, ENTERPRISE, etc.
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME,                     -- Fecha de expiración (30 días)
    is_active INTEGER DEFAULT 1,            -- 1=activa, 0=desactivada
    max_monthly_queries INTEGER DEFAULT -1, -- -1 = ilimitado
    notes TEXT
);
```

**Ejemplo de registro**:

```
| id | license_key              | email            | expires_at          | is_active |
|----|--------------------------|------------------|---------------------|-----------|
| 1  | RVC-PRO-A1B2C3D4E5F6G7H8 | user@gmail.com   | 2025-11-25 10:30:00 | 1         |
| 2  | RVC-PRO-9F8E7D6C5B4A3210 | otro@hotmail.com | 2025-12-01 15:45:00 | 1         |
```

### 2.3. Validación de Licencias

**Flujo de validación** (código real de `usage_limiter.py` líneas 212-265):

```python
def validate_license(self, license_key: str) -> dict:
    # 1. Buscar en BD
    SELECT plan_type, expires_at, email, is_active
    FROM pro_licenses
    WHERE license_key = ?
    
    # 2. Verificar existencia
    if not result:
        return {"valid": False, "reason": "Licencia no encontrada"}
    
    # 3. Verificar si está activa
    if not is_active:
        return {"valid": False, "reason": "Licencia desactivada"}
    
    # 4. Verificar expiración
    if now > expires_at:
        return {"valid": False, "reason": "Licencia expirada"}
    
    # 5. Calcular días restantes
    days_left = (expires_at - now).days
    
    # 6. Retornar validación exitosa
    return {
        "valid": True,
        "plan": "PRO",
        "expires_at": "25/11/2025",
        "days_left": 15,
        "email": "user@gmail.com"
    }
```

**¿Por qué NO se hashea la clave?**
- La clave ES el token de autenticación (como un JWT)
- Debe almacenarse en texto plano para poder validarla
- La seguridad viene de:
  - Aleatoriedad criptográfica (imposible adivinar)
  - Expiración automática (30 días)
  - Registro único por email
  - Desactivación manual posible

**Comparación con sistemas hash tradicionales**:

```
Sistema de contraseñas (hash):
- Usuario ingresa: "password123"
- Se hashea: bcrypt("password123") → $2b$12$...xyz
- Se compara: bcrypt("password123") == $2b$12$...xyz ✅

Sistema de licencias (token):
- Sistema genera: RVC-PRO-A1B2C3D4E5F6G7H8
- Se almacena: "RVC-PRO-A1B2C3D4E5F6G7H8" (texto plano)
- Se compara: input == db_value ✅
```

### 2.4. Tracking de Uso

**Tabla `usage_tracking`**:

```sql
CREATE TABLE usage_tracking (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    identifier TEXT NOT NULL,              -- IP del usuario
    endpoint TEXT NOT NULL,                -- /analyze, /api/comparar
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    user_agent TEXT,
    response_status INTEGER
);
```

**Flujo de verificación de límites**:

```python
# 1. Usuario hace request a /analyze
POST /analyze {"ticker": "AAPL"}

# 2. Frontend verifica límite ANTES de enviar
checkUsageLimitBeforeAction()
  ↓
POST /api/check-limit {"license_key": "RVC-PRO-XXX"}

# 3. Backend valida
def check_limit(identifier, license_key):
    if license_key:
        validation = validate_license(license_key)
        if validation["valid"]:
            # Usuario PRO - verificar límite de 200/día
            usage_count = get_usage_count(identifier, period="daily")
            return {
                "allowed": usage_count < 200,
                "remaining": 200 - usage_count,
                "plan": "PRO"
            }
    
    # Usuario FREE - verificar límite de 10/día
    usage_count = get_usage_count(identifier, period="daily")
    return {
        "allowed": usage_count < 10,
        "remaining": 10 - usage_count,
        "plan": "FREE"
    }

# 4. Si allowed=True, se procesa el análisis
# 5. Se registra el uso
track_usage(identifier, "/analyze")
```

---

## <a name="generacion"></a>🔧 3. GENERACIÓN DE LICENCIAS

### 3.1. CLI - Línea de Comandos (Recomendado)

**Script**: `manage_licenses.py` (ya incluido en el proyecto)

#### Crear Licencia

```bash
# Activar entorno virtual
& C:/rcv_proyecto/.venv/Scripts/Activate.ps1

# Generar licencia para un cliente
python manage_licenses.py create usuario@gmail.com

# Output:
🔑 Generando licencia PRO para: usuario@gmail.com
💰 Costo: $3 USD
⏱️  Duración: 30 días

¿Confirmar creación? (s/n): s

✅ ¡Licencia creada exitosamente!

==================================================
LICENCIA: RVC-PRO-A1B2C3D4E5F6G7H8
EMAIL: usuario@gmail.com
VÁLIDA HASTA: 25/11/2025
==================================================

📧 Envía esta licencia al cliente vía email:
   williamppmm@hotmail.com → usuario@gmail.com
```

#### Listar Todas las Licencias

```bash
python manage_licenses.py list

# Output:
📋 LICENCIAS REGISTRADAS (3)
====================================================================================================

🔑 RVC-PRO-A1B2C3D4E5F6G7H8
   Email: usuario@gmail.com
   Plan: PRO
   Creada: 26/10/2025 10:30
   Expira: 25/11/2025
   Estado: ✅ Activa

🔑 RVC-PRO-9F8E7D6C5B4A3210
   Email: otro@hotmail.com
   Plan: PRO
   Creada: 20/10/2025 15:45
   Expira: 19/11/2025
   Estado: ⚠️ Expira en 2 días

🔑 RVC-PRO-OBSOLETA123456
   Email: viejo@yahoo.com
   Plan: PRO
   Creada: 15/09/2025 08:00
   Expira: 15/10/2025
   Estado: ⏰ Expirada

====================================================================================================
```

#### Validar Licencia

```bash
python manage_licenses.py validate RVC-PRO-A1B2C3D4E5F6G7H8

# Output:
🔍 Validando licencia: RVC-PRO-A1B2C3D4E5F6G7H8

✅ LICENCIA VÁLIDA

==================================================
Plan: PRO
Email: usuario@gmail.com
Expira: 25/11/2025
Días restantes: 30
==================================================
```

#### Desactivar Licencia (abuso, reembolso, etc.)

```bash
python manage_licenses.py deactivate RVC-PRO-A1B2C3D4E5F6G7H8

# Output:
⚠️ Desactivando licencia: RVC-PRO-A1B2C3D4E5F6G7H8
¿Confirmar desactivación? (s/n): s

✅ Licencia desactivada exitosamente
```

#### Ver Estadísticas de Uso

```bash
python manage_licenses.py stats

# Output:
📊 ESTADÍSTICAS DE USO
==================================================
Total consultas: 1,234
Usuarios únicos: 87
Primera consulta: 2025-10-01T10:00:00
Última consulta: 2025-10-26T14:30:00
==================================================
```

### 3.2. Programáticamente (Python)

Si quieres integrar la generación de licencias en otro script:

```python
from usage_limiter import get_limiter

# Crear licencia
limiter = get_limiter()
license_key = limiter.create_license(
    email="usuario@gmail.com",
    plan_type="PRO",
    duration_days=30
)

print(f"Licencia creada: {license_key}")
# Output: Licencia creada: RVC-PRO-A1B2C3D4E5F6G7H8

# Validar licencia
validation = limiter.validate_license(license_key)
print(validation)
# Output: {
#   "valid": True,
#   "plan": "PRO",
#   "expires_at": "25/11/2025",
#   "days_left": 30,
#   "email": "usuario@gmail.com"
# }
```

### 3.3. Formato de la Clave

**Estructura**:
```
RVC-PRO-A1B2C3D4E5F6G7H8
│   │   │
│   │   └── Token aleatorio (16 caracteres hex)
│   └────── Tipo de plan
└────────── Prefijo del proyecto
```

**Ventajas del formato**:
- ✅ Fácil de identificar visualmente
- ✅ Compatible con copy-paste
- ✅ No contiene caracteres ambiguos (0 vs O, 1 vs I, etc.)
- ✅ Longitud manejable (28 caracteres totales)

---

### 3.4. ♻️ Renovación de Licencias

**Nuevo desde v2.0**: Sistema de renovación para clientes recurrentes

#### ¿Por qué RENOVAR en lugar de CREAR?

```
❌ ANTES (crear nueva cada mes):
usuario@gmail.com → RVC-PRO-ABC123... (octubre)
usuario@gmail.com → RVC-PRO-XYZ789... (noviembre)
usuario@gmail.com → RVC-PRO-QWE456... (diciembre)
Resultado: 3 licencias duplicadas, sin historial

✅ AHORA (renovar la existente):
usuario@gmail.com → RVC-PRO-ABC123... (creada: octubre)
                    ├─ Renovación #1 (noviembre) → +30 días
                    ├─ Renovación #2 (diciembre) → +30 días
                    └─ Renovación #3 (enero)     → +30 días
Resultado: 1 licencia, historial completo de pagos
```

#### Comando RENEW

```bash
# Por EMAIL (busca la licencia más reciente del usuario)
python manage_licenses.py renew usuario@gmail.com

# Por CLAVE DE LICENCIA (específica exactamente cuál renovar)
python manage_licenses.py renew RVC-PRO-ABC123XYZ

# Output:
♻️  Renovando licencia para: usuario@gmail.com
💰 Costo: $3 USD
⏱️  Extensión: 30 días adicionales

📋 Licencia encontrada:
   • Key: RVC-PRO-E1B01792FC12A949
   • Email: usuario@gmail.com
   • Expira: 25/11/2025
   • Renovaciones previas: 2
   • Estado: ✅ ACTIVA (5 días restantes) - Se extenderá

¿Confirmar renovación por 30 días más? (s/n): s

✅ ¡Licencia renovada exitosamente!

==================================================
LICENCIA: RVC-PRO-E1B01792FC12A949
EMAIL: usuario@gmail.com
EXPIRABA: 25/11/2025
NUEVA EXPIRACIÓN: 25/12/2025
RENOVACIÓN #3
==================================================

¿Deseas enviar confirmación por email? (s/n): s
✅ Email enviado exitosamente
```

#### Lógica de Renovación

**Licencia ACTIVA** (aún no expiró):
```python
# Extiende desde la fecha de expiración actual
Expira: 25/11/2025 → +30 días → Nueva expiración: 25/12/2025
```

**Licencia EXPIRADA** (ya pasó la fecha):
```python
# Reactiva y extiende desde HOY
Expira: 05/10/2025 (expirada) → +30 días → Nueva expiración: 25/11/2025
```

**Licencia INACTIVA** (desactivada manualmente):
```python
# Reactiva automáticamente y extiende desde HOY
is_active: 0 → 1
Expira: 01/09/2025 → +30 días → Nueva expiración: 25/11/2025
```

#### Tracking de Renovaciones

**Campos agregados a la BD**:
```sql
CREATE TABLE pro_licenses (
    -- Campos existentes...
    last_renewed_at DATETIME,       -- Fecha de última renovación
    renewal_count INTEGER DEFAULT 0 -- Contador de renovaciones
);
```

**Visualización en `list`**:
```bash
python manage_licenses.py list

📋 LICENCIAS REGISTRADAS (1)
====================================================================================================

🔑 RVC-PRO-E1B01792FC12A949
   Email: usuario@gmail.com
   Plan: PRO
   Creada: 01/10/2025 14:30
   Expira: 25/12/2025
   Estado: ✅ Activa
   Renovaciones: 3 vez/veces          # <-- Contador de pagos
   Última renovación: 25/11/2025 09:15  # <-- Fecha del último pago

====================================================================================================
```

#### Cuándo usar CREATE vs RENEW

| Comando | Cuándo usarlo | Resultado |
|---------|---------------|-----------|
| `create` | **Cliente NUEVO** (primer pago) | Genera licencia nueva |
| `renew` | **Cliente RECURRENTE** (pago mensual) | Extiende licencia existente |

**Ejemplo de flujo correcto**:
```bash
# Mes 1: Cliente nuevo
python manage_licenses.py create juan@empresa.com
# → Licencia creada: RVC-PRO-ABC123...

# Mes 2: Cliente renueva
python manage_licenses.py renew juan@empresa.com
# → Licencia extendida +30 días (renewal_count = 1)

# Mes 3: Cliente renueva de nuevo
python manage_licenses.py renew juan@empresa.com
# → Licencia extendida +30 días (renewal_count = 2)
```

#### Email de Renovación

**Diferencia con email de creación**:
- ✉️ **CREATE**: Email de bienvenida (primera vez)
- ♻️ **RENEW**: Email de confirmación de renovación

**Template incluye**:
- ♻️ Icono de renovación en lugar de bienvenida
- 📊 Número de renovación (#1, #2, #3...)
- 📅 Fecha de expiración anterior vs nueva
- ✅ Mensaje de continuidad (no necesita hacer nada)

**Configuración**: Ver [EMAIL_SETUP_GUIDE.md](EMAIL_SETUP_GUIDE.md)

---

## <a name="flujo-venta"></a>💰 4. FLUJO COMPLETO DE VENTA

### Escenario: Un usuario quiere actualizar a PRO

#### Paso 1: Usuario Alcanza el Límite FREE

```javascript
// Usuario hace 11º análisis del día
POST /analyze {"ticker": "AAPL"}
  ↓
// Frontend verifica límite
checkUsageLimitBeforeAction()
  ↓
POST /api/check-limit {}
  ↓
{
  "allowed": false,
  "remaining": 0,
  "limit": 10,
  "plan": "FREE",
  "reset_in": "8 horas"
}
  ↓
// Modal aparece automáticamente
```

#### Paso 2: Usuario Ve el Modal

**Contenido del modal** (`static/usage_limit.js`):

```
┌─────────────────────────────────────────┐
│    🎯 Límite de Consultas Alcanzado    │
│                                         │
│  Usadas: 10    Disponibles: 0          │
│  Se restablece en: 8 horas             │
│                                         │
│  ┌──────────┐    ┌──────────────┐      │
│  │   FREE   │    │  PRO - $3USD │      │
│  │  10/día  │    │   200/día    │      │
│  └──────────┘    └──────────────┘      │
│                                         │
│  💬 ¿Te gusta RVC Analyzer?            │
│     Contribuye al proyecto              │
│                                         │
│  [Contribuir $3 USD] [Más Info]        │
│                                         │
│  ¿Ya tienes licencia? Actívala aquí    │
└─────────────────────────────────────────┘
```

#### Paso 3: Usuario Hace Clic en "Contribuir $3 USD"

**Acción**: Se abre cliente de email con mensaje predefinido

```
Para: williamppmm@hotmail.com
Asunto: Quiero contribuir al sostenimiento de RVC Analyzer

Hola William,

Estoy interesado en contribuir al sostenimiento del proyecto 
RVC Analyzer con una licencia PRO ($3 USD/30 días).

Mi email es: [usuario debe completar]

¿Cómo puedo proceder con el pago?

Gracias!
```

#### Paso 4: Usuario Envía el Email

**Tú recibes**:
- Email del usuario interesado
- Confirmas que quiere pagar $3 USD
- Le indicas método de pago (PayPal, Transferencia, etc.)

#### Paso 5: Usuario Realiza el Pago

**Opciones de pago** (las que tú prefieras):

1. **PayPal** - paypal.me/williamppmm → Instantáneo
2. **Transferencia bancaria** - Detalles por email
3. **Stripe** - Si integras pasarela de pago
4. **Criptomonedas** - Si aceptas (USDT, Bitcoin, etc.)

#### Paso 6: Generas la Licencia

Una vez confirmado el pago:

```bash
# En tu terminal
python manage_licenses.py create usuario@gmail.com

# Copias la clave generada
RVC-PRO-A1B2C3D4E5F6G7H8
```

#### Paso 7: Envías la Licencia al Usuario

**Email de respuesta**:

```
Para: usuario@gmail.com
Asunto: Tu licencia RVC Analyzer PRO - ¡Activada!

Hola [nombre],

¡Gracias por tu contribución al proyecto RVC Analyzer! 🎉

Tu licencia PRO ha sido activada:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LICENCIA: RVC-PRO-A1B2C3D4E5F6G7H8
VÁLIDA HASTA: 25/11/2025 (30 días)
CONSULTAS DIARIAS: 200 (antes 10)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CÓMO ACTIVAR:

1. Ve a https://rvc-analyzer.com
2. Cuando aparezca el modal de límite, haz clic en 
   "¿Ya tienes licencia? Actívala aquí"
3. Pega tu clave: RVC-PRO-A1B2C3D4E5F6G7H8
4. ¡Listo! Ahora tienes acceso ilimitado por 30 días

BENEFICIOS:
✅ 200 consultas diarias (20x más que FREE)
✅ APIs premium (Alpha Vantage, Twelve Data)
✅ Datos en tiempo real
✅ Soporte prioritario

Si tienes algún problema, responde este email.

¡Gracias por apoyar el proyecto!

William Pérez
Creador de RVC Analyzer
```

#### Paso 8: Usuario Activa la Licencia

**En el navegador**:

```javascript
// Usuario hace clic en "Actívala aquí"
  ↓
// Aparece prompt
prompt("Ingresa tu clave de licencia PRO:")
  ↓
// Usuario pega: RVC-PRO-A1B2C3D4E5F6G7H8
  ↓
POST /api/validate-license {"license_key": "RVC-PRO-A1B2C3D4E5F6G7H8"}
  ↓
{
  "valid": true,
  "plan": "PRO",
  "expires_at": "25/11/2025",
  "days_left": 30,
  "email": "usuario@gmail.com"
}
  ↓
// Se guarda en localStorage
localStorage.setItem('rvc_license_key', 'RVC-PRO-A1B2C3D4E5F6G7H8')
  ↓
// Alerta de éxito
alert('✅ Licencia PRO activada exitosamente. Ahora tienes acceso ilimitado.')
  ↓
// Recarga página
location.reload()
  ↓
// Badge PRO aparece en navbar
┌────────────┐
│ ✨ PRO (30d)│
└────────────┘
```

#### Paso 9: Usuario Usa el Servicio PRO por 30 Días

```javascript
// Cada vez que analiza una acción
POST /analyze {"ticker": "TSLA"}
  ↓
// Frontend incluye la licencia
POST /api/check-limit {"license_key": "RVC-PRO-A1B2C3D4E5F6G7H8"}
  ↓
{
  "allowed": true,
  "remaining": 195,  // 200 - 5 usos hoy
  "limit": 200,
  "plan": "PRO",
  "license_days_left": 28
}
  ↓
// Análisis se procesa normalmente
```

#### Paso 10: Renovación (Día 30)

**Licencia expira** → Usuario vuelve a plan FREE → Proceso se repite

**Opcional**: Enviar email de recordatorio 3 días antes:

```
Para: usuario@gmail.com
Asunto: Tu licencia RVC PRO expira en 3 días

Hola [nombre],

Tu licencia PRO expira el 25/11/2025 (en 3 días).

¿Deseas renovar por otros 30 días ($3 USD)?

Responde este email si quieres continuar disfrutando de:
✅ 200 consultas diarias
✅ APIs premium
✅ Datos en tiempo real

¡Gracias por ser parte de RVC Analyzer!

William
```

---

## <a name="seguridad"></a>🔒 5. SEGURIDAD

### 5.1. ¿Es Seguro Almacenar Claves en Texto Plano?

**SÍ**, en este contexto específico:

#### Argumentos a Favor

1. **No es una contraseña reutilizable**
   - La clave se genera aleatoriamente por el sistema
   - El usuario NO la elige ni la reutiliza
   - Si se filtra, solo afecta a ESA licencia específica

2. **Imposible de adivinar**
   - 16^16 = 18 cuatrillones de combinaciones
   - Ataque de fuerza bruta es inviable
   - No hay diccionario de claves posibles

3. **Expiración automática**
   - Ventana de abuso: máximo 30 días
   - Después, la clave es inútil

4. **Trazabilidad completa**
   - Cada licencia está ligada a un email
   - Puedes desactivar licencias sospechosas
   - Logs de uso por IP

5. **Comparación con tokens JWT**
   - JWT se almacenan en texto plano en localStorage
   - JWT pueden tener expiración de 7-30 días
   - Modelo similar al tuyo

#### Riesgos y Mitigaciones

| Riesgo | Probabilidad | Mitigación |
|--------|--------------|------------|
| Filtración de BD | Baja | SQLite local, sin acceso público |
| Compartir licencia | Media | 1 licencia = 1 IP monitoreada, desactivación manual |
| Ataque de fuerza bruta | Muy baja | 16^16 combinaciones, rate limiting |
| Reventa de licencias | Baja | Email único, desactivación si se detecta |

### 5.2. Mejoras de Seguridad Futuras (Opcionales)

#### Nivel 1: Rate Limiting en Validación

```python
# Prevenir fuerza bruta en /api/validate-license
from functools import lru_cache
from time import time

failed_attempts = {}

def validate_license(license_key):
    ip = request.remote_addr
    
    # Máximo 5 intentos por IP por hora
    if ip in failed_attempts:
        attempts, timestamp = failed_attempts[ip]
        if time() - timestamp < 3600 and attempts >= 5:
            return {"valid": False, "reason": "Demasiados intentos"}
    
    # Validación normal...
```

#### Nivel 2: Binding de IP

```python
# Vincular licencia a la IP del primer uso
def activate_license(license_key, user_ip):
    # Primera activación → guardar IP
    cursor.execute("""
        UPDATE pro_licenses 
        SET bound_ip = ?
        WHERE license_key = ? AND bound_ip IS NULL
    """, (user_ip, license_key))
    
    # Validación → verificar IP
    cursor.execute("""
        SELECT bound_ip FROM pro_licenses
        WHERE license_key = ?
    """, (license_key,))
    
    bound_ip = cursor.fetchone()[0]
    if bound_ip and bound_ip != user_ip:
        return {"valid": False, "reason": "Licencia vinculada a otra IP"}
```

#### Nivel 3: Device Fingerprinting

```javascript
// Frontend genera fingerprint del navegador
const fingerprint = await getDeviceFingerprint();

// Se envía con cada request
POST /api/check-limit {
  "license_key": "RVC-PRO-XXX",
  "device_fingerprint": "abc123..."
}

// Backend valida que sea el mismo dispositivo
```

#### Nivel 4: Cifrado de BD (SQLCipher)

```python
# Cambiar SQLite por SQLCipher
import sqlcipher

conn = sqlcipher.connect('data/rvc_database.db')
conn.execute("PRAGMA key = 'tu_clave_de_cifrado_segura'")
```

**Recomendación**: Nivel 1 (rate limiting) es suficiente para empezar.

---

## <a name="faq"></a>❓ 6. FAQ - PREGUNTAS FRECUENTES

### ¿Necesito crear un proyecto separado para las licencias?

**NO**. Todo está en este mismo proyecto (`rcv_proyecto`). El sistema de licencias es parte integral de la aplicación.

### ¿Cómo se hashea la clave que le envío al usuario?

**NO se hashea**. La clave se genera con `secrets.token_hex(8)` y se envía tal cual al usuario. Es un **token aleatorio**, no un hash.

### ¿La clave que ve el usuario es la misma que está en la BD?

**SÍ**. Exactamente la misma. Ejemplo:
- BD: `RVC-PRO-A1B2C3D4E5F6G7H8`
- Usuario recibe: `RVC-PRO-A1B2C3D4E5F6G7H8`
- Usuario pega: `RVC-PRO-A1B2C3D4E5F6G7H8`

### ¿Qué pasa si alguien roba la BD?

- Solo vería las claves de licencias activas
- Podría usarlas temporalmente (hasta expiración)
- **Mitigación**: Monitorear IPs sospechosas, desactivar licencias comprometidas

### ¿Puedo cambiar el formato de la clave?

**SÍ**, edita `usage_limiter.py` línea 286:

```python
# Formato actual
license_key = f"RVC-PRO-{secrets.token_hex(8).upper()}"

# Formato alternativo 1: Solo números
license_key = f"RVC-{secrets.randbelow(10**12):012d}"
# Output: RVC-123456789012

# Formato alternativo 2: UUID
import uuid
license_key = f"RVC-PRO-{uuid.uuid4()}"
# Output: RVC-PRO-550e8400-e29b-41d4-a716-446655440000

# Formato alternativo 3: Base64
import base64
license_key = f"RVC-{base64.urlsafe_b64encode(secrets.token_bytes(12)).decode()}"
# Output: RVC-a3d8f9B2c1E4g7H5j6K9
```

### ¿Cómo escalo si tengo 1000+ licencias?

**SQLite soporta bien hasta ~100,000 registros**. Si creces más:

```python
# Migrar a PostgreSQL
# requirements.txt
psycopg2-binary==2.9.9

# usage_limiter.py
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    database="rvc_db",
    user="admin",
    password="secure_password"
)
```

### ¿Puedo automatizar el proceso de pago?

**SÍ**, integrando Stripe o PayPal:

```python
# Webhook de Stripe
@app.route("/webhook/stripe", methods=["POST"])
def stripe_webhook():
    payload = request.get_data()
    sig_header = request.headers['Stripe-Signature']
    
    event = stripe.Webhook.construct_event(
        payload, sig_header, webhook_secret
    )
    
    if event['type'] == 'payment_intent.succeeded':
        email = event['data']['object']['receipt_email']
        
        # Generar licencia automáticamente
        limiter = get_limiter()
        license_key = limiter.create_license(email, "PRO", 30)
        
        # Enviar email con licencia
        send_license_email(email, license_key)
    
    return {"status": "success"}
```

### ¿Qué pasa si un usuario pierde su licencia?

**Opciones**:

1. **Consultar por email**:
   ```bash
   python manage_licenses.py list | grep "usuario@gmail.com"
   ```

2. **Agregar endpoint de recuperación**:
   ```python
   @app.route("/api/recover-license", methods=["POST"])
   def recover_license():
       email = request.json.get("email")
       
       # Buscar licencia activa
       cursor.execute("""
           SELECT license_key FROM pro_licenses
           WHERE email = ? AND is_active = 1 
           AND expires_at > datetime('now')
       """, (email,))
       
       license = cursor.fetchone()
       if license:
           # Enviar por email
           send_license_email(email, license[0])
           return {"message": "Licencia enviada a tu email"}
       else:
           return {"error": "No se encontró licencia activa"}, 404
   ```

### ♻️ ¿Cuándo uso CREATE vs RENEW?

**CREATE**: Primera vez que un cliente paga
```bash
python manage_licenses.py create nuevo_cliente@gmail.com
# → Genera licencia nueva: RVC-PRO-ABC123...
```

**RENEW**: Cliente paga mensualmente (2do, 3er pago...)
```bash
python manage_licenses.py renew nuevo_cliente@gmail.com
# → Extiende licencia existente +30 días
# → Incrementa contador: renewal_count = 1, 2, 3...
```

**Ventaja de RENEW**:
- ✅ Un solo registro por cliente (no duplicados)
- ✅ Historial completo de pagos (`renewal_count`)
- ✅ Fecha de última renovación (`last_renewed_at`)
- ✅ Mejor análisis de retención

### ♻️ ¿Qué pasa si renuevo una licencia expirada?

**Se reactiva automáticamente desde HOY**:
```bash
# Licencia expiró el 01/10/2025
# Hoy es 25/10/2025

python manage_licenses.py renew usuario@gmail.com

# Resultado:
# ✅ Licencia reactivada
# 📅 Nueva expiración: 24/11/2025 (hoy + 30 días)
# 🔄 renewal_count incrementado
# ✅ is_active = 1
```

### ♻️ ¿Puedo renovar antes de que expire?

**SÍ, y es lo recomendado**:
```bash
# Licencia expira el 25/12/2025
# Hoy es 20/12/2025 (5 días antes)

python manage_licenses.py renew usuario@gmail.com

# Resultado:
# 📅 Nueva expiración: 24/01/2026 (expira actual + 30 días)
# ✅ No pierde los 5 días restantes
```

### ♻️ ¿Cómo veo el historial de renovaciones?

**Comando LIST muestra todo**:
```bash
python manage_licenses.py list

🔑 RVC-PRO-ABC123XYZ
   Email: usuario@gmail.com
   Plan: PRO
   Creada: 01/10/2025 14:30        # Primera compra
   Expira: 25/01/2026               # Fecha actual de expiración
   Estado: ✅ Activa
   Renovaciones: 3 vez/veces        # 3 pagos adicionales
   Última renovación: 25/12/2025    # Último pago recibido
```

**Cálculo de ingresos**:
```python
# Cliente con 3 renovaciones = 4 pagos totales
# 1 creación + 3 renovaciones = $3 + $3 + $3 + $3 = $12 USD total
```

### ¿Cuánto cuesta mantener el sistema?

**Costos**:
- SQLite: **GRATIS** (incluido en Python)
- Servidor: Depende del hosting (Render/Railway ~$0-7/mes)
- APIs premium: $50-100/mes (se cubren con ~30-50 licencias PRO)

**ROI**:
```
Ingresos: 50 licencias × $3 = $150/mes
Costos: APIs $80 + Hosting $7 = $87/mes
Ganancia: $63/mes
```

### ¿Cómo evito que compartan licencias?

**Estrategias**:

1. **Monitoreo de IPs**:
   ```sql
   -- Ver cuántas IPs usan la misma licencia
   SELECT license_key, COUNT(DISTINCT identifier) as ips
   FROM usage_tracking ut
   JOIN pro_licenses pl ON ...
   GROUP BY license_key
   HAVING ips > 3  -- Sospechoso si >3 IPs
   ```

2. **Límite de activaciones**:
   ```python
   # Solo permitir 2 dispositivos por licencia
   cursor.execute("""
       SELECT COUNT(DISTINCT device_fingerprint)
       FROM usage_tracking
       WHERE license_key = ?
   """, (license_key,))
   
   if count >= 2:
       return {"error": "Límite de dispositivos alcanzado"}
   ```

3. **Términos de servicio**:
   - "1 licencia = 1 usuario"
   - "Compartir licencias = desactivación sin reembolso"

---

## 🎯 RESUMEN EJECUTIVO

### ✅ Lo Que YA Tienes Funcionando

- ✅ Sistema completo de generación de licencias (`manage_licenses.py`)
- ✅ Validación automática con expiración (30 días)
- ✅ Endpoints API (`/api/check-limit`, `/api/validate-license`)
- ✅ Modal frontend con activación de licencias
- ✅ Tracking de uso por IP
- ✅ Base de datos SQLite persistente
- ✅ Claves seguras criptográficamente (`secrets.token_hex`)

### ⚡ Cómo Empezar a Vender HOY

**Primera venta (Cliente NUEVO)**:
1. **Recibe pago** → PayPal, Transferencia, etc. ($3 USD)
2. **Ejecuta comando** → `python manage_licenses.py create email@cliente.com`
3. **Copia clave** → `RVC-PRO-XXXXX`
4. **Envía email** → "Tu licencia es: RVC-PRO-XXXXX"
5. **Usuario activa** → Pega en modal → 30 días de PRO ✅

**Renovaciones (Cliente RECURRENTE)**:
1. **Recibe pago** → Cliente paga el 2do, 3er mes... ($3 USD)
2. **Ejecuta comando** → `python manage_licenses.py renew email@cliente.com`
3. **Sistema extiende** → Misma licencia +30 días
4. **Envía confirmación** → "Licencia renovada hasta: DD/MM/YYYY"
5. **Automático** → Usuario sigue usando sin interrupciones ✅

### 🔒 Seguridad

- ✅ Token aleatorio de 64 bits (imposible de adivinar)
- ✅ Expiración automática (30 días)
- ✅ Desactivación manual disponible
- ✅ Trazabilidad por email + IP
- ✅ Nivel de seguridad adecuado para $3 USD/mes

### ♻️ Sistema de Renovación (NUEVO v2.0)

- ✅ Un registro por cliente (sin duplicados)
- ✅ Contador de renovaciones (`renewal_count`)
- ✅ Fecha de última renovación (`last_renewed_at`)
- ✅ Análisis de retención (cuántos meses paga cada cliente)
- ✅ Reactivación automática de licencias expiradas
- ✅ Email específico de renovación (diferente al de bienvenida)

### 📈 Próximos Pasos (Opcionales)

1. **Automatización de pagos** → Stripe webhook
2. **Email automático** → SendGrid/Mailgun (ya configurado, ver EMAIL_SETUP_GUIDE.md)
3. **Rate limiting** → Prevenir fuerza bruta
4. **Dashboard web** → Gestión visual de licencias

---

**¿Listo para vender tu primera licencia?** 🚀

```bash
# Cliente nuevo
python manage_licenses.py create tu-primer-cliente@gmail.com

# Cliente recurrente (mes 2, 3, 4...)
python manage_licenses.py renew tu-primer-cliente@gmail.com
```

---

**Última actualización**: 26 de octubre de 2025  
**Versión del sistema**: 2.0 (con renovación de licencias)  
**Contacto**: williamppmm@hotmail.com
