/**
 * main.js - Gestion de la navigation et initialisation de l'application
 * 
 * Fonctionnalités :
 * - Navigation par onglets (Backtest / Live Trading)
 * - Initialisation de l'application
 * - Gestion du statut de connexion
 * - Horloge en temps réel
 * - Gestion des événements globaux
 */

class MainApp {
    constructor() {
        this.currentTab = 'backtest';
        this.isInitialized = false;
        this.connectionCheckInterval = null;
        this.timeUpdateInterval = null;
        
        // Références aux éléments DOM
        this.tabs = {
            backtest: document.getElementById('backtest-tab'),
            liveTrading: document.getElementById('live-trading-tab')
        };
        
        this.tabContents = {
            backtest: document.getElementById('backtest-content'),
            liveTrading: document.getElementById('live-trading-content')
        };
        
        this.statusElements = {
            icon: document.getElementById('status-icon'),
            text: document.getElementById('status-text'),
            container: document.getElementById('connection-status')
        };
        
        this.timeElement = document.getElementById('current-time');
    }

    /**
     * Initialise l'application
     */
    async init() {
        console.log('🚀 Initialisation de l\'application...');
        
        try {
            // Initialisation des événements
            this.setupEventListeners();
            
            // Initialisation de l'horloge
            this.initClock();
            
            // Test de connexion au backend
            await this.checkConnection();
            
            // Démarrage des intervalles
            this.startIntervals();
            
            this.isInitialized = true;
            console.log('✅ Application initialisée avec succès');
            
            // Affichage du message de bienvenue
            this.showWelcomeMessage();
            
        } catch (error) {
            console.error('❌ Erreur lors de l\'initialisation:', error);
            window.Utils.showError('Erreur lors de l\'initialisation de l\'application');
        }
    }

    /**
     * Configure les event listeners raccourcis clavier
     */
    setupEventListeners() {
        // Navigation entre onglets
        this.tabs.backtest.addEventListener('click', () => this.switchTab('backtest'));
        this.tabs.liveTrading.addEventListener('click', () => this.switchTab('liveTrading'));
        
        // Raccourcis clavier
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey) {
                switch (e.key) {
                    case 'b':
                        e.preventDefault();
                        this.switchTab('backtest');
                        break;
                    case 'l':
                        e.preventDefault();
                        this.switchTab('liveTrading');
                        break;
                    case 'r':
                        e.preventDefault();
                        this.refreshCurrentTab();
                        break;
                }
            }
        });
        
        // Gestion de la fermeture de la fenêtre
        window.addEventListener('beforeunload', (e) => {
            if (this.isLiveTradingActive()) {
                e.preventDefault();
                e.returnValue = 'Le bot de trading est actif. Êtes-vous sûr de vouloir quitter ?';
                return e.returnValue;
            }
        });
        
        // Gestion du redimensionnement
        window.addEventListener('resize', () => {
            this.handleResize();
        });
        
        // Gestion de la visibilité de la page
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.onPageHidden();
            } else {
                this.onPageVisible();
            }
        });
    }

    /**
     * Bascule entre les onglets
     */
    switchTab(tabName) {
        if (this.currentTab === tabName) return;
        
        console.log(`🔄 Basculement vers l'onglet: ${tabName}`);
        
        // Désactiver l'onglet actuel
        this.tabs[this.currentTab].classList.remove('active');
        this.tabContents[this.currentTab].classList.remove('active');
        
        // Activer le nouvel onglet
        this.currentTab = tabName;
        this.tabs[this.currentTab].classList.add('active');
        this.tabContents[this.currentTab].classList.add('active');
        
        // Notifier le changement d'onglet
        this.onTabChange(tabName);
        
        // Sauvegarder la préférence
        window.Utils.saveToStorage('currentTab', tabName);
    }

    /**
     * Gestionnaire du changement d'onglet
     */
    onTabChange(tabName) {
        switch (tabName) {
            case 'backtest':
                if (window.BacktestManager) {
                    window.BacktestManager.onTabActivated();
                }
                break;
            case 'liveTrading':
                if (window.LiveTradingManager) {
                    window.LiveTradingManager.onTabActivated();
                }
                break;
        }
    }

    /**
     * Actualise l'onglet actuel
     */
    refreshCurrentTab() {
        console.log(`🔄 Actualisation de l'onglet: ${this.currentTab}`);
        
        switch (this.currentTab) {
            case 'backtest':
                if (window.BacktestManager) {
                    window.BacktestManager.refresh();
                }
                break;
            case 'liveTrading':
                if (window.LiveTradingManager) {
                    window.LiveTradingManager.refresh();
                }
                break;
        }
    }

    /**
     * Vérifie la connexion au backend
     */
    async checkConnection() {
        try {
            const isConnected = await window.API.testConnection();
            this.updateConnectionStatus(isConnected);
            return isConnected;
        } catch (error) {
            console.error('❌ Erreur de connexion:', error);
            this.updateConnectionStatus(false);
            return false;
        }
    }

    /**
     * Met à jour le statut de connexion
     */
    updateConnectionStatus(isConnected) {
        if (isConnected) {
            this.statusElements.icon.className = 'fas fa-circle text-success';
            this.statusElements.text.textContent = 'Connecté';
            this.statusElements.container.className = 'connection-status connected';
        } else {
            this.statusElements.icon.className = 'fas fa-circle text-danger';
            this.statusElements.text.textContent = 'Déconnecté';
            this.statusElements.container.className = 'connection-status disconnected';
        }
    }

    /**
     * Initialise l'horloge
     */
    initClock() {
        this.updateTime();
        this.timeUpdateInterval = setInterval(() => {
            this.updateTime();
        }, 1000);
    }

    /**
     * Met à jour l'heure affichée
     */
    updateTime() {
        const now = new Date();
        const timeString = window.Utils.formatDate(now, 'datetime');
        this.timeElement.textContent = timeString;
    }


    /**
     * Démarre les intervalles
     */
    startIntervals() {
        // Vérification de connexion toutes les 30 secondes
        this.connectionCheckInterval = setInterval(() => {
            this.checkConnection();
        }, 30000);
    }

    /**
     * Arrête les intervalles
     */
    stopIntervals() {
        if (this.connectionCheckInterval) {
            clearInterval(this.connectionCheckInterval);
            this.connectionCheckInterval = null;
        }
        
        if (this.timeUpdateInterval) {
            clearInterval(this.timeUpdateInterval);
            this.timeUpdateInterval = null;
        }
    }

    /**
     * Vérifie si le live trading est actif
     */
    isLiveTradingActive() {
        return window.LiveTradingManager && window.LiveTradingManager.isActive();
    }

    /**
     * Gestion du redimensionnement
     */
    handleResize() {
        // Notifier les gestionnaires de graphiques
        if (window.ChartManager) {
            window.ChartManager.handleResize();
        }
    }

    /**
     * Page cachée
     */
    onPageHidden() {
        console.log('📱 Page cachée - Pause des mises à jour');
        // Réduire la fréquence des mises à jour
    }

    /**
     * Page visible
     */
    onPageVisible() {
        console.log('👁️ Page visible - Reprise des mises à jour');
        // Reprendre les mises à jour normales
        this.checkConnection();
    }

    /**
     * Affiche le message de bienvenue
     */
    showWelcomeMessage() {
        window.Utils.showSuccess('Application initialisée avec succès !');
        
        // Cacher le message après 3 secondes
        setTimeout(() => {
            window.Utils.hideSuccess();
        }, 3000);
    }

    /**
     * Nettoyage avant destruction
     */
    destroy() {
        this.stopIntervals();
        
        // Nettoyage des event listeners
        document.removeEventListener('keydown', this.handleKeydown);
        window.removeEventListener('beforeunload', this.handleBeforeUnload);
        window.removeEventListener('resize', this.handleResize);
        document.removeEventListener('visibilitychange', this.handleVisibilityChange);
        
        console.log('🧹 Application nettoyée');
    }
}

// Instance globale
window.MainApp = null;

// Initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', async () => {
    console.log('📄 DOM chargé - Initialisation en cours...');
    
    try {
        // Création de l'instance principale
        window.MainApp = new MainApp();
        
        // Attendre que tous les scripts soient chargés
        await window.MainApp.init();
        
    } catch (error) {
        console.error('❌ Erreur fatale lors de l\'initialisation:', error);
        
        // Affichage d'un message d'erreur à l'utilisateur
        const errorDiv = document.createElement('div');
        errorDiv.className = 'fatal-error';
        errorDiv.innerHTML = `
            <h2>Erreur d'initialisation</h2>
            <p>Une erreur fatale s'est produite lors du chargement de l'application.</p>
            <p>Veuillez vérifier que le backend est démarré et recharger la page.</p>
            <button onclick="location.reload()">Recharger la page</button>
        `;
        document.body.appendChild(errorDiv);
    }
});

// Nettoyage avant fermeture
window.addEventListener('beforeunload', () => {
    if (window.MainApp) {
        window.MainApp.destroy();
    }
});

// Gestionnaire d'erreurs globales
window.addEventListener('error', (event) => {
    console.error('❌ Erreur JavaScript globale:', event.error);
    
    // Affichage d'un message d'erreur à l'utilisateur
    if (window.Utils) {
        window.Utils.showError('Une erreur inattendue s\'est produite. Veuillez recharger la page.');
    }
    event.preventDefault();
    return true; // Empêche le navigateur de gérer l'erreur
});