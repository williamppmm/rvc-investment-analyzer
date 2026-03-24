# Mobile — Implementación y Testing

Guía de responsividad móvil: qué se implementó, cómo probarlo y cómo mantenerlo.

---

## Tabla de Contenidos

1. [Qué se Implementó](#1-qué-se-implementó)
2. [Breakpoints y Media Queries](#2-breakpoints-y-media-queries)
3. [Testing Rápido (5 minutos)](#3-testing-rápido-5-minutos)
4. [Testing Completo por Página](#4-testing-completo-por-página)
5. [Verificaciones con JavaScript](#5-verificaciones-con-javascript)
6. [Problemas Comunes y Soluciones](#6-problemas-comunes-y-soluciones)
7. [Guía de Mantenimiento](#7-guía-de-mantenimiento)

---

## 1. Qué se Implementó

### Archivos Modificados

| Archivo | Cambios |
|---------|---------|
| `static/style.css` | Sistema de breakpoints, header/nav responsive, tipografía escalable, modales |
| `static/calculadora.css` | Tabs verticales, grids de formularios, tablas con scroll |
| `static/comparador.css` | Ranking cards, tabs verticales, inputs táctiles (44px+) |
| `static/top_opportunities.css` | Filtros en columna, stats responsive, soporte landscape |
| `templates/base.html` | Selector de moneda con clase CSS, eliminación de estilos inline |

### Características Clave

- **Touch targets:** Mínimo 44x44px en botones, links, inputs y selects (estándar WCAG 2.1)
- **Grids adaptativos:** 4 columnas → 2 → 1 según el viewport
- **Tablas:** Scroll horizontal con indicador "← Desliza para ver más →"
- **Tabs:** Horizontales en desktop, verticales en móvil
- **Score circles:** 120px (desktop) → 110px (tablet) → 90px (móvil)
- **Modales:** 90% ancho en tablets, 100% en móviles pequeños
- **Detección de touch:** `@media (hover: none) and (pointer: coarse)` para ajustar interacciones

### Tipografía Escalable

| Elemento | Desktop | Tablet | Móvil | Móvil pequeño |
|----------|---------|--------|-------|---------------|
| Hero Title | 2.1rem | 1.65rem | 1.5rem | 1.35rem |
| Body Text | 1rem | 0.95rem | 0.9rem | 0.85rem |
| Labels | 0.9rem | 0.85rem | 0.85rem | 0.8rem |

### Estándares Cumplidos

- ✅ WCAG 2.1 — touch targets 44x44px, contraste, tipografía ≥ 14px
- ✅ Apple iOS HIG — elementos táctiles de 44pt mínimo
- ✅ Google Material Design — touch targets 48dp, layouts flexibles

---

## 2. Breakpoints y Media Queries

```css
/* Detección de dispositivos táctiles */
@media (hover: none) and (pointer: coarse) { ... }

/* Tablets grandes */
@media (max-width: 1024px) { ... }

/* Tablets y móviles grandes */
@media (max-width: 768px) { ... }

/* Móviles estándar */
@media (max-width: 700px) { ... }

/* Móviles pequeños */
@media (max-width: 480px) { ... }

/* Landscape en móviles */
@media (max-width: 768px) and (orientation: landscape) { ... }
```

**Variables CSS disponibles:**
```css
--spacing-xs: 0.5rem  --spacing-sm: 0.75rem
--spacing-md: 1rem    --spacing-lg: 1.5rem
--spacing-xl: 2rem    --radius-sm: 6px
--radius-md: 8px      --radius-lg: 10px
```

---

## 3. Testing Rápido (5 minutos)

### Abrir Chrome DevTools

1. Abre la aplicación en Chrome
2. `F12` → `Ctrl+Shift+M` (toggle device mode)
3. Selecciona dispositivo o escribe el ancho manualmente

### Tamaños a Probar

```
📱 iPhone SE     → 375px  (móvil pequeño)
📱 iPhone 12     → 390px  (móvil estándar)
📲 iPad Mini     → 768px  (tablet)
💻 Desktop       → 1440px
```

### Checklist Express

**Móvil (375px):**
- [ ] Logo visible y correcto
- [ ] Navegación funciona (todos los links visibles)
- [ ] Inputs ocupan todo el ancho
- [ ] Botones con altura ≥ 44px
- [ ] Tablas con scroll horizontal
- [ ] Score circle del tamaño correcto
- [ ] Texto legible sin zoom
- [ ] Modal ocupa toda la pantalla

**Tablet (768px):**
- [ ] Logo de tamaño intermedio
- [ ] Grids en 2 columnas
- [ ] Formularios cómodos de usar

**Desktop (1440px):**
- [ ] Todo en su diseño original
- [ ] Sin elementos excesivamente anchos

---

## 4. Testing Completo por Página

### Inicio (index.html)

| Breakpoint | Verificar |
|------------|-----------|
| > 768px | Grid de scores en 4 columnas, score circle 120px |
| 768–480px | Grid en 2 columnas, score circle 110px, hero apilado |
| < 480px | Grid en 1 columna, score circle 90px, botones 44px+ |

### Comparador (comparador.html)

| Breakpoint | Verificar |
|------------|-----------|
| Desktop | 5 inputs en grid, tabs horizontales, tabla sin scroll |
| Tablet | Inputs en 1 columna, tabla con scroll si necesario |
| Móvil | Inputs todo el ancho, tabs verticales, tabla con "← Desliza →" |

### Calculadora (calculadora.html)

| Breakpoint | Verificar |
|------------|-----------|
| Desktop | Tabs horizontales, grids 3–4 columnas, tabla sin scroll |
| Tablet | Grids en 2 columnas |
| Móvil | Tabs verticales, todo en 1 columna, tabla con scroll |

### Top Opportunities (top_opportunities.html)

| Breakpoint | Verificar |
|------------|-----------|
| Desktop | Filtros en 3–4 columnas, stats horizontal, tabla completa |
| Tablet | Filtros en 2 columnas, tabla con scroll |
| Móvil | Filtros en 1 columna, stats apilados, tabla con scroll |

---

## 5. Verificaciones con JavaScript

### Detectar touch targets insuficientes (< 44px)

```javascript
document.querySelectorAll('button, a, input, select').forEach(el => {
  const rect = el.getBoundingClientRect();
  if (rect.width < 44 || rect.height < 44) {
    console.warn('Elemento muy pequeño:', el, `${rect.width}x${rect.height}`);
    el.style.outline = '2px solid red';
  }
});
```

### Detectar overflow horizontal no deseado

```javascript
const body = document.body;
const html = document.documentElement;
if (Math.max(body.scrollWidth, html.scrollWidth) > window.innerWidth) {
  console.warn('⚠️ Overflow horizontal detectado');
  document.querySelectorAll('*').forEach(el => {
    if (el.scrollWidth > window.innerWidth)
      console.log('Elemento con overflow:', el);
  });
}
```

### Detectar texto muy pequeño

```javascript
document.querySelectorAll('*').forEach(el => {
  const fontSize = parseFloat(window.getComputedStyle(el).fontSize);
  if (fontSize < 14 && el.innerText && el.innerText.trim().length > 0)
    console.warn('Texto pequeño:', el.innerText.substring(0, 30), `→ ${fontSize}px`);
});
```

---

## 6. Problemas Comunes y Soluciones

### Botones muy pequeños para tocar
```css
.btn { min-height: 44px; padding: 12px 20px; }
```

### Navegación rota en móvil
```css
.site-nav { flex-wrap: wrap; }
```

### Tabla sale de la pantalla
```css
.table-container { overflow-x: auto; -webkit-overflow-scrolling: touch; }
```

### Modal muy grande en móvil
```css
@media (max-width: 480px) {
  .modal__container { width: 100%; max-height: 100vh; }
}
```

### Inputs hacen auto-zoom en iOS
```css
input, select, textarea { font-size: 16px; }  /* Evita zoom automático en iOS */
```

---

## 7. Guía de Mantenimiento

### Al agregar nuevas páginas

1. Usar las variables CSS existentes (`--spacing-*`, `--radius-*`)
2. Aplicar breakpoints consistentes con los definidos en sección 2
3. Probar en al menos 3 tamaños: 375px, 768px, 1440px
4. Asegurar touch targets de 44px mínimo

### Al agregar nuevos componentes

1. Diseñar mobile-first (desde 375px hacia arriba)
2. Usar `flexbox` / `grid` con `auto-fit` / `auto-fill`
3. Aplicar tipografía en `rem`/`em` (no valores fijos en px)

### Objetivos Lighthouse (Mobile)

```
Performance:    > 90
Accessibility:  > 90
Best Practices: > 90
SEO:            > 90
```

Para correr Lighthouse: `F12` → pestaña "Lighthouse" → seleccionar "Mobile" → "Generate report".
