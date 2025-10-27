const tickerInput = document.getElementById("ticker-input");
const analyzeBtn = document.getElementById("analyze-btn");
const clearCacheBtn = document.getElementById("clear-cache-btn");
const loading = document.getElementById("loading");
const resultsSection = document.getElementById("results");
const errorMessage = document.getElementById("error-message");
const rvcScoreSection = document.querySelector(".rvc-score");
const breakdownSection = document.querySelector(".breakdown");
const manualToggleBtn = document.getElementById("toggle-manual-btn");
const manualSection = document.getElementById("manual-input");
const manualHint = document.getElementById("manual-hint");
const manualFieldsContainer = document.getElementById("manual-fields");
const manualFeedback = document.getElementById("manual-feedback");
const applyManualBtn = document.getElementById("apply-manual-btn");
const cancelManualBtn = document.getElementById("cancel-manual-btn");

const MANUAL_TOGGLE_LABEL_DEFAULT = "Editar métricas manualmente";
const MANUAL_TOGGLE_LABEL_PROMPT = "Completar métricas manualmente";
const MANUAL_TOGGLE_LABEL_CLOSE = "Ocultar formulario manual";
const MANUAL_HINT_DEFAULT =
    "Si las APIs no devuelven datos recientes puedes capturar los valores de fuentes confiables e ingresarlos aqui.";
const MANUAL_HINT_RECOMMENDED =
    "No se pudieron obtener todas las métricas críticas. Completa los valores manualmente antes de recalcular.";

const MANUAL_FIELDS = [
    { key: "current_price", label: "Precio actual (USD)", placeholder: "ej. 257.45", format: "number" },
    { key: "market_cap", label: "Market cap (USD)", placeholder: "ej. 1.2T", format: "number" },
    { key: "pe_ratio", label: "P/E", placeholder: "ej. 32.4", format: "number" },
    { key: "peg_ratio", label: "PEG", placeholder: "ej. 1.8", format: "number" },
    { key: "price_to_book", label: "P/B", placeholder: "ej. 6.5", format: "number" },
    { key: "roe", label: "ROE %", placeholder: "ej. 25.3%", format: "percent" },
    { key: "roic", label: "ROIC %", placeholder: "ej. 18.4%", format: "percent" },
    { key: "operating_margin", label: "Margen operativo %", placeholder: "ej. 21.7%", format: "percent" },
    { key: "net_margin", label: "Margen neto %", placeholder: "ej. 15.2%", format: "percent" },
    { key: "debt_to_equity", label: "Deuda/Patrimonio", placeholder: "ej. 0.45", format: "number" },
    { key: "current_ratio", label: "Razon corriente", placeholder: "ej. 1.9", format: "number" },
    { key: "quick_ratio", label: "Razon rapida", placeholder: "ej. 1.5", format: "number" },
    { key: "revenue_growth", label: "Crecimiento ingresos %", placeholder: "ej. 12.4%", format: "percent" },
    { key: "earnings_growth", label: "Crecimiento utilidades %", placeholder: "ej. 18.6%", format: "percent" },
    { key: "revenue_growth_5y", label: "Crecimiento ingresos 5y %", placeholder: "ej. 8.2%", format: "percent" },
    { key: "earnings_growth_next_y", label: "Crecimiento utilidades proximo ano %", placeholder: "ej. 14.0%", format: "percent" },
];

const manualInputs = new Map();
let currentTicker = null;

buildManualForm();

analyzeBtn.addEventListener("click", analyzeStock);
tickerInput.addEventListener("keypress", (event) => {
    if (event.key === "Enter") {
        analyzeStock();
    }
});
clearCacheBtn.addEventListener("click", clearCache);
if (manualToggleBtn && manualSection) {
    manualToggleBtn.addEventListener("click", () => {
        if (manualSection.classList.contains("hidden")) {
            openManualSection();
        } else {
            closeManualSection();
        }
    });
}
if (applyManualBtn) {
    applyManualBtn.addEventListener("click", applyManualOverrides);
}
if (cancelManualBtn) {
    cancelManualBtn.addEventListener("click", () => closeManualSection());
}

async function analyzeStock() {
    const ticker = tickerInput.value.trim().toUpperCase();
    if (!ticker) {
        showError("Por favor ingrese un ticker");
        return;
    }

    // Verificar límite de uso antes de analizar
    const canProceed = await checkUsageLimitBeforeAction();
    if (!canProceed) {
        return; // El modal de límite se mostrará automáticamente
    }

    toggleLoading(true);
    try {
        const licenseKey = localStorage.getItem('rvc_license_key');
        const response = await fetch("/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ 
                ticker,
                license_key: licenseKey 
            }),
        });
        const data = await response.json();
        
        if (response.status === 429) {
            // Límite alcanzado durante la consulta
            if (window.usageLimitManager && data.limit_info) {
                window.usageLimitManager.show(data.limit_info);
            }
            return;
        }
        
        if (!response.ok) {
            throw new Error(data.error || "No se pudo completar el análisis");
        }
        displayResults(data);
    } catch (error) {
        showError(error.message);
    } finally {
        toggleLoading(false);
    }
}

function toggleLoading(state) {
    if (state) {
        loading.classList.remove("hidden");
        resultsSection.classList.add("hidden");
        errorMessage.classList.add("hidden");
    } else {
        loading.classList.add("hidden");
    }
}

function displayResults(data) {
    resultsSection.classList.remove("hidden");
    errorMessage.classList.add("hidden");

    currentTicker = data.ticker;
    populateManualForm(data.metrics);
    updateManualControls(data.metrics, data.manual_overrides || null);

    const isEtf = Boolean(data.metrics.is_etf);
    const assetType = data.asset_type || data.metrics.asset_type;
    const analysisAllowed = assetType === "EQUITY" && data.analysis_allowed !== false && !isEtf;
    if (rvcScoreSection) {
        rvcScoreSection.classList.toggle("muted", !analysisAllowed);
    }
    if (breakdownSection) {
        breakdownSection.classList.toggle("hidden", !analysisAllowed);
    }
    document.getElementById("company-name").textContent =
        data.company_name || `Análisis de ${data.ticker}`;
    document.getElementById("ticker-badge").textContent = data.ticker;

    const primarySource = formatSourceName(data.metrics.primary_source);
    const sourceBadge = document.getElementById("source-badge");
    sourceBadge.textContent = `Fuente: ${primarySource}`;
    sourceBadge.classList.toggle(
        "source-badge--warning",
        data.metrics.primary_source === "fallback_example"
    );

    const sectorBadge = document.getElementById("sector-badge");
    sectorBadge.classList.remove("sector-badge--missing");
    if (data.sector && data.sector !== "Desconocido") {
        sectorBadge.textContent = data.sector;
    } else {
        const sectorSource = data.metrics.provenance
            ? data.metrics.provenance.sector
            : null;
        const lastTried = sectorSource
            ? formatSourceName(sectorSource)
            : primarySource;
        sectorBadge.textContent = `Sector sin datos (${lastTried})`;
        sectorBadge.classList.add("sector-badge--missing");
    }

    const assetBadge = document.getElementById("asset-type-badge");
    if (isEtf) {
        assetBadge.textContent = "Tipo: ETF";
        assetBadge.classList.remove("hidden");
    } else if (data.metrics.asset_type) {
        const label = data.metrics.asset_type_label || data.metrics.asset_type;
        assetBadge.textContent = `Tipo: ${label}`;
        assetBadge.classList.remove("hidden");
    } else {
        assetBadge.classList.add("hidden");
    }

    document.getElementById("confidence-badge").textContent =
        `Confianza: ${data.rvc_score.confidence_level}`;

    const score = data.rvc_score.total_score;
    const scoreCircle = document.getElementById("score-circle");
    if (typeof score === "number") {
        document.getElementById("score-value").textContent = score.toFixed(1);
    } else {
        document.getElementById("score-value").textContent = "--";
    }
    document.getElementById("classification").textContent = data.rvc_score.classification;
    document.getElementById("recommendation").textContent = data.rvc_score.recommendation;

    if (typeof score === "number" && score >= 70) {
        scoreCircle.style.background = "linear-gradient(135deg, #10b981, #34d399)";
    } else if (typeof score === "number" && score >= 50) {
        scoreCircle.style.background = "linear-gradient(135deg, #f59e0b, #fbbf24)";
    } else if (typeof score === "number") {
        scoreCircle.style.background = "linear-gradient(135deg, #ef4444, #f87171)";
    } else {
        scoreCircle.style.background = "linear-gradient(135deg, #4b5563, #6b7280)";
    }

    const breakdown = data.rvc_score.breakdown || {};
    // Claves del backend: valoracion, calidad, salud, crecimiento
    updateDimension("val", breakdown.valoracion || {}, isEtf);
    updateDimension("qual", breakdown.calidad, isEtf);
    updateDimension("health", breakdown.salud, isEtf);
    updateDimension("growth", breakdown.crecimiento, isEtf);

    populateMetrics(data.metrics);
    document.getElementById("completeness").textContent =
        data.metrics.data_completeness || 0;
    const timestamp = data.metrics.scraped_at
        ? `| Datos obtenidos: ${new Date(data.metrics.scraped_at).toLocaleString()}`
        : "";
    document.getElementById("data-timestamp").textContent = timestamp;
    showWarnings(data.metrics.warnings || []);

    const etfSection = document.getElementById("etf-profile");
    if (isEtf) {
        const etfProfile = data.metrics.etf_profile || {};
        const etfSummary = data.etf_summary || {};
        const etfScore = etfSummary.score || {};

        document.getElementById("etf-description").textContent =
            etfProfile.description || data.rvc_score.recommendation || "ETF detectado.";
        const category = etfProfile.category || data.metrics.category;
        const provider = etfProfile.provider;
        const dataSource = etfProfile.data_source;

        updateMetaBadge("etf-category", category ? `Categoría: ${category}` : "");
        updateMetaBadge("etf-provider", provider ? `Proveedor: ${provider}` : "");
        updateMetaBadge(
            "etf-data-source",
            dataSource ? `Fuente: ${dataSource}` : ""
        );

        if (typeof etfScore.total_score === "number") {
            document.getElementById("classification").textContent = etfScore.label || "ETF";
        }
        etfSection.classList.remove("hidden");
    } else {
        etfSection.classList.add("hidden");
    }

    // Renderizar gráfico RVC Compass si es una acción analizable
    if (analysisAllowed && window.RVCCompass) {
        // Actualizar nombre en la descripción
        const compassTickerName = document.getElementById("compass-ticker-name");
        if (compassTickerName) {
            compassTickerName.textContent = data.company_name || data.ticker;
        }
        // Mostrar y renderizar el gráfico
        window.RVCCompass.show(data);
    } else if (window.RVCCompass) {
        // Ocultar el gráfico si no es analizable
        window.RVCCompass.hide();
    }
}

function updateDimension(prefix, dimData, isEtf) {
    const score = typeof dimData.score === "number" ? dimData.score : 0;
    const progress = document.getElementById(`${prefix}-progress`);
    const scoreElement = document.getElementById(`${prefix}-score`);
    const metricsElement = document.getElementById(`${prefix}-metrics`);

    if (typeof dimData.score === "number") {
        progress.style.width = `${score}%`;
    } else {
        progress.style.width = "0%";
    }
    if (typeof dimData.score === "number" && dimData.score >= 70) {
        progress.style.background = "linear-gradient(90deg, #10b981, #34d399)";
    } else if (typeof dimData.score === "number" && dimData.score >= 50) {
        progress.style.background = "linear-gradient(90deg, #f59e0b, #fbbf24)";
    } else if (typeof dimData.score === "number") {
        progress.style.background = "linear-gradient(90deg, #ef4444, #f87171)";
    } else {
        progress.style.background = "linear-gradient(90deg, #6b7280, #9ca3af)";
    }

    scoreElement.textContent =
        typeof dimData.score === "number" ? dimData.score.toFixed(1) : "--";
    const used = dimData.metrics_used || [];
    metricsElement.textContent = used.length ? used.join(", ") : "Sin datos";
}

function populateMetrics(metrics) {
    const grid = document.getElementById("metrics-grid");
    grid.innerHTML = "";
    const provenance = metrics.provenance || {};
    const scrapedAt = metrics.scraped_at
        ? new Date(metrics.scraped_at).toLocaleString()
        : "";
    const currency = metrics.price_currency || metrics.currency || "USD";
    const priceConversions = metrics.price_converted || {};
    const marketCapConversions = metrics.market_cap_converted || {};
    const isEtf = Boolean(metrics.is_etf);
    let fields;
    if (isEtf) {
        fields = [
            { key: "current_price", label: "Precio Mercado", format: "currency" },
            { key: "nav", label: "NAV", format: "currency_simple" },
            { key: "expense_ratio", label: "Expense Ratio", format: "percent" },
            { key: "ytd_return", label: "YTD Return", format: "percent" },
            { key: "premium_discount", label: "Premium/Discount", format: "percent" },
            { key: "assets_under_management", label: "AUM", format: "marketcap_simple" },
            { key: "dividend_yield", label: "Dividend Yield", format: "percent" },
            { key: "holdings_count", label: "Holdings", format: "integer" },
            { key: "index_tracked", label: "Índice", format: "text" },
            { key: "volume", label: "Volumen Diario", format: "number_compact" },
        ];
    } else {
        fields = [
            { key: "current_price", label: "Precio Actual", format: "currency" },
            { key: "market_cap", label: "Market Cap", format: "marketcap" },
            { key: "pe_ratio", label: "P/E Ratio", format: "number" },
            { key: "peg_ratio", label: "PEG Ratio", format: "number" },
            { key: "price_to_book", label: "P/B Ratio", format: "number" },
            { key: "roe", label: "ROE", format: "percent" },
            { key: "roic", label: "ROIC", format: "percent" },
            { key: "operating_margin", label: "Op. Margin", format: "percent" },
            { key: "net_margin", label: "Net Margin", format: "percent" },
            { key: "debt_to_equity", label: "Debt/Equity", format: "number" },
            { key: "current_ratio", label: "Current Ratio", format: "number" },
            { key: "quick_ratio", label: "Quick Ratio", format: "number" },
            { key: "revenue_growth", label: "Rev. Growth", format: "percent" },
            { key: "earnings_growth", label: "Earn. Growth", format: "percent" },
        ];
    }
    const valuePriority = {
        revenue_growth: [
            "revenue_growth_5y",
            "revenue_growth",
            "revenue_growth_qoq",
        ],
        earnings_growth: [
            "earnings_growth_this_y",
            "earnings_growth_next_y",
            "earnings_growth_next_5y",
            "earnings_growth_qoq",
            "earnings_growth",
        ],
    };

    fields.forEach((field) => {
        const candidates = valuePriority[field.key] || [field.key];
        let value;
        let sourceKey = candidates[0] || field.key;
        for (const candidate of candidates) {
            const candidateValue = metrics[candidate];
            if (candidateValue !== undefined && candidateValue !== null) {
                value = candidateValue;
                sourceKey = candidate;
                break;
            }
        }
        const item = document.createElement("div");
        item.classList.add("metric-item");
        let displayValue = "N/A";
        if (field.format === "currency") {
            displayValue = formatPriceDisplay(value, currency, priceConversions);
        } else if (field.format === "currency_simple") {
            displayValue = typeof value === "number"
                ? formatPriceDisplay(value, metrics.nav_currency || currency, null)
                : "N/A";
        } else if (field.format === "marketcap") {
            displayValue = formatMarketCapDisplay(value, currency, marketCapConversions);
        } else if (field.format === "marketcap_simple") {
            displayValue = formatMarketCapDisplay(value, currency, null);
        } else if (field.format === "percent") {
            displayValue = formatPercentageValue(value);
        } else if (field.format === "number_compact") {
            displayValue = formatCompactNumber(value);
        } else if (field.format === "integer") {
            displayValue = formatInteger(value);
        } else if (field.format === "text") {
            displayValue = formatTextValue(value);
        } else if (typeof value === "number") {
            displayValue =
                field.format === "percent"
                    ? `${value.toFixed(1)}%`
                    : value.toFixed(2);
        }
        item.innerHTML = `
            <div class="metric-name">${field.label}</div>
            <div class="metric-value">${displayValue}</div>
        `;
        const source = provenance[sourceKey];
        const tooltipParts = [`Fuente: ${formatSourceName(source)}`];
        if (scrapedAt) {
            tooltipParts.push(`Fecha: ${scrapedAt}`);
        }
        item.title = tooltipParts.join(" | ");
        grid.appendChild(item);
    });
}

function buildManualForm() {
    if (!manualFieldsContainer) {
        return;
    }
    manualFieldsContainer.innerHTML = "";
    manualInputs.clear();

    MANUAL_FIELDS.forEach((field) => {
        const wrapper = document.createElement("div");
        wrapper.className = "manual-field";

        const label = document.createElement("label");
        label.setAttribute("for", `manual-${field.key}`);
        label.textContent = field.label;

        const input = document.createElement("input");
        input.type = "text";
        input.id = `manual-${field.key}`;
        input.name = field.key;
        input.dataset.field = field.key;
        if (field.placeholder) {
            input.placeholder = field.placeholder;
        }
        input.autocomplete = "off";
        input.inputMode = "decimal";
        input.addEventListener("input", () => clearManualFeedback());

        label.appendChild(input);
        wrapper.appendChild(label);
        manualFieldsContainer.appendChild(wrapper);
        manualInputs.set(field.key, input);
    });
}

function formatManualFieldValue(value, field) {
    if (value === null || value === undefined) {
        return "";
    }
    if (typeof value === "number") {
        if (field && field.format === "percent") {
            return value.toFixed(1).replace(/\.0$/, "");
        }
        if (!Number.isInteger(value) && Math.abs(value) < 1000) {
            return value.toFixed(2).replace(/\.?0+$/, "");
        }
        return value.toString();
    }
    return String(value);
}

function populateManualForm(metrics) {
    if (!manualInputs.size) {
        return;
    }
    MANUAL_FIELDS.forEach((field) => {
        const input = manualInputs.get(field.key);
        if (!input) {
            return;
        }
        const rawValue = metrics ? metrics[field.key] : null;
        const formatted = formatManualFieldValue(rawValue, field);
        input.value = formatted;
        input.dataset.original = formatted;
    });
}

function openManualSection() {
    if (!manualSection) {
        return;
    }
    manualSection.classList.remove("hidden");
    if (manualToggleBtn) {
        manualToggleBtn.textContent = MANUAL_TOGGLE_LABEL_CLOSE;
    }
}

function closeManualSection() {
    if (!manualSection) {
        return;
    }
    manualSection.classList.add("hidden");
    if (manualToggleBtn) {
        const recommended = manualSection.classList.contains("manual-input--highlight");
        manualToggleBtn.textContent = recommended
            ? MANUAL_TOGGLE_LABEL_PROMPT
            : MANUAL_TOGGLE_LABEL_DEFAULT;
    }
}

function updateManualControls(metrics, manualOverrides) {
    if (!manualToggleBtn || !manualSection) {
        return;
    }
    manualToggleBtn.classList.remove("hidden");
    const recommended = Boolean(metrics && metrics.manual_input_recommended);
    manualSection.classList.toggle("manual-input--highlight", recommended);
    if (manualHint) {
        manualHint.textContent = recommended ? MANUAL_HINT_RECOMMENDED : MANUAL_HINT_DEFAULT;
    }
    // Mantener el formulario cerrado por defecto, solo cambiar el texto del botón
    if (recommended) {
        manualToggleBtn.textContent = MANUAL_TOGGLE_LABEL_PROMPT;
        // NO abrir automáticamente - el usuario debe hacerlo manualmente
        // openManualSection();
    } else if (manualSection.classList.contains("hidden")) {
        manualToggleBtn.textContent = MANUAL_TOGGLE_LABEL_DEFAULT;
    } else {
        manualToggleBtn.textContent = MANUAL_TOGGLE_LABEL_CLOSE;
    }

    if (manualOverrides) {
        const messages = [];
        if (Array.isArray(manualOverrides.applied) && manualOverrides.applied.length) {
            messages.push(`Se aplicaron ${manualOverrides.applied.length} ajustes manuales.`);
        }
        const invalidKeys = manualOverrides.invalid
            ? Object.keys(manualOverrides.invalid)
            : [];
        if (invalidKeys.length) {
            messages.push(`Valores ignorados: ${invalidKeys.join(", ")}`);
        }
        if (messages.length) {
            showManualFeedback(messages.join(" "), invalidKeys.length > 0);
        } else {
            clearManualFeedback();
        }
    } else {
        clearManualFeedback();
    }
}

async function applyManualOverrides() {
    if (!currentTicker) {
        showManualFeedback("Analiza un ticker antes de editar las métricas.", true);
        return;
    }
    const overrides = {};
    let hasChanges = false;
    manualInputs.forEach((input, key) => {
        const value = input.value.trim();
        const original = input.dataset.original ?? "";
        if (value === "" && original === "") {
            return;
        }
        if (value === "" && original !== "") {
            overrides[key] = null;
            hasChanges = true;
            return;
        }
        if (value !== original) {
            overrides[key] = value;
            hasChanges = true;
        }
    });
    if (!hasChanges) {
        showManualFeedback("No hay cambios para aplicar.", true);
        return;
    }

    try {
        showManualFeedback("Aplicando ajustes manuales...", false);
        const response = await fetch("/api/manual-metrics", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ ticker: currentTicker, overrides }),
        });
        const data = await response.json();
        if (!response.ok) {
            const invalidKeys = data.invalid_fields ? Object.keys(data.invalid_fields) : [];
            let message = data.error || "No se pudieron aplicar los ajustes manuales.";
            if (invalidKeys.length) {
                message += ` Valores ignorados: ${invalidKeys.join(", ")}.`;
            }
            showManualFeedback(message, true);
            return;
        }

        displayResults(data);
        const messages = [];
        if (data.manual_overrides && Array.isArray(data.manual_overrides.applied) && data.manual_overrides.applied.length) {
            messages.push(`Se aplicaron ${data.manual_overrides.applied.length} ajustes manuales.`);
        }
        const invalidKeys = data.manual_overrides && data.manual_overrides.invalid
            ? Object.keys(data.manual_overrides.invalid)
            : [];
        if (invalidKeys.length) {
            messages.push(`Valores ignorados: ${invalidKeys.join(", ")}`);
        }
        if (messages.length) {
            showManualFeedback(messages.join(" "), invalidKeys.length > 0);
        } else {
            clearManualFeedback();
        }
    } catch (error) {
        showManualFeedback(
            error.message || "No se pudieron aplicar los ajustes manuales.",
            true
        );
    }
}

function showManualFeedback(message, isError = false) {
    if (!manualFeedback) {
        return;
    }
    manualFeedback.textContent = message;
    manualFeedback.classList.remove("hidden");
    manualFeedback.classList.toggle("manual-feedback--error", Boolean(isError));
}

function clearManualFeedback() {
    if (!manualFeedback) {
        return;
    }
    manualFeedback.textContent = "";
    manualFeedback.classList.add("hidden");
    manualFeedback.classList.remove("manual-feedback--error");
}

function showWarnings(warnings) {
    const panel = document.getElementById("warnings-panel");
    const list = document.getElementById("warnings-list");
    list.innerHTML = "";
    if (!warnings.length) {
        panel.classList.add("hidden");
        return;
    }
    warnings.forEach((warning) => {
        const li = document.createElement("li");
        li.textContent = warning;
        list.appendChild(li);
    });
    panel.classList.remove("hidden");
}

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.classList.remove("hidden");
    resultsSection.classList.add("hidden");
    if (manualToggleBtn) {
        manualToggleBtn.classList.add("hidden");
    }
    if (manualSection) {
        manualSection.classList.add("hidden");
    }
    clearManualFeedback();
    currentTicker = null;
}

function updateMetaBadge(id, text) {
    const badge = document.getElementById(id);
    if (!badge) return;
    if (text) {
        badge.textContent = text;
        badge.classList.remove("hidden");
    } else {
        badge.textContent = "";
        badge.classList.add("hidden");
    }
}

function formatSourceName(rawSource) {
    if (!rawSource) {
        return "Desconocida";
    }
    const normalized = rawSource.split(":")[0];
    const mapping = {
        yahoo: "Yahoo Finance",
        finviz: "Finviz",
        marketwatch: "MarketWatch",
        fmp: "Financial Modeling Prep",
        twelvedata: "Twelve Data",
        alpha_vantage: "Alpha Vantage",
        fallback_example: "Datos de ejemplo",
    };
    return mapping[normalized] || normalized.toUpperCase();
}

function formatPercentageValue(value) {
    if (typeof value !== "number") {
        return "N/A";
    }
    const decimals = Math.abs(value) < 10 ? 2 : 1;
    return `${value.toFixed(decimals)}%`;
}

function formatPriceDisplay(value, currency, conversions) {
    if (typeof value !== "number") {
        return "N/A";
    }
    const target = window.CurrencyManager?.getCurrency?.() || "USD";
    let amount = value;
    let converted = false;
    const base = (currency || "USD").toUpperCase();
    if (base !== target) {
        if (conversions && typeof conversions[target] === "number") {
            amount = conversions[target];
            converted = true;
        } else if (base === "USD" && typeof window.CurrencyManager?.convertFromUSD === "function") {
            amount = window.CurrencyManager.convertFromUSD(value);
            converted = true;
        }
    }
    const symbol = converted || base === target
        ? (window.CurrencyManager?.getSymbol?.() || (target === "EUR" ? "€" : "$"))
        : (base === "EUR" ? "€" : "$");
    const formatter = new Intl.NumberFormat("es-CO", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    });
    return `${symbol} ${formatter.format(amount)}`;
}

function formatMarketCapDisplay(value, currency, conversions) {
    if (typeof value !== "number") {
        return "N/A";
    }
    const target = window.CurrencyManager?.getCurrency?.() || "USD";
    let amount = value;
    let converted = false;
    const base = (currency || "USD").toUpperCase();
    if (base !== target) {
        if (conversions && typeof conversions[target] === "number") {
            amount = conversions[target];
            converted = true;
        } else if (base === "USD" && typeof window.CurrencyManager?.convertFromUSD === "function") {
            amount = window.CurrencyManager.convertFromUSD(value);
            converted = true;
        }
    }
    const symbol = converted || base === target
        ? (window.CurrencyManager?.getSymbol?.() || (target === "EUR" ? "€" : "$"))
        : (base === "EUR" ? "€" : "$");
    // Escala a T/B/M manteniendo símbolo y sin sufijo de moneda
    const formatter = new Intl.NumberFormat("es-CO", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    });
    const thresholds = [
        { value: 1e12, suffix: "T" },
        { value: 1e9, suffix: "B" },
        { value: 1e6, suffix: "M" },
    ];
    for (const t of thresholds) {
        if (amount >= t.value) {
            const scaled = amount / t.value;
            return `${symbol} ${formatter.format(scaled)}${t.suffix}`;
        }
    }
    return `${symbol} ${formatter.format(amount)}`;
}

function formatCompactNumber(value) {
    if (typeof value !== "number") {
        const parsed = Number(value);
        if (!Number.isFinite(parsed)) {
            return "N/A";
        }
        value = parsed;
    }
    const formatter = new Intl.NumberFormat("en-US", {
        notation: "compact",
        compactDisplay: "short",
        maximumFractionDigits: 2,
    });
    return formatter.format(value);
}

function formatInteger(value) {
    if (typeof value !== "number") {
        const parsed = Number(value);
        if (!Number.isFinite(parsed)) {
            return "N/A";
        }
        value = parsed;
    }
    return new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(value);
}

function formatTextValue(value) {
    if (value === undefined || value === null || value === "") {
        return "N/A";
    }
    return String(value);
}

async function clearCache() {
    const ticker = tickerInput.value.trim().toUpperCase();
    try {
        const response = await fetch("/cache/clear", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ ticker: ticker || null }),
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || "No se pudo limpiar la cache");
        }
        window.alert(
            data.cleared === "ticker"
                ? `Cache limpiada para ${ticker}`
                : "Cache global limpiada correctamente"
        );
        resultsSection.classList.add("hidden");
        errorMessage.classList.add("hidden");
        if (manualToggleBtn) {
            manualToggleBtn.classList.add("hidden");
        }
        if (manualSection) {
            manualSection.classList.add("hidden");
        }
        clearManualFeedback();
        currentTicker = null;
    } catch (error) {
        showError(error.message);
    }
}
