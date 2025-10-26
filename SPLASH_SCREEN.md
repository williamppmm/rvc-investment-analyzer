# 🎬 Sistema de Splash Screen con Logo RVC

## 📋 Descripción

Sistema inteligente de transición con video del logo RVC que se muestra al entrar al sitio, optimizado para no afectar la experiencia del usuario.

## ✨ Características

### 🎯 Comportamiento Inteligente
- ✅ Solo se muestra en primera visita
- ✅ Se vuelve a mostrar cada 24 horas
- ✅ Permite skip con clic o tecla ESC
- ✅ Auto-oculta al terminar el video (2-3 segundos)
- ✅ Timeout de seguridad si el video no carga

### 🎨 Diseño
- Fondo con degradado matching al tema (#1a1a2e → #16213e)
- Animación de entrada suave (fade + scale)
- Efecto de brillo sutil en el video
- Texto "skip" con pulsación suave
- Totalmente responsive

### ⚡ Performance
- Video optimizado (< 500KB recomendado)
- Fallback a WebM si está disponible
- Loading spinner mientras carga
- No bloquea la carga de la página principal
- LocalStorage para tracking (no cookies)

## 📁 Estructura de Archivos

```
static/
├── splash.css           # Estilos del splash screen
├── splash.js            # Lógica del splash screen
└── video/
    ├── README.md        # Especificaciones del video
    ├── .gitkeep         # Placeholder para Git
    ├── rvc-logo-intro.mp4   # Video principal (REQUERIDO)
    └── rvc-logo-intro.webm  # Video fallback (OPCIONAL)
```

## 🎥 Video Requerido

### Nombre del archivo:
**`rvc-logo-intro.mp4`** (colocar en `static/video/`)

### Especificaciones:
```
Duración:    2-3 segundos máximo
Resolución:  1280x720 (HD) o 1920x1080 (Full HD)
Formato:     MP4 (H.264 codec)
Tamaño:      < 500KB (optimizado)
Audio:       No requerido (se reproduce muted)
FPS:         24-30
Bitrate:     ~1.5 Mbps video
```

### Optimización con FFmpeg:
```bash
# Desde video original a optimizado
ffmpeg -i original.mp4 \
  -vcodec libx264 \
  -crf 28 \
  -preset fast \
  -vf "scale=1280:720" \
  -an \
  -movflags +faststart \
  static/video/rvc-logo-intro.mp4

# Crear versión WebM (fallback)
ffmpeg -i original.mp4 \
  -c:v libvpx-vp9 \
  -crf 30 \
  -b:v 0 \
  -vf "scale=1280:720" \
  -an \
  static/video/rvc-logo-intro.webm
```

### Conversión de otros formatos:
```bash
# Desde MOV
ffmpeg -i logo.mov -vcodec libx264 -crf 23 -preset medium -an static/video/rvc-logo-intro.mp4

# Desde AVI
ffmpeg -i logo.avi -vcodec libx264 -crf 23 -preset medium -an static/video/rvc-logo-intro.mp4

# Desde GIF animado
ffmpeg -i logo.gif -movflags faststart -pix_fmt yuv420p -vf "scale=1280:720" static/video/rvc-logo-intro.mp4
```

## 🎮 Uso

### Configuración por defecto:
El splash se activa automáticamente. No requiere configuración adicional.

### Control desde consola (debugging):
```javascript
// Resetear y mostrar de nuevo
RVCSplash.reset();
location.reload();

// Solo resetear (para próxima visita)
RVCSplash.reset();

// Mostrar manualmente
RVCSplash.show();
```

### Ajustes en el código:

**Cambiar cooldown (24 horas por defecto):**
```javascript
// En splash.js, línea ~10
this.COOLDOWN_HOURS = 24; // Cambiar a 12, 48, etc.
```

**Desactivar en desarrollo:**
```javascript
// En splash.js, método shouldShow(), línea ~24
shouldShow() {
    return false; // Desactivar completamente
    // ... resto del código
}
```

**Mostrar siempre (testing):**
```javascript
// En splash.js, método shouldShow(), línea ~24
shouldShow() {
    return true; // Mostrar en cada carga
}
```

## 🎨 Personalización

### Cambiar colores del fondo:
```css
/* En splash.css, línea ~8 */
#rvc-splash {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    /* Cambiar por tus colores */
}
```

### Cambiar duración del video:
```javascript
/* En splash.js, línea ~11 */
this.SPLASH_DURATION = 2500; // Milisegundos (2.5s)
```

### Ocultar texto de skip:
```css
/* En splash.css, agregar: */
.splash-skip-text {
    display: none;
}
```

## 🐛 Troubleshooting

### El video no se reproduce:
1. Verificar que el archivo existe en `static/video/rvc-logo-intro.mp4`
2. Verificar permisos del archivo
3. Comprobar que el formato es compatible (MP4 H.264)
4. Revisar la consola del navegador (F12) para errores

### El splash no aparece:
1. Verificar en consola: "RVC Splash: Cooldown activo"
   - Solución: Ejecutar `RVCSplash.reset()` en consola
2. Verificar que `splash.js` está cargado
3. Verificar que `splash.css` está cargado

### El video es muy pesado:
1. Re-optimizar con FFmpeg (ver comandos arriba)
2. Reducir resolución a 720p
3. Aumentar CRF (más compresión): `-crf 30` o `-crf 32`
4. Usar formato WebM (mejor compresión)

## 📊 Performance

### Impacto en PageSpeed:
- **LCP (Largest Contentful Paint):** No afecta (overlay)
- **FID (First Input Delay):** Mínimo (< 50ms)
- **CLS (Cumulative Layout Shift):** 0 (posición fixed)
- **Tamaño total:** ~300-500KB (solo primera visita)

### Cache:
El video se cachea automáticamente por el navegador después de la primera carga.

## 🚀 Integración

### Archivos modificados:
- ✅ `templates/base.html` - Enlaces a CSS y JS
- ✅ `static/splash.css` - Estilos
- ✅ `static/splash.js` - Lógica
- ✅ `static/video/` - Carpeta para el video

### No requiere cambios en:
- Backend (Flask)
- Base de datos
- Otros templates
- Configuración del servidor

## 📝 Notas

- El splash se muestra **antes** del modal de límite de uso
- Compatible con todos los navegadores modernos (Chrome, Firefox, Safari, Edge)
- Accesible: permite skip inmediato
- Mobile-friendly: responsive design
- No requiere JavaScript para fallar gracefully (CSS solo)

## 🎯 Mejores Prácticas

1. **Video corto:** Máximo 3 segundos
2. **Optimizado:** < 500KB de tamaño
3. **Sin audio:** O muy bajo volumen
4. **Fondo sólido:** Matching al tema del sitio
5. **Animación suave:** Sin transiciones bruscas
6. **Formato correcto:** MP4 H.264 + WebM fallback

## 🔄 Actualización del Video

Para cambiar el video:
1. Optimizar nuevo video con FFmpeg
2. Reemplazar `static/video/rvc-logo-intro.mp4`
3. Limpiar cache: `Ctrl + Shift + R` en navegador
4. Opcional: `RVCSplash.reset()` para testing inmediato
