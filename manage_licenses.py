#!/usr/bin/env python3
"""
Script de administración para gestionar licencias PRO de RVC Analyzer.
Uso:
    python manage_licenses.py create email@example.com
    python manage_licenses.py list
    python manage_licenses.py validate RVC-PRO-XXX
    python manage_licenses.py deactivate RVC-PRO-XXX
"""

import sys
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from usage_limiter import get_limiter
from datetime import datetime

# Intentar cargar variables de entorno desde .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv no está instalado, usar variables de entorno del sistema

def send_license_email(recipient_email: str, license_key: str, expiry_date: str):
    """
    Enviar email con la licencia al cliente.
    
    Args:
        recipient_email: Email del cliente
        license_key: Clave de licencia generada
        expiry_date: Fecha de expiración (formato: dd/mm/yyyy)
    
    Returns:
        bool: True si se envió exitosamente, False si hubo error
    """
    sender_email = "williamppmm@hotmail.com"
    
    # Crear mensaje
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Tu licencia RVC Analyzer PRO - ¡Activada!"
    msg['From'] = sender_email
    msg['To'] = recipient_email
    
    # Cuerpo del email en texto plano
    text_body = f"""
Hola,

¡Gracias por tu contribución al proyecto RVC Analyzer! 🎉

Tu licencia PRO ha sido activada:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LICENCIA: {license_key}
VÁLIDA HASTA: {expiry_date} (30 días)
CONSULTAS DIARIAS: 200 (antes 10)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CÓMO ACTIVAR:

1. Ve a https://rvc-analyzer.com (o localhost:5000 si es local)
2. Cuando aparezca el modal de límite, haz clic en 
   "¿Ya tienes licencia? Actívala aquí"
3. Pega tu clave: {license_key}
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
williamppmm@hotmail.com
"""
    
    # Cuerpo del email en HTML
    html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #4a8fe3 0%, #175499 100%); 
                   color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
        .header h1 {{ margin: 0; font-size: 24px; }}
        .content {{ background: #f9f9f9; padding: 30px; border: 1px solid #ddd; }}
        .license-box {{ background: white; border-left: 4px solid #4a8fe3; 
                        padding: 20px; margin: 20px 0; border-radius: 5px; }}
        .license-key {{ font-size: 18px; font-weight: bold; color: #175499; 
                        background: #e8f4fd; padding: 10px; border-radius: 5px; 
                        text-align: center; margin: 10px 0; letter-spacing: 1px; }}
        .steps {{ background: white; padding: 20px; margin: 20px 0; border-radius: 5px; }}
        .steps ol {{ padding-left: 20px; }}
        .steps li {{ margin: 10px 0; }}
        .benefits {{ list-style: none; padding: 0; }}
        .benefits li {{ padding: 8px 0; padding-left: 25px; position: relative; }}
        .benefits li:before {{ content: "✅"; position: absolute; left: 0; }}
        .footer {{ text-align: center; padding: 20px; color: #666; font-size: 14px; }}
        .button {{ display: inline-block; background: #4a8fe3; color: white; 
                   padding: 12px 30px; text-decoration: none; border-radius: 5px; 
                   margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎉 Tu Licencia PRO Está Activada</h1>
            <p>RVC Analyzer - Investment Analysis Tool</p>
        </div>
        
        <div class="content">
            <p>Hola,</p>
            <p>¡Gracias por tu contribución al proyecto RVC Analyzer!</p>
            
            <div class="license-box">
                <h3 style="margin-top: 0; color: #175499;">📋 Detalles de tu Licencia</h3>
                <div class="license-key">{license_key}</div>
                <p><strong>Válida hasta:</strong> {expiry_date} (30 días)</p>
                <p><strong>Consultas diarias:</strong> 200 (antes: 10)</p>
            </div>
            
            <div class="steps">
                <h3 style="margin-top: 0; color: #175499;">🔐 Cómo Activar tu Licencia</h3>
                <ol>
                    <li>Ve a <strong>https://rvc-analyzer.com</strong></li>
                    <li>Cuando aparezca el modal de límite, haz clic en<br>
                        <em>"¿Ya tienes licencia? Actívala aquí"</em></li>
                    <li>Pega tu clave: <code>{license_key}</code></li>
                    <li>¡Listo! Ahora tienes acceso PRO por 30 días 🚀</li>
                </ol>
            </div>
            
            <div style="background: white; padding: 20px; border-radius: 5px;">
                <h3 style="margin-top: 0; color: #175499;">✨ Beneficios de tu Plan PRO</h3>
                <ul class="benefits">
                    <li>200 consultas diarias (20x más que FREE)</li>
                    <li>APIs premium (Alpha Vantage, Twelve Data)</li>
                    <li>Datos en tiempo real</li>
                    <li>Soporte prioritario</li>
                    <li>Contribuyes al sostenimiento del proyecto</li>
                </ul>
            </div>
            
            <p style="text-align: center; margin-top: 30px;">
                ¿Tienes algún problema?<br>
                <strong>Responde este email</strong> y te ayudaré personalmente.
            </p>
        </div>
        
        <div class="footer">
            <p><strong>William Pérez</strong><br>
            Creador de RVC Analyzer<br>
            <a href="mailto:williamppmm@hotmail.com">williamppmm@hotmail.com</a></p>
            
            <p style="font-size: 12px; color: #999; margin-top: 20px;">
                Este email fue generado automáticamente por el sistema de licencias de RVC Analyzer.
            </p>
        </div>
    </div>
</body>
</html>
"""
    
    # Adjuntar ambas versiones
    part1 = MIMEText(text_body, 'plain', 'utf-8')
    part2 = MIMEText(html_body, 'html', 'utf-8')
    msg.attach(part1)
    msg.attach(part2)
    
    try:
        # Obtener credenciales desde variables de entorno
        smtp_server = os.getenv('SMTP_SERVER')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        smtp_email = os.getenv('SMTP_EMAIL')
        smtp_password = os.getenv('SMTP_PASSWORD')
        
        # Validar que las credenciales estén configuradas
        if not all([smtp_server, smtp_email, smtp_password]):
            print(f"\n⚠️  Credenciales SMTP no configuradas.")
            print("   Para enviar emails automáticamente:")
            print("   1. Copia .env.example a .env")
            print("   2. Completa SMTP_SERVER, SMTP_EMAIL, SMTP_PASSWORD")
            print("   3. Consulta las instrucciones en .env.example\n")
            return False
        
        print(f"\n📧 Enviando email a {recipient_email}...")
        print(f"   Servidor: {smtp_server}:{smtp_port}")
        print(f"   Desde: {smtp_email}")
        
        # Conectar y enviar
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Activar encriptación TLS
            server.login(smtp_email, smtp_password)
            server.send_message(msg)
        
        print(f"✅ Email enviado exitosamente a {recipient_email}")
        return True
        
    except smtplib.SMTPAuthenticationError:
        print(f"\n❌ Error de autenticación SMTP.")
        print("   Verifica que SMTP_EMAIL y SMTP_PASSWORD sean correctos.")
        print("   Para Hotmail/Gmail, usa una 'contraseña de aplicación'.")
        return False
        
    except smtplib.SMTPException as e:
        print(f"\n❌ Error SMTP: {e}")
        print("   Verifica la configuración de SMTP_SERVER y SMTP_PORT.")
        return False
        
    except Exception as e:
        print(f"\n❌ Error inesperado al enviar email: {e}")
        return False


def create_license(email: str):
    """Crear una nueva licencia de 30 días por $3 USD."""
    limiter = get_limiter()
    
    print(f"\n🔑 Generando licencia PRO para: {email}")
    print(f"💰 Costo: $3 USD")
    print(f"⏱️  Duración: 30 días")
    
    confirm = input("\n¿Confirmar creación? (s/n): ")
    if confirm.lower() != 's':
        print("❌ Cancelado")
        return
    
    try:
        license_key = limiter.create_license(
            email=email,
            plan_type="PRO",
            duration_days=30
        )
        
        print(f"\n✅ ¡Licencia creada exitosamente!")
        print(f"\n{'='*50}")
        print(f"LICENCIA: {license_key}")
        print(f"EMAIL: {email}")
        
        # Calcular fecha de expiración correctamente
        from datetime import timedelta
        expiry_date = datetime.now() + timedelta(days=30)
        expiry_str = expiry_date.strftime('%d/%m/%Y')
        
        print(f"VÁLIDA HASTA: {expiry_str}")
        print(f"{'='*50}\n")
        
        # Preguntar si quiere enviar email automáticamente
        send_email = input("¿Deseas enviar la licencia por email automáticamente? (s/n): ")
        
        if send_email.lower() == 's':
            email_sent = send_license_email(email, license_key, expiry_str)
            if email_sent:
                print("✅ Email enviado exitosamente")
            else:
                print("\n📋 Email NO configurado. Copia y envía manualmente:")
                print(f"   Para: {email}")
                print(f"   Asunto: Tu licencia RVC Analyzer PRO")
                print(f"   Licencia: {license_key}")
        else:
            print(f"\n📧 Recuerda enviar la licencia al cliente:")
            print(f"   Para: {email}")
            print(f"   Licencia: {license_key}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


def renew_license(email_or_key: str):
    """Renovar una licencia existente por 30 días adicionales."""
    limiter = get_limiter()
    
    print(f"\n♻️  Renovando licencia para: {email_or_key}")
    print(f"💰 Costo: $3 USD")
    print(f"⏱️  Extensión: 30 días adicionales")
    
    # Primero verificar si existe sin hacer UPDATE
    import sqlite3
    conn = sqlite3.connect(limiter.db_path)
    cursor = conn.cursor()
    
    if email_or_key.startswith('RVC-'):
        cursor.execute("""
            SELECT license_key, email, expires_at, is_active, renewal_count
            FROM pro_licenses
            WHERE license_key = ?
        """, (email_or_key,))
    else:
        cursor.execute("""
            SELECT license_key, email, expires_at, is_active, renewal_count
            FROM pro_licenses
            WHERE email = ?
            ORDER BY created_at DESC
            LIMIT 1
        """, (email_or_key,))
    
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        print(f"\n⚠️  No se encontró licencia existente para: {email_or_key}")
        print(f"   💡 Usa 'create' para generar una nueva licencia.")
        return
    
    license_key, email, expires_at, is_active, renewal_count = result
    
    # Verificar si está expirada
    from datetime import datetime
    now = datetime.now()
    expiry_date = datetime.fromisoformat(expires_at) if expires_at else None
    is_expired = expiry_date < now if expiry_date else False
    
    # Mostrar información actual
    print(f"\n📋 Licencia encontrada:")
    print(f"   • Key: {license_key}")
    print(f"   • Email: {email}")
    print(f"   • Expira: {expiry_date.strftime('%d/%m/%Y') if expiry_date else 'N/A'}")
    print(f"   • Renovaciones previas: {renewal_count if renewal_count else 0}")
    
    if is_expired:
        print(f"   • Estado: ⏰ EXPIRADA - Se reactivará")
    elif not is_active:
        print(f"   • Estado: ❌ INACTIVA - Se reactivará")
    else:
        days_left = (expiry_date - now).days if expiry_date else 0
        print(f"   • Estado: ✅ ACTIVA ({days_left} días restantes) - Se extenderá")
    
    confirm = input("\n¿Confirmar renovación por 30 días más? (s/n): ")
    if confirm.lower() != 's':
        print("❌ Cancelado")
        return
    
    # Renovar por 30 días
    result = limiter.renew_license(email_or_key, duration_days=30)
    
    if result["success"]:
        print(f"\n✅ ¡Licencia renovada exitosamente!")
        print(f"\n{'='*50}")
        print(f"LICENCIA: {result['license_key']}")
        print(f"EMAIL: {result['email']}")
        print(f"EXPIRABA: {result['old_expires_at']}")
        print(f"NUEVA EXPIRACIÓN: {result['new_expires_at']}")
        print(f"RENOVACIÓN #{result['renewal_count']}")
        print(f"{'='*50}\n")
        
        # Preguntar si quiere enviar email
        send_email = input("¿Deseas enviar confirmación por email? (s/n): ")
        
        if send_email.lower() == 's':
            email_sent = send_renewal_email(
                result['email'],
                result['license_key'],
                result['new_expires_at'],
                result['renewal_count']
            )
            if email_sent:
                print("✅ Email enviado exitosamente")
            else:
                print("\n📧 Recuerda notificar al cliente:")
                print(f"   Para: {result['email']}")
                print(f"   Licencia renovada hasta: {result['new_expires_at']}")
        else:
            print(f"\n📧 Recuerda notificar al cliente:")
            print(f"   Para: {result['email']}")
            print(f"   Licencia renovada hasta: {result['new_expires_at']}")
    else:
        print(f"\n❌ Error al renovar: {result.get('reason')}")


def send_renewal_email(recipient_email: str, license_key: str, expiry_date: str, renewal_number: int):
    """
    Enviar email de confirmación de renovación.
    Similar a send_license_email pero adaptado para renovaciones.
    """
    sender_email = os.getenv('SMTP_EMAIL', 'williamppmm@hotmail.com')
    
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"Tu licencia RVC Analyzer PRO - Renovada (#{renewal_number})"
    msg['From'] = sender_email
    msg['To'] = recipient_email
    
    text_body = f"""
Hola,

¡Gracias por renovar tu contribución al proyecto RVC Analyzer! 🎉

Tu licencia PRO ha sido RENOVADA:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LICENCIA: {license_key}
NUEVA FECHA DE EXPIRACIÓN: {expiry_date}
RENOVACIÓN: #{renewal_number}
CONSULTAS DIARIAS: 200
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Tu licencia sigue activa automáticamente. No necesitas hacer nada.

BENEFICIOS PRO:
✅ 200 consultas diarias
✅ APIs premium (Alpha Vantage, Twelve Data)
✅ Datos en tiempo real
✅ Soporte prioritario

¡Gracias por seguir apoyando el proyecto!

William Pérez
Creador de RVC Analyzer
williamppmm@hotmail.com
"""
    
    html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #10b981 0%, #059669 100%); 
                   color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
        .header h1 {{ margin: 0; font-size: 24px; }}
        .content {{ background: #f9f9f9; padding: 30px; border: 1px solid #ddd; }}
        .renewal-box {{ background: white; border-left: 4px solid #10b981; 
                        padding: 20px; margin: 20px 0; border-radius: 5px; }}
        .license-key {{ font-size: 18px; font-weight: bold; color: #059669; 
                        background: #d1fae5; padding: 10px; border-radius: 5px; 
                        text-align: center; margin: 10px 0; letter-spacing: 1px; }}
        .benefits {{ list-style: none; padding: 0; }}
        .benefits li {{ padding: 8px 0; padding-left: 25px; position: relative; }}
        .benefits li:before {{ content: "✅"; position: absolute; left: 0; }}
        .footer {{ text-align: center; padding: 20px; color: #666; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>♻️ Licencia PRO Renovada</h1>
            <p>RVC Analyzer - Renovación #{renewal_number}</p>
        </div>
        
        <div class="content">
            <p>Hola,</p>
            <p>¡Gracias por renovar tu contribución al proyecto RVC Analyzer!</p>
            
            <div class="renewal-box">
                <h3 style="margin-top: 0; color: #059669;">📋 Detalles de Renovación</h3>
                <div class="license-key">{license_key}</div>
                <p><strong>Nueva fecha de expiración:</strong> {expiry_date}</p>
                <p><strong>Renovación:</strong> #{renewal_number}</p>
                <p><strong>Consultas diarias:</strong> 200</p>
            </div>
            
            <div style="background: #d1fae5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <p style="margin: 0; color: #059669; font-weight: bold;">
                    ✅ Tu licencia sigue activa automáticamente
                </p>
                <p style="margin: 5px 0 0 0; font-size: 0.9rem;">
                    No necesitas hacer nada. Tu acceso PRO continúa sin interrupciones.
                </p>
            </div>
            
            <div style="background: white; padding: 20px; border-radius: 5px;">
                <h3 style="margin-top: 0; color: #059669;">✨ Tus Beneficios PRO</h3>
                <ul class="benefits">
                    <li>200 consultas diarias</li>
                    <li>APIs premium (Alpha Vantage, Twelve Data)</li>
                    <li>Datos en tiempo real</li>
                    <li>Soporte prioritario</li>
                    <li>Contribuyes al sostenimiento del proyecto</li>
                </ul>
            </div>
            
            <p style="text-align: center; margin-top: 30px;">
                ¿Tienes alguna pregunta?<br>
                <strong>Responde este email</strong> y te ayudaré personalmente.
            </p>
        </div>
        
        <div class="footer">
            <p><strong>William Pérez</strong><br>
            Creador de RVC Analyzer<br>
            <a href="mailto:williamppmm@hotmail.com">williamppmm@hotmail.com</a></p>
            
            <p style="font-size: 12px; color: #999; margin-top: 20px;">
                Renovación procesada automáticamente por el sistema de licencias de RVC Analyzer.
            </p>
        </div>
    </div>
</body>
</html>
"""
    
    part1 = MIMEText(text_body, 'plain', 'utf-8')
    part2 = MIMEText(html_body, 'html', 'utf-8')
    msg.attach(part1)
    msg.attach(part2)
    
    try:
        smtp_server = os.getenv('SMTP_SERVER')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        smtp_email = os.getenv('SMTP_EMAIL')
        smtp_password = os.getenv('SMTP_PASSWORD')
        
        if not all([smtp_server, smtp_email, smtp_password]):
            return False
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_email, smtp_password)
            server.send_message(msg)
        
        return True
        
    except Exception:
        return False


def list_licenses():
    """Listar todas las licencias activas."""
    import sqlite3
    limiter = get_limiter()
    
    conn = sqlite3.connect(limiter.db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT license_key, email, plan_type, created_at, expires_at, is_active, 
               renewal_count, last_renewed_at
        FROM pro_licenses
        ORDER BY created_at DESC
    """)
    
    licenses = cursor.fetchall()
    conn.close()
    
    if not licenses:
        print("\n📋 No hay licencias registradas")
        return
    
    print(f"\n📋 LICENCIAS REGISTRADAS ({len(licenses)})")
    print("="*100)
    
    for lic in licenses:
        key, email, plan, created, expires, active, renewal_count, last_renewed = lic
        
        status = "✅ Activa" if active else "❌ Inactiva"
        
        created_dt = datetime.fromisoformat(created)
        expires_dt = datetime.fromisoformat(expires) if expires else None
        
        if expires_dt:
            days_left = (expires_dt - datetime.now()).days
            if days_left < 0:
                status = "⏰ Expirada"
            elif days_left <= 3:
                status = f"⚠️  Expira en {days_left} días"
        
        print(f"\n🔑 {key}")
        print(f"   Email: {email}")
        print(f"   Plan: {plan}")
        print(f"   Creada: {created_dt.strftime('%d/%m/%Y %H:%M')}")
        print(f"   Expira: {expires_dt.strftime('%d/%m/%Y') if expires_dt else 'Permanente'}")
        print(f"   Estado: {status}")
        
        # Mostrar renovaciones si existen
        if renewal_count and renewal_count > 0:
            print(f"   Renovaciones: {renewal_count} vez/veces")
            if last_renewed:
                last_renewed_dt = datetime.fromisoformat(last_renewed)
                print(f"   Última renovación: {last_renewed_dt.strftime('%d/%m/%Y %H:%M')}")
    
    print("\n" + "="*100)


def validate_license_cmd(license_key: str):
    """Validar una licencia."""
    limiter = get_limiter()
    
    print(f"\n🔍 Validando licencia: {license_key}")
    
    result = limiter.validate_license(license_key)
    
    if result["valid"]:
        print(f"\n✅ LICENCIA VÁLIDA")
        print(f"\n{'='*50}")
        print(f"Plan: {result['plan']}")
        print(f"Email: {result['email']}")
        print(f"Expira: {result['expires_at']}")
        if result.get('days_left'):
            print(f"Días restantes: {result['days_left']}")
        print(f"{'='*50}\n")
    else:
        print(f"\n❌ LICENCIA INVÁLIDA")
        print(f"Razón: {result.get('reason', 'Desconocida')}\n")


def deactivate_license(license_key: str):
    """Desactivar una licencia."""
    import sqlite3
    limiter = get_limiter()
    
    print(f"\n⚠️  Desactivando licencia: {license_key}")
    
    confirm = input("¿Confirmar desactivación? (s/n): ")
    if confirm.lower() != 's':
        print("❌ Cancelado")
        return
    
    try:
        conn = sqlite3.connect(limiter.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE pro_licenses
            SET is_active = 0
            WHERE license_key = ?
        """, (license_key,))
        
        if cursor.rowcount == 0:
            print(f"\n❌ Licencia no encontrada")
        else:
            conn.commit()
            print(f"\n✅ Licencia desactivada exitosamente")
        
        conn.close()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


def show_stats():
    """Mostrar estadísticas de uso."""
    limiter = get_limiter()
    stats = limiter.get_usage_stats()
    
    print(f"\n📊 ESTADÍSTICAS DE USO")
    print("="*50)
    print(f"Total consultas: {stats.get('total_queries', 0)}")
    print(f"Usuarios únicos: {stats.get('unique_metric', 0)}")
    print(f"Primera consulta: {stats.get('first_query', 'N/A')}")
    print(f"Última consulta: {stats.get('last_query', 'N/A')}")
    print("="*50 + "\n")


def delete_license(license_key: str):
    """Eliminar permanentemente una licencia de la base de datos."""
    import sqlite3
    limiter = get_limiter()
    
    print(f"\n⚠️  ELIMINACIÓN PERMANENTE")
    print(f"Licencia: {license_key}")
    print(f"\nEsto eliminará la licencia de la base de datos de forma IRREVERSIBLE.")
    print(f"Si solo quieres desactivarla temporalmente, usa: deactivate\n")
    
    confirm = input("¿Confirmar ELIMINACIÓN PERMANENTE? (escribe 'ELIMINAR' para confirmar): ")
    if confirm != 'ELIMINAR':
        print("❌ Cancelado - Eliminación no confirmada")
        return
    
    try:
        conn = sqlite3.connect(limiter.db_path)
        cursor = conn.cursor()
        
        # Primero mostrar info de la licencia
        cursor.execute("""
            SELECT email, plan_type, created_at, expires_at
            FROM pro_licenses
            WHERE license_key = ?
        """, (license_key,))
        
        license_info = cursor.fetchone()
        
        if not license_info:
            print(f"\n❌ Licencia no encontrada: {license_key}")
            conn.close()
            return
        
        email, plan, created, expires = license_info
        
        # Eliminar la licencia
        cursor.execute("""
            DELETE FROM pro_licenses
            WHERE license_key = ?
        """, (license_key,))
        
        conn.commit()
        conn.close()
        
        print(f"\n✅ Licencia ELIMINADA permanentemente")
        print(f"\nDetalles de la licencia eliminada:")
        print(f"  • Key: {license_key}")
        print(f"  • Email: {email}")
        print(f"  • Plan: {plan}")
        print(f"  • Creada: {created}")
        print(f"  • Expiraba: {expires}\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


def main():
    if len(sys.argv) < 2:
        print("\n🔐 RVC Analyzer - Gestor de Licencias PRO")
        print("\nUso:")
        print("  python manage_licenses.py create <email>       - Crear licencia NUEVA ($3 USD / 30 días)")
        print("  python manage_licenses.py renew <email|key>    - Renovar licencia EXISTENTE ($3 USD / +30 días)")
        print("  python manage_licenses.py list                 - Listar todas las licencias")
        print("  python manage_licenses.py validate <key>       - Validar una licencia")
        print("  python manage_licenses.py deactivate <key>     - Desactivar una licencia")
        print("  python manage_licenses.py delete <key>         - ELIMINAR permanentemente una licencia")
        print("  python manage_licenses.py stats                - Ver estadísticas de uso")
        print("\n💡 Diferencia entre CREATE y RENEW:")
        print("  • CREATE: Genera una licencia nueva (primer pago del cliente)")
        print("  • RENEW: Extiende licencia existente por 30 días más (pago mensual recurrente)")
        print("\nEjemplos:")
        print("  python manage_licenses.py create usuario@gmail.com")
        print("  python manage_licenses.py renew usuario@gmail.com")
        print("  python manage_licenses.py renew RVC-PRO-ABC123XYZ")
        print("  python manage_licenses.py validate RVC-PRO-ABC123XYZ")
        print("  python manage_licenses.py delete RVC-PRO-ABC123XYZ\n")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "create":
        if len(sys.argv) < 3:
            print("❌ Error: Debes proporcionar un email")
            print("Uso: python manage_licenses.py create <email>")
            sys.exit(1)
        create_license(sys.argv[2])
    
    elif command == "renew":
        if len(sys.argv) < 3:
            print("❌ Error: Debes proporcionar un email o clave de licencia")
            print("Uso: python manage_licenses.py renew <email|license_key>")
            sys.exit(1)
        renew_license(sys.argv[2])
    
    elif command == "list":
        list_licenses()
    
    elif command == "validate":
        if len(sys.argv) < 3:
            print("❌ Error: Debes proporcionar una clave de licencia")
            print("Uso: python manage_licenses.py validate <license_key>")
            sys.exit(1)
        validate_license_cmd(sys.argv[2])
    
    elif command == "deactivate":
        if len(sys.argv) < 3:
            print("❌ Error: Debes proporcionar una clave de licencia")
            print("Uso: python manage_licenses.py deactivate <license_key>")
            sys.exit(1)
        deactivate_license(sys.argv[2])
    
    elif command == "delete":
        if len(sys.argv) < 3:
            print("❌ Error: Debes proporcionar una clave de licencia")
            print("Uso: python manage_licenses.py delete <license_key>")
            sys.exit(1)
        delete_license(sys.argv[2])
    
    elif command == "stats":
        show_stats()
    
    else:
        print(f"❌ Comando desconocido: {command}")
        print("Comandos válidos: create, renew, list, validate, deactivate, delete, stats")
        sys.exit(1)


if __name__ == "__main__":
    main()
