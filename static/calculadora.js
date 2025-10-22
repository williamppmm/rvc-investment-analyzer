let selectedScenario = 'moderado';

document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initScenarioCards();
    initCalculators();
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

async function calculateDCA() {
    const initialAmount = parseFloat(document.getElementById('dca-initial').value) || 0;
    const monthlyAmount = parseFloat(document.getElementById('dca-monthly').value) || 0;
    const years = parseInt(document.getElementById('dca-years').value, 10);
    const inflationPct = parseFloat(document.getElementById('dca-inflation').value) || 0;
    const marketTiming = document.getElementById('dca-timing').value;

    if (initialAmount < 0 || monthlyAmount < 0) {
        alert('Los montos no pueden ser negativos.');
        return;
    }

    if (initialAmount === 0 && monthlyAmount === 0) {
        alert('Ingresa al menos un capital inicial o un aporte mensual.');
        return;
    }

    if (!years || years <= 0 || years > 50) {
        alert('El periodo debe estar entre 1 y 50 anios.');
        return;
    }

    if (inflationPct < 0 || inflationPct > 15) {
        alert('La inflacion anual debe estar entre 0% y 15%.');
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
                annual_inflation: inflationPct / 100
            })
        });

        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || 'No se pudo calcular la proyeccion DCA.');
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
                <div class="value">$${formatNumber(res.final_value)}</div>
                <div class="subvalue">${res.cap_reached ? 'Limite de 1,000,000 USD alcanzado' : input.market_timing_label}</div>
            </div>
            <div class="result-card">
                <div class="label">Aportes totales (incluye capital inicial)</div>
                <div class="value">$${formatNumber(res.total_invested)}</div>
                <div class="subvalue">${input.effective_months} de ${input.total_months_planned} meses planificados</div>
            </div>
            <div class="result-card info">
                <div class="label">Ganancia generada</div>
                <div class="value">$${formatNumber(res.total_gain)}</div>
                <div class="subvalue">${formatPercent(res.total_return_pct)} sobre lo aportado</div>
            </div>
        </div>
    `;

    html += `
        <div class="chart-container">
            <h3>Proyeccion base vs simulacion con timing</h3>
            <p style="margin-bottom: 1rem;">
                Proyeccion lineal sin volatilidad: $${formatNumber(res.simple_projection)}. 
                Con ajuste por inflacion e interes compuesto: $${formatNumber(baseline.final_value || 0)} 
                (${formatPercent(baseline.return_pct)} retorno). 
                La simulacion con timing y precio variable termina en $${formatNumber(res.final_value)}.
            </p>
        </div>
    `;

    const milestones = Object.values(breakdown || {}).filter(Boolean);
    if (milestones.length) {
        html += `
            <div class="chart-container">
                <h3>Hitos alcanzados</h3>
                <div class="milestone-timeline">
        `;
        milestones.forEach((milestone) => {
            html += `
                <div class="milestone-item">
                    <div class="milestone-year">${milestone.years} anios</div>
                    <div class="milestone-value">$${formatNumber(milestone.value)}</div>
                    <div class="milestone-bar"></div>
                </div>
            `;
        });
        html += `</div></div>`;
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
        snapshots.forEach((row) => {
            html += `
                <tr>
                    <td>${row.month}</td>
                    <td>$${formatNumber(row.monthly_contribution)}</td>
                    <td>$${formatNumber(row.invested_to_date)}</td>
                    <td>$${formatNumber(row.portfolio_value)}</td>
                    <td>${formatPercent(row.return_pct)}</td>
                </tr>
            `;
        });
        html += `
                    </tbody>
                </table>
            </div>
        `;
    }

    if (res.cap_reached) {
        html += `
            <div class="insights-section" style="margin-top: 2rem;">
                <h3>Limite alcanzado</h3>
                <div class="insight-item">
                    <strong>Meta de 1,000,000 USD</strong>
                    <p style="margin: 0;">
                        Llegaste al limite en el mes ${res.cap_reached.month} (${res.cap_reached.years_elapsed} anios). 
                        A partir de ahi dejamos de sumar aportes para evitar resultados irreales.
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
    container.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

async function calculateLumpSum() {
    const totalAmount = parseFloat(document.getElementById('ls-total').value);
    const years = parseInt(document.getElementById('ls-years').value, 10);
    const scenario = document.getElementById('ls-scenario').value;

    if (!totalAmount || totalAmount <= 0) {
        alert('Ingresa un monto total positivo.');
        return;
    }

    if (!years || years <= 0 || years > 50) {
        alert('El periodo debe estar entre 1 y 50 anios.');
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
            throw new Error(data.error || 'No se pudo realizar la comparacion.');
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
        <h3>Resultados para ${result.years} anios (${capitalize(result.scenario)})</h3>
        <div class="results-grid" style="margin-bottom: 2rem;">
            <div class="result-card ${comparison.winner === 'Lump Sum' ? 'success' : ''}">
                <div class="label">${lump.strategy}</div>
                <div class="value">$${formatNumber(lump.final_value)}</div>
                <div class="subvalue">Ganancia: $${formatNumber(lump.total_gain)} (${formatPercent(lump.return_pct)})</div>
            </div>
            <div class="result-card ${comparison.winner === 'DCA' ? 'success' : ''}">
                <div class="label">${dca.strategy}</div>
                <div class="value">$${formatNumber(dca.final_value)}</div>
                <div class="subvalue">Ganancia: $${formatNumber(dca.total_gain)} (${formatPercent(dca.return_pct)})</div>
            </div>
        </div>

        <table class="comparison-table">
            <thead>
                <tr>
                    <th>Parametro</th>
                    <th>Lump Sum</th>
                    <th>DCA</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Capital inicial</td>
                    <td>$${formatNumber(result.total_amount)}</td>
                    <td>$${formatNumber(dca.monthly_amount)} mensual</td>
                </tr>
                <tr>
                    <td>Valor final</td>
                    <td>$${formatNumber(lump.final_value)} ${comparison.winner === 'Lump Sum' ? '<span class="winner-badge">Ganador</span>' : ''}</td>
                    <td>$${formatNumber(dca.final_value)} ${comparison.winner === 'DCA' ? '<span class="winner-badge">Ganador</span>' : ''}</td>
                </tr>
                <tr>
                    <td>Ganancia total</td>
                    <td>$${formatNumber(lump.total_gain)}</td>
                    <td>$${formatNumber(dca.total_gain)}</td>
                </tr>
            </tbody>
        </table>

        <div class="insights-section" style="margin-top: 2rem;">
            <h3>Recomendacion</h3>
            <div class="insight-item">
                <strong>${comparison.winner} aventaja por $${formatNumber(comparison.difference)} (${formatPercent(comparison.difference_pct)})</strong>
            </div>
            <div class="insight-item">
                <p style="margin: 0;">${comparison.recommendation}</p>
            </div>
        </div>
    `;

    container.innerHTML = html;
    container.classList.remove('hidden');
    container.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

async function calculateCompound() {
    const initialAmount = parseFloat(document.getElementById('ci-initial').value) || 0;
    const monthlyContribution = parseFloat(document.getElementById('ci-monthly').value) || 0;
    const years = parseInt(document.getElementById('ci-years').value, 10);
    const scenario = document.getElementById('ci-scenario').value;

    if (initialAmount < 0 || monthlyContribution < 0) {
        alert('Los montos no pueden ser negativos.');
        return;
    }

    if (initialAmount === 0 && monthlyContribution === 0) {
        alert('Ingresa al menos un monto inicial o una contribucion mensual.');
        return;
    }

    if (!years || years <= 0 || years > 50) {
        alert('El periodo debe estar entre 1 y 50 anios.');
        return;
    }

    const loading = document.getElementById('ci-loading');
    const results = document.getElementById('ci-results');

    loading.classList.remove('hidden');
    results.classList.add('hidden');

    try {
        const response = await fetch('/api/calcular-inversion', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                calculation_type: 'compound_interest',
                initial_amount: initialAmount,
                monthly_amount: monthlyContribution,
                years,
                scenario
            })
        });

        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || 'No se pudo calcular el interes compuesto.');
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
    const interestPct = result.interest_contribution_pct;
    const aportesPct = 100 - interestPct;

    let html = `
        <h3>Resumen del interes compuesto (${result.annual_return_pct}% anual)</h3>
        <div class="results-grid">
            <div class="result-card">
                <div class="label">Aportes totales</div>
                <div class="value">$${formatNumber(result.total_contributed)}</div>
                <div class="subvalue">Capital propio acumulado</div>
            </div>
            <div class="result-card success">
                <div class="label">Valor final</div>
                <div class="value">$${formatNumber(result.final_value)}</div>
                <div class="subvalue">Despues de ${result.years} anios</div>
            </div>
            <div class="result-card warning">
                <div class="label">Intereses generados</div>
                <div class="value">$${formatNumber(result.interest_earned)}</div>
                <div class="subvalue">${formatPercent(interestPct)} del total</div>
            </div>
        </div>

        <div class="chart-container">
            <h3>Desglose de aportes vs intereses</h3>
            <div style="display: flex; gap: 1rem; margin-top: 1rem; height: 60px;">
                <div style="flex: ${aportesPct}; background: linear-gradient(135deg, #17a2b8, #0056b3); border-radius: 8px; display: flex; align-items: center; justify-content: center; color: white; font-weight: 700;">
                    ${formatPercent(aportesPct)} aportes
                </div>
                <div style="flex: ${interestPct}; background: linear-gradient(135deg, #28a745, #20c997); border-radius: 8px; display: flex; align-items: center; justify-content: center; color: white; font-weight: 700;">
                    ${formatPercent(interestPct)} intereses
                </div>
            </div>
        </div>
    `;

    if (result.cap_reached) {
        html += `
            <div class="insights-section" style="margin-top: 2rem;">
                <h3>Limite alcanzado</h3>
                <div class="insight-item">
                    <p style="margin: 0;">El calculo se detuvo al llegar a 1,000,000 USD para mantener cifras realistas.</p>
                </div>
            </div>
        `;
    }

    html += `
        <div class="insights-section" style="margin-top: 2rem;">
            <h3>Lecturas sugeridas</h3>
            <div class="insight-item">
                <strong>Mensaje clave</strong>
                <p style="margin: 0;">${result.message}</p>
            </div>
            <div class="insight-item">
                <strong>Multiplicador</strong>
                <p style="margin: 0;">Tu capital final es ${(result.final_value / result.total_contributed).toFixed(2)} veces lo aportado.</p>
            </div>
        </div>
    `;

    container.innerHTML = html;
    container.classList.remove('hidden');
    container.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

async function calculateRetirement() {
    const currentAge = parseInt(document.getElementById('ret-current-age').value, 10);
    const retirementAge = parseInt(document.getElementById('ret-retirement-age').value, 10);
    const initialAmount = parseFloat(document.getElementById('ret-initial').value) || 0;
    const monthlyAmount = parseFloat(document.getElementById('ret-monthly').value) || 0;
    const annualReturnPct = parseFloat(document.getElementById('ret-return').value) || 0;
    const annualInflationPct = parseFloat(document.getElementById('ret-inflation').value) || 0;

    if (!currentAge || currentAge < 18 || currentAge > 75) {
        alert('La edad actual debe estar entre 18 y 75 anios.');
        return;
    }

    if (!retirementAge || retirementAge <= currentAge || retirementAge > 75) {
        alert('La edad de retiro debe ser mayor a la actual y no superar 75 anios.');
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
        alert('La inflacion debe estar entre 0% y 15%.');
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
                annual_return_override: annualReturnPct / 100
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
        <h3>Meta a los ${input.retirement_age} anios (horizonte ${input.years_to_retirement} anios)</h3>
        <div class="results-grid">
            <div class="result-card success">
                <div class="label">Capital proyectado</div>
                <div class="value">$${formatNumber(res.final_capital)}</div>
                <div class="subvalue">${formatPercent(res.average_return_pct)} anual esperado</div>
            </div>
            <div class="result-card">
                <div class="label">Capital inicial</div>
                <div class="value">$${formatNumber(res.initial_capital)}</div>
                <div class="subvalue">Punto de partida</div>
            </div>
            <div class="result-card info">
                <div class="label">Aportes durante el plan</div>
                <div class="value">$${formatNumber(res.total_contributions)}</div>
                <div class="subvalue">${input.effective_years} anios efectivos de ahorro</div>
            </div>
            <div class="result-card warning">
                <div class="label">Intereses generados</div>
                <div class="value">$${formatNumber(res.total_interest)}</div>
                <div class="subvalue">${formatPercent(composition.interest_pct)} del total</div>
            </div>
        </div>
    `;

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
                <td>$${formatNumber(scenario.final_value)}</td>
                <td>$${formatNumber(scenario.total_contributions)}</td>
                <td>$${formatNumber(scenario.total_interest)}</td>
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
                <h3>Limite alcanzado</h3>
                <div class="insight-item">
                    <strong>Meta de 1,000,000 USD</strong>
                    <p style="margin: 0;">
                        El plan alcanza el limite a los ${limit.details.year} anios (edad ${limit.details.age}). 
                        A partir de ese punto dejamos de sumar aportes para mantener proyecciones realistas.
                    </p>
                </div>
            </div>
        `;
    }

    if (milestones && milestones.length) {
        html += `
            <div class="chart-container">
                <h3>Hitos relevantes</h3>
                <div class="milestone-timeline">
        `;
        milestones.forEach((row) => {
            html += `
                <div class="milestone-item">
                    <div class="milestone-year">${row.amount >= 1000000 ? 'Meta final' : `$${formatNumber(row.amount)}`}</div>
                    <div class="milestone-value">Se alcanza en el anio ${row.year} (edad ${row.age})</div>
                    <div class="milestone-bar"></div>
                </div>
            `;
        });
        html += `</div></div>`;
    }

    if (yearly && yearly.length) {
        const displayRows = yearly.length > 12
            ? [...yearly.slice(0, 6), { ellipsis: true }, ...yearly.slice(-4)]
            : yearly;

        html += `
            <div class="yearly-table">
                <table>
                    <thead>
                        <tr>
                            <th>Anio (edad)</th>
                            <th>Aporte anual</th>
                            <th>Aportes acumulados</th>
                            <th>Interes del anio</th>
                            <th>Interes acumulado</th>
                            <th>Capital total</th>
                        </tr>
                    </thead>
                    <tbody>
        `;

        displayRows.forEach((row) => {
            if (row.ellipsis) {
                html += `
                    <tr>
                        <td colspan="6" style="text-align: center; font-style: italic; color: #6c757d;">... ${yearly.length - 10} anios intermedios ...</td>
                    </tr>
                `;
                return;
            }
            html += `
                <tr>
                    <td>${row.year} (${row.age})</td>
                    <td>$${formatNumber(row.annual_contribution)}</td>
                    <td>$${formatNumber(row.contributions_accumulated)}</td>
                    <td>$${formatNumber(row.interest_this_year)}</td>
                    <td>$${formatNumber(row.interest_accumulated)}</td>
                    <td>$${formatNumber(row.portfolio_value)}</td>
                </tr>
            `;
        });

        html += `
                    </tbody>
                </table>
            </div>
        `;
    }

    container.innerHTML = html;
    container.classList.remove('hidden');
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
    return unique.filter((item) => {
        if (!item) return false;
        if (seen.has(item.month)) return false;
        seen.add(item.month);
        return true;
    });
}

function formatNumber(value) {
    if (value === undefined || value === null || Number.isNaN(value)) {
        return '0';
    }
    return new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(value);
}

function formatPercent(value) {
    if (value === undefined || value === null || Number.isNaN(value)) {
        return '0%';
    }
    return `${value.toFixed(1)}%`;
}

function capitalize(text) {
    if (!text) {
        return '';
    }
    return text.charAt(0).toUpperCase() + text.slice(1);
}
