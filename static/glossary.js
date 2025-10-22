// ============================================
// GLOSARIO DE TÉRMINOS FINANCIEROS
// ============================================

const glossaryData = {
    "Métricas de Valoración": [
        {
            name: "P/E Ratio (Price-to-Earnings)",
            definition: "Relación entre el precio de la acción y las ganancias por acción. Indica cuánto paga el mercado por cada dólar de ganancia de la empresa.",
            example: "Un P/E de 20 significa que pagas $20 por cada $1 de ganancia anual. Ratios bajos (<15) pueden indicar valoración atractiva, mientras que ratios altos (>30) pueden sugerir sobrevaloración o altas expectativas de crecimiento."
        },
        {
            name: "PEG Ratio (Price/Earnings to Growth)",
            definition: "P/E ajustado por el crecimiento esperado. Se calcula dividiendo el P/E entre la tasa de crecimiento de ganancias.",
            example: "Un PEG menor a 1 generalmente indica que la acción está infravalorada considerando su crecimiento. Por ejemplo, P/E de 20 con crecimiento del 25% = PEG de 0.8 (atractivo)."
        },
        {
            name: "P/B Ratio (Price-to-Book)",
            definition: "Compara el precio de mercado con el valor en libros (activos - pasivos) de la empresa.",
            example: "P/B menor a 1 puede indicar que la empresa cotiza por debajo de su valor contable. Útil para evaluar empresas con muchos activos tangibles como bancos o inmobiliarias."
        },
        {
            name: "EV/EBITDA",
            definition: "Valor de empresa dividido por ganancias antes de intereses, impuestos, depreciación y amortización. Mide valoración independiente de la estructura de capital.",
            example: "Útil para comparar empresas con diferentes niveles de deuda. Un EV/EBITDA de 8-12 es típico para empresas maduras."
        },
        {
            name: "Dividend Yield",
            definition: "Rendimiento por dividendos, calculado como dividendo anual dividido por precio de la acción.",
            example: "Si una acción cuesta $100 y paga $4 en dividendos anuales, el yield es 4%. Los yields típicos varían de 1-6% dependiendo del sector."
        }
    ],
    "Métricas de Rentabilidad": [
        {
            name: "ROE (Return on Equity)",
            definition: "Retorno sobre el patrimonio. Mide la rentabilidad generada sobre el capital de los accionistas.",
            example: "Un ROE del 15% significa que la empresa genera $15 de ganancia por cada $100 de capital de accionistas. ROEs superiores al 15% son considerados excelentes."
        },
        {
            name: "ROIC (Return on Invested Capital)",
            definition: "Retorno sobre capital invertido. Mide la eficiencia con la que la empresa utiliza todo su capital (deuda + patrimonio).",
            example: "Un ROIC del 12% indica que por cada $100 invertidos, la empresa genera $12 de beneficio operativo. ROIC > costo de capital indica creación de valor."
        },
        {
            name: "ROA (Return on Assets)",
            definition: "Retorno sobre activos. Mide la eficiencia con la que la empresa utiliza sus activos para generar ganancias.",
            example: "ROA del 8% significa que la empresa genera $8 de ganancia por cada $100 en activos. Es especialmente útil para comparar empresas del mismo sector."
        },
        {
            name: "Margen Neto",
            definition: "Porcentaje de ingresos que se convierte en ganancia neta después de todos los gastos e impuestos.",
            example: "Un margen neto del 20% significa que de cada $100 en ventas, $20 son ganancia neta. Márgenes superiores al 10% son considerados buenos."
        },
        {
            name: "Margen Operativo",
            definition: "Porcentaje de ingresos que queda después de costos operativos, antes de intereses e impuestos.",
            example: "Margen operativo del 25% indica eficiencia operativa. Permite comparar rentabilidad independiente de la estructura de capital."
        },
        {
            name: "Margen Bruto",
            definition: "Porcentaje de ingresos que queda después de restar el costo de los productos vendidos.",
            example: "Margen bruto del 60% indica que de cada $100 en ventas, $60 quedan después de costos directos. Márgenes altos sugieren poder de fijación de precios."
        }
    ],
    "Métricas de Salud Financiera": [
        {
            name: "Debt-to-Equity (D/E)",
            definition: "Relación entre deuda total y patrimonio. Mide el apalancamiento financiero de la empresa.",
            example: "D/E de 0.5 significa que por cada $1 de patrimonio hay $0.50 de deuda. Valores menores a 1 son generalmente saludables, pero varía por industria."
        },
        {
            name: "Current Ratio",
            definition: "Activos corrientes dividido por pasivos corrientes. Mide la capacidad de pagar obligaciones a corto plazo.",
            example: "Current Ratio de 2.0 significa que por cada $1 de deuda a corto plazo, hay $2 en activos líquidos. Valores mayores a 1.5 son considerados saludables."
        },
        {
            name: "Quick Ratio (Acid Test)",
            definition: "Similar al Current Ratio pero excluye inventarios. Mide liquidez inmediata.",
            example: "Quick Ratio de 1.2 indica buena liquidez para cubrir deudas sin depender de vender inventario. Valores superiores a 1 son positivos."
        },
        {
            name: "Interest Coverage",
            definition: "Capacidad de pagar intereses de la deuda. Se calcula dividiendo EBIT entre gastos por intereses.",
            example: "Cobertura de 8x significa que la empresa gana 8 veces más que lo que paga en intereses. Valores superiores a 3 indican bajo riesgo financiero."
        },
        {
            name: "Free Cash Flow (FCF)",
            definition: "Efectivo que genera la empresa después de gastos de capital. Disponible para dividendos, recompra de acciones o reducción de deuda.",
            example: "FCF positivo y creciente indica salud financiera y capacidad de retornar valor a accionistas sin comprometer el crecimiento."
        }
    ],
    "Métricas de Crecimiento": [
        {
            name: "Crecimiento de Ingresos (YoY)",
            definition: "Tasa de crecimiento de ventas comparada con el año anterior.",
            example: "Crecimiento de ingresos del 15% anual es robusto. Empresas de crecimiento típicamente crecen >20%, mientras que empresas maduras ~5-10%."
        },
        {
            name: "Crecimiento de EPS",
            definition: "Tasa de crecimiento de las ganancias por acción.",
            example: "Crecimiento sostenido de EPS >10% anual es excelente. Más importante que el crecimiento aislado es la consistencia a lo largo del tiempo."
        },
        {
            name: "Tasa de Retención",
            definition: "Porcentaje de ganancias que la empresa reinvierte en lugar de pagar como dividendos.",
            example: "Retención del 70% significa que de cada $100 ganados, $70 se reinvierten y $30 se pagan como dividendos. Alta retención puede indicar oportunidades de crecimiento."
        }
    ],
    "Estrategias de Inversión": [
        {
            name: "Dollar Cost Averaging (DCA)",
            definition: "Estrategia de invertir cantidades fijas de dinero a intervalos regulares, independientemente del precio del activo.",
            example: "Invertir $500 mensuales en lugar de $6,000 de una vez reduce el riesgo de entrar al mercado en el momento equivocado."
        },
        {
            name: "Lump Sum",
            definition: "Invertir todo el capital disponible de una sola vez.",
            example: "Estudios muestran que históricamente Lump Sum supera a DCA ~65% del tiempo, pero DCA reduce el riesgo psicológico."
        },
        {
            name: "Interés Compuesto",
            definition: "Reinversión de ganancias que a su vez generan más ganancias. La fuerza más poderosa en inversiones a largo plazo.",
            example: "Invertir $10,000 al 10% anual durante 30 años con interés compuesto genera $174,494, vs $40,000 con interés simple."
        },
        {
            name: "Value Investing",
            definition: "Estrategia de comprar acciones infravaloradas basándose en análisis fundamental.",
            example: "Buscar empresas con P/E bajo, P/B bajo y fundamentos sólidos que el mercado temporalmente ignora."
        },
        {
            name: "Buy and Hold",
            definition: "Estrategia de mantener inversiones a largo plazo independiente de volatilidad de corto plazo.",
            example: "Mantener acciones de calidad durante 10+ años para beneficiarse del crecimiento compuesto y minimizar impuestos."
        }
    ],
    "Conceptos de Riesgo": [
        {
            name: "Diversificación",
            definition: "Distribuir inversiones entre diferentes activos para reducir riesgo específico.",
            example: "Invertir en 20-30 acciones de diferentes sectores reduce el riesgo de que un evento específico afecte todo el portafolio."
        },
        {
            name: "Volatilidad",
            definition: "Medida de cuánto fluctúa el precio de un activo. Mayor volatilidad = mayor riesgo y potencial retorno.",
            example: "Una acción que varía ±30% anualmente es más volátil que una que varía ±10%. La volatilidad no es mala si tienes horizonte largo."
        },
        {
            name: "Drawdown",
            definition: "Caída máxima desde un pico histórico antes de recuperarse.",
            example: "Si tu portafolio cayó de $100,000 a $70,000, el drawdown es del 30%. Entender drawdowns ayuda a prepararse psicológicamente."
        },
        {
            name: "Inflación",
            definition: "Incremento general de precios que reduce el poder adquisitivo del dinero.",
            example: "Con inflación del 3% anual, necesitas crecer tus inversiones >3% solo para mantener tu poder de compra real."
        }
    ],
    "Términos de Mercado": [
        {
            name: "ETF (Exchange-Traded Fund)",
            definition: "Fondo de inversión que cotiza en bolsa y generalmente replica un índice. Ofrece diversificación instantánea.",
            example: "VOO replica el S&P 500. Comprar 1 acción de VOO es como comprar pequeñas porciones de las 500 empresas más grandes de EE.UU."
        },
        {
            name: "S&P 500",
            definition: "Índice que agrupa las 500 empresas más grandes que cotizan en EE.UU. Referencia principal del mercado americano.",
            example: "Retorno promedio histórico del S&P 500: ~10% anual. Usado como benchmark para evaluar fondos y gestores activos."
        },
        {
            name: "Bull Market / Bear Market",
            definition: "Bull market: mercado alcista con precios subiendo. Bear market: mercado bajista con caída >20% desde máximos.",
            example: "Los bull markets duran en promedio 9 años, los bear markets ~1.5 años. Ambos son normales y esperables."
        },
        {
            name: "Ticker Symbol",
            definition: "Código único de letras que identifica a una empresa en bolsa.",
            example: "AAPL = Apple, MSFT = Microsoft, TSLA = Tesla. Usados para buscar información y ejecutar órdenes."
        }
    ]
};

// ============================================
// FUNCIONALIDAD DEL MODAL
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('glossary-modal');
    const helpButton = document.getElementById('help-button');
    const closeButton = document.getElementById('close-glossary');
    const overlay = modal.querySelector('.modal__overlay');
    const searchInput = document.getElementById('glossary-search');
    const glossaryContent = document.getElementById('glossary-content');
    const footerLink = document.getElementById('footer-glossary-link');

    // Renderizar glosario
    function renderGlossary(filterText = '') {
        glossaryContent.innerHTML = '';

        Object.entries(glossaryData).forEach(([category, terms]) => {
            const filteredTerms = terms.filter(term => {
                if (!filterText) return true;
                const searchLower = filterText.toLowerCase();
                return term.name.toLowerCase().includes(searchLower) ||
                       term.definition.toLowerCase().includes(searchLower);
            });

            if (filteredTerms.length > 0) {
                const categorySection = document.createElement('div');
                categorySection.className = 'glossary-category';

                const categoryTitle = document.createElement('h3');
                categoryTitle.className = 'glossary-category__title';
                categoryTitle.textContent = category;
                categorySection.appendChild(categoryTitle);

                filteredTerms.forEach(term => {
                    const termDiv = document.createElement('div');
                    termDiv.className = 'glossary-term';

                    const termName = document.createElement('h4');
                    termName.className = 'glossary-term__name';
                    termName.textContent = term.name;

                    const termDef = document.createElement('p');
                    termDef.className = 'glossary-term__definition';
                    termDef.textContent = term.definition;

                    termDiv.appendChild(termName);
                    termDiv.appendChild(termDef);

                    if (term.example) {
                        const termExample = document.createElement('div');
                        termExample.className = 'glossary-term__example';
                        termExample.innerHTML = `<strong>Ejemplo:</strong> ${term.example}`;
                        termDiv.appendChild(termExample);
                    }

                    categorySection.appendChild(termDiv);
                });

                glossaryContent.appendChild(categorySection);
            }
        });

        if (glossaryContent.children.length === 0) {
            glossaryContent.innerHTML = '<p style="text-align: center; color: var(--muted); padding: 2rem;">No se encontraron términos que coincidan con tu búsqueda.</p>';
        }
    }

    // Abrir modal
    function openModal() {
        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
        searchInput.value = '';
        renderGlossary();
        searchInput.focus();
    }

    // Cerrar modal
    function closeModal() {
        modal.classList.add('hidden');
        document.body.style.overflow = '';
    }

    // Event listeners
    helpButton.addEventListener('click', openModal);
    closeButton.addEventListener('click', closeModal);
    overlay.addEventListener('click', closeModal);

    footerLink.addEventListener('click', function(e) {
        e.preventDefault();
        openModal();
    });

    // Búsqueda en tiempo real
    searchInput.addEventListener('input', function(e) {
        renderGlossary(e.target.value);
    });

    // Cerrar con ESC
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
            closeModal();
        }
    });

    // Renderizar glosario inicial
    renderGlossary();
});

// ============================================
// HELPER: Crear tooltip para términos
// ============================================

function createTooltip(term, definition) {
    return `<span class="term-tooltip">${term}<span class="term-tooltip__content">${definition}</span></span>`;
}

// Exportar para uso en otras páginas si es necesario
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { glossaryData, createTooltip };
}
