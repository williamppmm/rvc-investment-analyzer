/**
 * Calculadora de Inversión - Cliente JavaScript
 */

// Estado global
let selectedScenario = 'moderado';

// Inicialización
document.addEventListener('DOMContentLoaded', () => {
    initializeTabs();
    initializeScenarioCards();
    initializeCalculators();
});

/**
 * Inicializa el sistema de tabs
 */
function initializeTabs() {
    const tabs = document.querySelectorAll('.calc-tab');
    const contents = document.querySelectorAll('.calc-content');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const targetTab = tab.getAttribute('data-tab');

            // Actualizar tabs activos
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            // Actualizar contenido visible
            contents.forEach(content => {
                content.classList.remove('active');
            });

            const targetContent = {
                'dca': 'dca-content',
                'lump-sum': 'lump-sum-content',
                'compound': 'compound-content'
            }[targetTab];

            document.getElementById(targetContent)?.classList.add('active');
        });
    });
}

/**
 * Inicializa las tarjetas de escenarios
 */
function initializeScenarioCards() {
    const cards = document.querySelectorAll('.scenario-card');

    cards.forEach(card => {
        card.addEventListener('click', () => {
            // Remover selección anterior
            cards.forEach(c => c.classList.remove('selected'));

            // Seleccionar nueva tarjeta
            card.classList.add('selected');
            selectedScenario = card.getAttribute('data-scenario');
        });
    });
}

/**
 * Inicializa los botones de las calculadoras
 */
function initializeCalculators() {
    // DCA Calculator
    document.getElementById('calculate-dca').addEventListener('click', calculateDCA);

    // Lump Sum vs DCA
    document.getElementById('calculate-lump-sum').addEventListener('click', calculateLumpSum);

    // Compound Interest
    document.getElementById('calculate-compound').addEventListener('click', calculateCompound);

    // Enter key support
    ['dca-monthly', 'dca-years'].forEach(id => {
        document.getElementById(id)?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') calculateDCA();
        });
    });

    ['ls-total', 'ls-years'].forEach(id => {
        document.getElementById(id)?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') calculateLumpSum();
        });
    });

    ['ci-initial', 'ci-monthly', 'ci-years'].forEach(id => {
        document.getElementById(id)?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') calculateCompound();
        });
    });
}

/**
 * Calcula proyección DCA
 */
async function calculateDCA() {
    const monthlyAmount = parseFloat(document.getElementById('dca-monthly').value);
    const years = parseInt(document.getElementById('dca-years').value);
    const marketTiming = document.getElementById('dca-timing').value;

    if (!monthlyAmount || monthlyAmount <= 0) {
        alert('Por favor ingrese un monto mensual válido');
        return;
    }

    if (!years || years <= 0 || years > 50) {
        alert('Por favor ingrese un período válido (1-50 años)');
        return;
    }

    const loading = document.getElementById('dca-loading');
    const results = document.getElementById('dca-results');

    loading.classList.remove('hidden');
    results.classList.add('hidden');

    try {
        const response = await fetch('/api/calcular-inversion', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                calculation_type: 'dca',
                monthly_amount: monthlyAmount,
                years: years,
                scenario: selectedScenario,
                market_timing: marketTiming
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Error en el cálculo');
        }

        renderDCAResults(data.result);
    } catch (error) {
        alert(`Error: ${error.message}`);
    } finally {
        loading.classList.add('hidden');
    }
}

/**
 * Renderiza resultados DCA
 */
function renderDCAResults(result) {
    const container = document.getElementById('dca-results');
    const { input, results: res, breakdown, insights, monthly_simulation } = result;

    let html = `
        <div class="results-grid">
            <div class="result-card">
                <div class="label">Total Invertido</div>
                <div class="value">$${formatNumber(res.total_invested)}</div>
                <div class="subvalue">${input.total_months} meses × $${formatNumber(input.monthly_amount)}</div>
            </div>
            <div class="result-card success">
                <div class="label">Valor Final</div>
                <div class="value">$${formatNumber(res.final_value)}</div>
                <div class="subvalue">Escenario: ${input.scenario}</div>
            </div>
            <div class="result-card info">
                <div class="label">Ganancia Total</div>
                <div class="value">$${formatNumber(res.total_gain)}</div>
                <div class="subvalue">+${res.total_return_pct.toFixed(1)}%</div>
            </div>
        </div>
    `;

    // Milestones
    if (breakdown.years_5 || breakdown.years_10 || breakdown.years_15 || breakdown.years_20) {
        html += `
            <div class="chart-container">
                <h3>📅 Hitos de tu inversión</h3>
                <div class="milestone-timeline">
        `;

        [breakdown.years_5, breakdown.years_10, breakdown.years_15, breakdown.years_20].forEach(milestone => {
            if (milestone) {
                const percentage = (milestone.value / res.final_value) * 100;
                html += `
                    <div class="milestone-item">
                        <div class="milestone-year">${milestone.years} años</div>
                        <div class="milestone-bar" style="background: linear-gradient(90deg, #667eea ${percentage}%, #e9ecef ${percentage}%);"></div>
                        <div class="milestone-value">$${formatNumber(milestone.value)}</div>
                    </div>
                `;
            }
        });

        html += `
                </div>
            </div>
        `;
    }

    // Insights
    if (insights && insights.length > 0) {
        html += `
            <div class="insights-section">
                <h3>💡 Insights clave</h3>
        `;

        insights.forEach(insight => {
            html += `
                <div class="insight-item">
                    <span style="font-size: 1.5rem;">📌</span>
                    <span>${insight}</span>
                </div>
            `;
        });

        html += `</div>`;
    }

    container.innerHTML = html;
    container.classList.remove('hidden');

    // Scroll suave a resultados
    container.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

/**
 * Calcula comparación Lump Sum vs DCA
 */
async function calculateLumpSum() {
    const totalAmount = parseFloat(document.getElementById('ls-total').value);
    const years = parseInt(document.getElementById('ls-years').value);
    const scenario = document.getElementById('ls-scenario').value;

    if (!totalAmount || totalAmount <= 0) {
        alert('Por favor ingrese un monto total válido');
        return;
    }

    if (!years || years <= 0 || years > 50) {
        alert('Por favor ingrese un período válido (1-50 años)');
        return;
    }

    const loading = document.getElementById('ls-loading');
    const results = document.getElementById('ls-results');

    loading.classList.remove('hidden');
    results.classList.add('hidden');

    try {
        const response = await fetch('/api/calcular-inversion', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                calculation_type: 'lump_sum_vs_dca',
                total_amount: totalAmount,
                years: years,
                scenario: scenario
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Error en el cálculo');
        }

        renderLumpSumResults(data.result);
    } catch (error) {
        alert(`Error: ${error.message}`);
    } finally {
        loading.classList.add('hidden');
    }
}

/**
 * Renderiza resultados Lump Sum vs DCA
 */
function renderLumpSumResults(result) {
    const container = document.getElementById('ls-results');
    const { lump_sum, dca, comparison } = result;

    let html = `
        <h3>📊 Comparación de Estrategias</h3>

        <div class="results-grid" style="margin-bottom: 2rem;">
            <div class="result-card ${comparison.winner === 'Lump Sum' ? 'success' : ''}">
                <div class="label">${lump_sum.strategy} ${comparison.winner === 'Lump Sum' ? '🏆' : ''}</div>
                <div class="value">$${formatNumber(lump_sum.final_value)}</div>
                <div class="subvalue">Ganancia: $${formatNumber(lump_sum.total_gain)} (+${lump_sum.return_pct.toFixed(1)}%)</div>
            </div>
            <div class="result-card ${comparison.winner === 'DCA' ? 'success' : ''}">
                <div class="label">${dca.strategy} ${comparison.winner === 'DCA' ? '🏆' : ''}</div>
                <div class="value">$${formatNumber(dca.final_value)}</div>
                <div class="subvalue">Ganancia: $${formatNumber(dca.total_gain)} (+${dca.return_pct.toFixed(1)}%)</div>
            </div>
        </div>

        <table class="comparison-table">
            <thead>
                <tr>
                    <th>Métrica</th>
                    <th>Lump Sum</th>
                    <th>DCA</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><strong>Monto mensual</strong></td>
                    <td>$${formatNumber(result.total_amount)} (mes 1)</td>
                    <td>$${formatNumber(dca.monthly_amount)}/mes</td>
                </tr>
                <tr>
                    <td><strong>Valor final</strong></td>
                    <td>$${formatNumber(lump_sum.final_value)} ${comparison.winner === 'Lump Sum' ? '<span class="winner-badge">GANADOR</span>' : ''}</td>
                    <td>$${formatNumber(dca.final_value)} ${comparison.winner === 'DCA' ? '<span class="winner-badge">GANADOR</span>' : ''}</td>
                </tr>
                <tr>
                    <td><strong>Ganancia total</strong></td>
                    <td>$${formatNumber(lump_sum.total_gain)}</td>
                    <td>$${formatNumber(dca.total_gain)}</td>
                </tr>
                <tr>
                    <td><strong>Retorno %</strong></td>
                    <td>+${lump_sum.return_pct.toFixed(1)}%</td>
                    <td>+${dca.return_pct.toFixed(1)}%</td>
                </tr>
            </tbody>
        </table>

        <div class="insights-section" style="margin-top: 2rem;">
            <h3>💡 Recomendación</h3>
            <div class="insight-item">
                <span style="font-size: 1.5rem;">📌</span>
                <span><strong>${comparison.winner}</strong> tiene ventaja de $${formatNumber(comparison.difference)} (${comparison.difference_pct.toFixed(1)}%)</span>
            </div>
            <div class="insight-item">
                <span style="font-size: 1.5rem;">💭</span>
                <span>${comparison.recommendation}</span>
            </div>
        </div>
    `;

    container.innerHTML = html;
    container.classList.remove('hidden');

    container.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

/**
 * Calcula impacto del interés compuesto
 */
async function calculateCompound() {
    const initialAmount = parseFloat(document.getElementById('ci-initial').value) || 0;
    const monthlyContribution = parseFloat(document.getElementById('ci-monthly').value) || 0;
    const years = parseInt(document.getElementById('ci-years').value);
    const scenario = document.getElementById('ci-scenario').value;

    if (initialAmount < 0 || monthlyContribution < 0) {
        alert('Los montos no pueden ser negativos');
        return;
    }

    if (initialAmount === 0 && monthlyContribution === 0) {
        alert('Debe ingresar al menos un monto inicial o una contribución mensual');
        return;
    }

    if (!years || years <= 0 || years > 50) {
        alert('Por favor ingrese un período válido (1-50 años)');
        return;
    }

    const loading = document.getElementById('ci-loading');
    const results = document.getElementById('ci-results');

    loading.classList.remove('hidden');
    results.classList.add('hidden');

    try {
        const response = await fetch('/api/calcular-inversion', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                calculation_type: 'compound_interest',
                initial_amount: initialAmount,
                monthly_amount: monthlyContribution,
                years: years,
                scenario: scenario
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Error en el cálculo');
        }

        renderCompoundResults(data.result);
    } catch (error) {
        alert(`Error: ${error.message}`);
    } finally {
        loading.classList.add('hidden');
    }
}

/**
 * Renderiza resultados del interés compuesto
 */
function renderCompoundResults(result) {
    const container = document.getElementById('ci-results');

    const interestPercentage = result.interest_contribution_pct;
    const contributionPercentage = 100 - interestPercentage;

    let html = `
        <h3>⚡ El Poder del Interés Compuesto</h3>

        <div class="results-grid">
            <div class="result-card">
                <div class="label">Total Aportado</div>
                <div class="value">$${formatNumber(result.total_contributed)}</div>
                <div class="subvalue">Tu dinero</div>
            </div>
            <div class="result-card success">
                <div class="label">Valor Final</div>
                <div class="value">$${formatNumber(result.final_value)}</div>
                <div class="subvalue">Después de ${result.years} años</div>
            </div>
            <div class="result-card warning">
                <div class="label">Intereses Ganados</div>
                <div class="value">$${formatNumber(result.interest_earned)}</div>
                <div class="subvalue">${interestPercentage.toFixed(1)}% del total</div>
            </div>
        </div>

        <div class="chart-container">
            <h3>📊 Composición de tu riqueza final</h3>
            <div style="display: flex; gap: 1rem; margin-top: 1rem; height: 60px;">
                <div style="flex: ${contributionPercentage}; background: linear-gradient(135deg, #17a2b8, #0056b3); border-radius: 8px; display: flex; align-items: center; justify-content: center; color: white; font-weight: 700;">
                    ${contributionPercentage.toFixed(1)}% Aportes
                </div>
                <div style="flex: ${interestPercentage}; background: linear-gradient(135deg, #28a745, #20c997); border-radius: 8px; display: flex; align-items: center; justify-content: center; color: white; font-weight: 700;">
                    ${interestPercentage.toFixed(1)}% Interés
                </div>
            </div>
        </div>

        <div class="insights-section">
            <h3>💡 Insight clave</h3>
            <div class="insight-item">
                <span style="font-size: 2rem;">🎯</span>
                <div>
                    <strong>${result.message}</strong>
                    <p style="margin: 0.5rem 0 0 0; color: #6c757d;">
                        Aportaste $${formatNumber(result.total_contributed)}, pero el interés compuesto
                        generó $${formatNumber(result.interest_earned)} adicionales. ¡Esto es magia financiera!
                    </p>
                </div>
            </div>
            <div class="insight-item">
                <span style="font-size: 2rem;">⏰</span>
                <div>
                    <strong>El tiempo es tu mejor aliado</strong>
                    <p style="margin: 0.5rem 0 0 0; color: #6c757d;">
                        A ${result.annual_return_pct.toFixed(0)}% anual durante ${result.years} años,
                        tu dinero creció ${((result.final_value / result.total_contributed) - 1).toFixed(2)}x.
                        Cuanto más tiempo inviertas, mayor es el impacto del interés compuesto.
                    </p>
                </div>
            </div>
        </div>
    `;

    container.innerHTML = html;
    container.classList.remove('hidden');

    container.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

/**
 * Formatea números con separadores de miles
 */
function formatNumber(num) {
    if (num === null || num === undefined) return 'N/A';
    return new Intl.NumberFormat('en-US', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(num);
}
