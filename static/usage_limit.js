/**
 * SISTEMA DE LÍMITE DE USO - MODAL FREEMIUM
 * Gestiona límites de consultas gratuitas y promociona plan PRO
 */

class UsageLimitManager {
    constructor() {
        this.modal = null;
        this.licenseKey = localStorage.getItem('rvc_license_key');
        this.init();
    }

    init() {
        // Crear modal si no existe
        if (!document.getElementById('usage-limit-modal')) {
            this.createModal();
        }
        this.modal = document.getElementById('usage-limit-modal');
        this.attachEvents();
    }

    createModal() {
        const modalHTML = `
            <div id="usage-limit-modal" class="usage-limit-modal">
                <div class="limit-modal-content">
                    <div class="limit-modal-header">
                        <button class="limit-modal-close" aria-label="Cerrar">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M18 6L6 18M6 6l12 12"/>
                            </svg>
                        </button>
                        <div class="limit-modal-icon">🎯</div>
                        <h2>Límite de Consultas Alcanzado</h2>
                        <p>Has utilizado todas tus consultas gratuitas de esta semana</p>
                    </div>

                    <div class="limit-modal-body">
                        <div class="usage-stats">
                            <div class="usage-stat">
                                <span class="usage-stat-value" id="queries-used">0</span>
                                <span class="usage-stat-label">Consultas usadas</span>
                            </div>
                            <div class="usage-stat">
                                <span class="usage-stat-value" id="queries-remaining">0</span>
                                <span class="usage-stat-label">Disponibles</span>
                            </div>
                        </div>

                        <div class="limit-explanation">
                            <h3>
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <circle cx="12" cy="12" r="10"/>
                                    <path d="M12 16v-4M12 8h.01"/>
                                </svg>
                                ¿Por qué hay límites?
                            </h3>
                            <p>
                                Las APIs de datos financieros gratuitas tienen limitaciones estrictas.
                                Para mantener el servicio disponible para todos, limitamos a 
                                <strong>20 consultas gratuitas por día</strong>. 
                                <span id="reset-info"></span>
                            </p>
                        </div>

                        <div class="plan-comparison">
                            <h3>🚀 Actualiza a RVC Analyzer PRO</h3>
                            <div class="plans-grid">
                                <div class="plan-card">
                                    <h4 class="plan-name">FREE</h4>
                                    <div class="plan-price">
                                        $0
                                        <small>/día</small>
                                    </div>
                                    <ul class="plan-features">
                                        <li>20 consultas diarias</li>
                                        <li>APIs gratuitas (limitadas)</li>
                                        <li>Datos con posible retraso</li>
                                        <li class="unavailable">Sin soporte prioritario</li>
                                        <li class="unavailable">Funciones limitadas</li>
                                    </ul>
                                </div>

                                <div class="plan-card featured">
                                    <span class="plan-badge">✨ Recomendado</span>
                                    <h4 class="plan-name">PRO</h4>
                                    <div class="plan-price">
                                        $3 USD
                                        <small>/30 días</small>
                                    </div>
                                    <ul class="plan-features">
                                        <li>200 consultas diarias (10x más)</li>
                                        <li>APIs premium (Alpha Vantage, Twelve Data)</li>
                                        <li>Datos en tiempo real</li>
                                        <li>Soporte prioritario</li>
                                        <li>Contribuyes al sostenimiento del proyecto</li>
                                    </ul>
                                </div>
                            </div>
                        </div>

                        <div class="contact-creator">
                            <h4>💬 ¿Te gusta RVC Analyzer? Contribuye al proyecto</h4>
                            <div class="creator-info">
                                <div class="creator-avatar">WP</div>
                                <div class="creator-details">
                                    <h5>William Pérez</h5>
                                    <p>Desarrollador & Creador de RVC Analyzer</p>
                                </div>
                            </div>
                            <p style="font-size: 0.9rem; color: #6c757d; margin: 0.5rem 0 1rem; text-align: center;">
                                Con solo <strong>$3 USD/mes</strong> ayudas a mantener las APIs premium activas 
                                y el proyecto en línea. ¡Obtén acceso ilimitado por 30 días!
                            </p>
                            <div class="contact-methods">
                                <a href="mailto:williamppmm@hotmail.com?subject=Quiero%20contribuir%20al%20sostenimiento%20de%20RVC%20Analyzer&body=Hola%20William%2C%0A%0AEstoy%20interesado%20en%20contribuir%20al%20sostenimiento%20del%20proyecto%20RVC%20Analyzer%20con%20una%20licencia%20PRO%20(%243%20USD%2F30%20d%C3%ADas).%0A%0AMi%20email%20es%3A%20%0A%0A%C2%BFC%C3%B3mo%20puedo%20proceder%20con%20el%20pago%3F%0A%0AGracias%21" 
                                   class="contact-btn primary"
                                   target="_blank">
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                                        <path d="M22 6l-10 7L2 6"/>
                                    </svg>
                                    Contribuir ($3 USD/30 días)
                                </a>
                                <a href="/about" class="contact-btn secondary">
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <circle cx="12" cy="12" r="10"/>
                                        <path d="M12 16v-4M12 8h.01"/>
                                    </svg>
                                    Más Información
                                </a>
                            </div>
                        </div>
                    </div>

                    <div class="modal-footer-note">
                        <p>
                            <strong>¿Ya tienes una licencia PRO?</strong> 
                            <a href="#" id="activate-license-link" style="color: #667eea; font-weight: 600;">
                                Actívala aquí
                            </a>
                        </p>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHTML);
    }

    attachEvents() {
        // Cerrar modal
        const closeBtn = this.modal.querySelector('.limit-modal-close');
        closeBtn?.addEventListener('click', () => this.hide());

        // Cerrar al hacer clic fuera
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.hide();
            }
        });

        // Activar licencia
        const activateLink = document.getElementById('activate-license-link');
        activateLink?.addEventListener('click', (e) => {
            e.preventDefault();
            this.showLicenseInput();
        });

        // ESC para cerrar
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.modal.classList.contains('active')) {
                this.hide();
            }
        });
    }

    async checkLimit() {
        try {
            const response = await fetch('/api/check-limit', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    license_key: this.licenseKey
                })
            });

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Error checking limit:', error);
            return { allowed: true }; // Fail open
        }
    }

    async show(usageData) {
        // Actualizar estadísticas
        const usedEl = document.getElementById('queries-used');
        const remainingEl = document.getElementById('queries-remaining');
        const resetInfoEl = document.getElementById('reset-info');

        if (usedEl) usedEl.textContent = usageData.limit - usageData.remaining;
        if (remainingEl) remainingEl.textContent = usageData.remaining;
        
        if (resetInfoEl && usageData.reset_in) {
            resetInfoEl.innerHTML = `<br><strong>Se restablece en: ${usageData.reset_in}</strong> (${usageData.reset_date})`;
        }
        
        // Si es usuario PRO
        if (usageData.plan === 'PRO') {
            const headerEl = document.querySelector('.limit-modal-header h2');
            const subheaderEl = document.querySelector('.limit-modal-header p');
            
            if (usageData.remaining === 0) {
                // PRO que alcanzó el límite diario de 200
                if (headerEl) headerEl.textContent = '⚡ Límite Diario PRO Alcanzado';
                if (subheaderEl) {
                    subheaderEl.textContent = `Has usado tus 200 consultas diarias. El límite se restablece en ${usageData.reset_in}.`;
                }
            } else if (usageData.license_days_left !== undefined) {
                // PRO con licencia activa (mostrar días restantes)
                const daysLeft = usageData.license_days_left;
                if (headerEl) headerEl.textContent = '✨ Licencia PRO Activa';
                if (subheaderEl) {
                    subheaderEl.textContent = `Te quedan ${daysLeft} día${daysLeft !== 1 ? 's' : ''} de acceso PRO (${usageData.remaining} consultas hoy)`;
                }
            }
        }

        // Mostrar modal
        this.modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    hide() {
        this.modal.classList.remove('active');
        document.body.style.overflow = '';
    }

    showLicenseInput() {
        const key = prompt('Ingresa tu clave de licencia PRO:');
        if (key) {
            this.activateLicense(key);
        }
    }

    async activateLicense(licenseKey) {
        try {
            const response = await fetch('/api/validate-license', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ license_key: licenseKey })
            });

            const data = await response.json();

            if (data.valid) {
                localStorage.setItem('rvc_license_key', licenseKey);
                this.licenseKey = licenseKey;
                alert('✅ Licencia PRO activada exitosamente. Ahora tienes acceso ilimitado.');
                this.hide();
                location.reload();
            } else {
                alert('❌ Licencia inválida: ' + (data.reason || 'Clave no reconocida'));
            }
        } catch (error) {
            console.error('Error validating license:', error);
            alert('❌ Error al validar la licencia. Intenta nuevamente.');
        }
    }

    // Mostrar badge de plan en el navbar
    showPlanBadge(plan, daysLeft = null) {
        const navbar = document.querySelector('.navbar');
        if (!navbar || document.getElementById('plan-badge')) return;

        const badge = document.createElement('div');
        badge.id = 'plan-badge';
        badge.className = plan === 'PRO' ? 'plan-badge pro' : 'plan-badge free';
        
        let badgeHTML = `
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z"/>
            </svg>
            ${plan}
        `;
        
        if (plan === 'PRO' && daysLeft !== null && daysLeft <= 7) {
            badgeHTML += ` <span style="font-size:0.75rem; opacity:0.8;">(${daysLeft}d)</span>`;
        }
        
        badge.innerHTML = badgeHTML;
        badge.style.cssText = `
            position: fixed;
            top: 70px;
            right: 20px;
            background: ${plan === 'PRO' ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' : '#6c757d'};
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.875rem;
            font-weight: 600;
            z-index: 999;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        `;
        navbar.appendChild(badge);
    }
}

// Inicializar al cargar
let usageLimitManager;
document.addEventListener('DOMContentLoaded', () => {
    usageLimitManager = new UsageLimitManager();
});

// Función helper para verificar antes de analizar
async function checkUsageLimitBeforeAction() {
    if (!usageLimitManager) {
        usageLimitManager = new UsageLimitManager();
    }

    const limitCheck = await usageLimitManager.checkLimit();
    
    if (!limitCheck.allowed) {
        usageLimitManager.show(limitCheck);
        return false;
    }

    // Mostrar advertencia si quedan pocas consultas
    if (limitCheck.plan === 'FREE' && limitCheck.remaining <= 3 && limitCheck.remaining > 0) {
        showWarningToast(`⚠️ Te quedan ${limitCheck.remaining} consultas gratuitas hoy`);
    } else if (limitCheck.plan === 'PRO' && limitCheck.remaining <= 20 && limitCheck.remaining > 0) {
        showWarningToast(`⚠️ PRO: Te quedan ${limitCheck.remaining} consultas hoy (de 200)`);
    }

    return true;
}

function showWarningToast(message) {
    // Crear toast simple
    const toast = document.createElement('div');
    toast.className = 'usage-warning-toast';
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        top: 80px;
        right: 20px;
        background: #ffc107;
        color: #856404;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        z-index: 9999;
        animation: slideIn 0.3s ease;
    `;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}
