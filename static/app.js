const tickerInput = document.getElementById("ticker-input");
const analyzeBtn = document.getElementById("analyze-btn");
const clearCacheBtn = document.getElementById("clear-cache-btn");
const loading = document.getElementById("loading");
const resultsSection = document.getElementById("results");
const errorMessage = document.getElementById("error-message");
const rvcScoreSection = document.querySelector(".rvc-score");
const breakdownSection = document.querySelector(".breakdown");

analyzeBtn.addEventListener("click", analyzeStock);
tickerInput.addEventListener("keypress", (event) => {
    if (event.key === "Enter") {
        analyzeStock();
    }
});
clearCacheBtn.addEventListener("click", clearCache);

async function analyzeStock() {
    const ticker = tickerInput.value.trim().toUpperCase();
    if (!ticker) {
        showError("Por favor ingrese un ticker");
        return;
    }

    toggleLoading(true);
    try {
        const response = await fetch("/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ ticker }),
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || "No se pudo completar el analisis");
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
        data.company_name || `Analisis de ${data.ticker}`;
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

    const breakdown = data.rvc_score.breakdown;
    updateDimension("val", breakdown.valoracion, isEtf);
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
            { key: "current_price", label: `Precio Mercado (${currency})`, format: "currency" },
            { key: "nav", label: `NAV (${metrics.nav_currency || currency})`, format: "currency_simple" },
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
            { key: "current_price", label: `Precio Actual (${currency})`, format: "currency" },
            { key: "market_cap", label: `Market Cap (${currency})`, format: "marketcap" },
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
    const fallbackMap = {
        revenue_growth: ["revenue_growth_5y", "revenue_growth_qoq"],
        earnings_growth: [
            "earnings_growth_this_y",
            "earnings_growth_next_y",
            "earnings_growth_next_5y",
            "earnings_growth_qoq",
        ],
    };

    fields.forEach((field) => {
        let value = metrics[field.key];
        let sourceKey = field.key;
        if (value === undefined) {
            const fallbacks = fallbackMap[field.key] || [];
            for (const alt of fallbacks) {
                if (metrics[alt] !== undefined) {
                    value = metrics[alt];
                    sourceKey = alt;
                    break;
                }
            }
        }
        const item = document.createElement("div");
        item.classList.add("metric-item");
        let displayValue = "N/A";
        if (field.format === "currency") {
            displayValue = formatPriceDisplay(value, currency, priceConversions);
        } else if (field.format === "currency_simple") {
            displayValue = typeof value === "number"
                ? formatCurrencyAmount(value, metrics.nav_currency || currency)
                : "N/A";
        } else if (field.format === "marketcap") {
            displayValue = formatMarketCapDisplay(value, currency, marketCapConversions);
        } else if (field.format === "marketcap_simple") {
            displayValue = formatMarketCapValue(value, currency);
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
    const parts = [`${formatCurrencyAmount(value, currency)}`];
    const extras = [];
    if (conversions) {
        Object.entries(conversions).forEach(([code, amount]) => {
            if (code === currency) {
                return;
            }
            if (typeof amount !== "number") {
                return;
            }
            extras.push(`${formatCurrencyAmount(amount, code)}`);
        });
    }
    if (extras.length) {
        parts.push(`(${extras.join(" | ")})`);
    }
    return parts.join(" ");
}

function formatMarketCapDisplay(value, currency, conversions) {
    if (typeof value !== "number") {
        return "N/A";
    }
    const parts = [`${formatMarketCapValue(value, currency)}`];
    const extras = [];
    if (conversions) {
        Object.entries(conversions).forEach(([code, amount]) => {
            if (code === currency) {
                return;
            }
            if (typeof amount !== "number") {
                return;
            }
            extras.push(`${formatMarketCapValue(amount, code)}`);
        });
    }
    if (extras.length) {
        parts.push(`(${extras.join(" | ")})`);
    }
    return parts.join(" ");
}

function formatCurrencyAmount(amount, currency) {
    const symbols = { USD: "$", EUR: "€", GBP: "£", JPY: "¥" };
    const symbol = symbols[currency] || "";
    const formatter = new Intl.NumberFormat("en-US", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    });
    return `${symbol}${formatter.format(amount)} ${currency}`;
}

function formatMarketCapValue(amount, currency) {
    if (typeof amount !== "number") {
        const parsed = Number(amount);
        if (!Number.isFinite(parsed)) {
            return "N/A";
        }
        amount = parsed;
    }
    const formatter = new Intl.NumberFormat("en-US", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    });
    const symbols = { USD: "$", EUR: "€", GBP: "£", JPY: "¥" };
    const symbol = symbols[currency] || "";
    const thresholds = [
        { value: 1e12, suffix: "T" },
        { value: 1e9, suffix: "B" },
        { value: 1e6, suffix: "M" },
    ];
    for (const threshold of thresholds) {
        if (amount >= threshold.value) {
            const scaled = amount / threshold.value;
            return `${symbol}${formatter.format(scaled)}${threshold.suffix} ${currency}`;
        }
    }
    return `${symbol}${formatter.format(amount)} ${currency}`;
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
    } catch (error) {
        showError(error.message);
    }
}
