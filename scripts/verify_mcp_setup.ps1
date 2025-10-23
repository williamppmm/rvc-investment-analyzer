# ============================================
# SCRIPT DE VERIFICACION MCP - RVC Analyzer
# ============================================
# Verifica que todos los requisitos para MCP esten instalados

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "Verificacion de Setup MCP - RVC Analyzer" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$allGood = $true

# ============================================
# 1. Verificar Node.js
# ============================================
Write-Host "[1/5] Verificando Node.js..." -ForegroundColor Yellow

try {
    $nodeVersion = node --version 2>$null
    if ($nodeVersion) {
        Write-Host "  OK Node.js instalado: $nodeVersion" -ForegroundColor Green

        # Verificar version minima (v18+)
        $versionNumber = [int]($nodeVersion -replace 'v(\d+)\..*', '$1')
        if ($versionNumber -lt 18) {
            Write-Host "  ADVERTENCIA: Se recomienda Node.js v18 o superior" -ForegroundColor Yellow
            Write-Host "  Tu version: $nodeVersion (puede funcionar pero no esta garantizado)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  ERROR Node.js NO encontrado" -ForegroundColor Red
        Write-Host "  Descarga desde: https://nodejs.org/" -ForegroundColor Yellow
        $allGood = $false
    }
} catch {
    Write-Host "  ERROR Node.js NO instalado" -ForegroundColor Red
    Write-Host "  Descarga desde: https://nodejs.org/" -ForegroundColor Yellow
    $allGood = $false
}

Write-Host ""

# ============================================
# 2. Verificar npm
# ============================================
Write-Host "[2/5] Verificando npm..." -ForegroundColor Yellow

try {
    $npmVersion = npm --version 2>$null
    if ($npmVersion) {
        Write-Host "  OK npm instalado: v$npmVersion" -ForegroundColor Green
    } else {
        Write-Host "  ERROR npm NO encontrado" -ForegroundColor Red
        Write-Host "  npm viene con Node.js, reinstala Node.js" -ForegroundColor Yellow
        $allGood = $false
    }
} catch {
    Write-Host "  ERROR npm NO instalado" -ForegroundColor Red
    $allGood = $false
}

Write-Host ""

# ============================================
# 3. Verificar servidor MCP de SQLite
# ============================================
Write-Host "[3/5] Verificando servidor MCP SQLite..." -ForegroundColor Yellow

try {
    # Intentar ejecutar el servidor para ver si esta disponible
    $mcpCheck = npx -y @modelcontextprotocol/server-sqlite --version 2>&1

    if ($LASTEXITCODE -eq 0) {
        Write-Host "  OK Servidor MCP SQLite disponible" -ForegroundColor Green
        Write-Host "  Version: $mcpCheck" -ForegroundColor Gray
    } else {
        Write-Host "  AVISO Servidor MCP SQLite no instalado globalmente" -ForegroundColor Yellow
        Write-Host "  (Esto esta bien si usas npx, se descargara automaticamente)" -ForegroundColor Gray
    }
} catch {
    Write-Host "  AVISO No se pudo verificar el servidor MCP" -ForegroundColor Yellow
    Write-Host "  (Esto esta bien si usas npx)" -ForegroundColor Gray
}

Write-Host ""

# ============================================
# 4. Verificar base de datos cache
# ============================================
Write-Host "[4/5] Verificando base de datos cache..." -ForegroundColor Yellow

$dbPath = Join-Path $PSScriptRoot "..\data\cache.db"

if (Test-Path $dbPath) {
    $dbSize = (Get-Item $dbPath).Length
    $dbSizeKB = [math]::Round($dbSize / 1KB, 2)
    Write-Host "  OK Base de datos encontrada: $dbPath" -ForegroundColor Green
    Write-Host "  Tamano: $dbSizeKB KB" -ForegroundColor Gray

    # Mostrar ruta absoluta para configuracion
    $absolutePath = Resolve-Path $dbPath
    $configPath = $absolutePath.Path -replace '\\', '/'
    Write-Host ""
    Write-Host "  Ruta para configuracion MCP:" -ForegroundColor Cyan
    Write-Host "  $configPath" -ForegroundColor White
} else {
    Write-Host "  AVISO Base de datos NO encontrada" -ForegroundColor Yellow
    Write-Host "  Ruta esperada: $dbPath" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  Esto es normal si nunca has ejecutado la app." -ForegroundColor Gray
    Write-Host "  Para crear la base de datos:" -ForegroundColor Yellow
    Write-Host "    1. cd C:\rcv_proyecto" -ForegroundColor White
    Write-Host "    2. python app.py" -ForegroundColor White
    Write-Host "    3. Abre http://localhost:5000 y analiza un ticker" -ForegroundColor White
}

Write-Host ""

# ============================================
# 5. Verificar configuracion Claude Code
# ============================================
Write-Host "[5/5] Verificando configuracion Claude Code..." -ForegroundColor Yellow

$settingsPath = "$env:APPDATA\Code\User\globalStorage\anthropic.claude-code\settings.json"

if (Test-Path $settingsPath) {
    Write-Host "  OK Archivo de configuracion encontrado" -ForegroundColor Green
    Write-Host "  Ruta: $settingsPath" -ForegroundColor Gray

    # Leer contenido
    try {
        $settingsContent = Get-Content $settingsPath -Raw | ConvertFrom-Json

        if ($settingsContent.mcpServers) {
            if ($settingsContent.mcpServers.'rvc-cache') {
                Write-Host "  OK Servidor MCP 'rvc-cache' configurado" -ForegroundColor Green

                $serverConfig = $settingsContent.mcpServers.'rvc-cache'
                Write-Host ""
                Write-Host "  Configuracion actual:" -ForegroundColor Cyan
                Write-Host "  - Command: $($serverConfig.command)" -ForegroundColor Gray
                Write-Host "  - Database: $($serverConfig.args[-1])" -ForegroundColor Gray
                Write-Host "  - Disabled: $($serverConfig.disabled)" -ForegroundColor Gray

                # Verificar que la ruta en la config existe
                $configDbPath = $serverConfig.args[-1]
                if (Test-Path $configDbPath) {
                    Write-Host "  OK Ruta de DB en config es valida" -ForegroundColor Green
                } else {
                    Write-Host "  ERROR ADVERTENCIA: Ruta de DB en config NO existe" -ForegroundColor Red
                    Write-Host "  Configurado: $configDbPath" -ForegroundColor Yellow
                    $allGood = $false
                }
            } else {
                Write-Host "  AVISO Servidor 'rvc-cache' NO configurado" -ForegroundColor Yellow
                Write-Host "  Necesitas agregar la configuracion MCP" -ForegroundColor Yellow
            }
        } else {
            Write-Host "  AVISO No hay servidores MCP configurados" -ForegroundColor Yellow
            Write-Host "  Necesitas agregar la seccion 'mcpServers'" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  ERROR No se pudo leer el archivo de configuracion" -ForegroundColor Red
        Write-Host "  El archivo puede tener formato JSON invalido" -ForegroundColor Yellow
    }
} else {
    Write-Host "  AVISO Archivo de configuracion NO encontrado" -ForegroundColor Yellow
    Write-Host "  Ruta esperada: $settingsPath" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  Para crear el archivo:" -ForegroundColor Yellow
    Write-Host "    1. Abre Claude Code" -ForegroundColor White
    Write-Host "    2. Ctrl + Shift + P" -ForegroundColor White
    Write-Host "    3. 'Preferences: Open User Settings (JSON)'" -ForegroundColor White
}

Write-Host ""

# ============================================
# RESUMEN
# ============================================
Write-Host "============================================" -ForegroundColor Cyan
if ($allGood) {
    Write-Host "OK TODO LISTO - Configuracion correcta" -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Proximos pasos:" -ForegroundColor Yellow
    Write-Host "1. Asegurate de haber configurado Claude Code settings.json" -ForegroundColor White
    Write-Host "2. Reinicia Claude Code (Ctrl+Shift+P -> 'Developer: Reload Window')" -ForegroundColor White
    Write-Host "3. Prueba preguntando: 'Cuantos tickers tengo en cache?'" -ForegroundColor White
} else {
    Write-Host "AVISO FALTAN REQUISITOS" -ForegroundColor Yellow
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Revisa los errores marcados con ERROR arriba" -ForegroundColor Yellow
    Write-Host "Consulta MCP_SETUP_GUIDE.md para mas ayuda" -ForegroundColor White
}

Write-Host ""
