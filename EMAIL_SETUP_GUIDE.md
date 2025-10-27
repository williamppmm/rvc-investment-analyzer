# 📧 GUÍA DE CONFIGURACIÓN DE EMAIL AUTOMÁTICO

**Última actualización**: 26 de octubre de 2025

---

## 🎯 ¿Qué hace esta funcionalidad?

Cuando generas una licencia con `python manage_licenses.py create email@cliente.com`, el sistema **puede enviar automáticamente** un email profesional al cliente con:

✅ Clave de licencia  
✅ Fecha de expiración  
✅ Instrucciones de activación  
✅ Beneficios del plan PRO  
✅ Diseño HTML profesional  

---

## 🚀 CONFIGURACIÓN RÁPIDA (5 minutos)

### Paso 1: Copiar archivo de ejemplo

```bash
# En la carpeta del proyecto
copy .env.example .env
# O en Linux/Mac:
cp .env.example .env
```

### Paso 2: Elegir proveedor de email

Tienes 3 opciones (de más fácil a más avanzado):

---

## 📮 OPCIÓN 1: HOTMAIL/OUTLOOK (Recomendado para empezar)

### ✅ Ventajas
- Gratis
- Fácil de configurar
- Ya tienes cuenta (williamppmm@hotmail.com)

### 📋 Pasos

1. **Ve a tu cuenta de Microsoft**: https://account.live.com/proofs/AppPassword

2. **Genera una contraseña de aplicación**:
   - Haz clic en "Crear una nueva contraseña de aplicación"
   - Copia la contraseña generada (ejemplo: `abcd efgh ijkl mnop`)

3. **Edita `.env`**:
   ```env
   SMTP_SERVER=smtp-mail.outlook.com
   SMTP_PORT=587
   SMTP_EMAIL=williamppmm@hotmail.com
   SMTP_PASSWORD=abcdefghijklmnop  # Sin espacios
   ```

4. **¡Listo!** Prueba con:
   ```bash
   python manage_licenses.py create test@ejemplo.com
   ```

---

## 📮 OPCIÓN 2: GMAIL

### ✅ Ventajas
- Gratis
- Muy confiable
- Integración con Google

### 📋 Pasos

1. **Activa verificación en 2 pasos**:
   - Ve a: https://myaccount.google.com/security
   - Activa "Verificación en 2 pasos"

2. **Genera contraseña de aplicación**:
   - Ve a: https://myaccount.google.com/apppasswords
   - Selecciona "Correo" y tu dispositivo
   - Copia la contraseña de 16 caracteres

3. **Edita `.env`**:
   ```env
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SMTP_EMAIL=tu_email@gmail.com
   SMTP_PASSWORD=abcdefghijklmnop  # 16 caracteres sin espacios
   ```

---

## 📮 OPCIÓN 3: SENDGRID (Recomendado para producción)

### ✅ Ventajas
- 100 emails/día GRATIS
- Muy confiable (99.9% entrega)
- Análitica de emails
- No requiere tu contraseña personal

### 📋 Pasos

1. **Regístrate en SendGrid**:
   - Ve a: https://sendgrid.com
   - Crea cuenta gratuita (100 emails/día)

2. **Crea un API Key**:
   - Ve a: Settings > API Keys
   - Clic en "Create API Key"
   - Nombre: "RVC Analyzer"
   - Permisos: "Full Access"
   - Copia el API Key (SG.xxxxxxxxxxxx)

3. **Verifica tu dominio/email de envío**:
   - Ve a: Settings > Sender Authentication
   - Verifica tu email williamppmm@hotmail.com

4. **Edita `.env`**:
   ```env
   SMTP_SERVER=smtp.sendgrid.net
   SMTP_PORT=587
   SMTP_EMAIL=apikey
   SMTP_PASSWORD=SG.xxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

---

## 🧪 PRUEBA DE CONFIGURACIÓN

### Opción A: Crear licencia de prueba

```bash
# Activar entorno virtual
& C:/rcv_proyecto/.venv/Scripts/Activate.ps1

# Generar licencia de prueba para ti mismo
python manage_licenses.py create williamppmm@hotmail.com

# Output esperado:
🔑 Generando licencia PRO para: williamppmm@hotmail.com
💰 Costo: $3 USD
⏱️  Duración: 30 días

¿Confirmar creación? (s/n): s

✅ ¡Licencia creada exitosamente!

==================================================
LICENCIA: RVC-PRO-XXXXXXXXXXXX
EMAIL: williamppmm@hotmail.com
VÁLIDA HASTA: 25/11/2025
==================================================

¿Deseas enviar la licencia por email automáticamente? (s/n): s

📧 Enviando email a williamppmm@hotmail.com...
   Servidor: smtp-mail.outlook.com:587
   Desde: williamppmm@hotmail.com
✅ Email enviado exitosamente a williamppmm@hotmail.com
```

### Opción B: Script de prueba rápido

```python
# test_email.py
from manage_licenses import send_license_email
from datetime import datetime, timedelta

expiry = (datetime.now() + timedelta(days=30)).strftime('%d/%m/%Y')
result = send_license_email(
    recipient_email="williamppmm@hotmail.com",
    license_key="RVC-PRO-TEST123456789",
    expiry_date=expiry
)

if result:
    print("✅ Email de prueba enviado")
else:
    print("❌ Revisa la configuración")
```

---

## ⚠️ SOLUCIÓN DE PROBLEMAS

### Error: "Credenciales SMTP no configuradas"

**Causa**: El archivo `.env` no existe o está incompleto.

**Solución**:
```bash
# Verifica que existe .env (no .env.example)
dir .env

# Si no existe, créalo:
copy .env.example .env

# Edita .env y completa las credenciales
```

### Error: "Error de autenticación SMTP"

**Causa**: Email o contraseña incorrectos.

**Solución para Hotmail/Outlook**:
1. NO uses tu contraseña normal
2. Debes generar una "contraseña de aplicación"
3. Ve a: https://account.live.com/proofs/AppPassword
4. Elimina espacios de la contraseña antes de copiarla a `.env`

**Solución para Gmail**:
1. Verifica que tengas activada verificación en 2 pasos
2. Genera una contraseña de aplicación en: https://myaccount.google.com/apppasswords
3. Usa los 16 caracteres SIN espacios

### Error: "Connection refused" o "Timeout"

**Causa**: Puerto o servidor SMTP incorrecto.

**Solución**:
```env
# Hotmail/Outlook
SMTP_SERVER=smtp-mail.outlook.com  # NO smtp.office365.com
SMTP_PORT=587  # NO 465

# Gmail
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

### Error: "SMTPSenderRefused"

**Causa**: Email de envío no verificado (común en SendGrid).

**Solución**:
1. Ve a SendGrid > Settings > Sender Authentication
2. Verifica tu email de envío
3. Revisa tu bandeja de entrada para confirmar

---

## 📊 COMPARACIÓN DE OPCIONES

| Característica | Hotmail | Gmail | SendGrid |
|----------------|---------|-------|----------|
| **Costo** | Gratis | Gratis | Gratis (100/día) |
| **Límite diario** | ~300 emails | ~500 emails | 100 emails |
| **Facilidad** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Confiabilidad** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Analítica** | ❌ | ❌ | ✅ |
| **Recomendado para** | Pruebas | Uso personal | Producción |

---

## 🔒 SEGURIDAD

### ✅ Buenas Prácticas

1. **NUNCA** subas `.env` a GitHub (ya está en `.gitignore`)
2. **USA** contraseñas de aplicación, NO tu contraseña personal
3. **ROTA** las credenciales cada 3-6 meses
4. **LIMITA** el acceso al archivo `.env` (solo tú)

### 🔐 Permisos de archivo .env (Opcional)

```bash
# Linux/Mac - Solo lectura para el propietario
chmod 600 .env

# Windows - Usar propiedades de archivo > Seguridad
```

---

## 📧 EJEMPLO DE EMAIL RECIBIDO

Así se verá el email que recibe el cliente:

```
┌─────────────────────────────────────────┐
│  🎉 Tu Licencia PRO Está Activada      │
│  RVC Analyzer - Investment Analysis     │
├─────────────────────────────────────────┤
│                                         │
│  Hola,                                  │
│  ¡Gracias por tu contribución!          │
│                                         │
│  📋 Detalles de tu Licencia             │
│  ┌─────────────────────────────────┐   │
│  │ RVC-PRO-A1B2C3D4E5F6G7H8       │   │
│  └─────────────────────────────────┘   │
│  Válida hasta: 25/11/2025 (30 días)    │
│  Consultas diarias: 200                 │
│                                         │
│  🔐 Cómo Activar                        │
│  1. Ve a rvc-analyzer.com               │
│  2. Clic en "¿Ya tienes licencia?"      │
│  3. Pega: RVC-PRO-A1B2C3D4E5F6G7H8     │
│  4. ¡Listo! 🚀                          │
│                                         │
│  ✨ Beneficios PRO                       │
│  ✅ 200 consultas diarias               │
│  ✅ APIs premium                        │
│  ✅ Datos en tiempo real                │
│  ✅ Soporte prioritario                 │
│                                         │
│  William Pérez                          │
│  williamppmm@hotmail.com                │
└─────────────────────────────────────────┘
```

**Versión HTML**: Incluye colores, gradientes, y diseño profesional.

---

## 🚀 FLUJO COMPLETO CON EMAIL AUTOMÁTICO

```
1. Cliente te contacta y paga $3 USD
   ↓
2. Ejecutas: python manage_licenses.py create cliente@gmail.com
   ↓
3. Sistema pregunta: ¿Confirmar creación? (s/n): s
   ↓
4. Licencia generada: RVC-PRO-XXXXXXXXXXXX
   ↓
5. Sistema pregunta: ¿Enviar email automáticamente? (s/n): s
   ↓
6. Email enviado automáticamente ✅
   ↓
7. Cliente recibe email con instrucciones
   ↓
8. Cliente activa licencia en el modal
   ↓
9. ¡Cliente usa PRO por 30 días! 🎉
```

---

## 📝 NOTAS ADICIONALES

### ¿Puedo usar otro proveedor de email?

**SÍ**. Cualquier servidor SMTP funciona. Ejemplos:

```env
# Mailgun
SMTP_SERVER=smtp.mailgun.org
SMTP_PORT=587

# Amazon SES
SMTP_SERVER=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587

# Zoho Mail
SMTP_SERVER=smtp.zoho.com
SMTP_PORT=587
```

### ¿Cómo personalizar el template del email?

Edita la función `send_license_email()` en `manage_licenses.py`:

```python
# Línea ~50-120 del archivo
html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <!-- Agrega tus estilos personalizados aquí -->
</head>
...
```

### ¿Puedo enviar emails de prueba sin crear licencias?

**SÍ**, usa el script de prueba:

```python
from manage_licenses import send_license_email

send_license_email(
    recipient_email="tu_email@test.com",
    license_key="RVC-PRO-DEMO123456789",
    expiry_date="31/12/2025"
)
```

---

## ✅ CHECKLIST DE CONFIGURACIÓN

- [ ] Copié `.env.example` a `.env`
- [ ] Elegí proveedor de email (Hotmail/Gmail/SendGrid)
- [ ] Generé contraseña de aplicación
- [ ] Completé credenciales en `.env`
- [ ] Probé con `python manage_licenses.py create mi_email@test.com`
- [ ] Confirmé recepción del email
- [ ] Verifiqué formato HTML del email
- [ ] Revisé que no haya errores en el log

---

**¿Necesitas ayuda?** Abre un issue en GitHub o contacta a williamppmm@hotmail.com

---

**Última actualización**: 26 de octubre de 2025  
**Versión**: 1.0
