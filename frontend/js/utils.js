// ====================================
// UTILS.JS - Fonctions utilitaires
// ====================================

// ====================================
// VALIDATION
// ====================================

/**
 * Valide un montant (capital, prix, etc.)
 * @param {string|number} value - Valeur à valider
 * @param {number} min - Valeur minimale (défaut: 0)
 * @param {number} max - Valeur maximale (défaut: Infinity)
 * @returns {boolean}
 */
function validateAmount(value, min = 0, max = Infinity) {
    const num = parseFloat(value);
    return !isNaN(num) && num >= min && num <= max;
}

/**
 * Valide une période de dates
 * @param {string} startDate - Date de début (format YYYY-MM-DD)
 * @param {string} endDate - Date de fin (format YYYY-MM-DD)
 * @returns {boolean}
 */
function validateDateRange(startDate, endDate) {
    const start = new Date(startDate);
    const end = new Date(endDate);
    const now = new Date();
    
    return start <= end && end <= now && start >= new Date('2017-01-01');
}

/**
 * Valide un symbole crypto (ex: BTC/USDT, BTCUSDT)
 * @param {string} symbol - Symbole à valider
 * @returns {boolean}
 */
function validateCryptoSymbol(symbol) {
    const normalizedSymbol = symbol.replace('/', '').toUpperCase();
    return /^[A-Z]{3,10}USDT?$/.test(normalizedSymbol);
}

/**
 * Valide un timeframe
 * @param {string} timeframe - Timeframe à valider
 * @returns {boolean}
 */
function validateTimeframes(timeframes) {
    const validTimeframes = ['5m', '15m', '30m', '1h', '4h', '1d'];
    return timeframes.filter(timeframe => validTimeframes.includes(timeframe));
}

function validateSymbols(symbols) {
    const validSymbols = ['BTCUSDC', 'ETHUSDC', 'BNBUSDC', 'XRPUSDC', 'LTCUSDC'];
    return symbols.filter(symbol => validSymbols.includes(symbol));
}

function validateStrategies(strategies) {
    const validStrategies = ['buy_and_hold'];
    return strategies.filter(strategy => validStrategies.includes(strategy.name));
}

/**
 * Valide un pourcentage (0-100)
 * @param {string|number} value - Valeur à valider
 * @returns {boolean}
 */
function validatePercentage(value) {
    return validateAmount(value, 0, 100);
}

// ====================================
// CONVERSION ET FORMATAGE
// ====================================

/**
 * Formate un nombre en devise (USDT)
 * @param {number} value - Valeur à formater
 * @param {number} decimals - Nombre de décimales (défaut: 2)
 * @returns {string}
 */
function formatCurrency(value, decimals = 2) {
    if (isNaN(value)) return '0.00 USDT';
    return `${parseFloat(value).toFixed(decimals)} USDT`;
}

/**
 * Formate un pourcentage
 * @param {number} value - Valeur à formater (ex: 0.1234 = 12.34%)
 * @param {number} decimals - Nombre de décimales (défaut: 2)
 * @returns {string}
 */
function formatPercentage(value, decimals = 2) {
    if (isNaN(value)) return '0.00%';
    return `${(value * 100).toFixed(decimals)}%`;
}

/**
 * Formate une date en format lisible
 * @param {string|Date} date - Date à formater
 * @param {string} format - Format ('short', 'long', 'datetime')
 * @returns {string}
 */
function formatDate(date, format = 'short') {
    const d = new Date(date);
    
    switch (format) {
        case 'short':
            return d.toLocaleDateString('fr-FR');
        case 'long':
            return d.toLocaleDateString('fr-FR', { 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
            });
        case 'datetime':
            return d.toLocaleString('fr-FR');
        default:
            return d.toLocaleDateString('fr-FR');
    }
}

/**
 * Formate un nombre avec séparateurs de milliers
 * @param {number} value - Valeur à formater
 * @param {number} decimals - Nombre de décimales (défaut: 2)
 * @returns {string}
 */
function formatNumber(value, decimals = 2) {
    if (isNaN(value)) return '0';
    return new Intl.NumberFormat('fr-FR', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    }).format(value);
}

/**
 * Normalise un symbole crypto (BTC/USDT -> BTCUSDT)
 * @param {string} symbol - Symbole à normaliser
 * @returns {string}
 */
function normalizeSymbol(symbol) {
    return symbol.replace('/', '').toUpperCase();
}

/**
 * Convertit un symbole normalisé en format lisible (BTCUSDT -> BTC/USDT)
 * @param {string} symbol - Symbole à convertir
 * @returns {string}
 */
function formatSymbol(symbol) {
    const normalized = symbol.toUpperCase();
    if (normalized.endsWith('USDC')) {
        const base = normalized.slice(0, -4);
        return `${base}/USDC`;
    }
    return normalized;
}

function formatTimeframe(timeframe) {
    if (timeframe.endsWith('m')) {
        timeframe = timeframe.replace('m', ' minutes');
    } else if (timeframe.endsWith('h')) {
        timeframe = timeframe.replace('h', ' heures');
    } else if (timeframe.endsWith('d')) {
        timeframe = timeframe.replace('d', ' jours');
    } else if (timeframe.endsWith('w')) {
        timeframe = timeframe.replace('w', ' semaines');
    } else if (timeframe.endsWith('M')) {
        timeframe = timeframe.replace('M', ' mois');
    }
    return timeframe;
}

// ====================================
// CALCULS UTILITAIRES
// ====================================

/**
 * Calcule le pourcentage de variation
 * @param {number} initialValue - Valeur initiale
 * @param {number} finalValue - Valeur finale
 * @returns {number} Pourcentage de variation (ex: 0.1234 = 12.34%)
 */
function calculatePercentageChange(initialValue, finalValue) {
    if (initialValue === 0) return 0;
    return (finalValue - initialValue) / initialValue;
}

/**
 * Calcule le Profit & Loss (PnL)
 * @param {number} entryPrice - Prix d'entrée
 * @param {number} exitPrice - Prix de sortie
 * @param {number} quantity - Quantité tradée
 * @param {number} commission - Commission (défaut: 0.001 = 0.1%)
 * @returns {object} {pnl, pnlPercent, fees}
 */
function calculatePnL(entryPrice, exitPrice, quantity, commission = 0.001) {
    const grossPnL = (exitPrice - entryPrice) * quantity;
    const entryFee = entryPrice * quantity * commission;
    const exitFee = exitPrice * quantity * commission;
    const totalFees = entryFee + exitFee;
    const netPnL = grossPnL - totalFees;
    const pnlPercent = calculatePercentageChange(entryPrice, exitPrice);
    
    return {
        pnl: netPnL,
        pnlPercent: pnlPercent,
        fees: totalFees
    };
}

/**
 * Calcule la position size basée sur le risque
 * @param {number} capital - Capital disponible
 * @param {number} entryPrice - Prix d'entrée
 * @param {number} stopLoss - Prix de stop-loss
 * @param {number} riskPercent - Pourcentage de risque (défaut: 0.02 = 2%)
 * @returns {number} Taille de position
 */
function calculatePositionSize(capital, entryPrice, stopLoss, riskPercent = 0.02) {
    const riskAmount = capital * riskPercent;
    const priceRisk = Math.abs(entryPrice - stopLoss);
    
    if (priceRisk === 0) return 0;
    
    return riskAmount / priceRisk;
}

// ====================================
// GESTION DES ERREURS
// ====================================

/**
 * Affiche un message d'erreur dans l'interface
 * @param {string} message - Message d'erreur
 * @param {string} containerId - ID du conteneur pour l'erreur
 */
function showError(message, containerId = 'error-container') {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `
            <div class="error-message">
                <span class="error-icon">⚠️</span>
                <span class="error-text">${message}</span>
                <button class="error-close" onclick="hideError('${containerId}')">×</button>
            </div>
        `;
        container.style.display = 'block';
    }
}

/**
 * Cache un message d'erreur
 * @param {string} containerId - ID du conteneur d'erreur
 */
function hideError(containerId = 'error-container') {
    const container = document.getElementById(containerId);
    if (container) {
        container.style.display = 'none';
        container.innerHTML = '';
    }
}

/**
 * Affiche un message de succès
 * @param {string} message - Message de succès
 * @param {string} containerId - ID du conteneur pour le succès
 */
function showSuccess(message, containerId = 'success-container') {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `
            <div class="success-message">
                <span class="success-icon">✅</span>
                <span class="success-text">${message}</span>
                <button class="success-close" onclick="hideSuccess('${containerId}')">×</button>
            </div>
        `;
        container.style.display = 'block';
        
        // Auto-hide après 3 secondes
        setTimeout(() => hideSuccess(containerId), 3000);
    }
}

/**
 * Cache un message de succès
 * @param {string} containerId - ID du conteneur de succès
 */
function hideSuccess(containerId = 'success-container') {
    const container = document.getElementById(containerId);
    if (container) {
        container.style.display = 'none';
        container.innerHTML = '';
    }
}

// ====================================
// GESTION DU LOADING
// ====================================

/**
 * Affiche un indicateur de chargement
 * @param {string} containerId - ID du conteneur
 * @param {string} message - Message de chargement
 */
function showLoading(containerId, message = 'Chargement...') {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `
            <div class="loading-container">
                <div class="loading-spinner"></div>
                <div class="loading-text">${message}</div>
            </div>
        `;
        container.style.display = 'block';
    }
}

/**
 * Cache un indicateur de chargement
 * @param {string} containerId - ID du conteneur
 */
function hideLoading(containerId) {
    const container = document.getElementById(containerId);
    if (container) {
        container.style.display = 'none';
        container.innerHTML = '';
    }
}

// ====================================
// UTILITAIRES DIVERS
// ====================================

/**
 * Génère un ID unique
 * @returns {string}
 */
function generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
}

/**
 * Sauvegarde des données dans localStorage
 * @param {string} key - Clé de sauvegarde
 * @param {any} data - Données à sauvegarder
 */
function saveToStorage(key, data) {
    try {
        localStorage.setItem(key, JSON.stringify(data));
    } catch (error) {
        console.error('Erreur sauvegarde localStorage:', error);
    }
}

/**
 * Récupère des données depuis localStorage
 * @param {string} key - Clé de récupération
 * @param {any} defaultValue - Valeur par défaut
 * @returns {any}
 */
function loadFromStorage(key, defaultValue = null) {
    try {
        const item = localStorage.getItem(key);
        return item ? JSON.parse(item) : defaultValue;
    } catch (error) {
        console.error('Erreur lecture localStorage:', error);
        return defaultValue;
    }
}

/**
 * Debounce une fonction
 * @param {Function} func - Fonction à debouncer
 * @param {number} wait - Délai en ms
 * @returns {Function}
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Copie du texte dans le presse-papiers
 * @param {string} text - Texte à copier
 * @returns {Promise<boolean>}
 */
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        return true;
    } catch (error) {
        console.error('Erreur copie presse-papiers:', error);
        return false;
    }
}

// ====================================
// EXPORT DES FONCTIONS
// ====================================

// Export pour utilisation dans d'autres fichiers
window.Utils = {
    // Validation
    validateAmount,
    validateDateRange,
    validateCryptoSymbol,
    validateTimeframes,
    validateSymbols,
    validateStrategies,
    validatePercentage,
    
    // Formatage
    formatCurrency,
    formatPercentage,
    formatDate,
    formatNumber,
    normalizeSymbol,
    formatSymbol,
    formatTimeframe,
    
    // Calculs
    calculatePercentageChange,
    calculatePnL,
    calculatePositionSize,
    
    // Interface
    showError,
    hideError,
    showSuccess,
    hideSuccess,
    showLoading,
    hideLoading,
    
    // Utilitaires
    generateId,
    saveToStorage,
    loadFromStorage,
    debounce,
    copyToClipboard
};