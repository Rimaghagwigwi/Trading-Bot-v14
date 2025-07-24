/**
 * API.js - Communication avec le backend Flask
 * Gère toutes les interactions avec les endpoints REST
 */

class ApiClient {
    constructor(baseUrl = 'http://192.168.1.77:5000') {
        this.baseUrl = baseUrl;
        this.defaultHeaders = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        };
    }

    /**
     * Initialise l'API client (vérification de connexion)
     */
    async init() {
        console.log('🚀 Initialisation du client API...');
        
        const connectionTest = await this.testConnection();
        
        if (connectionTest.success) {
            console.log('✅ Connexion API établie');
            return true;
        } else {
            console.error('❌ Impossible de se connecter au backend');
            return false;
        }
    }

    /**
     * Méthode générique pour les requêtes HTTP
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const config = {
            headers: this.defaultHeaders,
            ...options
        };

        try {
            const response = await fetch(url, config);
            
            // Vérifier si la réponse est OK
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ error: 'Erreur inconnue' }));
                throw new Error(errorData.error || `Erreur HTTP ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`Erreur API [${endpoint}]:`, error);
            throw error;
        }
    }

    /**
     * Méthodes HTTP génériques
     */
    async get(endpoint, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const url = queryString ? `${endpoint}?${queryString}` : endpoint;
        
        return this.request(url, {
            method: 'GET'
        });
    }

    async post(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async put(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    async delete(endpoint) {
        return this.request(endpoint, {
            method: 'DELETE'
        });
    }

    // ==========================================
    // ENDPOINTS BACKTEST
    // ==========================================

    /**
     * Récupère la liste des stratégies disponibles
     */
    async getStrategies() {
        return this.get('/api/strategies');
    }

    /**
     * Récupère les données de marché historiques
     */
    async getMarketData(symbol, timeframe, startDate, endDate) {
        // Validation des paramètres
        if (!Utils.validateCryptoSymbol(symbol)) {
            throw new Error('Symbole crypto invalide');
        }
        if (!Utils.validateTimeframe(timeframe)) {
            throw new Error('Timeframe invalide');
        }
        if (!Utils.validateDateRange(startDate, endDate)) {
            throw new Error('Période de dates invalide');
        }

        const params = {
            symbol: Utils.normalizeSymbol(symbol),
            timeframe,
            start_date: startDate,
            end_date: endDate
        };

        return this.get('/api/market-data', params);
    }

    /**
     * Lance un backtest
     */
    async runBacktest(config) {
        // Validation de la configuration
        if (!this.validateBacktestConfig(config)) {
            throw new Error('Configuration de backtest invalide');
        }

        config.symbols = config.symbols.map(Utils.normalizeSymbol);

        return this.post('/api/backtest', config);
    }

    /**
     * Récupère l'historique des backtests
     */
    async getBacktestHistory(limit = 50) {
        return this.get('/api/backtest/history', { limit });
    }

    /**
     * Récupère les détails d'un backtest spécifique
     */
    async getBacktestDetails(backtestId) {
        return this.get(`/api/backtest/${backtestId}`);
    }

    // ==========================================
    // ENDPOINTS LIVE TRADING (À développer)
    // ==========================================

    /**
     * Récupère le statut du bot de trading
     */
    async getLiveStatus() {
        return this.get('/api/live/status');
    }

    /**
     * Démarre le bot de trading
     */
    async startLiveTrading(config) {
        this.validateLiveTradingConfig(config);
        return this.post('/api/live/start', config);
    }

    /**
     * Arrête le bot de trading
     */
    async stopLiveTrading() {
        return this.post('/api/live/stop');
    }

    /**
     * Récupère l'état du portefeuille
     */
    async getPortfolio() {
        return this.get('/api/live/portfolio');
    }

    /**
     * Récupère l'historique des trades
     */
    async getTradeHistory(limit = 100) {
        return this.get('/api/live/trades', { limit });
    }

    /**
     * Récupère les logs en temps réel
     */
    async getLiveLogs(limit = 200) {
        return this.get('/api/live/logs', { limit });
    }

    /**
     * Met à jour les paramètres de risque
     */
    async updateRiskParameters(params) {
        return this.put('/api/live/risk-params', params);
    }

    // ==========================================
    // ENDPOINTS SYSTÈME
    // ==========================================

    /**
     * Vérifie la santé du système
     */
    async getHealth() {
        return this.get('/health');
    }

    /**
     * Récupère les configurations par défaut
     */
    async getDefaultConfig() {
        return this.get('/api/config/defaults');
    }

    /**
     * Récupère les timeframes disponibles
     */
    async getAvailableTimeframes() {
        return this.get('/api/config/timeframes');
    }

    /**
     * Récupère les symboles crypto disponibles
     */
    async getAvailableSymbols() {
        return this.get('/api/config/symbols');
    }

    /**
     * Récupère les stratégies disponibles
     */
    async getAvailableStrategies() {
        return this.get('/api/config/strategies');
    }

    // ==========================================
    // MÉTHODES DE VALIDATION
    // ==========================================

    /**
     * Valide la configuration de backtest
     */
    validateBacktestConfig(config) {
        const required = ['symbols', 'timeframe', 'strategy', 'strategy_params', 'initial_capital', 'start_date', 'end_date', 'commission_rate'];
        for (const field of required) {
            if (!config[field]) {
                throw new Error(`Champ requis manquant: ${field}`);
            }
        }
        return true;
    }

    /**
     * Valide la configuration de live trading
     */
    validateLiveTradingConfig(config) {
        if (!config) {
            throw new Error('Configuration de trading manquante');
        } else {
            return true;
        }
    }

    // ==========================================
    // MÉTHODES UTILITAIRES
    // ==========================================

    /**
     * Gère les erreurs d'API avec messages utilisateur
     */
    handleApiError(error, context = '') {
        const errorMessage = error.message || 'Erreur inconnue';
        const fullMessage = context ? `${context}: ${errorMessage}` : errorMessage;
        
        console.error('Erreur API:', fullMessage);
        
        // Afficher l'erreur à l'utilisateur
        if (Utils.showError) {
            Utils.showError(fullMessage);
        }
        
        return {
            success: false,
            error: fullMessage,
            timestamp: new Date().toISOString()
        };
    }

    /**
     * Wrapper pour les appels API avec gestion d'erreurs
     */
    async safeApiCall(apiMethod, context = '', showLoading = true) {
        try {
            if (showLoading && Utils.showLoading) {
                Utils.showLoading();
            }

            const result = await apiMethod();
            
            if (Utils.hideLoading) {
                Utils.hideLoading();
            }
            
            return {
                success: true,
                data: result,
                timestamp: new Date().toISOString()
            };
        } catch (error) {
            if (Utils.hideLoading) {
                Utils.hideLoading();
            }
            
            return this.handleApiError(error, context);
        }
    }

    /**
     * Teste la connexion avec le backend
     */
    async testConnection() {
        return this.safeApiCall(
            () => this.getHealth(),
            'Test de connexion'
        );
    }
}

// ==========================================
// INSTANCES ET EXPORTS
// ==========================================

// Instance globale du client API
const apiClient = new ApiClient();

// Export vers l'objet global window pour utilisation dans d'autres fichiers
window.API = {
    client: apiClient,
    
    // Méthodes de raccourci pour les opérations courantes
    backtest: {
        getMarketData: (symbol, timeframe, startDate, endDate) => 
            apiClient.safeApiCall(() => apiClient.getMarketData(symbol, timeframe, startDate, endDate), 'Récupération des données de marché'),
        run: (config) => apiClient.safeApiCall(() => apiClient.runBacktest(config), 'Lancement du backtest'),
        getHistory: (limit) => apiClient.safeApiCall(() => apiClient.getBacktestHistory(limit), 'Récupération de l\'historique'),
        getDetails: (id) => apiClient.safeApiCall(() => apiClient.getBacktestDetails(id), 'Récupération des détails')
    },
    
    live: {
        getStatus: () => apiClient.safeApiCall(() => apiClient.getLiveStatus(), 'Récupération du statut'),
        start: (config) => apiClient.safeApiCall(() => apiClient.startLiveTrading(config), 'Démarrage du trading'),
        stop: () => apiClient.safeApiCall(() => apiClient.stopLiveTrading(), 'Arrêt du trading'),
        getPortfolio: () => apiClient.safeApiCall(() => apiClient.getPortfolio(), 'Récupération du portefeuille'),
        getTrades: (limit) => apiClient.safeApiCall(() => apiClient.getTradeHistory(limit), 'Récupération des trades'),
        getLogs: (limit) => apiClient.safeApiCall(() => apiClient.getLiveLogs(limit), 'Récupération des logs'),
        updateParameters: (params) => apiClient.safeApiCall(() => apiClient.updateLiveParameters(params), 'Mise à jour des paramètres de trading')
    },
    
    config: {
        getDefaults: () => apiClient.safeApiCall(() => apiClient.getDefaultConfig(), 'Récupération de la configuration'),
        getTimeframes: () => apiClient.safeApiCall(() => apiClient.getAvailableTimeframes(), 'Récupération des timeframes'),
        getSymbols: () => apiClient.safeApiCall(() => apiClient.getAvailableSymbols(), 'Récupération des symboles'),
        getStrategies: () => apiClient.safeApiCall(() => apiClient.getAvailableStrategies(), 'Récupération des stratégies')
    },
    
    // Méthodes utilitaires
    testConnection: () => apiClient.testConnection(),
    init: () => apiClient.init()
};

// Auto-initialisation au chargement
document.addEventListener('DOMContentLoaded', async () => {
    await window.API.init();
});

// Export pour les modules (si utilisé)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ApiClient, apiClient };
}