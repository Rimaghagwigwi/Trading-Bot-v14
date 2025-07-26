/**
 * API.js - Communication with Flask backend
 * Handles all interactions with REST endpoints
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
     * Initializes the API client (connection check)
     */
    async init() {
        console.log('🚀 Initializing API client...');
        
        const connectionTest = await this.testConnection();
        
        if (connectionTest.success) {
            console.log('✅ API connection established');
            return true;
        } else {
            console.error('❌ Unable to connect to backend');
            return false;
        }
    }

    /**
     * Generic method for HTTP requests
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const config = {
            headers: this.defaultHeaders,
            ...options
        };

        try {
            const response = await fetch(url, config);
            
            // Check if response is OK
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
                throw new Error(errorData.error || `HTTP Error ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`API Error [${endpoint}]:`, error);
            throw error;
        }
    }

    /**
     * Generic HTTP methods
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
    // BACKTEST ENDPOINTS
    // ==========================================

    /**
     * Gets the list of available strategies
     */
    async getStrategies() {
        return this.get('/api/strategies');
    }

    /**
     * Gets historical market data
     */
    async getMarketData(symbol, timeframe, startDate, endDate) {
        // Parameter validation
        if (!Utils.validateCryptoSymbol(symbol)) {
            throw new Error('Invalid crypto symbol');
        }
        if (!Utils.validateTimeframe(timeframe)) {
            throw new Error('Invalid timeframe');
        }
        if (!Utils.validateDateRange(startDate, endDate)) {
            throw new Error('Invalid date range');
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
     * Runs a backtest
     */
    async runBacktest(config) {
        // Config validation
        if (!this.validateBacktestConfig(config)) {
            throw new Error('Invalid backtest configuration');
        }

        config.symbols = config.symbols.map(Utils.normalizeSymbol);

        return this.post('/api/backtest', config);
    }

    /**
     * Gets backtest history
     */
    async getBacktestHistory(limit = 50) {
        return this.get('/api/backtest/history', { limit });
    }

    /**
     * Gets details of a specific backtest
     */
    async getBacktestDetails(backtestId) {
        return this.get(`/api/backtest/${backtestId}`);
    }

    // ==========================================
    // LIVE TRADING ENDPOINTS (To be developed)
    // ==========================================

    /**
     * Gets the trading bot status
     */
    async getLiveStatus() {
        return this.get('/api/live/status');
    }

    /**
     * Starts the trading bot
     */
    async startLiveTrading(config) {
        this.validateLiveTradingConfig(config);
        return this.post('/api/live/start', config);
    }

    /**
     * Stops the trading bot
     */
    async stopLiveTrading() {
        return this.post('/api/live/stop');
    }

    /**
     * Gets portfolio state
     */
    async getPortfolio() {
        return this.get('/api/live/portfolio');
    }

    /**
     * Gets trade history
     */
    async getTradeHistory(limit = 100) {
        return this.get('/api/live/trades', { limit });
    }

    /**
     * Gets real-time logs
     */
    async getLiveLogs(limit = 200) {
        return this.get('/api/live/logs', { limit });
    }

    /**
     * Updates risk parameters
     */
    async updateRiskParameters(params) {
        return this.put('/api/live/risk-params', params);
    }

    // ==========================================
    // SYSTEM ENDPOINTS
    // ==========================================

    /**
     * Checks system health
     */
    async getHealth() {
        return this.get('/health');
    }

    /**
     * Gets default configurations
     */
    async getDefaultConfig() {
        return this.get('/api/config/defaults');
    }

    /**
     * Gets available timeframes
     */
    async getAvailableTimeframes() {
        return this.get('/api/config/timeframes');
    }

    /**
     * Gets available crypto symbols
     */
    async getAvailableSymbols() {
        return this.get('/api/config/symbols');
    }

    /**
     * Gets available strategies
     */
    async getAvailableStrategies() {
        return this.get('/api/config/strategies');
    }

    // ==========================================
    // VALIDATION METHODS
    // ==========================================

    /**
     * Validates backtest configuration
     */
    validateBacktestConfig(config) {
        const required = ['symbols', 'timeframe', 'strategy', 'strategy_params', 'initial_capital', 'start_date', 'end_date', 'commission_rate'];
        for (const field of required) {
            if (!config[field]) {
                throw new Error(`Missing required field: ${field}`);
            }
        }
        return true;
    }

    /**
     * Validates live trading configuration
     */
    validateLiveTradingConfig(config) {
        if (!config) {
            throw new Error('Missing trading configuration');
        } else {
            return true;
        }
    }

    // ==========================================
    // UTILITY METHODS
    // ==========================================

    /**
     * Handles API errors with user messages
     */
    handleApiError(error, context = '') {
        const errorMessage = error.message || 'Unknown error';
        const fullMessage = context ? `${context}: ${errorMessage}` : errorMessage;
        
        console.error('API Error:', fullMessage);
        
        // Show error to user
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
     * Wrapper for API calls with error handling
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
     * Tests connection with backend
     */
    async testConnection() {
        return this.safeApiCall(
            () => this.getHealth(),
            'Connection test'
        );
    }
}

// ==========================================
// INSTANCES AND EXPORTS
// ==========================================

// Global instance of API client
const apiClient = new ApiClient();

// Export to global window object for use in other files
window.API = {
    client: apiClient,
    
    // Shortcut methods for common operations
    backtest: {
        getMarketData: (symbol, timeframe, startDate, endDate) => 
            apiClient.safeApiCall(() => apiClient.getMarketData(symbol, timeframe, startDate, endDate), 'Fetching market data'),
        run: (config) => apiClient.safeApiCall(() => apiClient.runBacktest(config), 'Running backtest'),
        getHistory: (limit) => apiClient.safeApiCall(() => apiClient.getBacktestHistory(limit), 'Fetching history'),
        getDetails: (id) => apiClient.safeApiCall(() => apiClient.getBacktestDetails(id), 'Fetching details')
    },
    
    live: {
        getStatus: () => apiClient.safeApiCall(() => apiClient.getLiveStatus(), 'Fetching status'),
        start: (config) => apiClient.safeApiCall(() => apiClient.startLiveTrading(config), 'Starting trading'),
        stop: () => apiClient.safeApiCall(() => apiClient.stopLiveTrading(), 'Stopping trading'),
        getPortfolio: () => apiClient.safeApiCall(() => apiClient.getPortfolio(), 'Fetching portfolio'),
        getTrades: (limit) => apiClient.safeApiCall(() => apiClient.getTradeHistory(limit), 'Fetching trades'),
        getLogs: (limit) => apiClient.safeApiCall(() => apiClient.getLiveLogs(limit), 'Fetching logs'),
        updateParameters: (params) => apiClient.safeApiCall(() => apiClient.updateLiveParameters(params), 'Updating trading parameters')
    },
    
    config: {
        getDefaults: () => apiClient.safeApiCall(() => apiClient.getDefaultConfig(), 'Fetching configuration'),
        getTimeframes: () => apiClient.safeApiCall(() => apiClient.getAvailableTimeframes(), 'Fetching timeframes'),
        getSymbols: () => apiClient.safeApiCall(() => apiClient.getAvailableSymbols(), 'Fetching symbols'),
        getStrategies: () => apiClient.safeApiCall(() => apiClient.getAvailableStrategies(), 'Fetching strategies')
    },
    
    // Utility methods
    testConnection: () => apiClient.testConnection(),
    init: () => apiClient.init()
};

// Auto-initialize on load
document.addEventListener('DOMContentLoaded', async () => {
    await window.API.init();
});

// Export for modules (if used)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ApiClient, apiClient };
}