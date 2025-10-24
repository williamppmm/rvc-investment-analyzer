/**
 * Top Opportunities JavaScript Module
 * Gestiona la funcionalidad de filtrado, ordenamiento y visualización
 */

class TopOpportunities {
    constructor() {
        this.baseUrl = '/api/top-opportunities';
        this.currentData = null;
        this.isLoading = false;
        
        // Elementos del DOM
        this.elements = {
            minScoreSlider: document.getElementById('min-score-slider'),
            minScoreValue: document.getElementById('min-score-value'),
            sectorSelect: document.getElementById('sector-select'),
            sortSelect: document.getElementById('sort-select'),
            limitSelect: document.getElementById('limit-select'),
            applyFiltersBtn: document.getElementById('apply-filters'),
            resetFiltersBtn: document.getElementById('reset-filters'),
            clearCacheBtn: document.getElementById('clear-cache'),
            statusBanner: document.getElementById('status-banner'),
            loadingContainer: document.getElementById('loading-container'),
            errorContainer: document.getElementById('error-container'),
            resultsSection: document.getElementById('results-section'),
            opportunitiesTable: document.getElementById('opportunities-table'),
            opportunitiesTbody: document.getElementById('opportunities-tbody'),
            emptyState: document.getElementById('empty-state'),
            retryButton: document.getElementById('retry-button'),
            errorMessage: document.getElementById('error-message'),
            
            // Stats elements
            totalCount: document.getElementById('total-count'),
            averageScore: document.getElementById('average-score'),
            sectorsCount: document.getElementById('sectors-count'),
            topTicker: document.getElementById('top-ticker'),
            resultsCount: document.getElementById('results-count'),
            lastUpdated: document.getElementById('last-updated')
        };
        
        this.initializeEventListeners();
        this.loadInitialData();
    }
    
    showNotice(message, type = 'info', timeout = 4000) {
        const banner = this.elements.statusBanner;
        if (!banner) return;
        banner.className = `notice notice--${type}`;
        banner.textContent = message;
        banner.classList.remove('hidden');
        if (timeout > 0) {
            clearTimeout(this._noticeTimer);
            this._noticeTimer = setTimeout(() => {
                banner.classList.add('hidden');
            }, timeout);
        }
    }
    
    initializeEventListeners() {
        // Slider de score mínimo
        this.elements.minScoreSlider.addEventListener('input', (e) => {
            this.elements.minScoreValue.textContent = e.target.value;
        });
        
        // Botones de filtros
        this.elements.applyFiltersBtn.addEventListener('click', () => {
            this.loadData();
        });
        
        this.elements.resetFiltersBtn.addEventListener('click', () => {
            this.resetFilters();
        });

        // Borrar caché global
        this.elements.clearCacheBtn.addEventListener('click', async () => {
            const confirmed = window.confirm(
                'Esta acción borrará TODOS los datos en caché (análisis anteriores) y no se puede deshacer.\n\n¿Deseas continuar?'
            );
            if (!confirmed) return;

            try {
                // Deshabilitar botones durante la operación
                this.elements.clearCacheBtn.disabled = true;
                this.elements.clearCacheBtn.textContent = '🧹 Borrando...';

                const resp = await fetch('/cache/clear', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({})
                });

                if (!resp.ok) {
                    const err = await resp.json().catch(() => ({}));
                    throw new Error(err.error || `HTTP ${resp.status}`);
                }

                // Feedback estilizado y recargar datos
                this.showNotice('Caché borrada correctamente. Recargando datos…', 'success');
                await this.loadData();
            } catch (e) {
                console.error('Error limpiando caché:', e);
                this.showNotice('No se pudo borrar la caché: ' + (e.message || 'Error desconocido'), 'error', 6000);
            } finally {
                this.elements.clearCacheBtn.disabled = false;
                this.elements.clearCacheBtn.textContent = '🗑️ Borrar caché';
            }
        });
        
        // Retry button
        this.elements.retryButton.addEventListener('click', () => {
            this.loadData();
        });
        
        // Auto-aplicar filtros cuando cambian los selects
        [this.elements.sectorSelect, this.elements.sortSelect, this.elements.limitSelect].forEach(element => {
            element.addEventListener('change', () => {
                // Pequeño delay para mejor UX
                setTimeout(() => this.loadData(), 100);
            });
        });
        
        // Enter key en filtros
        document.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && e.target.closest('.filters-section')) {
                this.loadData();
            }
        });
    }
    
    resetFilters() {
        this.elements.minScoreSlider.value = 50;
        this.elements.minScoreValue.textContent = '50';
        this.elements.sectorSelect.value = '';
        this.elements.sortSelect.value = 'rvc_score';
        this.elements.limitSelect.value = '20';
        
        this.loadData();
    }
    
    buildApiUrl() {
        const params = new URLSearchParams();
        
        const minScore = this.elements.minScoreSlider.value;
        const sector = this.elements.sectorSelect.value;
        const sortBy = this.elements.sortSelect.value;
        const limit = this.elements.limitSelect.value;
        
        if (minScore && minScore !== '50') {
            params.append('min_score', minScore);
        }
        if (sector) {
            params.append('sector', sector);
        }
        if (sortBy && sortBy !== 'rvc_score') {
            params.append('sort_by', sortBy);
        }
        if (limit && limit !== '50') {
            params.append('limit', limit);
        }
        
        return `${this.baseUrl}?${params.toString()}`;
    }
    
    showLoading() {
        this.isLoading = true;
        this.elements.loadingContainer.style.display = 'block';
        this.elements.errorContainer.classList.add('hidden');
        this.elements.resultsSection.style.display = 'none';
        this.elements.applyFiltersBtn.disabled = true;
        this.elements.applyFiltersBtn.textContent = '⏳ Cargando...';
    }
    
    hideLoading() {
        this.isLoading = false;
        this.elements.loadingContainer.style.display = 'none';
        this.elements.applyFiltersBtn.disabled = false;
        this.elements.applyFiltersBtn.textContent = '🔍 Aplicar Filtros';
    }
    
    showError(message = 'Error desconocido') {
        this.hideLoading();
        this.elements.errorContainer.classList.remove('hidden');
        this.elements.errorMessage.textContent = message;
        this.elements.resultsSection.style.display = 'none';
    }
    
    showResults() {
        this.hideLoading();
        this.elements.errorContainer.classList.add('hidden');
        this.elements.resultsSection.style.display = 'block';
    }
    
    async loadInitialData() {
        // Cargar con filtros por defecto
        await this.loadData();
    }
    
    async loadData() {
        if (this.isLoading) return;
        
        this.showLoading();
        
        try {
            const url = this.buildApiUrl();
            console.log('🔍 Cargando datos desde:', url);
            
            const response = await fetch(url);
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || `HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.status !== 'success') {
                throw new Error(data.message || 'Respuesta inválida del servidor');
            }
            
            this.currentData = data;
            this.renderData(data);
            this.showResults();
            
        } catch (error) {
            console.error('❌ Error cargando datos:', error);
            this.showError(`Error al cargar datos: ${error.message}`);
        }
    }
    
    renderData(data) {
        const { opportunities, metadata } = data.data;
        
        // Actualizar estadísticas
        this.updateStats(metadata, opportunities);
        
        // Renderizar tabla
        this.renderTable(opportunities);
        
        // Actualizar información de resultados
        this.updateResultsInfo(metadata);
    }
    
    updateStats(metadata, opportunities) {
        this.elements.totalCount.textContent = metadata.total_count;
        this.elements.averageScore.textContent = metadata.average_score.toFixed(1);
        this.elements.sectorsCount.textContent = metadata.sectors_available.length;
        
        if (opportunities.length > 0) {
            this.elements.topTicker.textContent = opportunities[0].ticker;
        } else {
            this.elements.topTicker.textContent = '-';
        }
    }
    
    updateResultsInfo(metadata) {
        const count = metadata.total_count;
        const countText = count === 1 ? 'oportunidad encontrada' : 'oportunidades encontradas';
        this.elements.resultsCount.textContent = `${count} ${countText}`;
        
        // Formatear fecha
        const date = new Date(metadata.generated_at);
        const timeStr = date.toLocaleTimeString('es-ES', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
        this.elements.lastUpdated.textContent = `Actualizado: ${timeStr}`;
    }
    
    renderTable(opportunities) {
        const tbody = this.elements.opportunitiesTbody;
        
        if (opportunities.length === 0) {
            this.showEmptyState();
            return;
        }
        
        this.hideEmptyState();
        
        tbody.innerHTML = opportunities.map((opportunity, index) => {
            return this.createTableRow(opportunity, index + 1);
        }).join('');
    }
    
    createTableRow(opportunity, rank) {
        const {
            ticker,
            company_name,
            rvc_score,
            classification,
            sector,
            current_price,
            market_cap,
            pe_ratio
        } = opportunity;
        
        // Formatear valores
        const formattedPrice = current_price ? `$${current_price.toFixed(2)}` : '-';
        const formattedMarketCap = market_cap ? this.formatMarketCap(market_cap) : '-';
        const formattedPE = pe_ratio ? pe_ratio.toFixed(1) : '-';
        const scoreClass = this.getScoreClass(rvc_score);
        const rankClass = rank <= 3 ? `rank-${rank}` : '';
        
        return `
            <tr class="opportunity-row">
                <td class="rank-cell ${rankClass}">
                    ${rank <= 3 ? this.getRankIcon(rank) : rank}
                </td>
                <td class="ticker-cell">
                    <strong>${ticker}</strong>
                </td>
                <td class="company-cell">
                    <div class="company-info">
                        <div class="company-name">${company_name || ticker}</div>
                        <div class="company-sector">${sector}</div>
                    </div>
                </td>
                <td class="score-cell">
                    <div class="score-badge ${scoreClass}">
                        ${rvc_score.toFixed(1)}
                    </div>
                </td>
                <td class="classification-cell">
                    <span class="classification-badge">${classification}</span>
                </td>
                <td class="sector-cell">
                    ${sector}
                </td>
                <td class="price-cell">
                    ${formattedPrice}
                </td>
                <td class="market-cap-cell">
                    ${formattedMarketCap}
                </td>
                <td class="pe-cell">
                    ${formattedPE}
                </td>
                <td class="actions-cell">
                    <button class="btn-analyze" onclick="analyzeStock('${ticker}')">
                        🔍 Analizar
                    </button>
                </td>
            </tr>
        `;
    }
    
    getRankIcon(rank) {
        const icons = { 1: '🥇', 2: '🥈', 3: '🥉' };
        return icons[rank] || rank;
    }
    
    getScoreClass(score) {
        if (score >= 80) return 'score-excellent';
        if (score >= 70) return 'score-good';
        if (score >= 60) return 'score-fair';
        return 'score-poor';
    }
    
    formatMarketCap(marketCap) {
        if (marketCap >= 1e12) {
            return `$${(marketCap / 1e12).toFixed(1)}T`;
        } else if (marketCap >= 1e9) {
            return `$${(marketCap / 1e9).toFixed(1)}B`;
        } else if (marketCap >= 1e6) {
            return `$${(marketCap / 1e6).toFixed(1)}M`;
        }
        return `$${marketCap.toFixed(0)}`;
    }
    
    showEmptyState() {
        this.elements.opportunitiesTable.style.display = 'none';
        this.elements.emptyState.classList.remove('hidden');
    }
    
    hideEmptyState() {
        this.elements.opportunitiesTable.style.display = 'table';
        this.elements.emptyState.classList.add('hidden');
    }
}

// Funciones globales para acciones rápidas
window.applyQuickFilter = function(type) {
    const app = window.topOpportunitiesApp;
    
    switch(type) {
        case 'premium':
            app.elements.minScoreSlider.value = 75;
            app.elements.minScoreValue.textContent = '75';
            app.elements.sectorSelect.value = '';
            app.elements.limitSelect.value = '10';
            break;
            
        case 'technology':
            app.elements.sectorSelect.value = 'technology';
            app.elements.minScoreSlider.value = 60;
            app.elements.minScoreValue.textContent = '60';
            break;
            
        case 'large-cap':
            app.elements.sortSelect.value = 'market_cap';
            app.elements.minScoreSlider.value = 50;
            app.elements.minScoreValue.textContent = '50';
            app.elements.limitSelect.value = '20';
            break;
            
        case 'reset':
            app.resetFilters();
            return;
    }
    
    app.loadData();
};

// Función para analizar una acción específica
window.analyzeStock = function(ticker) {
    // Redirigir a la página principal con el ticker pre-cargado
    const url = new URL('/', window.location.origin);
    url.searchParams.set('ticker', ticker);
    window.open(url.toString(), '_blank');
};

// Inicializar la aplicación cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    console.log('🏆 Inicializando Top Opportunities...');
    window.topOpportunitiesApp = new TopOpportunities();
});