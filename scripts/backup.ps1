# ============================================
# BACKUP SCRIPT - RVC Analyzer (PowerShell)
# ============================================
# Script para crear backups automáticos del proyecto en Windows
# Uso: .\scripts\backup.ps1 [-Type daily|weekly|monthly]

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("daily", "weekly", "monthly")]
    [string]$Type = "daily"
)

# Configuración
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$BackupRoot = Join-Path $ProjectRoot "backups"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$DateOnly = Get-Date -Format "yyyyMMdd"

# Configuración según tipo de backup
$RetentionDays = switch ($Type) {
    "daily"   { 7 }
    "weekly"  { 30 }
    "monthly" { 365 }
}

$BackupDir = Join-Path $BackupRoot $Type

# Crear directorios si no existen
if (-not (Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
}

# Nombre del archivo de backup
$BackupFile = Join-Path $BackupDir "rcv_backup_${Type}_${DateOnly}.zip"

Write-Host "============================================" -ForegroundColor Yellow
Write-Host "RVC Analyzer - Backup $Type" -ForegroundColor Yellow
Write-Host "============================================" -ForegroundColor Yellow
Write-Host "Timestamp: $Timestamp"
Write-Host "Backup file: $BackupFile"
Write-Host ""

# ============================================
# VERIFICAR GIT STATUS
# ============================================
Write-Host "[1/5] Verificando estado de Git..." -ForegroundColor Yellow

Set-Location $ProjectRoot

$GitStatus = git status --porcelain 2>$null
if ($GitStatus) {
    Write-Host "⚠️  ADVERTENCIA: Hay cambios sin commitear en Git" -ForegroundColor Red
    Write-Host "Cambios detectados:" -ForegroundColor Yellow
    git status --short
    Write-Host ""
    $Response = Read-Host "¿Continuar con el backup de todas formas? (y/n)"
    if ($Response -notmatch "^[Yy]$") {
        Write-Host "Backup cancelado" -ForegroundColor Red
        exit 1
    }
}

Write-Host "✓ Git status verificado" -ForegroundColor Green
Write-Host ""

# ============================================
# CREAR BACKUP
# ============================================
Write-Host "[2/5] Creando backup..." -ForegroundColor Yellow

# Patrones a excluir
$ExcludePatterns = @(
    "*.pyc",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    ".git",
    "*.log",
    "backups",
    "data\cache.db",
    "data\temp",
    ".DS_Store",
    "Thumbs.db",
    ".env"
)

# Crear lista de archivos temporales excluyendo patrones
$TempFileList = Join-Path $env:TEMP "rcv_backup_files.txt"
Get-ChildItem -Path $ProjectRoot -Recurse -File | Where-Object {
    $file = $_
    $shouldExclude = $false
    foreach ($pattern in $ExcludePatterns) {
        if ($file.FullName -like "*$pattern*") {
            $shouldExclude = $true
            break
        }
    }
    -not $shouldExclude
} | ForEach-Object { $_.FullName } | Out-File $TempFileList

# Crear ZIP usando System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

try {
    # Si el archivo ya existe, eliminarlo
    if (Test-Path $BackupFile) {
        Remove-Item $BackupFile -Force
    }

    # Crear nuevo archivo ZIP
    $zip = [System.IO.Compression.ZipFile]::Open($BackupFile, [System.IO.Compression.ZipArchiveMode]::Create)

    Get-Content $TempFileList | ForEach-Object {
        $file = $_
        if (Test-Path $file) {
            $relativePath = $file.Substring($ProjectRoot.Length + 1)
            $entry = $zip.CreateEntry($relativePath)
            $entryStream = $entry.Open()
            $fileStream = [System.IO.File]::OpenRead($file)
            $fileStream.CopyTo($entryStream)
            $fileStream.Close()
            $entryStream.Close()
        }
    }

    $zip.Dispose()

    $BackupSize = (Get-Item $BackupFile).Length / 1MB
    Write-Host "✓ Backup creado exitosamente ($([math]::Round($BackupSize, 2)) MB)" -ForegroundColor Green
}
catch {
    Write-Host "✗ Error al crear backup: $_" -ForegroundColor Red
    exit 1
}
finally {
    Remove-Item $TempFileList -Force -ErrorAction SilentlyContinue
}

Write-Host ""

# ============================================
# CREAR BACKUP DE BASE DE DATOS
# ============================================
Write-Host "[3/5] Backup de base de datos..." -ForegroundColor Yellow

$DbFile = Join-Path $ProjectRoot "data\cache.db"
$DbBackup = Join-Path $BackupDir "cache_db_${DateOnly}.db"

if (Test-Path $DbFile) {
    Copy-Item $DbFile $DbBackup -Force
    $DbSize = (Get-Item $DbBackup).Length / 1KB
    Write-Host "✓ Database backup creado ($([math]::Round($DbSize, 2)) KB)" -ForegroundColor Green
}
else {
    Write-Host "⚠️  No se encontró base de datos en data\cache.db" -ForegroundColor Yellow
}

Write-Host ""

# ============================================
# LIMPIAR BACKUPS ANTIGUOS
# ============================================
Write-Host "[4/5] Limpiando backups antiguos..." -ForegroundColor Yellow

$CutoffDate = (Get-Date).AddDays(-$RetentionDays)
$DeletedCount = 0

# Limpiar archivos .zip antiguos
Get-ChildItem -Path $BackupDir -Filter "rcv_backup_${Type}_*.zip" | Where-Object {
    $_.LastWriteTime -lt $CutoffDate
} | ForEach-Object {
    Write-Host "  Eliminando: $($_.Name)"
    Remove-Item $_.FullName -Force
    $DeletedCount++
}

# Limpiar backups de DB antiguos
Get-ChildItem -Path $BackupDir -Filter "cache_db_*.db" | Where-Object {
    $_.LastWriteTime -lt $CutoffDate
} | ForEach-Object {
    Write-Host "  Eliminando: $($_.Name)"
    Remove-Item $_.FullName -Force
}

if ($DeletedCount -eq 0) {
    Write-Host "✓ No hay backups antiguos para eliminar" -ForegroundColor Green
}
else {
    Write-Host "✓ $DeletedCount backups antiguos eliminados" -ForegroundColor Green
}

Write-Host ""

# ============================================
# RESUMEN
# ============================================
Write-Host "[5/5] Resumen del backup" -ForegroundColor Yellow

$TotalBackups = (Get-ChildItem -Path $BackupDir -Filter "rcv_backup_${Type}_*.zip").Count
$TotalSize = (Get-ChildItem -Path $BackupDir -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB

Write-Host "Tipo: $Type"
Write-Host "Total backups $Type: $TotalBackups"
Write-Host "Espacio usado: $([math]::Round($TotalSize, 2)) MB"
Write-Host "Retención: $RetentionDays días"
Write-Host ""

Write-Host "============================================" -ForegroundColor Green
Write-Host "✓ Backup completado exitosamente" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host "Archivo: $BackupFile"
Write-Host "Timestamp: $Timestamp"
Write-Host ""

# ============================================
# NOTAS DE USO
# ============================================
# Para restaurar un backup:
# Expand-Archive -Path backups\daily\rcv_backup_daily_YYYYMMDD.zip -DestinationPath C:\ruta\destino
#
# Para automatizar (Task Scheduler):
# Crear tarea programada que ejecute:
# powershell.exe -ExecutionPolicy Bypass -File "C:\rcv_proyecto\scripts\backup.ps1" -Type daily
