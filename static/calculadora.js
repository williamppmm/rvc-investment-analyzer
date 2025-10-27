let selectedScenario = 'moderado';

document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initScenarioCards();
    initCalculators();
    initMoneyInputs();
});

function initTabs() {
    const tabs = document.querySelectorAll('.calc-tab');
    const sections = document.querySelectorAll('.calc-content');

    tabs.forEach((tab) => {
        tab.addEventListener('click', () => {
            const target = tab.getAttribute('data-tab');

            tabs.forEach((t) => t.classList.remove('active'));
            tab.classList.add('active');

            sections.forEach((section) => {
                section.classList.toggle('active', section.id === `${target}-content`);
            });
        });
    });
}

function initScenarioCards() {
    const cards = document.querySelectorAll('.scenario-card');

    cards.forEach((card) => {
        card.addEventListener('click', () => {
            cards.forEach((c) => c.classList.remove('selected'));
            card.classList.add('selected');
            selectedScenario = card.getAttribute('data-scenario') || 'moderado';
        });
    });
}

function initCalculators() {
    document.getElementById('calculate-retirement')?.addEventListener('click', calculateRetirement);
    document.getElementById('calculate-dca')?.addEventListener('click', calculateDCA);
    document.getElementById('calculate-lump-sum')?.addEventListener('click', calculateLumpSum);
    document.getElementById('calculate-compound')?.addEventListener('click', calculateCompound);

    // Toggle visibility del campo "número de simulaciones" según el modo
    document.getElementById('ci-mode')?.addEventListener('change', (e) => {
        const pathsGroup = document.getElementById('ci-paths-group');
        if (e.target.value === 'simulation') {
            pathsGroup.style.display = 'block';
        } else {
            pathsGroup.style.display = 'none';
        }
    });

    const fields = [
        'ret-current-age', 'ret-retirement-age', 'ret-initial', 'ret-monthly', 'ret-return', 'ret-inflation',
        'dca-initial', 'dca-monthly', 'dca-years', 'dca-inflation',
        'ls-total', 'ls-years',
        'ci-initial', 'ci-monthly', 'ci-years'
    ];

    fields.forEach((id) => {
        const el = document.getElementById(id);
        if (el) {
            el.addEventListener('keypress', (ev) => {
                if (ev.key === 'Enter') {
                    switch (true) {
                        case id.startsWith('ret-'):
                            calculateRetirement();
                            break;
                        case id.startsWith('dca-'):
                            calculateDCA();
                            break;
                        case id.startsWith('ls-'):
                            calculateLumpSum();
                            break;
                        case id.startsWith('ci-'):
                            calculateCompound();
                            break;
                        default:
                            break;
                    }
                }
            });
        }
    });
}

function initMoneyInputs() {
    const moneyIds = [
        'ret-initial', 'ret-monthly',
        'dca-initial', 'dca-monthly',
        'ls-total',
        'ci-initial', 'ci-monthly'
    ];
    moneyIds.forEach((id) => {
        const el = document.getElementById(id);
        if (!el) return;
        // Normalizar valor inicial a formato con miles (sin símbolos)
        const n = parseLocaleInt(el.value);
        el.value = formatPlain(n);
        // Formatear al salir del campo
        el.addEventListener('blur', () => {
            const val = parseLocaleInt(el.value);
            el.value = formatPlain(val);
        });
        // Limpiar caracteres no válidos durante la edición
        el.addEventListener('input', () => {
            const cleaned = el.value.replace(/[^0-9\.]/g, '');
            el.value = cleaned;
        });
    });
}

function parseLocaleInt(text) {
    if (text === undefined || text === null) return 0;
    const s = String(text).trim();
    if (!s) return 0;
    // es-CO: separador de miles '.'
    const normalized = s.replace(/\./g, '');
    const n = parseInt(normalized, 10);
    return Number.isFinite(n) ? n : 0;
}

function formatPlain(value) {
    const n = Number(value) || 0;
    return new Intl.NumberFormat('es-CO', { maximumFractionDigits: 0 }).format(n);
}

/**
 * Obtiene la tasa anual según el escenario
 * (fallback si el backend no envía annual_return)
 */
function rateFromScenario(scenario) {
    if (scenario === 'conservador') return 0.07;
    if (scenario === 'optimista') return 0.12;
    return 0.10; // moderado (default)
}

async function calculateDCA() {
    const initialAmount = parseLocaleInt(document.getElementById('dca-initial').value);
    const monthlyAmount = parseLocaleInt(document.getElementById('dca-monthly').value);
    const years = parseInt(document.getElementById('dca-years').value, 10);
    const inflationPct = parseFloat(document.getElementById('dca-inflation').value) || 0;
    const marketTiming = document.getElementById('dca-timing').value;
    const indexContributions = document.getElementById('dca-indexing')?.checked ?? true;

    if (initialAmount < 0 || monthlyAmount < 0) {
        alert('Los montos no pueden ser negativos.');
        return;
    }

    if (initialAmount === 0 && monthlyAmount === 0) {
        alert('Ingresa al menos un capital inicial o un aporte mensual.');
        return;
    }

    if (!years || years <= 0 || years > 50) {
        alert('El período debe estar entre 1 y 50 años.');
        return;
    }

    if (inflationPct < 0 || inflationPct > 15) {
        alert('La inflación anual debe estar entre 0% y 15%.');
        return;
    }

    const loading = document.getElementById('dca-loading');
    const results = document.getElementById('dca-results');

    loading.classList.remove('hidden');
    results.classList.add('hidden');

    try {
        const response = await fetch('/api/calcular-inversion', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                calculation_type: 'dca',
                initial_amount: initialAmount,
                monthly_amount: monthlyAmount,
                years,
                scenario: selectedScenario,
                market_timing: marketTiming,
                annual_inflation: inflationPct / 100,
                index_contributions_annually: indexContributions
            })
        });

        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || 'No se pudo calcular la proyección DCA.');
        }

        renderDCAResults(data.result);
    } catch (error) {
        alert(`Error: ${error.message}`);
    } finally {
        loading.classList.add('hidden');
    }
}

function renderDCAResults(result) {
    const container = document.getElementById('dca-results');
    const { input, results: res, breakdown, insights, monthly_simulation: timeline } = result;
    const baseline = res.baseline_projection || {};

    let html = `
        <h3>Resumen para el escenario ${capitalize(input.scenario)} (${input.expected_annual_return}% anual)</h3>
        <div class="results-grid">
            <div class="result-card success">
                <div class="label">Capital final</div>
                <div class="value">${formatMoney(res.final_value)}</div>
                <div class="subvalue">${res.cap_reached ? `Límite de ${formatMoney(1000000)} alcanzado` : input.market_timing_label}</div>
            </div>
            <div class="result-card">
                <div class="label">Aportes totales (incluye capital inicial)</div>
                <div class="value">${formatMoney(res.total_invested)}</div>
                <div class="subvalue">${input.effective_months} de ${input.total_months_planned} meses planificados</div>
            </div>
            <div class="result-card info">
                <div class="label">Ganancia generada</div>
                <div class="value">${formatMoney(res.total_gain)}</div>
                <div class="subvalue">${formatPercent(res.total_return_pct)} sobre lo aportado</div>
            </div>
        </div>
    `;

    // Bloque "Nominal vs Hoy" (poder adquisitivo)
    const inflationPct = input.annual_inflation_pct || 0;
    const years = input.years || 0;
    if (inflationPct > 0 && years > 0) {
        const realValue = calculateRealValue(res.final_value, years, inflationPct);
        html += `
            <div class="chart-container" style="background: #f8f9fa; border-left: 4px solid #4a8fe3;">
                <h3>💡 Nominal vs Poder Adquisitivo</h3>
                <div class="results-grid" style="margin-bottom: 0;">
                    <div class="result-card" style="background: linear-gradient(135deg, #4a8fe3, #175499);">
                        <div class="label">Capital final (nominal)</div>
                        <div class="value">${formatMoney(res.final_value)}</div>
                        <div class="subvalue">Valor en dólares del futuro</div>
                    </div>
                    <div class="result-card" style="background: linear-gradient(135deg, #28a745, #20c997);">
                        <div class="label">Equivalente hoy</div>
                        <div class="value">${formatMoney(realValue)}</div>
                        <div class="subvalue">Poder adquisitivo actual</div>
                    </div>
                </div>
                <p style="margin-top: 1rem; margin-bottom: 0; color: #6c757d; font-size: 0.9rem;">
                    Con inflación de ${formatPercent(inflationPct)} anual por ${years} años, 
                    ${formatMoney(res.final_value)} equivale a ${formatMoney(realValue)} en poder de compra actual.
                    ${input.index_contributions_annually !== false 
                        ? 'Como activaste la indexación anual, tus aportes crecen con la inflación manteniendo tu esfuerzo real constante.' 
                        : 'Sin indexación anual, tus aportes pierden poder adquisitivo cada año.'}
                </p>
            </div>
        `;
    }

    html += `
        <div class="chart-container">
            <h3>Proyección base vs simulación con timing</h3>
            <p style="margin-bottom: 1rem;">
                Proyección lineal sin volatilidad: ${formatMoney(res.simple_projection)}. 
                Con ajuste por inflación e interés compuesto: ${formatMoney(baseline.final_value || 0)} 
                (${formatPercent(baseline.return_pct)} retorno). 
                La simulación con timing y precio variable termina en ${formatMoney(res.final_value)}.
            </p>
        </div>
    `;

    const milestones = Object.values(breakdown || {}).filter(Boolean).sort((a, b) => (a.years || 0) - (b.years || 0));
    if (milestones.length) {
        html += `
            <div class="chart-container">
                <div id="chart-dca-milestones" style="width: 100%; height: 400px;"></div>
            </div>
        `;
    }

    if (timeline && timeline.length) {
        const snapshots = pickTimelineSnapshots(timeline);
        html += `
            <div class="yearly-table">
                <table>
                    <thead>
                        <tr>
                            <th>Mes</th>
                            <th>Aporte del mes</th>
                            <th>Aportes acumulados</th>
                            <th>Valor del portafolio</th>
                            <th>Rentabilidad acumulada</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        // Asegurar orden ascendente por mes
        snapshots.sort((a, b) => (a.month || 0) - (b.month || 0)).forEach((row) => {
            html += `
                <tr>
                    <td>${row.month}</td>
                    <td>${formatMoney(row.monthly_contribution)}</td>
                    <td>${formatMoney(row.invested_to_date)}</td>
                    <td>${formatMoney(row.portfolio_value)}</td>
                    <td>${formatPercent(row.return_pct)}</td>
                </tr>
            `;
        });
        html += `
                    </tbody>
                </table>
            </div>
        `;

        // Tabla anual agregada
        const yearlyData = aggregateMonthlyToYearly(timeline, inflationPct);
        if (yearlyData.length > 0) {
            html += `
                <div class="yearly-table" style="margin-top: 2rem;">
                    <h3>📊 Resumen Anual</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>Año</th>
                                <th>Aportes del año</th>
                                <th>Aportes acumulados</th>
                                <th>Valor nominal</th>
                                ${inflationPct > 0 ? '<th>Valor real (hoy)</th>' : ''}
                                <th>Rentabilidad</th>
                            </tr>
                        </thead>
                        <tbody>
            `;
            yearlyData.forEach((row) => {
                html += `
                    <tr>
                        <td>${row.year}</td>
                        <td>${formatMoney(row.contributions)}</td>
                        <td>${formatMoney(row.invested)}</td>
                        <td>${formatMoney(row.portfolioValue)}</td>
                        ${inflationPct > 0 ? `<td>${formatMoney(row.portfolioValueReal || 0)}</td>` : ''}
                        <td>${formatPercent(row.returnPct)}</td>
                    </tr>
                `;
            });
            html += `
                        </tbody>
                    </table>
                    ${inflationPct > 0 ? `
                    <p style="margin-top: 1rem; color: #6c757d; font-size: 0.9rem;">
                        💡 <strong>Valor real (hoy)</strong>: muestra el poder adquisitivo del portafolio expresado en dólares de hoy, 
                        descontando el efecto de la inflación del ${formatPercent(inflationPct)} anual.
                    </p>
                    ` : ''}
                </div>
            `;
        }
    }

    if (res.cap_reached) {
        html += `
            <div class="insights-section" style="margin-top: 2rem;">
                <h3>Límite alcanzado</h3>
                <div class="insight-item">
                    <strong>Meta de ${formatMoney(1000000)}</strong>
                    <p style="margin: 0;">
                        Llegaste al límite en el mes ${res.cap_reached.month} (${res.cap_reached.years_elapsed} años). 
                        A partir de ahí dejamos de sumar aportes para evitar resultados irreales.
                    </p>
                </div>
            </div>
        `;
    }

    if (insights && insights.length) {
        html += `<div class="insights-section" style="margin-top: 2rem;"><h3>Ideas clave</h3>`;
        insights.forEach((item) => {
            html += `
                <div class="insight-item">
                    <strong>Dato</strong>
                    <p style="margin: 0;">${item}</p>
                </div>
            `;
        });
        html += `</div>`;
    }

    container.innerHTML = html;
    container.classList.remove('hidden');

    // Renderizar gráfico de hitos DCA si existen
    if (milestones.length) {
        setTimeout(() => {
            const milestonesData = milestones.map(m => ({
                year: m.years,
                amount: m.value,
                gain: m.gain
            }));
            createDCAMilestonesChart(milestonesData);
        }, 100);
    }

    container.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

async function calculateLumpSum() {
    const totalAmount = parseLocaleInt(document.getElementById('ls-total').value);
    const years = parseInt(document.getElementById('ls-years').value, 10);
    const scenario = document.getElementById('ls-scenario').value;

    if (!totalAmount || totalAmount <= 0) {
        alert('Ingresa un monto total positivo.');
        return;
    }

    if (!years || years <= 0 || years > 50) {
        alert('El período debe estar entre 1 y 50 años.');
        return;
    }

    const loading = document.getElementById('ls-loading');
    const results = document.getElementById('ls-results');

    loading.classList.remove('hidden');
    results.classList.add('hidden');

    try {
        const response = await fetch('/api/calcular-inversion', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                calculation_type: 'lump_sum_vs_dca',
                total_amount: totalAmount,
                years,
                scenario
            })
        });

        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || 'No se pudo realizar la comparación.');
        }

        renderLumpSumResults(data.result);
    } catch (error) {
        alert(`Error: ${error.message}`);
    } finally {
        loading.classList.add('hidden');
    }
}

function renderLumpSumResults(result) {
    const container = document.getElementById('ls-results');
    const { lump_sum: lump, dca, comparison } = result;

    let html = `
    <h3>Resultados para ${result.years} años (${capitalize(result.scenario)})</h3>
        <div class="results-grid" style="margin-bottom: 2rem;">
            <div class="result-card ${comparison.winner === 'Lump Sum' ? 'success' : ''}">
                <div class="label">${lump.strategy}</div>
                <div class="value">${formatMoney(lump.final_value)}</div>
                <div class="subvalue">Ganancia: ${formatMoney(lump.total_gain)} (${formatPercent(lump.return_pct)})</div>
            </div>
            <div class="result-card ${comparison.winner === 'DCA' ? 'success' : ''}">
                <div class="label">${dca.strategy}</div>
                <div class="value">${formatMoney(dca.final_value)}</div>
                <div class="subvalue">Ganancia: ${formatMoney(dca.total_gain)} (${formatPercent(dca.return_pct)})</div>
            </div>
        </div>

        <!-- Gráfico 1: Evolución del valor (Lump Sum vs DCA) -->
        <div class="chart-container">
            <div id="chart-ls-vs-dca-evolution" style="width: 100%; height: 450px;"></div>
        </div>

        <!-- Gráfico 2: Composición final (Aportes vs Intereses) -->
        <div class="chart-container">
            <div id="chart-ls-vs-dca-composition" style="width: 100%; height: 400px;"></div>
        </div>

        <div class="insights-section" style="margin-top: 2rem;">
            <h3>Recomendación</h3>
            <div class="insight-item">
                <strong>${comparison.winner} aventaja por ${formatMoney(comparison.difference)} (${formatPercent(comparison.difference_pct)})</strong>
            </div>
            <div class="insight-item">
                <p style="margin: 0;">${comparison.recommendation}</p>
            </div>
        </div>
    `;

    container.innerHTML = html;
    container.classList.remove('hidden');

    // Renderizar gráficos Plotly
    setTimeout(() => {
        createLumpSumVsDCACharts(result);
    }, 100);

    container.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

async function calculateCompound() {
    const initialAmount = parseLocaleInt(document.getElementById('ci-initial').value);
    const monthlyContribution = parseLocaleInt(document.getElementById('ci-monthly').value);
    const years = parseInt(document.getElementById('ci-years').value, 10);
    const scenario = document.getElementById('ci-scenario').value;
    const mode = document.getElementById('ci-mode').value;
    const numPaths = parseInt(document.getElementById('ci-paths').value, 10) || 5;

    if (initialAmount < 0 || monthlyContribution < 0) {
        alert('Los montos no pueden ser negativos.');
        return;
    }

    if (initialAmount === 0 && monthlyContribution === 0) {
        alert('Ingresa al menos un monto inicial o una contribución mensual.');
        return;
    }

    if (!years || years <= 0 || years > 50) {
        alert('El período debe estar entre 1 y 50 años.');
        return;
    }

    const loading = document.getElementById('ci-loading');
    const results = document.getElementById('ci-results');

    loading.classList.remove('hidden');
    results.classList.add('hidden');

    try {
        const payload = {
            calculation_type: 'compound_interest',
            initial_amount: initialAmount,
            monthly_amount: monthlyContribution,
            years,
            scenario,
            mode
        };

        if (mode === 'simulation') {
            payload.num_paths = Math.min(Math.max(numPaths, 1), 20);
        }

        const response = await fetch('/api/calcular-inversion', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || 'No se pudo calcular el interés compuesto.');
        }

        renderCompoundResults(data.result);
    } catch (error) {
        alert(`Error: ${error.message}`);
    } finally {
        loading.classList.add('hidden');
    }
}

function renderCompoundResults(result) {
    const container = document.getElementById('ci-results');
    const mode = result.mode || 'deterministic';
    
    let html = '';

    if (mode === 'deterministic') {
        // Modo determinista (fórmula pura)
        const interestPct = result.interest_contribution_pct;
        const aportesPct = 100 - interestPct;

        html = `
        <h3>📐 Modo determinista: ${result.annual_return_pct}% anual</h3>
            <div class="results-grid">
                <div class="result-card">
                    <div class="label">Aportes totales</div>
                    <div class="value">${formatMoney(result.total_contributed)}</div>
                    <div class="subvalue">Capital propio acumulado</div>
                </div>
                <div class="result-card success">
                    <div class="label">Valor final</div>
                    <div class="value">${formatMoney(result.final_value)}</div>
                    <div class="subvalue">Después de ${result.years} años</div>
                </div>
                <div class="result-card warning">
                    <div class="label">Intereses generados</div>
                    <div class="value">${formatMoney(result.interest_earned)}</div>
                    <div class="subvalue">${formatPercent(interestPct)} del total</div>
                </div>
            </div>

            <div class="chart-container" style="margin-top: 2rem;">
                <div id="chart-compound-deterministic" style="width: 100%; height: 450px;"></div>
            </div>

            <div class="chart-container" style="margin-top: 2rem;">
                <h3>Desglose de aportes vs intereses</h3>
                <div style="display: flex; gap: 1rem; margin-top: 1rem; height: 60px;">
                    <div style="flex: ${aportesPct}; background: linear-gradient(135deg, #f59e0b, #d97706); border-radius: 8px; display: flex; align-items: center; justify-content: center; color: white; font-weight: 700;">
                        ${formatPercent(aportesPct)} aportes
                    </div>
                    <div style="flex: ${interestPct}; background: linear-gradient(135deg, #3b82f6, #2563eb); border-radius: 8px; display: flex; align-items: center; justify-content: center; color: white; font-weight: 700;">
                        ${formatPercent(interestPct)} intereses
                    </div>
                </div>
            </div>
        `;

        if (result.cap_reached) {
            html += `
                <div class="insights-section" style="margin-top: 2rem;">
                    <h3>🎯 Límite alcanzado</h3>
                    <div class="insight-item">
                        <p style="margin: 0;">El cálculo se detuvo al llegar a ${formatMoney(1000000)} para mantener cifras realistas.</p>
                    </div>
                </div>
            `;
        }

        html += `
            <div class="insights-section" style="margin-top: 2rem;">
                <h3>💡 Lecturas clave</h3>
                <div class="insight-item">
                    <strong>Mensaje</strong>
                    <p style="margin: 0;">${result.message}</p>
                </div>
                <div class="insight-item">
                    <strong>Multiplicador</strong>
                    <p style="margin: 0;">Tu capital final es ${(result.final_value / result.total_contributed).toFixed(2)}x lo aportado.</p>
                </div>
            </div>
        `;

    } else {
        // Modo simulación (con volatilidad)
        const avgInterestPct = result.avg_interest_contribution_pct;
        const avgAportesPct = 100 - avgInterestPct;

        html = `
        <h3>📊 Modo simulación: ${result.annual_return_pct}% anual ± ${result.volatility_pct}% vol</h3>
            <div class="results-grid">
                <div class="result-card">
                    <div class="label">Promedio final</div>
                    <div class="value">${formatMoney(result.avg_final_value)}</div>
                    <div class="subvalue">De ${result.num_paths} simulaciones</div>
                </div>
                <div class="result-card warning">
                    <div class="label">Rango de resultados</div>
                    <div class="value">${formatMoney(result.min_final_value)} - ${formatMoney(result.max_final_value)}</div>
                    <div class="subvalue">Variación ±${formatPercent(result.range_pct / 2)}</div>
                </div>
                <div class="result-card success">
                    <div class="label">Intereses promedio</div>
                    <div class="value">${formatMoney(result.avg_interest_earned)}</div>
                    <div class="subvalue">${formatPercent(avgInterestPct)} del total</div>
                </div>
            </div>

            <div class="chart-container">
                <div id="chart-compound-simulation" style="width: 100%; height: 500px;"></div>
            </div>

            <div class="chart-container" style="margin-top: 2rem;">
                <h3>Desglose promedio: aportes vs intereses</h3>
                <div style="display: flex; gap: 1rem; margin-top: 1rem; height: 60px;">
                    <div style="flex: ${avgAportesPct}; background: linear-gradient(135deg, #f59e0b, #d97706); border-radius: 8px; display: flex; align-items: center; justify-content: center; color: white; font-weight: 700;">
                        ${formatPercent(avgAportesPct)} aportes
                    </div>
                    <div style="flex: ${avgInterestPct}; background: linear-gradient(135deg, #3b82f6, #2563eb); border-radius: 8px; display: flex; align-items: center; justify-content: center; color: white; font-weight: 700;">
                        ${formatPercent(avgInterestPct)} intereses
                    </div>
                </div>
            </div>

            <div class="insights-section" style="margin-top: 2rem;">
                <h3>💡 Interpretación</h3>
                <div class="insight-item">
                    <strong>Mensaje</strong>
                    <p style="margin: 0;">${result.message}</p>
                </div>
                <div class="insight-item">
                    <strong>Volatilidad</strong>
                    <p style="margin: 0;">Con ${result.volatility_pct}% de volatilidad (${result.scenario}), los resultados pueden variar significativamente según el orden de retornos mensuales.</p>
                </div>
            </div>
        `;
    }

    container.innerHTML = html;
    container.classList.remove('hidden');

    // Renderizar gráfico según el modo
    if (mode === 'simulation') {
        setTimeout(() => {
            createCompoundSimulationChart(result);
        }, 100);
    } else if (mode === 'deterministic' && result.yearly_series && result.yearly_series.length > 0) {
        setTimeout(() => {
            createCompoundDeterministicChart(result);
        }, 100);
    }

    container.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

async function calculateRetirement() {
    const currentAge = parseInt(document.getElementById('ret-current-age').value, 10);
    const retirementAge = parseInt(document.getElementById('ret-retirement-age').value, 10);
    const initialAmount = parseLocaleInt(document.getElementById('ret-initial').value);
    const monthlyAmount = parseLocaleInt(document.getElementById('ret-monthly').value);
    const annualReturnPct = parseFloat(document.getElementById('ret-return').value) || 0;
    const annualInflationPct = parseFloat(document.getElementById('ret-inflation').value) || 0;
    const indexContributions = document.getElementById('ret-indexing')?.checked ?? true;

    if (!currentAge || currentAge < 18 || currentAge > 75) {
        alert('La edad actual debe estar entre 18 y 75 años.');
        return;
    }

    if (!retirementAge || retirementAge <= currentAge || retirementAge > 75) {
        alert('La edad de retiro debe ser mayor a la actual y no superar 75 años.');
        return;
    }

    if (initialAmount < 0 || monthlyAmount < 0) {
        alert('Los montos no pueden ser negativos.');
        return;
    }

    if (annualReturnPct < -10 || annualReturnPct > 20) {
        alert('El rendimiento anual debe estar entre -10% y 20%.');
        return;
    }

    if (annualInflationPct < 0 || annualInflationPct > 15) {
        alert('La inflación debe estar entre 0% y 15%.');
        return;
    }

    const loading = document.getElementById('ret-loading');
    const results = document.getElementById('ret-results');

    loading.classList.remove('hidden');
    results.classList.add('hidden');

    try {
        const response = await fetch('/api/calcular-inversion', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                calculation_type: 'retirement_plan',
                current_age: currentAge,
                retirement_age: retirementAge,
                initial_amount: initialAmount,
                monthly_amount: monthlyAmount,
                scenario: 'moderado',
                annual_inflation: annualInflationPct / 100,
                annual_return_override: annualReturnPct / 100,
                index_contributions_annually: indexContributions
            })
        });

        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || 'No se pudo calcular el plan.');
        }

        renderRetirementResults(data.result);
    } catch (error) {
        alert(`Error: ${error.message}`);
    } finally {
        loading.classList.add('hidden');
    }
}

function renderRetirementResults(result) {
    const container = document.getElementById('ret-results');
    const { input, results: res, scenarios, yearly_projections: yearly, milestones, composition, limit } = result;

    let html = `
    <h3>Meta a los ${input.retirement_age} años (horizonte ${input.years_to_retirement} años)</h3>
        <div class="results-grid">
            <div class="result-card success">
                <div class="label">Capital proyectado</div>
                <div class="value">${formatMoney(res.final_capital)}</div>
                <div class="subvalue">${formatPercent(res.average_return_pct)} anual esperado</div>
            </div>
            <div class="result-card">
                <div class="label">Capital inicial</div>
                <div class="value">${formatMoney(res.initial_capital)}</div>
                <div class="subvalue">Punto de partida</div>
            </div>
            <div class="result-card info">
                <div class="label">Aportes durante el plan</div>
                <div class="value">${formatMoney(res.total_contributions)}</div>
                <div class="subvalue">${input.effective_years} años efectivos de ahorro</div>
            </div>
            <div class="result-card warning">
                <div class="label">Intereses generados</div>
                <div class="value">${formatMoney(res.total_interest)}</div>
                <div class="subvalue">${formatPercent(composition.interest_pct)} del total</div>
            </div>
        </div>
    `;

    // Bloque "Nominal vs Hoy" (poder adquisitivo)
    const inflationPct = (input.annual_inflation || 0) * 100;
    const years = input.years_to_retirement || 0;
    if (inflationPct > 0 && years > 0) {
        const realValue = calculateRealValue(res.final_capital, years, inflationPct);
        html += `
            <div class="chart-container" style="background: #f8f9fa; border-left: 4px solid #4a8fe3;">
                <h3>💡 Nominal vs Poder Adquisitivo</h3>
                <div class="results-grid" style="margin-bottom: 0;">
                    <div class="result-card" style="background: linear-gradient(135deg, #4a8fe3, #175499);">
                        <div class="label">Capital proyectado (nominal)</div>
                        <div class="value">${formatMoney(res.final_capital)}</div>
                        <div class="subvalue">Valor a los ${input.retirement_age} años</div>
                    </div>
                    <div class="result-card" style="background: linear-gradient(135deg, #28a745, #20c997);">
                        <div class="label">Equivalente hoy</div>
                        <div class="value">${formatMoney(realValue)}</div>
                        <div class="subvalue">Poder adquisitivo actual</div>
                    </div>
                </div>
                <p style="margin-top: 1rem; margin-bottom: 0; color: #6c757d; font-size: 0.9rem;">
                    Con inflación de ${formatPercent(inflationPct)} anual por ${years} años, 
                    ${formatMoney(res.final_capital)} equivale a ${formatMoney(realValue)} en poder de compra actual.
                    ${input.index_contributions_annually !== false 
                        ? 'Como activaste la indexación anual, tus aportes crecen con la inflación manteniendo tu esfuerzo real constante.' 
                        : 'Sin indexación anual, tus aportes pierden poder adquisitivo cada año.'}
                </p>
            </div>
        `;
    }

    // GRÁFICOS MODERNOS PLOTLY
    if (yearly && yearly.length) {
        // Preparar datos para los gráficos
        const yearLabels = yearly.map(row => row.year);
        const ageLabels = yearly.map(row => row.age);
        const nominalValues = yearly.map(row => row.portfolio_value);
        const realValues = inflationPct > 0 ? yearly.map(row => calculateRealValue(row.portfolio_value, row.year, inflationPct)) : [];
        const annualContributions = yearly.map(row => row.annual_contribution);
        const annualInterest = yearly.map(row => row.interest_this_year);
        const cumulativeContributions = yearly.map(row => row.contributions_accumulated);
        const cumulativeInterest = yearly.map(row => row.interest_accumulated);

        // Gráfico 1: Evolución del capital (nominal vs real)
        if (inflationPct > 0) {
            html += `
                <div class="chart-container">
                    <div id="chart-nominal-vs-real" style="width: 100%; height: 450px;"></div>
                </div>
            `;
        }

        // Gráfico 2: Desglose anual (barras apiladas)
        html += `
            <div class="chart-container">
                <div id="chart-annual-breakdown" style="width: 100%; height: 450px;"></div>
            </div>
        `;

        // Gráfico 3: Acumulados (líneas de área)
        html += `
            <div class="chart-container">
                <div id="chart-cumulative" style="width: 100%; height: 450px;"></div>
            </div>
        `;
    }

    html += `
        <div class="chart-container">
            <h3>Escenarios de rendimiento</h3>
            <table class="comparison-table">
                <thead>
                    <tr>
                        <th>Escenario</th>
                        <th>Capital final</th>
                        <th>Aportes</th>
                        <th>Intereses</th>
                        <th>Retorno %</th>
                    </tr>
                </thead>
                <tbody>
    `;

    ['conservador', 'realista', 'optimista'].forEach((key) => {
        const scenario = scenarios[key];
        if (!scenario) {
            return;
        }
        html += `
            <tr>
                <td>${capitalize(key)}</td>
                <td>${formatMoney(scenario.final_value)}</td>
                <td>${formatMoney(scenario.total_contributions)}</td>
                <td>${formatMoney(scenario.total_interest)}</td>
                <td>${formatPercent(scenario.return_pct)}</td>
            </tr>
        `;
    });

    html += `
                </tbody>
            </table>
        </div>
    `;

    if (limit && limit.reached && limit.details) {
        html += `
            <div class="insights-section">
                <h3>Límite alcanzado</h3>
                <div class="insight-item">
                    <strong>Meta de ${formatMoney(1000000)}</strong>
                    <p style="margin: 0;">
                        El plan alcanza el límite a los ${limit.details.year} años (edad ${limit.details.age}). 
                        A partir de ese punto dejamos de sumar aportes para mantener proyecciones realistas.
                    </p>
                </div>
            </div>
        `;
    }

    if (milestones && milestones.length) {
        html += `
            <div class="chart-container">
                <div id="chart-milestones" style="width: 100%; height: 400px;"></div>
            </div>
        `;
    }

    if (yearly && yearly.length) {
        html += `
            <div class="yearly-table">
                <h3>📊 Proyección Anual Detallada</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Año (edad)</th>
                            <th>Aporte anual</th>
                            <th>Aportes acumulados</th>
                            <th>Interés del año</th>
                            <th>Interes acumulado</th>
                            <th>Capital total (nominal)</th>
                            ${inflationPct > 0 ? '<th>Capital real (hoy)</th>' : ''}
                        </tr>
                    </thead>
                    <tbody>
        `;

        yearly.forEach((row) => {
            const realValue = inflationPct > 0 ? calculateRealValue(row.portfolio_value, row.year, inflationPct) : null;
            html += `
                <tr>
                    <td>${row.year} (${row.age})</td>
                    <td>${formatMoney(row.annual_contribution)}</td>
                    <td>${formatMoney(row.contributions_accumulated)}</td>
                    <td>${formatMoney(row.interest_this_year)}</td>
                    <td>${formatMoney(row.interest_accumulated)}</td>
                    <td>${formatMoney(row.portfolio_value)}</td>
                    ${inflationPct > 0 ? `<td>${formatMoney(realValue || 0)}</td>` : ''}
                </tr>
            `;
        });

        html += `
                    </tbody>
                </table>
                ${inflationPct > 0 ? `
                <p style="margin-top: 1rem; color: #6c757d; font-size: 0.9rem;">
                    💡 <strong>Capital real (hoy)</strong>: muestra el poder adquisitivo del portafolio expresado en dólares de hoy, 
                    descontando el efecto de la inflación del ${formatPercent(inflationPct)} anual.
                </p>
                ` : ''}
            </div>
        `;
    }

    container.innerHTML = html;
    container.classList.remove('hidden');

    // Renderizar gráficos Plotly después de insertar el HTML
    if (yearly && yearly.length) {
        const yearLabels = yearly.map(row => row.year);
        const nominalValues = yearly.map(row => row.portfolio_value);
        const realValues = inflationPct > 0 ? yearly.map(row => calculateRealValue(row.portfolio_value, row.year, inflationPct)) : [];
        const annualContributions = yearly.map(row => row.annual_contribution);
        const annualInterest = yearly.map(row => row.interest_this_year);
        const cumulativeContributions = yearly.map(row => row.contributions_accumulated);
        const cumulativeInterest = yearly.map(row => row.interest_accumulated);

        // Gráfico 1: Nominal vs Real
        if (inflationPct > 0) {
            setTimeout(() => {
                createNominalVsRealChart(yearLabels, nominalValues, realValues);
            }, 100);
        }

        // Gráfico 2: Desglose anual
        setTimeout(() => {
            createAnnualBreakdownChart(yearLabels, annualContributions, annualInterest);
        }, 100);

        // Gráfico 3: Acumulados
        setTimeout(() => {
            createCumulativeChart(yearLabels, cumulativeContributions, cumulativeInterest);
        }, 100);
    }

    // Gráfico 4: Hitos (si existen)
    if (milestones && milestones.length) {
        setTimeout(() => {
            createMilestonesChart(milestones, yearly);
        }, 100);
    }

    container.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function pickTimelineSnapshots(timeline) {
    if (timeline.length <= 6) {
        return timeline;
    }
    const last = timeline[timeline.length - 1];
    const first = timeline[0];
    const midIndex = Math.max(1, Math.floor(timeline.length / 2));
    const twelfth = timeline[Math.min(11, timeline.length - 1)];

    const unique = [first, timeline[midIndex], twelfth, last];
    const seen = new Set();
    const filtered = unique.filter((item) => {
        if (!item) return false;
        if (seen.has(item.month)) return false;
        seen.add(item.month);
        return true;
    });
    // Orden ascendente por mes para presentación
    return filtered.sort((a, b) => (a.month || 0) - (b.month || 0));
}

function formatNumber(value) {
    if (value === undefined || value === null || Number.isNaN(value)) {
        return '0';
    }
    return new Intl.NumberFormat('es-CO', { maximumFractionDigits: 0 }).format(value);
}

function formatPercent(value) {
    if (value === undefined || value === null || Number.isNaN(value)) {
        return '0%';
    }
    return `${new Intl.NumberFormat('es-CO', { maximumFractionDigits: 1 }).format(value)}%`;
}

function capitalize(text) {
    if (!text) {
        return '';
    }
    return text.charAt(0).toUpperCase() + text.slice(1);
}

function formatMoney(value) {
    // Calculadora: formatear con símbolo $ y separadores de miles
    const amount = Number(value) || 0;
    return '$' + new Intl.NumberFormat('es-CO', { maximumFractionDigits: 0 }).format(amount);
}

/**
 * Agrega datos mensuales en una tabla anual.
 * Retorna un array con un elemento por año, sumando aportes y tomando el último valor del año.
 */
function aggregateMonthlyToYearly(monthlyTimeline, annualInflationPct = 0) {
    if (!monthlyTimeline || monthlyTimeline.length === 0) {
        return [];
    }

    const yearlyData = {};
    const inflationRate = annualInflationPct / 100;

    monthlyTimeline.forEach(row => {
        const year = Math.floor((row.month - 1) / 12) + 1;
        
        if (!yearlyData[year]) {
            yearlyData[year] = {
                year: year,
                contributions: 0,
                portfolioValue: 0,
                invested: 0,
                returnPct: 0
            };
        }

        // Sumar contribuciones del año
        yearlyData[year].contributions += row.monthly_contribution || 0;
        // Tomar el último valor del año (se sobrescribe)
        yearlyData[year].portfolioValue = row.portfolio_value || 0;
        yearlyData[year].invested = row.invested_to_date || 0;
        yearlyData[year].returnPct = row.return_pct || 0;
    });

    // Convertir a array y calcular valores reales
    const result = Object.values(yearlyData).map(item => {
        let realValue = null;
        if (inflationRate > 0 && item.year > 0) {
            const deflationFactor = Math.pow(1 + inflationRate, item.year);
            realValue = item.portfolioValue / deflationFactor;
        }
        return {
            ...item,
            portfolioValueReal: realValue
        };
    });

    return result.sort((a, b) => a.year - b.year);
}

/**
 * Calcula el valor real (deflactado) desde un valor nominal.
 * Formula: valor_real = valor_nominal / (1 + inflacion)^(meses/12)
 */
function calculateRealValue(nominalValue, years, annualInflationPct) {
    if (!annualInflationPct || annualInflationPct === 0) {
        return nominalValue;
    }
    const inflationRate = annualInflationPct / 100;
    const realValue = nominalValue / Math.pow(1 + inflationRate, years);
    return realValue;
}

// ============================================
// GRÁFICOS PLOTLY MODERNOS - PLAN DE JUBILACIÓN
// ============================================

/**
 * Gráfico 1: Evolución del capital (nominal vs real)
 */
function createNominalVsRealChart(yearLabels, nominalValues, realValues) {
    const trace1 = {
        x: yearLabels,
        y: nominalValues,
        type: 'scatter',
        mode: 'lines',
        name: 'Capital nominal',
        line: {
            color: '#f59e0b',
            width: 3
        },
        hovertemplate: '<b>Año %{x}</b><br>Nominal: $%{y:,.0f}<extra></extra>'
    };

    const trace2 = {
        x: yearLabels,
        y: realValues,
        type: 'scatter',
        mode: 'lines',
        name: 'Capital real (hoy)',
        line: {
            color: '#3b82f6',
            width: 3
        },
        hovertemplate: '<b>Año %{x}</b><br>Real: $%{y:,.0f}<extra></extra>'
    };

    const layout = {
        title: {
            text: 'Evolución del capital: nominal vs equivalente en dólares de hoy',
            font: { size: 16, color: '#1f2937' }
        },
        xaxis: {
            title: 'Año',
            gridcolor: '#e5e7eb',
            showgrid: true
        },
        yaxis: {
            title: 'USD',
            gridcolor: '#e5e7eb',
            showgrid: true,
            tickformat: ',.0f'
        },
        legend: {
            x: 0.02,
            y: 0.98,
            bgcolor: 'rgba(255,255,255,0.8)',
            bordercolor: '#d1d5db',
            borderwidth: 1
        },
        hovermode: 'x unified',
        plot_bgcolor: '#ffffff',
        paper_bgcolor: '#ffffff',
        margin: { t: 60, b: 60, l: 80, r: 40 }
    };

    const config = {
        responsive: true,
        displayModeBar: true,
        displaylogo: false,
        modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d']
    };

    Plotly.newPlot('chart-nominal-vs-real', [trace1, trace2], layout, config);
}

/**
 * Gráfico 2: Desglose anual (aporte vs interés generado)
 */
function createAnnualBreakdownChart(yearLabels, annualContributions, annualInterest) {
    const trace1 = {
        x: yearLabels,
        y: annualContributions,
        type: 'bar',
        name: 'Aporte anual',
        marker: {
            color: '#f59e0b'
        },
        hovertemplate: '<b>Año %{x}</b><br>Aporte: $%{y:,.0f}<extra></extra>'
    };

    const trace2 = {
        x: yearLabels,
        y: annualInterest,
        type: 'bar',
        name: 'Interés del año',
        marker: {
            color: '#3b82f6'
        },
        hovertemplate: '<b>Año %{x}</b><br>Interés: $%{y:,.0f}<extra></extra>'
    };

    const layout = {
        title: {
            text: 'Desglose anual: aporte vs interés generado',
            font: { size: 16, color: '#1f2937' }
        },
        xaxis: {
            title: 'Año',
            gridcolor: '#e5e7eb'
        },
        yaxis: {
            title: 'USD',
            gridcolor: '#e5e7eb',
            showgrid: true,
            tickformat: ',.0f'
        },
        barmode: 'stack',
        legend: {
            x: 0.02,
            y: 0.98,
            bgcolor: 'rgba(255,255,255,0.8)',
            bordercolor: '#d1d5db',
            borderwidth: 1
        },
        hovermode: 'x unified',
        plot_bgcolor: '#ffffff',
        paper_bgcolor: '#ffffff',
        margin: { t: 60, b: 60, l: 80, r: 40 }
    };

    const config = {
        responsive: true,
        displayModeBar: true,
        displaylogo: false,
        modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d']
    };

    Plotly.newPlot('chart-annual-breakdown', [trace1, trace2], layout, config);
}

/**
 * Gráfico 3: Acumulados (aportes vs intereses)
 */
function createCumulativeChart(yearLabels, cumulativeContributions, cumulativeInterest) {
    const trace1 = {
        x: yearLabels,
        y: cumulativeContributions,
        type: 'scatter',
        mode: 'lines',
        name: 'Aportes acumulados',
        fill: 'tonexty',
        line: {
            color: '#f59e0b',
            width: 2
        },
        fillcolor: 'rgba(245, 158, 11, 0.3)',
        hovertemplate: '<b>Año %{x}</b><br>Aportes: $%{y:,.0f}<extra></extra>'
    };

    const trace2 = {
        x: yearLabels,
        y: cumulativeInterest,
        type: 'scatter',
        mode: 'lines',
        name: 'Interés acumulado',
        fill: 'tozeroy',
        line: {
            color: '#3b82f6',
            width: 2
        },
        fillcolor: 'rgba(59, 130, 246, 0.3)',
        hovertemplate: '<b>Año %{x}</b><br>Interés: $%{y:,.0f}<extra></extra>'
    };

    const layout = {
        title: {
            text: 'Acumulados: aportes vs intereses',
            font: { size: 16, color: '#1f2937' }
        },
        xaxis: {
            title: 'Año',
            gridcolor: '#e5e7eb',
            showgrid: true
        },
        yaxis: {
            title: 'USD',
            gridcolor: '#e5e7eb',
            showgrid: true,
            tickformat: ',.0f'
        },
        legend: {
            x: 0.02,
            y: 0.98,
            bgcolor: 'rgba(255,255,255,0.8)',
            bordercolor: '#d1d5db',
            borderwidth: 1
        },
        hovermode: 'x unified',
        plot_bgcolor: '#ffffff',
        paper_bgcolor: '#ffffff',
        margin: { t: 60, b: 60, l: 80, r: 40 }
    };

    const config = {
        responsive: true,
        displayModeBar: true,
        displaylogo: false,
        modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d']
    };

    Plotly.newPlot('chart-cumulative', [trace2, trace1], layout, config);
}

/**
 * Gráfico 4: Hitos relevantes (línea ascendente con marcadores)
 */
function createMilestonesChart(milestones, yearlyData) {
    // Construir datos para la línea de progreso
    const years = milestones.map(m => m.year);
    const amounts = milestones.map(m => m.amount);
    const ages = milestones.map(m => m.age);
    const labels = milestones.map(m => {
        if (m.amount >= 1000000) return 'Meta final';
        return formatMoney(m.amount);
    });

    // Línea de progreso
    const trace = {
        x: years,
        y: amounts,
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Progreso',
        line: {
            color: '#10b981',
            width: 3,
            shape: 'spline'
        },
        marker: {
            color: '#10b981',
            size: 12,
            symbol: 'circle',
            line: {
                color: '#ffffff',
                width: 2
            }
        },
        text: labels.map((label, i) => `${label}<br>Año ${years[i]} (edad ${ages[i]})`),
        hovertemplate: '<b>%{text}</b><br>Capital: $%{y:,.0f}<extra></extra>'
    };

    const layout = {
        title: {
            text: 'Hitos relevantes: progreso hacia tus metas',
            font: { size: 16, color: '#1f2937' }
        },
        xaxis: {
            title: 'Año',
            gridcolor: '#e5e7eb',
            showgrid: true,
            dtick: 5  // Marcas cada 5 años
        },
        yaxis: {
            title: 'Capital acumulado (USD)',
            gridcolor: '#e5e7eb',
            showgrid: true,
            tickformat: ',.0f'
        },
        annotations: milestones.map((m, i) => ({
            x: m.year,
            y: m.amount,
            text: labels[i],
            showarrow: true,
            arrowhead: 2,
            arrowsize: 1,
            arrowwidth: 2,
            arrowcolor: '#10b981',
            ax: 0,
            ay: -40,
            font: {
                size: 11,
                color: '#1f2937',
                family: 'system-ui, sans-serif'
            },
            bgcolor: 'rgba(255,255,255,0.9)',
            bordercolor: '#10b981',
            borderwidth: 1,
            borderpad: 4
        })),
        showlegend: false,
        hovermode: 'closest',
        plot_bgcolor: '#ffffff',
        paper_bgcolor: '#ffffff',
        margin: { t: 60, b: 60, l: 80, r: 40 }
    };

    const config = {
        responsive: true,
        displayModeBar: true,
        displaylogo: false,
        modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d']
    };

    Plotly.newPlot('chart-milestones', [trace], layout, config);
}

/**
 * Gráfico: Hitos DCA (simplificado para milestone breakdown)
 */
function createDCAMilestonesChart(milestonesData) {
    const years = milestonesData.map(m => m.year);
    const amounts = milestonesData.map(m => m.amount);
    const gains = milestonesData.map(m => m.gain || 0);
    
    // Crear texto personalizado con ganancia
    const customText = milestonesData.map((m, i) => 
        `Año ${m.year}<br>Capital: ${formatMoney(m.amount)}<br>Ganancia: ${formatMoney(m.gain || 0)}`
    );

    const trace = {
        x: years,
        y: amounts,
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Progreso DCA',
        line: {
            color: '#f59e0b',
            width: 3,
            shape: 'spline'
        },
        marker: {
            color: '#f59e0b',
            size: 12,
            symbol: 'circle',
            line: {
                color: '#ffffff',
                width: 2
            }
        },
        text: customText,
        hovertemplate: '<b>%{text}</b><extra></extra>'
    };

    const layout = {
        title: {
            text: 'Hitos alcanzados: progreso de tu inversión DCA',
            font: { size: 16, color: '#1f2937' }
        },
        xaxis: {
            title: 'Años',
            gridcolor: '#e5e7eb',
            showgrid: true
        },
        yaxis: {
            title: 'Capital acumulado (USD)',
            gridcolor: '#e5e7eb',
            showgrid: true,
            tickformat: ',.0f'
        },
        annotations: milestonesData.map((m) => ({
            x: m.year,
            y: m.amount,
            text: formatMoney(m.amount),
            showarrow: true,
            arrowhead: 2,
            arrowsize: 1,
            arrowwidth: 2,
            arrowcolor: '#f59e0b',
            ax: 0,
            ay: -40,
            font: {
                size: 11,
                color: '#1f2937',
                family: 'system-ui, sans-serif'
            },
            bgcolor: 'rgba(255,255,255,0.9)',
            bordercolor: '#f59e0b',
            borderwidth: 1,
            borderpad: 4
        })),
        showlegend: false,
        hovermode: 'closest',
        plot_bgcolor: '#ffffff',
        paper_bgcolor: '#ffffff',
        margin: { t: 60, b: 60, l: 80, r: 40 }
    };

    const config = {
        responsive: true,
        displayModeBar: true,
        displaylogo: false,
        modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d']
    };

    Plotly.newPlot('chart-dca-milestones', [trace], layout, config);
}

/**
 * Gráficos: Lump Sum vs DCA (evolución + composición)
 */
function createLumpSumVsDCACharts(result) {
    const years = result.years;
    const months = years * 12;
    
    // Generar series mensuales simuladas
    // Para Lump Sum: todo invertido mes 1, crece con tasa compuesta
    // Para DCA: aportes mensuales graduales
    
    // Obtener tasa anual (con fallback si no viene del backend)
    const annualReturn = result.annual_return ?? rateFromScenario(result.scenario);
    const monthlyReturn = Math.pow(1 + annualReturn, 1/12) - 1;
    const monthlyAmount = result.total_amount / months;
    
    const lumpSumSeries = [];
    const dcaSeries = [];
    const monthLabels = [];
    
    let lumpValue = result.total_amount;
    let dcaValue = 0;
    
    for (let month = 1; month <= months; month++) {
        // Lump Sum: crece desde el inicio
        lumpValue *= (1 + monthlyReturn);
        lumpSumSeries.push(lumpValue);
        
        // DCA: aporte mensual + crecimiento
        dcaValue += monthlyAmount;
        dcaValue *= (1 + monthlyReturn);
        dcaSeries.push(dcaValue);
        
        monthLabels.push(month);
    }
    
    // Gráfico 1: Evolución del portafolio
    createEvolutionChart(monthLabels, lumpSumSeries, dcaSeries, years);
    
    // Gráfico 2: Composición final (aportes vs intereses)
    createCompositionChart(result);
}

function createEvolutionChart(monthLabels, lumpSumSeries, dcaSeries, years) {
    const trace1 = {
        x: monthLabels,
        y: lumpSumSeries,
        type: 'scatter',
        mode: 'lines',
        name: 'Lump Sum',
        line: {
            color: '#3b82f6',
            width: 3
        },
        hovertemplate: '<b>Lump Sum</b><br>Mes %{x}<br>Valor: $%{y:,.0f}<extra></extra>'
    };

    const trace2 = {
        x: monthLabels,
        y: dcaSeries,
        type: 'scatter',
        mode: 'lines',
        name: 'DCA',
        line: {
            color: '#f59e0b',
            width: 3
        },
        hovertemplate: '<b>DCA</b><br>Mes %{x}<br>Valor: $%{y:,.0f}<extra></extra>'
    };

    const layout = {
        title: {
            text: 'Evolución del portafolio: Lump Sum vs DCA',
            font: { size: 16, color: '#1f2937' }
        },
        xaxis: {
            title: 'Meses',
            gridcolor: '#e5e7eb',
            showgrid: true,
            dtick: 12  // Marcas cada año
        },
        yaxis: {
            title: 'Valor del portafolio (USD)',
            gridcolor: '#e5e7eb',
            showgrid: true,
            tickformat: ',.0f'
        },
        legend: {
            x: 0.02,
            y: 0.98,
            bgcolor: 'rgba(255,255,255,0.8)',
            bordercolor: '#d1d5db',
            borderwidth: 1
        },
        hovermode: 'x unified',
        plot_bgcolor: '#ffffff',
        paper_bgcolor: '#ffffff',
        margin: { t: 60, b: 60, l: 80, r: 40 }
    };

    const config = {
        responsive: true,
        displayModeBar: true,
        displaylogo: false,
        modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d']
    };

    Plotly.newPlot('chart-ls-vs-dca-evolution', [trace1, trace2], layout, config);
}

function createCompositionChart(result) {
    const totalAmount = result.total_amount;
    const years = result.years;
    const months = years * 12;
    const monthlyAmount = totalAmount / months;
    
    // Definir los 3 escenarios con tasas anuales
    const scenarios = [
        { name: 'Conservador (7%)', rate: 0.07, color: '#ef4444' },
        { name: 'Moderado (10%)', rate: 0.10, color: '#3b82f6' },
        { name: 'Optimista (12%)', rate: 0.12, color: '#10b981' }
    ];
    
    // Calcular valores finales para cada escenario
    const lumpSumData = [];
    const dcaData = [];
    const labels = [];
    const colors = [];
    
    scenarios.forEach(scenario => {
        const monthlyRate = Math.pow(1 + scenario.rate, 1/12) - 1;
        
        // Lump Sum: inversión completa desde el inicio
        const lumpFinal = totalAmount * Math.pow(1 + scenario.rate, years);
        const lumpGain = lumpFinal - totalAmount;
        
        // DCA: aportes mensuales graduales
        let dcaValue = 0;
        for (let month = 1; month <= months; month++) {
            dcaValue += monthlyAmount;
            dcaValue *= (1 + monthlyRate);
        }
        const dcaGain = dcaValue - totalAmount;
        
        // Guardar datos
        labels.push(`LS - ${scenario.name}`, `DCA - ${scenario.name}`);
        lumpSumData.push(lumpGain, 0);  // Interés LS, 0 para DCA
        dcaData.push(0, dcaGain);        // 0 para LS, Interés DCA
        colors.push(scenario.color, scenario.color);
    });
    
    // Trace de aportes (base común)
    const traceAportes = {
        x: labels,
        y: new Array(labels.length).fill(totalAmount),
        type: 'bar',
        name: 'Aportes',
        marker: { color: '#f59e0b' },
        hovertemplate: '<b>%{x}</b><br>Aportes: $%{y:,.0f}<extra></extra>'
    };
    
    // Trace de intereses (varía según estrategia y escenario)
    const traceIntereses = {
        x: labels,
        y: lumpSumData.map((ls, i) => ls + dcaData[i]),
        type: 'bar',
        name: 'Intereses',
        marker: { color: colors },
        hovertemplate: '<b>%{x}</b><br>Intereses: $%{y:,.0f}<extra></extra>'
    };

    const layout = {
        title: {
            text: 'Composición por escenario: aportes vs intereses',
            font: { size: 16, color: '#1f2937' }
        },
        xaxis: {
            title: '',
            gridcolor: '#e5e7eb',
            tickangle: -45
        },
        yaxis: {
            title: 'USD',
            gridcolor: '#e5e7eb',
            showgrid: true,
            tickformat: ',.0f'
        },
        barmode: 'stack',
        legend: {
            x: 0.02,
            y: 0.98,
            bgcolor: 'rgba(255,255,255,0.8)',
            bordercolor: '#d1d5db',
            borderwidth: 1
        },
        hovermode: 'closest',
        plot_bgcolor: '#ffffff',
        paper_bgcolor: '#ffffff',
        margin: { t: 60, b: 100, l: 80, r: 40 }
    };

    const config = {
        responsive: true,
        displayModeBar: true,
        displaylogo: false,
        modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d']
    };

    Plotly.newPlot('chart-ls-vs-dca-composition', [traceAportes, traceIntereses], layout, config);
}

/**
 * Gráfico: Simulación de Interés Compuesto con múltiples caminos
 */
function createCompoundSimulationChart(result) {
    const paths = result.paths || [];
    if (paths.length === 0) return;

    const traces = [];
    const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16'];

    // Crear una línea por cada camino simulado
    paths.forEach((path, idx) => {
        const yearLabels = path.yearly_series.map(s => s.year);
        const values = path.yearly_series.map(s => s.portfolio_value);

        traces.push({
            x: yearLabels,
            y: values,
            type: 'scatter',
            mode: 'lines',
            name: `Camino ${path.path_id}`,
            line: {
                color: colors[idx % colors.length],
                width: 2
            },
            hovertemplate: '<b>Camino %{data.name}</b><br>Año %{x}<br>Valor: $%{y:,.0f}<extra></extra>'
        });
    });

    // Calcular promedio de todos los caminos
    const firstPath = paths[0].yearly_series;
    const avgValues = firstPath.map((_, yearIdx) => {
        const sum = paths.reduce((acc, path) => {
            return acc + (path.yearly_series[yearIdx]?.portfolio_value || 0);
        }, 0);
        return sum / paths.length;
    });

    // Agregar línea de promedio (más gruesa y destacada)
    traces.push({
        x: firstPath.map(s => s.year),
        y: avgValues,
        type: 'scatter',
        mode: 'lines',
        name: 'Promedio',
        line: {
            color: '#1f2937',
            width: 4,
            dash: 'dash'
        },
        hovertemplate: '<b>Promedio</b><br>Año %{x}<br>Valor: $%{y:,.0f}<extra></extra>'
    });

    const layout = {
        title: {
            text: `Múltiples caminos simulados (volatilidad ${result.volatility_pct}%)`,
            font: { size: 16, color: '#1f2937' }
        },
        xaxis: {
            title: 'Años',
            gridcolor: '#e5e7eb',
            showgrid: true
        },
        yaxis: {
            title: 'Valor del portafolio (USD)',
            gridcolor: '#e5e7eb',
            showgrid: true,
            tickformat: ',.0f'
        },
        legend: {
            x: 0.02,
            y: 0.98,
            bgcolor: 'rgba(255,255,255,0.9)',
            bordercolor: '#d1d5db',
            borderwidth: 1
        },
        hovermode: 'x unified',
        plot_bgcolor: '#ffffff',
        paper_bgcolor: '#ffffff',
        margin: { t: 60, b: 60, l: 80, r: 40 }
    };

    const config = {
        responsive: true,
        displayModeBar: true,
        displaylogo: false,
        modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d']
    };

    Plotly.newPlot('chart-compound-simulation', traces, layout, config);
}

/**
 * Gráfico: Interés Compuesto modo determinista (evolución aportes vs intereses)
 */
function createCompoundDeterministicChart(result) {
    const series = result.yearly_series || [];
    if (series.length === 0) return;

    const years = series.map(s => s.year);
    const contributions = series.map(s => s.contributions_accumulated);
    const interests = series.map(s => s.interest_accumulated);
    const totals = series.map(s => s.portfolio_value);

    // Trace 1: Aportes acumulados
    const traceContributions = {
        x: years,
        y: contributions,
        type: 'scatter',
        mode: 'lines',
        name: 'Aportes acumulados',
        fill: 'tozeroy',
        line: {
            color: '#f59e0b',
            width: 2
        },
        fillcolor: 'rgba(245, 158, 11, 0.2)',
        hovertemplate: '<b>Aportes</b><br>Año %{x}<br>$%{y:,.0f}<extra></extra>'
    };

    // Trace 2: Intereses acumulados (apilado sobre aportes)
    const traceInterests = {
        x: years,
        y: interests,
        type: 'scatter',
        mode: 'lines',
        name: 'Intereses acumulados',
        fill: 'tonexty',
        line: {
            color: '#3b82f6',
            width: 2
        },
        fillcolor: 'rgba(59, 130, 246, 0.3)',
        hovertemplate: '<b>Intereses</b><br>Año %{x}<br>$%{y:,.0f}<extra></extra>'
    };

    // Trace 3: Valor total (línea destacada)
    const traceTotal = {
        x: years,
        y: totals,
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Valor total',
        line: {
            color: '#10b981',
            width: 3,
            dash: 'dot'
        },
        marker: {
            color: '#10b981',
            size: 6
        },
        hovertemplate: '<b>Valor total</b><br>Año %{x}<br>$%{y:,.0f}<extra></extra>'
    };

    const layout = {
        title: {
            text: 'Evolución del portafolio: aportes vs intereses',
            font: { size: 16, color: '#1f2937' }
        },
        xaxis: {
            title: 'Años',
            gridcolor: '#e5e7eb',
            showgrid: true
        },
        yaxis: {
            title: 'USD',
            gridcolor: '#e5e7eb',
            showgrid: true,
            tickformat: ',.0f'
        },
        legend: {
            x: 0.02,
            y: 0.98,
            bgcolor: 'rgba(255,255,255,0.9)',
            bordercolor: '#d1d5db',
            borderwidth: 1
        },
        hovermode: 'x unified',
        plot_bgcolor: '#ffffff',
        paper_bgcolor: '#ffffff',
        margin: { t: 60, b: 60, l: 80, r: 40 }
    };

    const config = {
        responsive: true,
        displayModeBar: true,
        displaylogo: false,
        modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d']
    };

    Plotly.newPlot('chart-compound-deterministic', [traceContributions, traceInterests, traceTotal], layout, config);
}
