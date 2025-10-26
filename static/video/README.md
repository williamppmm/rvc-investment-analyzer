# Video Assets

## Logo de Transición

### Archivo requerido:
**Nombre:** `rvc-logo-intro.mp4`

### Especificaciones técnicas:
- **Duración:** 2-3 segundos máximo
- **Resolución:** 1920x1080 (Full HD) o 1280x720 (HD)
- **Formato:** MP4 (H.264 codec)
- **Tamaño:** < 500KB (optimizado para web)
- **Audio:** Opcional (preferiblemente sin audio o muy bajo)

### Recomendaciones de optimización:
```bash
# Usando ffmpeg para optimizar:
ffmpeg -i original.mp4 -vcodec libx264 -crf 28 -preset fast -vf "scale=1280:720" -an rvc-logo-intro.mp4
```

### Conversión de formatos:
Si tienes el video en otro formato (MOV, AVI, etc.):
```bash
ffmpeg -i input.mov -vcodec libx264 -crf 23 -preset medium -acodec aac -b:a 128k rvc-logo-intro.mp4
```

### Notas:
- El video debe tener fondo transparente o color sólido (#1a1a2e recomendado)
- La animación debe ser suave y profesional
- Considerar versión WebM como fallback: `rvc-logo-intro.webm`
