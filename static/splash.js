/**
 * RVC SPLASH SCREEN
 * Sistema de transición con logo animado
 * - Solo se muestra en primera visita o cada 24 horas
 * - Permite skip con clic o ESC
 * - Fallback si el video no carga
 */

class RVCSplashScreen {
    constructor() {
        this.STORAGE_KEY = 'rvc_splash_shown';
        this.SPLASH_DURATION = 2500; // 2.5 segundos (video + margen)
        this.COOLDOWN_HOURS = 24; // Mostrar cada 24 horas
        this.splashElement = null;
        this.videoElement = null;
        this.skipped = false;
    }

    /**
     * Verifica si debe mostrarse el splash
     */
    shouldShow() {
        // En desarrollo, siempre mostrar (comentar en producción)
        // return true; // ⚠️ TESTING MODE - Cambiar a comentario en producción

        const lastShown = localStorage.getItem(this.STORAGE_KEY);
        
        if (!lastShown) {
            return true; // Primera visita
        }

        const lastShownTime = parseInt(lastShown, 10);
        const now = Date.now();
        const cooldownMs = this.COOLDOWN_HOURS * 60 * 60 * 1000;

        return (now - lastShownTime) > cooldownMs;
    }

    /**
     * Marca el splash como mostrado
     */
    markAsShown() {
        localStorage.setItem(this.STORAGE_KEY, Date.now().toString());
    }

    /**
     * Crea el HTML del splash screen
     */
    createSplashHTML() {
        return `
            <div id="rvc-splash">
                <div class="splash-video-container">
                    <video 
                        id="logo-intro-video" 
                        playsinline 
                        muted 
                        autoplay
                        preload="auto"
                    >
                        <source src="/static/video/rvc-logo-intro.mp4" type="video/mp4">
                        <source src="/static/video/rvc-logo-intro.webm" type="video/webm">
                        Tu navegador no soporta video HTML5.
                    </video>
                    <div class="splash-loader"></div>
                </div>
                <div class="splash-skip-text">Presiona ESC o clic para continuar</div>
            </div>
        `;
    }

    /**
     * Oculta el splash con animación
     */
    hide() {
        if (this.skipped) return; // Evitar múltiples llamadas
        
        this.skipped = true;
        
        if (this.splashElement) {
            this.splashElement.classList.add('fade-out');
            
            setTimeout(() => {
                if (this.splashElement && this.splashElement.parentNode) {
                    this.splashElement.remove();
                }
                document.body.classList.remove('splash-active');
            }, 500); // Duración de la animación fade-out
        }

        this.markAsShown();
    }

    /**
     * Maneja errores de carga del video
     */
    handleVideoError() {
        console.warn('RVC Splash: Error al cargar el video, ocultando splash');
        this.hide();
    }

    /**
     * Inicializa y muestra el splash
     */
    show() {
        if (!this.shouldShow()) {
            console.log('RVC Splash: Cooldown activo, saltando splash');
            return;
        }

        // Prevenir scroll
        document.body.classList.add('splash-active');

        // Insertar HTML
        document.body.insertAdjacentHTML('afterbegin', this.createSplashHTML());
        
        this.splashElement = document.getElementById('rvc-splash');
        this.videoElement = document.getElementById('logo-intro-video');

        if (!this.videoElement) {
            console.error('RVC Splash: No se pudo encontrar el elemento de video');
            this.hide();
            return;
        }

        // Event listeners del video
        this.videoElement.addEventListener('ended', () => {
            console.log('RVC Splash: Video terminado');
            this.hide();
        });

        this.videoElement.addEventListener('error', () => {
            this.handleVideoError();
        });

        // Mostrar loader si el video tarda en cargar
        this.videoElement.addEventListener('loadstart', () => {
            this.splashElement.classList.add('loading');
        });

        this.videoElement.addEventListener('canplay', () => {
            this.splashElement.classList.remove('loading');
        });

        // Skip con clic
        this.splashElement.addEventListener('click', () => {
            console.log('RVC Splash: Usuario hizo clic para skip');
            this.hide();
        });

        // Skip con ESC
        const escHandler = (e) => {
            if (e.key === 'Escape') {
                console.log('RVC Splash: Usuario presionó ESC para skip');
                this.hide();
                document.removeEventListener('keydown', escHandler);
            }
        };
        document.addEventListener('keydown', escHandler);

        // Timeout de seguridad (si el video se cuelga)
        setTimeout(() => {
            if (!this.skipped) {
                console.log('RVC Splash: Timeout de seguridad alcanzado');
                this.hide();
            }
        }, this.SPLASH_DURATION + 1000);

        console.log('RVC Splash: Mostrando splash screen');
    }

    /**
     * Resetear (para testing)
     */
    reset() {
        localStorage.removeItem(this.STORAGE_KEY);
        console.log('RVC Splash: Storage reseteado');
    }
}

// Instancia global
let rvcSplash = null;

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    rvcSplash = new RVCSplashScreen();
    rvcSplash.show();
});

// Exponer para debugging en consola
window.RVCSplash = {
    reset: () => {
        if (rvcSplash) rvcSplash.reset();
    },
    show: () => {
        if (rvcSplash) rvcSplash.show();
    }
};
