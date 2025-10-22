# Scripts de Mantenimiento - RVC Analyzer

Esta carpeta contiene scripts de utilidad para mantenimiento del proyecto.

---

## 📋 Scripts Disponibles

### 1. `backup.sh` (Linux/Mac/Git Bash)

Script de backup automático compatible con Linux, macOS y Git Bash en Windows.

**Uso**:
```bash
# Backup diario (retención: 7 días)
./scripts/backup.sh daily

# Backup semanal (retención: 30 días)
./scripts/backup.sh weekly

# Backup mensual (retención: 365 días)
./scripts/backup.sh monthly
```

**Características**:
- ✅ Verifica estado de Git antes del backup
- ✅ Excluye archivos temporales y caché
- ✅ Crea backup separado de la base de datos
- ✅ Limpia backups antiguos automáticamente
- ✅ Reporta tamaño y resumen del backup

**Automatización con Cron** (Linux/Mac):
```bash
# Editar crontab
crontab -e

# Agregar estas líneas:
# Backup diario a las 2 AM
0 2 * * * /ruta/completa/rcv_proyecto/scripts/backup.sh daily

# Backup semanal los domingos a las 3 AM
0 3 * * 0 /ruta/completa/rcv_proyecto/scripts/backup.sh weekly

# Backup mensual el día 1 a las 4 AM
0 4 1 * * /ruta/completa/rcv_proyecto/scripts/backup.sh monthly
```

---

### 2. `backup.ps1` (Windows PowerShell)

Script de backup automático para Windows usando PowerShell.

**Uso**:
```powershell
# Backup diario (retención: 7 días)
.\scripts\backup.ps1 -Type daily

# Backup semanal (retención: 30 días)
.\scripts\backup.ps1 -Type weekly

# Backup mensual (retención: 365 días)
.\scripts\backup.ps1 -Type monthly

# Si no se especifica tipo, usa "daily" por defecto
.\scripts\backup.ps1
```

**Características**:
- ✅ Verifica estado de Git antes del backup
- ✅ Crea archivo ZIP con compresión
- ✅ Excluye archivos temporales y caché
- ✅ Backup separado de la base de datos
- ✅ Limpia backups antiguos automáticamente
- ✅ Reporta tamaño y resumen del backup

**Automatización con Task Scheduler** (Windows):

1. Abrir Task Scheduler (`taskschd.msc`)
2. Crear nueva tarea básica
3. Configurar trigger (diario, semanal, mensual)
4. Acción: "Iniciar un programa"
   - Programa: `powershell.exe`
   - Argumentos: `-ExecutionPolicy Bypass -File "C:\rcv_proyecto\scripts\backup.ps1" -Type daily`
5. Guardar tarea

---

## 📁 Estructura de Backups

Los backups se guardan en:

```
rcv_proyecto/
├── backups/
│   ├── daily/
│   │   ├── rcv_backup_daily_20251022.tar.gz    (o .zip en Windows)
│   │   ├── rcv_backup_daily_20251023.tar.gz
│   │   ├── cache_db_20251022.db
│   │   └── cache_db_20251023.db
│   ├── weekly/
│   │   ├── rcv_backup_weekly_20251022.tar.gz
│   │   └── cache_db_20251022.db
│   └── monthly/
│       ├── rcv_backup_monthly_20251001.tar.gz
│       └── cache_db_20251001.db
```

**NOTA**: La carpeta `backups/` está incluida en `.gitignore` y NO se sube a Git.

---

## 🔄 Restaurar un Backup

### Linux/Mac/Git Bash:
```bash
# Restaurar backup a directorio actual
tar -xzf backups/daily/rcv_backup_daily_20251022.tar.gz -C .

# Restaurar backup a ubicación específica
tar -xzf backups/daily/rcv_backup_daily_20251022.tar.gz -C /ruta/destino

# Restaurar solo la base de datos
cp backups/daily/cache_db_20251022.db data/cache.db
```

### Windows PowerShell:
```powershell
# Restaurar backup a directorio actual
Expand-Archive -Path backups\daily\rcv_backup_daily_20251022.zip -DestinationPath . -Force

# Restaurar backup a ubicación específica
Expand-Archive -Path backups\daily\rcv_backup_daily_20251022.zip -DestinationPath C:\ruta\destino

# Restaurar solo la base de datos
Copy-Item backups\daily\cache_db_20251022.db data\cache.db
```

---

## 🚫 Archivos Excluidos del Backup

Los siguientes archivos/directorios NO se incluyen en los backups:

- `*.pyc` - Bytecode de Python
- `__pycache__/` - Cache de Python
- `.venv/`, `venv/`, `env/` - Entornos virtuales
- `.git/` - Historial de Git (usa Git para versionado)
- `*.log` - Archivos de log
- `backups/` - Evitar backups recursivos
- `data/cache.db` - Se hace backup separado
- `data/temp/` - Archivos temporales
- `.DS_Store`, `Thumbs.db` - Archivos del sistema operativo
- `.env` - Variables de entorno (seguridad)

**Razón**: Estos archivos se pueden regenerar o contienen datos sensibles.

---

## ⚙️ Política de Retención

| Tipo | Frecuencia Recomendada | Retención | Uso |
|------|------------------------|-----------|-----|
| **Daily** | Diario (2 AM) | 7 días | Desarrollo activo, recuperación rápida |
| **Weekly** | Semanal (Domingos 3 AM) | 30 días | Puntos de restauración semanales |
| **Monthly** | Mensual (Día 1 a las 4 AM) | 365 días | Archivo histórico, compliance |

**Total espacio estimado**:
- Daily: ~7 backups × 2 MB = 14 MB
- Weekly: ~4 backups × 2 MB = 8 MB
- Monthly: ~12 backups × 2 MB = 24 MB
- **Total**: ~46 MB

---

## ✅ Mejores Prácticas

1. **Antes de cambios importantes**:
   ```bash
   ./scripts/backup.sh daily
   ```

2. **Antes de actualizar dependencias**:
   ```bash
   ./scripts/backup.sh weekly
   ```

3. **Antes de desplegar a producción**:
   ```bash
   ./scripts/backup.sh monthly
   ```

4. **Verificar backup periódicamente**:
   ```bash
   # Listar backups disponibles
   ls -lh backups/daily/

   # Verificar integridad (Linux/Mac)
   tar -tzf backups/daily/rcv_backup_daily_20251022.tar.gz | head
   ```

5. **Almacenamiento externo**:
   - Considera copiar backups mensuales a Google Drive, Dropbox, etc.
   - Comando de ejemplo:
     ```bash
     cp backups/monthly/rcv_backup_monthly_*.tar.gz ~/Dropbox/RVC_Backups/
     ```

---

## 🛡️ Seguridad

- ⚠️ **NO** incluir archivos `.env` en backups (ya está excluido)
- ⚠️ **NO** subir backups a repositorios públicos
- ✅ Backups locales están en `.gitignore`
- ✅ Base de datos se respalda por separado
- ✅ Git status verificado antes de cada backup

---

## 🐛 Troubleshooting

### "Permission denied" (Linux/Mac)
```bash
chmod +x scripts/backup.sh
```

### "Execution Policy" error (Windows)
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Backup muy grande
- Verificar que `.venv/` y `__pycache__/` estén excluidos
- Tamaño normal del proyecto: ~2-5 MB comprimido

### No se eliminan backups antiguos
- Verificar permisos de escritura en carpeta `backups/`
- En Windows, ejecutar PowerShell como Administrador

---

## 📝 Próximos Scripts Planeados

Según el DEVELOPMENT_ROADMAP.md, futuros scripts incluirán:

- `scripts/setup_env.sh` - Configuración inicial del entorno
- `scripts/run_tests.sh` - Ejecutar suite de tests completa
- `scripts/deploy.sh` - Script de despliegue a Railway
- `scripts/db_maintenance.sh` - Limpieza y optimización de SQLite
- `scripts/api_usage_report.sh` - Reporte de uso de APIs (Phase 9)

---

**Última actualización**: Octubre 2025
