// ============================================
// COMPARADOR DE ACCIONES - JAVASCRIPT
// ============================================

// Helper function para generar iconos SVG consistentes
function iconHTML(name, size = 16, className = '') {
    return `<svg class="icon ${className}" width="${size}" height="${size}" aria-hidden="true">
        <use href="/static/icons.svg#${name}"></use>
    </svg>`;
}

// Mapeo de emojis de categoría a iconos SVG
const categoryIconMap = {
    '🏆': 'trophy',      // SWEET SPOT
    '⭐': 'star',        // PREMIUM
    '💎': 'gem',         // VALOR
    '⚠️': 'alert-triangle',  // CARA
    '🪤': 'alert-circle',    // TRAMPA
    '🔴': 'x-circle'     // EVITAR
};

// Helper para obtener icono de categoría
function getCategoryIcon(emoji, size = 16) {
    const iconName = categoryIconMap[emoji] || 'alert-circle';
    return iconHTML(iconName, size);
}

document.addEventListener('DOMContentLoaded', function() {
    // Elementos del DOM
    const compareBtn = document.getElementById('compare-btn');
    const clearBtn = document.getElementById('clear-btn');
    const loading = document.getElementById('loading');
    const resultsContainer = document.getElementById('results-container');
    const errorMessage = document.getElementById('error-message');

    // Event Listeners
    compareBtn.addEventListener('click', handleCompare);
    clearBtn.addEventListener('click', handleClear);

    // Tab switching
    const tabButtons = document.querySelectorAll('.tab-btn');
    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });

    // Handle Enter key on inputs
    document.querySelectorAll('.ticker-input').forEach(input => {
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                handleCompare();
            }
        });
    });

    const breakdownOrder = [
        { key: 'quality', label: 'Calidad', icon: 'trophy' },
        { key: 'valuation', label: 'Valoración', icon: 'dollar-sign' },
        { key: 'health', label: 'Salud financiera', icon: 'shield' },
        { key: 'growth', label: 'Crecimiento', icon: 'trending-up' },
    ];

    // ========================================
    // UTILIDADES PARA GRÁFICOS MODERNOS
    // ========================================

    // Validación segura de números
    const safeNum = (v, def = 0) => (typeof v === 'number' && isFinite(v)) ? v : def;
    
    // Limitar valores entre 0 y 1
    const clamp01 = v => Math.max(0, Math.min(1, v));
    
    // Paleta de colores moderna (Tailwind-style)
    const scoreColor = score => {
        if (score >= 75) return '#10b981'; // Verde esmeralda
        if (score >= 60) return '#f59e0b'; // Ámbar
        if (score >= 45) return '#f97316'; // Naranja
        return '#ef4444'; // Rojo
    };

    // Configuración base para layouts de Plotly
    const baseLayout = (opts = {}) => ({
        font: { family: 'Inter, system-ui, -apple-system, sans-serif', size: 13, color: '#1f2937' },
        plot_bgcolor: '#fafafa',
        paper_bgcolor: 'white',
        margin: { l: 60, r: 40, t: 80, b: 60 },
        xaxis: { gridcolor: '#e5e7eb', linecolor: '#d1d5db' },
        yaxis: { gridcolor: '#e5e7eb', linecolor: '#d1d5db' },
        ...opts
    });

    // Configuración base para gráficos
    const baseConfig = {
        responsive: true,
        displayModeBar: true,
        displaylogo: false,
        modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d', 'zoom2d', 'autoScale2d']
    };

    // Limitar número de empresas para visualización
    const limitCompanies = (companies, max = 10) => companies.slice(0, Math.min(companies.length, max));

    // ========================================
    // MAIN FUNCTIONS
    // ========================================

    async function handleCompare() {
        // Recopilar tickers
        const tickers = [];
        for (let i = 1; i <= 5; i++) {
            const input = document.getElementById(`ticker-${i}`);
            const value = input.value.trim().toUpperCase();
            if (value) {
                tickers.push(value);
            }
        }

        // Validación
        if (tickers.length < 2) {
            showError('Debe ingresar al menos 2 tickers para comparar');
            return;
        }

        // Remover duplicados
        const uniqueTickers = [...new Set(tickers)];
        if (uniqueTickers.length < tickers.length) {
            showError('No puede ingresar tickers duplicados');
            return;
        }

        // Verificar límite de uso antes de comparar
        const canProceed = await checkUsageLimitBeforeAction();
        if (!canProceed) {
            return; // Modal de límite se muestra automáticamente
        }

        // Mostrar loading
        hideError();
        resultsContainer.classList.add('hidden');
        loading.classList.remove('hidden');
        compareBtn.disabled = true;

        try {
            // Obtener licencia si existe
            const licenseKey = localStorage.getItem('rvc_license_key');
            
            // Llamar a la API
            const response = await fetch('/api/comparar', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    tickers: uniqueTickers,
                    license_key: licenseKey 
                })
            });

            const data = await response.json();

            if (response.status === 429) {
                // Límite alcanzado
                if (window.usageLimitManager && data.limit_info) {
                    window.usageLimitManager.show(data.limit_info);
                }
                return;
            }

            if (!response.ok) {
                throw new Error(data.error || 'Error al comparar tickers');
            }

            // Mostrar resultados
            displayResults(data);

        } catch (error) {
            showError(error.message);
        } finally {
            loading.classList.add('hidden');
            compareBtn.disabled = false;
        }
    }

    function handleClear() {
        // Limpiar inputs
        for (let i = 1; i <= 5; i++) {
            document.getElementById(`ticker-${i}`).value = '';
        }

        // Ocultar resultados
        resultsContainer.classList.add('hidden');
        hideError();
    }

    // ========================================
    // DISPLAY RESULTS
    // ========================================

    function displayResults(data) {
        const { companies, ranking } = data;

        if (!companies || companies.length === 0) {
            showError('No se obtuvieron datos para ningún ticker');
            return;
        }

        // 1. Mostrar ranking
        displayRanking(companies);

        // 2. Crear gráficos
        createScatterPlot(companies);
        createBarChart(companies);
        createRadarChart(companies.slice(0, 3)); // Solo las primeras 3

        // 3. Crear tabla comparativa
        createComparisonTable(companies);

        // 4. Detalle por pilar
        displayBreakdown(companies);

        // 5. Mostrar conclusión
        displayConclusion(companies);

        // Mostrar contenedor de resultados
        resultsContainer.classList.remove('hidden');

        // Scroll suave hacia resultados
        resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    // ========================================
    // RANKING SECTION
    // ========================================

    function displayRanking(companies) {
        const container = document.getElementById('ranking-cards');
        container.innerHTML = '';

        companies.forEach((company, index) => {
            const card = createRankingCard(company, index + 1);
            container.appendChild(card);
        });
    }

    function createRankingCard(company, position) {
        const card = document.createElement('div');
        card.className = 'ranking-card';

        // Agregar clase especial para top 3
        if (position === 1) card.classList.add('gold');
        else if (position === 2) card.classList.add('silver');
        else if (position === 3) card.classList.add('bronze');

        // Medallas SVG con colores
        const medalColors = {
            1: 'style="color: #FFD700;"',  // Gold
            2: 'style="color: #C0C0C0;"',  // Silver
            3: 'style="color: #CD7F32;"'   // Bronze
        };
        const medal = position <= 3 
            ? `<svg class="icon" width="20" height="20" ${medalColors[position]} aria-hidden="true">
                <use href="/static/icons.svg#award"></use>
              </svg>`
            : '';

        const categoryClass = getCategoryClass(company.category.name);
        const recClass = getRecommendationClass(company.recommendation);
        const primarySource = formatSourceName(company.primary_source);
        const sourceClass = company.primary_source === 'fallback_example'
            ? 'rank-source rank-source-warning'
            : 'rank-source';
        const companyName = formatCompanyName(company);

        card.innerHTML = `
            <div class="rank-position">${medal || position}</div>
            <div class="rank-ticker">${company.ticker}</div>
            <div class="rank-info">
                <div class="rank-company">${companyName}</div>
                <div class="${sourceClass}">Fuente: ${primarySource}</div>
                <div class="rank-category ${categoryClass}">
                    ${getCategoryIcon(company.category.emoji, 16)} ${company.category.name}
                </div>
                <div class="rank-confidence">Confianza: ${company.confidence_level || 'N/A'}</div>
            </div>
            <div class="rank-score">${company.investment_score.toFixed(0)}</div>
            <div class="rank-recommendation ${recClass}">
                ${company.recommendation}
            </div>
        `;

        return card;
    }

    // ========================================
    // GRÁFICO 1: SCATTER PLOT - Mapa de Inversión (Moderno)
    // ========================================

    function createScatterPlot(companies) {
        const data = limitCompanies(companies, 10);
        
        const traces = data.map(company => {
            const categoryName = company.category.name;
            const color = getCategoryColor(categoryName);
            const x = safeNum(company.valuation_score, 0);
            const y = safeNum(company.quality_score, 0);

            return {
                x: [x],
                y: [y],
                mode: 'markers+text',
                type: 'scatter',
                name: company.ticker,
                text: [company.ticker],
                textposition: 'top center',
                textfont: {
                    size: 13,
                    color: '#1f2937',
                    family: 'Inter, system-ui, sans-serif',
                    weight: 600
                },
                marker: {
                    size: 18,
                    color: color,
                    opacity: 0.9,
                    line: {
                        color: 'rgba(255,255,255,0.95)',
                        width: 2.5
                    }
                },
                hovertemplate:
                    `<b>${company.ticker}</b><br>` +
                    `Calidad: ${y.toFixed(1)}<br>` +
                    `Valoración: ${x.toFixed(1)}<br>` +
                    `Score Inversión: ${safeNum(company.investment_score, 0).toFixed(1)}<br>` +
                    `Categoría: ${categoryName}<br>` +
                    '<extra></extra>'
            };
        });

        // Zona ideal (Sweet Spot) con diseño moderno
        const sweetSpotZone = {
            type: 'rect',
            x0: 60, y0: 70, x1: 100, y1: 100,
            fillcolor: 'rgba(16, 185, 129, 0.12)',
            line: { 
                color: 'rgba(16, 185, 129, 0.4)',
                width: 2,
                dash: 'dot'
            },
            layer: 'below'
        };

        const layout = {
            ...baseLayout({
                title: {
                    text: 'Mapa de Inversión: Calidad vs Valoración',
                    font: { size: 20, weight: 700, color: '#111827' }
                },
                height: 550
            }),
            xaxis: {
                title: { 
                    text: 'Score de Valoración (0=Caro, 100=Barato)',
                    font: { size: 13, color: '#4b5563' }
                },
                range: [0, 105],
                gridcolor: '#e5e7eb',
                linecolor: '#d1d5db',
                showgrid: true
            },
            yaxis: {
                title: { 
                    text: 'Score de Calidad (0=Mala, 100=Excelente)',
                    font: { size: 13, color: '#4b5563' }
                },
                range: [0, 105],
                gridcolor: '#e5e7eb',
                linecolor: '#d1d5db',
                showgrid: true
            },
            shapes: [sweetSpotZone],
            annotations: [
                {
                    x: 80, y: 85,
                    text: '⭐ ZONA IDEAL',
                    showarrow: false,
                    font: { size: 13, color: '#059669', family: 'Inter, sans-serif', weight: 600 }
                }
            ],
            showlegend: false,
            hovermode: 'closest'
        };

        Plotly.newPlot('scatter-plot', traces, layout, baseConfig);
        window.addEventListener('resize', () => Plotly.Plots.resize('scatter-plot'));
    }

    // ========================================
    // GRÁFICO 2: BAR CHART - Ranking con efecto Lollipop (Moderno)
    // ========================================

    function createBarChart(companies) {
        const data = limitCompanies(companies, 10);
        const sortedCompanies = [...data].sort((a, b) =>
            b.investment_score - a.investment_score
        );

        const x = sortedCompanies.map(c => safeNum(c.investment_score, 0));
        const y = sortedCompanies.map(c => c.ticker);

        // Stems (barras translúcidas de fondo)
        const stems = {
            x: x,
            y: y,
            type: 'bar',
            orientation: 'h',
            marker: {
                color: x.map(scoreColor),
                opacity: 0.2
            },
            hoverinfo: 'skip',
            showlegend: false,
            base: 0
        };

        // Heads (círculos en los extremos con valores)
        const heads = {
            x: x,
            y: y,
            mode: 'markers+text',
            type: 'scatter',
            marker: {
                size: 14,
                color: x.map(scoreColor),
                opacity: 1,
                line: {
                    color: 'rgba(255,255,255,0.95)',
                    width: 2
                }
            },
            text: x.map(v => Math.round(v)),
            textposition: 'middle right',
            textfont: {
                size: 12,
                weight: 600,
                color: '#1f2937'
            },
            hovertemplate: '<b>%{y}</b><br>Score: %{x:.1f}<extra></extra>'
        };

        const layout = {
            ...baseLayout({
                title: {
                    text: 'Ranking por Score de Inversión',
                    font: { size: 20, weight: 700, color: '#111827' }
                },
                height: Math.max(400, sortedCompanies.length * 50)
            }),
            xaxis: {
                title: { 
                    text: 'Score (0–100)',
                    font: { size: 13, color: '#4b5563' }
                },
                range: [0, Math.max(100, Math.ceil(Math.max(...x, 0) / 5) * 5)],
                gridcolor: '#e5e7eb',
                linecolor: '#d1d5db',
                showgrid: true
            },
            yaxis: {
                title: '',
                automargin: true,
                gridcolor: '#e5e7eb',
                linecolor: '#d1d5db'
            },
            bargap: 0.65,
            showlegend: false
        };

        Plotly.newPlot('bars-chart', [stems, heads], layout, baseConfig);
        window.addEventListener('resize', () => Plotly.Plots.resize('bars-chart'));
    }

    // ========================================
    // GRÁFICO 3: RADAR CHART - Perfil Multidimensional (Moderno)
    // ========================================

    function createRadarChart(companies) {
        const data = limitCompanies(companies, 10);
        const topN = Math.max(1, Math.min(3, data.length));
        const topCompanies = data.slice(0, topN);

        const metrics = [
            { key: 'quality_score', label: 'Calidad' },
            { key: 'valuation_score', label: 'Valoración' },
            { key: 'financial_health_score', label: 'Salud Financiera' },
            { key: 'growth_score', label: 'Crecimiento' }
        ];

        const theta = [...metrics.map(m => m.label), metrics[0].label];
        const paletteLines = [
            'rgba(79,70,229,1)',   // Índigo
            'rgba(16,185,129,1)',  // Esmeralda
            'rgba(245,158,11,1)'   // Ámbar
        ];

        const traces = topCompanies.map((company, index) => {
            const rVals = metrics.map(m => {
                const val = safeNum(company[m.key], 0);
                return clamp01(val / 100) * 100; // Asegurar rango 0-100
            });
            rVals.push(rVals[0]); // Cerrar el círculo

            const color = paletteLines[index % paletteLines.length];

            return {
                type: 'scatterpolar',
                r: rVals,
                theta: theta,
                fill: 'toself',
                name: company.ticker,
                line: {
                    color: color,
                    width: 2.5
                },
                fillcolor: color.replace(',1)', ',0.15)'),
                marker: {
                    size: 7,
                    color: color
                },
                hovertemplate: '<b>%{theta}</b><br>Score: %{r:.1f}<extra></extra>'
            };
        });

        const layout = {
            ...baseLayout({
                title: {
                    text: 'Perfil Comparativo Multidimensional',
                    font: { size: 20, weight: 700, color: '#111827' }
                },
                height: 550
            }),
            polar: {
                bgcolor: '#fafafa',
                radialaxis: {
                    visible: true,
                    range: [0, 100],
                    tickvals: [0, 20, 40, 60, 80, 100],
                    gridcolor: '#e5e7eb',
                    linecolor: '#d1d5db',
                    tickfont: { size: 11, color: '#6b7280' },
                    angle: 90
                },
                angularaxis: {
                    gridcolor: '#e5e7eb',
                    linecolor: '#d1d5db',
                    tickfont: { size: 12, color: '#374151', weight: 600 }
                }
            },
            showlegend: true,
            legend: {
                orientation: 'h',
                x: 0,
                y: 1.12,
                xanchor: 'left',
                yanchor: 'bottom',
                font: { size: 12, color: '#374151' },
                bgcolor: 'rgba(255,255,255,0.9)',
                bordercolor: '#e5e7eb',
                borderwidth: 1
            }
        };

        Plotly.newPlot('radar-chart', traces, layout, baseConfig);
        window.addEventListener('resize', () => Plotly.Plots.resize('radar-chart'));
    }

    // ========================================
    // TABLA COMPARATIVA
    // ========================================

    function createComparisonTable(companies) {
        const table = document.getElementById('comparison-table');
        table.innerHTML = '';

        // Header
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        headerRow.innerHTML = '<th>Métrica</th>';
        companies.forEach(c => {
            headerRow.innerHTML += `<th>${c.ticker}</th>`;
        });
        thead.appendChild(headerRow);
        table.appendChild(thead);

        // Body
        const tbody = document.createElement('tbody');

        // Sección: DECISIÓN
        tbody.appendChild(createSectionRow(`${iconHTML('target', 16)} DECISIÓN`, companies.length));
        tbody.appendChild(createMetricRow('Score de Inversión', companies, c =>
            formatScore(c.investment_score)
        ));
        tbody.appendChild(createMetricRow('Categoría', companies, c =>
            `${getCategoryIcon(c.category.emoji, 16)} ${c.category.name}`
        ));
        tbody.appendChild(createMetricRow('Recomendación', companies, c =>
            c.recommendation
        ));
        tbody.appendChild(createMetricRow('Fuente principal', companies, c =>
            formatSourceName(c.primary_source)
        ));

        // Sección: PRECIO
        tbody.appendChild(createSectionRow(`${iconHTML('dollar-sign', 16)} PRECIO`, companies.length));
        tbody.appendChild(createMetricRow('Precio Actual', companies, c =>
            formatPriceCell(c)
        ));
        tbody.appendChild(createMetricRow('Market Cap', companies, c =>
            formatMarketCapCell(c)
        ));

        // Sección: SCORES
        tbody.appendChild(createSectionRow(`${iconHTML('bar-chart', 16)} SCORES`, companies.length));
        tbody.appendChild(createMetricRow('Calidad', companies, c =>
            formatScore(c.quality_score)
        ));
        tbody.appendChild(createMetricRow('Valoración', companies, c =>
            formatScore(c.valuation_score)
        ));
        tbody.appendChild(createMetricRow('Salud Financiera', companies, c =>
            formatScore(c.financial_health_score)
        ));
        tbody.appendChild(createMetricRow('Crecimiento', companies, c =>
            formatScore(c.growth_score)
        ));

        // Sección: CALIDAD
        tbody.appendChild(createSectionRow(`${iconHTML('trophy', 16)} CALIDAD DEL NEGOCIO`, companies.length));
        tbody.appendChild(createMetricRow('ROE', companies, c =>
            formatPercentage(c.metrics.roe)
        ));
        tbody.appendChild(createMetricRow('ROIC', companies, c =>
            formatPercentage(c.metrics.roic)
        ));
        tbody.appendChild(createMetricRow('Margen Operativo', companies, c =>
            formatPercentage(c.metrics.operating_margin)
        ));
        tbody.appendChild(createMetricRow('Margen Neto', companies, c =>
            formatPercentage(c.metrics.net_margin)
        ));

        // Sección: VALORACIÓN
        tbody.appendChild(createSectionRow(`${iconHTML('dollar-sign', 16)} VALORACIÓN`, companies.length));
        tbody.appendChild(createMetricRow('P/E Ratio', companies, c =>
            formatRatio(c.metrics.pe_ratio)
        ));
        tbody.appendChild(createMetricRow('PEG Ratio', companies, c =>
            formatRatio(c.metrics.peg_ratio)
        ));
        tbody.appendChild(createMetricRow('P/B Ratio', companies, c =>
            formatRatio(c.metrics.price_to_book)
        ));

        // Sección: BALANCE
        tbody.appendChild(createSectionRow(`${iconHTML('shield', 16)} SALUD FINANCIERA`, companies.length));
        tbody.appendChild(createMetricRow('Debt/Equity', companies, c =>
            formatRatio(c.metrics.debt_to_equity)
        ));
        tbody.appendChild(createMetricRow('Current Ratio', companies, c =>
            formatRatio(c.metrics.current_ratio)
        ));
        tbody.appendChild(createMetricRow('Quick Ratio', companies, c =>
            formatRatio(c.metrics.quick_ratio)
        ));

        // Sección: CRECIMIENTO
        tbody.appendChild(createSectionRow(`${iconHTML('trending-up', 16)} CRECIMIENTO`, companies.length));
        tbody.appendChild(createMetricRow('Crecimiento Ingresos', companies, c =>
            formatPercentage(c.metrics.revenue_growth)
        ));
        tbody.appendChild(createMetricRow('Crecimiento Beneficios', companies, c =>
            formatPercentage(c.metrics.earnings_growth)
        ));

        table.appendChild(tbody);
    }

    function createSectionRow(title, colspan) {
        const row = document.createElement('tr');
        row.innerHTML = `<td colspan="${colspan + 1}" class="section-header">${title}</td>`;
        return row;
    }

    function createMetricRow(metricName, companies, valueFormatter) {
        const row = document.createElement('tr');
        row.innerHTML = `<td class="metric-name">${metricName}</td>`;
        companies.forEach(company => {
            const value = valueFormatter(company);
            row.innerHTML += `<td>${value}</td>`;
        });
        return row;
    }

    // ========================================
    // DETALLE DEL BREAKDOWN
    // ========================================

    function displayBreakdown(companies) {
        const container = document.getElementById('breakdown-grid');
        if (!container) return;
        container.innerHTML = '';

        companies.forEach(company => {
            const breakdown = company.breakdown || {};
            const dimensions = breakdownOrder.map(dim => {
                const data = breakdown[dim.key] || {};
                const scoreValue = typeof data.score === 'number'
                    ? data.score.toFixed(1)
                    : '--';
                const metricsUsed = Array.isArray(data.metrics_used) && data.metrics_used.length
                    ? data.metrics_used.map(item => `<li>${item}</li>`).join('')
                    : '<li>Sin datos disponibles</li>';
                return `
                    <div class="dimension-card">
                        <div class="dimension-header">
                            <span class="dimension-label">${iconHTML(dim.icon, 18)} ${dim.label}</span>
                            <span class="dimension-score">${scoreValue}</span>
                        </div>
                        <ul class="dimension-metrics">
                            ${metricsUsed}
                        </ul>
                    </div>
                `;
            }).join('');

            const card = document.createElement('div');
            card.className = 'breakdown-card';
            card.innerHTML = `
                <div class="breakdown-header">
                    <div class="breakdown-title">
                        <span class="breakdown-ticker">${company.ticker}</span>
                        <span class="breakdown-score">${company.investment_score.toFixed(1)}/100</span>
                    </div>
                    <div class="breakdown-subtitle">
                        <span>${formatCompanyName(company)}</span>
                        <span class="breakdown-confidence">Confianza: ${company.confidence_level || 'N/A'}</span>
                    </div>
                </div>
                <div class="breakdown-dimensions">
                    ${dimensions}
                </div>
            `;

            container.appendChild(card);
        });
    }

    // ========================================
    // CONCLUSIÓN
    // ========================================

    function displayConclusion(companies) {
        const best = companies[0];
        const worst = companies[companies.length - 1];

        // Mejor opción
        const bestCard = document.getElementById('best-option');
        const bestCategoryClass = getCategoryClass(best.category.name);
        bestCard.innerHTML = `
            <h3>🟢 Mejor Opción: ${best.ticker}</h3>
            <div class="score-big" style="color: #28a745;">
                ${best.investment_score.toFixed(0)}/100
            </div>
            <div class="category-badge ${bestCategoryClass}">
                ${getCategoryIcon(best.category.emoji, 16)} ${best.category.name}
            </div>
            <div class="reason">
                <strong>Razón:</strong> ${best.category.desc}
            </div>
            <div class="reason">
                <strong>Confianza:</strong> ${best.confidence_level || 'N/A'}
            </div>
            <div class="reason">
                <strong>Recomendación:</strong> ${best.recommendation}
            </div>
        `;

        // Peor opción
        const worstCard = document.getElementById('worst-option');
        const worstCategoryClass = getCategoryClass(worst.category.name);
        worstCard.innerHTML = `
            <h3>🔴 Evitar: ${worst.ticker}</h3>
            <div class="score-big" style="color: #dc3545;">
                ${worst.investment_score.toFixed(0)}/100
            </div>
            <div class="category-badge ${worstCategoryClass}">
                ${getCategoryIcon(worst.category.emoji, 16)} ${worst.category.name}
            </div>
            <div class="reason">
                <strong>Razón:</strong> ${worst.category.desc}
            </div>
            <div class="reason">
                <strong>Confianza:</strong> ${worst.confidence_level || 'N/A'}
            </div>
            <div class="reason">
                <strong>Recomendación:</strong> ${worst.recommendation}
            </div>
        `;
    }

    // ========================================
    // UTILIDADES
    // ========================================

    function switchTab(tabName) {
        // Desactivar todos los tabs
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });

        // Activar el tab seleccionado
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        document.getElementById(`${tabName}-tab`).classList.add('active');
    }

    function getCategoryClass(categoryName) {
        const mapping = {
            'SWEET SPOT': 'category-sweet-spot',
            'PREMIUM': 'category-premium',
            'VALOR': 'category-valor',
            'CARA': 'category-cara',
            'TRAMPA': 'category-trampa',
            'EVITAR': 'category-evitar'
        };
        return mapping[categoryName] || 'category-evitar';
    }

    function getCategoryColor(categoryName) {
        const colorMapping = {
            'SWEET SPOT': '#28a745',
            'PREMIUM': '#007bff',
            'VALOR': '#17a2b8',
            'CARA': '#ffc107',
            'TRAMPA': '#fd7e14',
            'EVITAR': '#dc3545'
        };
        return colorMapping[categoryName] || '#6c757d';
    }

    function getRecommendationClass(recommendation) {
        if (recommendation.includes('COMPRAR') || recommendation.includes('🟢')) {
            return 'rec-green';
        } else if (recommendation.includes('CONSIDERAR') || recommendation.includes('🟡')) {
            return 'rec-yellow';
        } else if (recommendation.includes('ESPERAR') || recommendation.includes('⚠️')) {
            return 'rec-orange';
        } else {
            return 'rec-red';
        }
    }

    function formatScore(score) {
        if (score === null || score === undefined) return 'N/A';
        const value = score.toFixed(0);
        let className = 'value-danger';
        if (score >= 75) className = 'value-excellent';
        else if (score >= 60) className = 'value-good';
        else if (score >= 45) className = 'value-warning';
        return `<span class="${className}">${value}</span>`;
    }

    function formatSourceName(rawSource) {
        if (!rawSource) {
            return 'Desconocida';
        }
        const normalized = rawSource.split(':')[0];
        const mapping = {
            yahoo: 'Yahoo Finance',
            finviz: 'Finviz',
            marketwatch: 'MarketWatch',
            fmp: 'Financial Modeling Prep',
            alpha_vantage: 'Alpha Vantage',
            fallback_example: 'Datos de ejemplo'
        };
        return mapping[normalized] || normalized.toUpperCase();
    }

    function formatCompanyName(company) {
        const name = company.company_name;
        if (!name || isSuspiciousName(name)) {
            return 'Nombre no disponible';
        }
        return name;
    }

    function isSuspiciousName(name) {
        const normalized = name.trim().toLowerCase();
        if (!normalized) return true;
        const suspicious = [
            'yahoo finance',
            'finance.yahoo.com',
            'captcha',
            'temporarily unavailable',
            'will be right back',
            'service unavailable'
        ];
        return suspicious.some(keyword => normalized.includes(keyword));
    }

    function formatPercentage(value) {
        if (value === null || value === undefined) return 'N/A';
        const formatted = value.toFixed(1) + '%';
        let className = '';
        if (value >= 20) className = 'value-excellent';
        else if (value >= 10) className = 'value-good';
        else if (value >= 5) className = 'value-warning';
        else className = 'value-danger';
        return `<span class="${className}">${formatted}</span>`;
    }

    function formatRatio(value) {
        if (value === null || value === undefined) return 'N/A';
        return value.toFixed(2);
    }

    function formatPriceCell(company) {
        const currency = company.price_currency || company.currency || 'USD';
        return formatPriceDisplay(company.current_price, currency, company.price_converted);
    }

    function formatMarketCapCell(company) {
        const currency = company.price_currency || company.currency || 'USD';
        return formatMarketCapDisplay(company.market_cap, currency, company.market_cap_converted);
    }

    function formatPriceDisplay(value, currency, conversions) {
        if (typeof value !== 'number') return 'N/A';
        const target = window.CurrencyManager?.getCurrency?.() || 'USD';
        let amount = value;
        let converted = false;
        const base = (currency || 'USD').toUpperCase();
        if (base !== target) {
            if (conversions && typeof conversions[target] === 'number') {
                amount = conversions[target];
                converted = true;
            } else if (base === 'USD' && typeof window.CurrencyManager?.convertFromUSD === 'function') {
                amount = window.CurrencyManager.convertFromUSD(value);
                converted = true;
            }
        }
        const symbol = converted || base === target
            ? (window.CurrencyManager?.getSymbol?.() || (target === 'EUR' ? '€' : '$'))
            : (base === 'EUR' ? '€' : '$');
        const formatter = new Intl.NumberFormat('es-CO', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
        return `${symbol} ${formatter.format(amount)}`;
    }

    function formatMarketCapDisplay(value, currency, conversions) {
        if (typeof value !== 'number') return 'N/A';
        const target = window.CurrencyManager?.getCurrency?.() || 'USD';
        let amount = value;
        let converted = false;
        const base = (currency || 'USD').toUpperCase();
        if (base !== target) {
            if (conversions && typeof conversions[target] === 'number') {
                amount = conversions[target];
                converted = true;
            } else if (base === 'USD' && typeof window.CurrencyManager?.convertFromUSD === 'function') {
                amount = window.CurrencyManager.convertFromUSD(value);
                converted = true;
            }
        }
        const symbol = converted || base === target
            ? (window.CurrencyManager?.getSymbol?.() || (target === 'EUR' ? '€' : '$'))
            : (base === 'EUR' ? '€' : '$');
        const formatter = new Intl.NumberFormat('es-CO', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
        const thresholds = [
            { value: 1e12, suffix: 'T' },
            { value: 1e9, suffix: 'B' },
            { value: 1e6, suffix: 'M' }
        ];
        for (const threshold of thresholds) {
            if (amount >= threshold.value) {
                const scaled = amount / threshold.value;
                return `${symbol} ${formatter.format(scaled)}${threshold.suffix}`;
            }
        }
        return `${symbol} ${formatter.format(amount)}`;
    }

    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.classList.remove('hidden');
        setTimeout(() => {
            errorMessage.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }, 100);
    }

    function hideError() {
        errorMessage.classList.add('hidden');
    }
});
