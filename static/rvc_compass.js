/**
 * RVC Compass - Visualización interactiva de análisis RVC
 * Gráfico de dispersión 2D: Calidad vs Valoración
 * - Punto: posición (calidad, valoración)
 * - Tamaño interno: Salud Financiera
 * - Halo externo: Crecimiento
 * - Zonas: Sweet Spot, Premium, Value, Risky, Overvalued, Avoid
 *
 * @version 2.0 - Corregido bug de puntos extraños
 */

/**
 * Definición de zonas de inversión en el espacio RVC
 * Usando coordenadas rectangulares (x0, x1, y0, y1) para eliminar espacios blancos
 *
 * Distribución del mapa (Grid 3x3, 0-100):
 * - Eje X (Valoración): 0=cara, 100=barata
 * - Eje Y (Calidad): 0=baja, 100=alta
 */
const RVC_ZONES = [
    // Fila superior (Calidad 70-100)
    {
        name: 'SWEET SPOT',
        description: 'Ideal: Alta calidad a precio atractivo',
        x0: 70, x1: 100, y0: 70, y1: 100,
        fill: 'rgba(22, 163, 74, 0.12)',
        textColor: '#16a34a'
    },
    {
        name: 'QUALITY',
        description: 'Buena calidad a valoración razonable',
        x0: 40, x1: 70, y0: 70, y1: 100,
        fill: 'rgba(16, 185, 129, 0.08)',
        textColor: '#10b981'
    },
    {
        name: 'PREMIUM',
        description: 'Excelente negocio pero valoración elevada',
        x0: 0, x1: 40, y0: 70, y1: 100,
        fill: 'rgba(59, 130, 246, 0.10)',
        textColor: '#3b82f6'
    },

    // Fila media (Calidad 40-70)
    {
        name: 'VALUE',
        description: 'Calidad aceptable a buen precio',
        x0: 70, x1: 100, y0: 40, y1: 70,
        fill: 'rgba(234, 179, 8, 0.08)',
        textColor: '#d97706'
    },
    {
        name: 'FAIR',
        description: 'Calidad y valoración equilibradas',
        x0: 40, x1: 70, y0: 40, y1: 70,
        fill: 'rgba(156, 163, 175, 0.06)',
        textColor: '#6b7280'
    },
    {
        name: 'CAUTION',
        description: 'Calidad media pero precio elevado',
        x0: 0, x1: 40, y0: 40, y1: 70,
        fill: 'rgba(245, 158, 11, 0.08)',
        textColor: '#f59e0b'
    },

    // Fila inferior (Calidad 0-40)
    {
        name: 'RISKY',
        description: 'Baja calidad, incluso si es barata',
        x0: 70, x1: 100, y0: 0, y1: 40,
        fill: 'rgba(249, 115, 22, 0.08)',
        textColor: '#f97316'
    },
    {
        name: 'SPECULATIVE',
        description: 'Calidad cuestionable, alto riesgo',
        x0: 40, x1: 70, y0: 0, y1: 40,
        fill: 'rgba(220, 38, 38, 0.08)',
        textColor: '#dc2626'
    },
    {
        name: 'OVERVALUED',
        description: 'Baja calidad a precio elevado - evitar',
        x0: 0, x1: 40, y0: 0, y1: 40,
        fill: 'rgba(239, 68, 68, 0.10)',
        textColor: '#ef4444'
    }
];

/**
 * Calcula el centro de una zona rectangular para colocar etiquetas
 */
function getZoneCenter(zone) {
    return {
        x: (zone.x0 + zone.x1) / 2,
        y: (zone.y0 + zone.y1) / 2
    };
}

/**
 * Determina el color del punto según el score RVC
 */
function getPointColor(rvcScore) {
    if (rvcScore >= 75) return '#16a34a';  // Verde - Excelente
    if (rvcScore >= 60) return '#eab308';  // Amarillo - Bueno
    if (rvcScore >= 45) return '#f97316';  // Naranja - Moderado
    return '#ef4444';  // Rojo - Bajo
}

/**
 * Formatea números para display
 */
function formatNumber(num, decimals = 2) {
    if (num === null || num === undefined || num === 'N/A') return 'N/A';
    if (typeof num === 'number') {
        return num.toLocaleString('en-US', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        });
    }
    return num;
}

/**
 * Formatea el nombre de la fuente de datos
 */
function formatSourceName(source) {
    if (!source) return 'N/A';
    const sourceMap = {
        'alpha_vantage': 'Alpha Vantage',
        'twelve_data': 'Twelve Data',
        'fmp': 'FMP',
        'yfinance': 'Yahoo Finance',
        'fallback_example': 'Ejemplo',
        'manual': 'Manual'
    };
    return sourceMap[source] || source;
}

/**
 * Formatea capitalización de mercado
 */
function formatMarketCap(marketCap) {
    if (!marketCap || marketCap === 'N/A') return 'N/A';

    const num = parseFloat(marketCap);
    if (isNaN(num)) return marketCap;

    if (num >= 1e12) return `$${(num / 1e12).toFixed(2)}T`;
    if (num >= 1e9) return `$${(num / 1e9).toFixed(2)}B`;
    if (num >= 1e6) return `$${(num / 1e6).toFixed(2)}M`;
    return `$${num.toLocaleString()}`;
}

/**
 * Crea el tooltip HTML con información detallada
 */
function createTooltipHTML(data) {
    const m = data.metrics;
    const s = data.scores;

    return `<b>${data.company} (${data.ticker})</b><br>` +
           `<br><b>Scores RVC:</b><br>` +
           `Quality: ${formatNumber(s.quality, 1)} · Valuation: ${formatNumber(s.valuation, 1)}<br>` +
           `Health: ${formatNumber(s.health, 1)} · Growth: ${formatNumber(s.growth, 1)}<br>` +
           `<b>Score Total: ${formatNumber(data.rvc_score, 1)}/100</b><br>` +
           `<br><b>Precio:</b> $${formatNumber(m.price, 2)} · <b>MC:</b> ${formatMarketCap(m.market_cap)}<br>` +
           `<b>P/E:</b> ${formatNumber(m.pe, 2)} · <b>PEG:</b> ${formatNumber(m.peg, 2)} · <b>P/B:</b> ${formatNumber(m.pb, 2)}<br>` +
           `<b>ROE:</b> ${formatNumber(m.roe, 1)}% · <b>ROIC:</b> ${formatNumber(m.roic, 1)}%<br>` +
           `<b>Márgenes:</b> Op ${formatNumber(m.op_margin, 1)}% · Net ${formatNumber(m.net_margin, 1)}%<br>` +
           `<b>Deuda:</b> D/E ${formatNumber(m.de, 2)} · Current ${formatNumber(m.current, 2)} · Quick ${formatNumber(m.quick, 2)}<br>` +
           `<b>Crecimiento:</b> Ventas ${formatNumber(m.rev_growth, 1)}% · Utilidades ${formatNumber(m.earn_growth, 1)}%<br>` +
           `<br><i>${data.label}</i>`;
}

/**
 * Renderiza el gráfico RVC Compass usando Plotly.js
 *
 * @param {string} containerId - ID del elemento contenedor
 * @param {object} analysisData - Datos del análisis RVC
 */
function renderRVCCompass(containerId, analysisData) {
    // Validar que tenemos los datos necesarios
    if (!analysisData || !analysisData.rvc_score || !analysisData.rvc_score.breakdown) {
        console.error('Datos de análisis incompletos para RVC Compass');
        return;
    }

    const breakdown = analysisData.rvc_score.breakdown;
    const metrics = analysisData.metrics;

    // Extraer scores (manejar formato legacy y nuevo)
    const quality = breakdown.calidad?.score ?? breakdown.calidad ?? 0;
    const valuation = breakdown.valoracion?.score ?? breakdown.valoracion ?? 0;
    const health = breakdown.salud?.score ?? breakdown.salud ?? 0;
    const growth = breakdown.crecimiento?.score ?? breakdown.crecimiento ?? 0;
    const rvcScore = analysisData.rvc_score.total_score ?? analysisData.investment_scores?.investment_score ?? 0;

    // Preparar datos para el tooltip
    const chartData = {
        ticker: analysisData.ticker,
        company: analysisData.company_name,
        rvc_score: rvcScore,
        label: analysisData.rvc_score.classification,
        scores: { quality, valuation, health, growth },
        metrics: {
            price: metrics.current_price,
            market_cap: metrics.market_cap,
            pe: metrics.pe_ratio,
            peg: metrics.peg_ratio,
            pb: metrics.price_to_book,
            roe: metrics.roe,
            roic: metrics.roic,
            op_margin: metrics.operating_margin,
            net_margin: metrics.net_margin,
            de: metrics.debt_to_equity,
            current: metrics.current_ratio,
            quick: metrics.quick_ratio,
            rev_growth: metrics.revenue_growth_5y || metrics.revenue_growth,
            earn_growth: metrics.earnings_growth_this_y || metrics.earnings_growth
        }
    };

    // Epsilon para solapar ligeramente y eliminar líneas finas (anti-aliasing)
    const EPS = 0.3;

    // Crear shapes rectangulares robustos (sin espacios blancos)
    const shapes = RVC_ZONES.map(zone => ({
        type: 'rect',
        xref: 'x',
        yref: 'y',
        x0: zone.x0 - EPS,
        x1: zone.x1 + EPS,
        y0: zone.y0 - EPS,
        y1: zone.y1 + EPS,
        fillcolor: zone.fill,
        line: { width: 0 },
        layer: 'below'
    }));

    // Crear annotations para las etiquetas de zona
    // Incluir descripción debajo del nombre para contexto visual
    const annotations = RVC_ZONES.map(zone => {
        const center = getZoneCenter(zone);
        return {
            x: center.x,
            y: center.y,
            text: `<b>${zone.name}</b><br><span style="font-size:8px;">${zone.description}</span>`,
            showarrow: false,
            font: {
                size: 10,
                color: zone.textColor,
                family: 'Inter, system-ui, sans-serif',
                weight: 600
            },
            opacity: 0.65,
            align: 'center'
        };
    });

    // NO crear trazas invisibles - causan puntos extraños fuera del gráfico
    // Los tooltips de zonas se manejan con las annotations directamente
    const zoneTraces = [];

    // Calcular tamaños proporcionales y limitados
    // Salud: 12-28 (más conservador)
    const healthSize = Math.max(12, Math.min(28, (health / 100) * 28));
    // Crecimiento: 20-40 (halo más grande pero controlado)
    const growthSize = Math.max(20, Math.min(40, (growth / 100) * 40));

    // Mapear confianza al estilo del borde del halo
    const confidenceLevel = analysisData.rvc_score?.confidence_level || 'Media';
    const dataCompleteness = analysisData.metrics?.data_completeness || 0;

    // Calcular confidence score numérico (0-1)
    let confidenceScore = 0.8; // Default medio
    if (confidenceLevel === 'Alta' || confidenceLevel === 'High') {
        confidenceScore = 0.95;
    } else if (confidenceLevel === 'Media' || confidenceLevel === 'Medium') {
        confidenceScore = 0.80;
    } else if (confidenceLevel === 'Baja' || confidenceLevel === 'Low') {
        confidenceScore = 0.60;
    }

    // Ajustar por completitud de datos
    confidenceScore = confidenceScore * (dataCompleteness / 100);

    // Mapear confianza a estilo de línea
    const haloLine = confidenceScore >= 0.90
        ? { width: 3, dash: 'solid', color: 'rgba(148, 163, 184, 0.65)' }
        : confidenceScore >= 0.75
        ? { width: 3, dash: 'dot', color: 'rgba(148, 163, 184, 0.55)' }
        : confidenceScore >= 0.60
        ? { width: 2, dash: 'dash', color: 'rgba(148, 163, 184, 0.45)' }
        : { width: 2, dash: 'dashdot', color: 'rgba(148, 163, 184, 0.35)' };

    // Traza 1: Halo externo (Growth) - Anillo con estilo según confianza
    const haloTrace = {
        type: 'scatter',
        mode: 'markers',
        x: [valuation],
        y: [quality],
        marker: {
            size: growthSize,
            color: 'rgba(0,0,0,0)',
            line: haloLine
        },
        hoverinfo: 'skip',
        showlegend: false,
        name: 'Growth Halo'
    };

    // Ajustar opacidad del punto según completitud de datos
    const pointOpacity = dataCompleteness >= 90 ? 0.98
                       : dataCompleteness >= 70 ? 0.90
                       : dataCompleteness >= 50 ? 0.80
                       : 0.70;

    // Traza 2: Punto principal (Health como tamaño, opacidad según datos)
    const pointTrace = {
        type: 'scatter',
        mode: 'markers',
        x: [valuation],
        y: [quality],
        marker: {
            size: healthSize,
            color: getPointColor(rvcScore),
            line: {
                width: 2,
                color: '#ffffff'
            },
            opacity: pointOpacity
        },
        text: [createTooltipHTML(chartData)],
        hovertemplate: '%{text}<extra></extra>',
        showlegend: false,
        name: analysisData.ticker
    };

    // Preparar título con recomendación
    const headline = `${analysisData.company_name} (${analysisData.ticker})`;
    const classification = analysisData.rvc_score.classification;
    const recommendation = analysisData.rvc_score.recommendation || '';
    const subtitle = recommendation.length > 60
        ? `${classification} · ${recommendation.substring(0, 57)}...`
        : `${classification} · ${recommendation}`;

    // Layout del gráfico
    const layout = {
        title: {
            text: `${headline}<br><sub style="font-size: 0.75em; color: #64748b;">${subtitle}</sub>`,
            x: 0.02,
            font: {
                size: 16,
                family: 'Inter, system-ui, sans-serif',
                color: '#1f2937'
            }
        },
        xaxis: {
            title: {
                text: 'Valoración (→ más alto = más barata)<br><sub>P/E, PEG, P/B normalizados</sub>',
                font: { size: 13, family: 'Inter, system-ui, sans-serif' },
                standoff: 15
            },
            range: [0, 100],  // Rango exacto 0-100 (sin extensión)
            zeroline: false,
            gridcolor: '#e5e7eb',
            gridwidth: 1,
            showgrid: true,
            tick0: 0,
            dtick: 10  // Ticks cada 10 unidades
        },
        yaxis: {
            title: {
                text: 'Calidad del Negocio<br><sub>ROE, ROIC, Márgenes</sub>',
                font: { size: 13, family: 'Inter, system-ui, sans-serif' },
                standoff: 15
            },
            range: [0, 100],  // Rango exacto 0-100 (sin extensión)
            zeroline: false,
            gridcolor: '#e5e7eb',
            gridwidth: 1,
            showgrid: true,
            tick0: 0,
            dtick: 10
        },
        shapes: shapes,
        annotations: [...annotations],  // Copiar anotaciones de zonas
        plot_bgcolor: '#ffffff',
        paper_bgcolor: '#ffffff',
        margin: { l: 80, r: 40, t: 110, b: 90 },  // Márgenes más amplios para metadata
        hovermode: 'closest',
        hoverlabel: {
            bgcolor: '#1f2937',
            font: {
                size: 12,
                family: 'Inter, system-ui, sans-serif',
                color: '#ffffff'
            },
            align: 'left',
            bordercolor: '#ffffff'
        },
        dragmode: 'zoom'  // Por defecto zoom (el usuario puede cambiar a pan desde la barra)
    };

    // Agregar anotación de completitud de datos (superior izquierda)
    layout.annotations.push({
        x: 0,
        y: 1.08,
        xref: 'paper',
        yref: 'paper',
        xanchor: 'left',
        showarrow: false,
        text: `<b>Completitud:</b> ${dataCompleteness}% | <b>Confianza:</b> ${confidenceLevel}`,
        font: { size: 11, color: '#475569', family: 'Inter, system-ui, sans-serif' },
        bgcolor: 'rgba(241, 245, 249, 0.8)',
        bordercolor: '#cbd5e1',
        borderwidth: 1,
        borderpad: 4
    });

    // Agregar anotación de fuente y timestamp (inferior derecha)
    const scrapedAt = analysisData.metrics?.scraped_at
        ? new Date(analysisData.metrics.scraped_at).toLocaleString('es-ES', {
              year: 'numeric',
              month: '2-digit',
              day: '2-digit',
              hour: '2-digit',
              minute: '2-digit'
          })
        : new Date().toLocaleString('es-ES', {
              year: 'numeric',
              month: '2-digit',
              day: '2-digit',
              hour: '2-digit',
              minute: '2-digit'
          });

    const primarySource = analysisData.metrics?.primary_source || 'N/A';
    layout.annotations.push({
        x: 1,
        y: -0.12,
        xref: 'paper',
        yref: 'paper',
        xanchor: 'right',
        showarrow: false,
        text: `Fuente: ${formatSourceName(primarySource)} · ${scrapedAt}`,
        font: { size: 10, color: '#64748b', family: 'Inter, system-ui, sans-serif' }
    });

    // Configuración de Plotly con mejoras de accesibilidad
    const config = {
        displayModeBar: true,
        displaylogo: false,
        responsive: true,
        doubleClick: 'reset',  // Doble clic para resetear zoom
        modeBarButtonsToRemove: ['lasso2d', 'select2d'],  // Mantener Pan y Zoom disponibles
        modeBarButtonsToAdd: [],
        toImageButtonOptions: {
            format: 'png',
            filename: `rvc_compass_${analysisData.ticker}_${new Date().toISOString().split('T')[0]}`,
            height: 700,
            width: 1000,
            scale: 2
        },
        scrollZoom: true,  // Permitir zoom con scroll del mouse
        modeBarButtons: [
            ['zoom2d', 'pan2d'],  // Primero zoom, luego pan
            ['zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d'],
            ['toImage']
        ]
    };

    // Renderizar el gráfico - SOLO halo y punto principal
    // Si por alguna razón hay trazas extra, filtrarlas aquí
    const allTraces = [haloTrace, pointTrace];

    // Limpieza defensiva: eliminar cualquier traza extra que venga del backend
    // (por ejemplo, si analysisData.extra_traces existe)
    // Si necesitas agregar benchmarks, deben tener showlegend=false y hoverinfo='skip'

    Plotly.newPlot(
        containerId,
        allTraces,
        layout,
        config
    );

    // Agregar leyenda explicativa debajo del gráfico
    addCompassLegend(containerId);
}

/**
 * Agrega una leyenda explicativa debajo del gráfico
 */
function addCompassLegend(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    // Buscar si ya existe la leyenda
    let legendDiv = container.querySelector('.rvc-compass-legend');
    if (legendDiv) return;

    legendDiv = document.createElement('div');
    legendDiv.className = 'rvc-compass-legend';
    legendDiv.innerHTML = `
        <div class="legend-title">Guía de interpretación del mapa:</div>
        <div class="legend-items">
            <div class="legend-item">
                <span class="legend-icon" style="width: 14px; height: 14px; background: #16a34a; border-radius: 50%;"></span>
                <span><strong>Tamaño del punto</strong> = Salud Financiera (más grande = mejor)</span>
            </div>
            <div class="legend-item">
                <span class="legend-icon" style="width: 18px; height: 18px; border: 2px solid #94a3b8; border-radius: 50%;"></span>
                <span><strong>Anillo externo</strong> = Potencial de Crecimiento (más grande = mayor)</span>
            </div>
            <div class="legend-item">
                <span class="legend-icon" style="width: 18px; height: 18px; border: 3px solid #94a3b8; border-radius: 50%; opacity: 0.9;"></span>
                <span><strong>Estilo del anillo</strong> = Confianza (sólido=alta, punteado=media, discontinuo=baja)</span>
            </div>
            <div class="legend-item">
                <span class="legend-icon" style="width: 14px; height: 14px; background: #16a34a; border-radius: 50%; opacity: 0.7;"></span>
                <span><strong>Opacidad del punto</strong> = Completitud de datos (más opaco = más completo)</span>
            </div>
            <div class="legend-item" style="grid-column: 1 / -1; margin-top: 12px; padding-top: 12px; border-top: 2px solid #e5e7eb;">
                <strong style="color: #1f2937; font-size: 0.9em;">Zonas del mapa (9 cuadrantes):</strong>
            </div>
            <div class="legend-item">
                <span class="legend-icon" style="width: 14px; height: 14px; background: rgba(22, 163, 74, 0.3);"></span>
                <span><strong style="color: #16a34a;">Verde intenso</strong> = SWEET SPOT (ideal para invertir)</span>
            </div>
            <div class="legend-item">
                <span class="legend-icon" style="width: 14px; height: 14px; background: rgba(16, 185, 129, 0.3);"></span>
                <span><strong style="color: #10b981;">Verde claro</strong> = QUALITY (buena calidad)</span>
            </div>
            <div class="legend-item">
                <span class="legend-icon" style="width: 14px; height: 14px; background: rgba(234, 179, 8, 0.3);"></span>
                <span><strong style="color: #d97706;">Amarillo</strong> = VALUE (precio atractivo)</span>
            </div>
            <div class="legend-item">
                <span class="legend-icon" style="width: 14px; height: 14px; background: rgba(59, 130, 246, 0.3);"></span>
                <span><strong style="color: #3b82f6;">Azul</strong> = PREMIUM (excelente pero caro)</span>
            </div>
            <div class="legend-item">
                <span class="legend-icon" style="width: 14px; height: 14px; background: rgba(156, 163, 175, 0.3);"></span>
                <span><strong style="color: #6b7280;">Gris</strong> = FAIR (equilibrado, neutro)</span>
            </div>
            <div class="legend-item">
                <span class="legend-icon" style="width: 14px; height: 14px; background: rgba(245, 158, 11, 0.3);"></span>
                <span><strong style="color: #f59e0b;">Naranja claro</strong> = CAUTION (caro para su calidad)</span>
            </div>
            <div class="legend-item">
                <span class="legend-icon" style="width: 14px; height: 14px; background: rgba(249, 115, 22, 0.3);"></span>
                <span><strong style="color: #f97316;">Naranja</strong> = RISKY (baja calidad)</span>
            </div>
            <div class="legend-item">
                <span class="legend-icon" style="width: 14px; height: 14px; background: rgba(220, 38, 38, 0.3);"></span>
                <span><strong style="color: #dc2626;">Rojo suave</strong> = SPECULATIVE (muy cuestionable)</span>
            </div>
            <div class="legend-item">
                <span class="legend-icon" style="width: 14px; height: 14px; background: rgba(239, 68, 68, 0.3);"></span>
                <span><strong style="color: #ef4444;">Rojo</strong> = OVERVALUED (evitar)</span>
            </div>
            <div class="legend-item" style="grid-column: 1 / -1; margin-top: 12px; padding-top: 12px; border-top: 1px solid #e5e7eb;">
                <span style="font-size: 0.85em; color: #6b7280;">💡 <strong>Tip:</strong> Cada zona muestra su nombre y descripción. Usa los botones de zoom/pan de la barra superior para explorar el mapa.</span>
            </div>
        </div>
    `;

    container.appendChild(legendDiv);
}

/**
 * Muestra el contenedor del gráfico y renderiza
 */
function showRVCCompass(analysisData) {
    const compassSection = document.getElementById('rvc-compass-section');
    if (!compassSection) {
        console.error('Contenedor #rvc-compass-section no encontrado');
        return;
    }

    compassSection.classList.remove('hidden');

    // Pequeño delay para asegurar que el contenedor está visible
    setTimeout(() => {
        renderRVCCompass('rvc-compass-chart', analysisData);
    }, 100);
}

/**
 * Oculta el gráfico RVC Compass
 */
function hideRVCCompass() {
    const compassSection = document.getElementById('rvc-compass-section');
    if (compassSection) {
        compassSection.classList.add('hidden');
    }
}

// Exportar funciones para uso global
window.RVCCompass = {
    render: renderRVCCompass,
    show: showRVCCompass,
    hide: hideRVCCompass
};
