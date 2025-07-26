// ====================================
// UTILS.JS - Utility functions
// ====================================

// ====================================
// VALIDATION
// ====================================

/**
 * Validates an amount (capital, price, etc.)
 * @param {string|number} value - Value to validate
 * @param {number} min - Minimum value (default: 0)
 * @param {number} max - Maximum value (default: Infinity)
 * @returns {boolean}
 */
function validateAmount(value, min = 0, max = Infinity) {
    const num = parseFloat(value);
    return !isNaN(num) && num >= min && num <= max;
}

/**
 * Validates a date range
 * @param {string} startDate - Start date (format YYYY-MM-DD)
 * @param {string} endDate - End date (format YYYY-MM-DD)
 * @returns {boolean}
 */
function validateDateRange(startDate, endDate) {
    const start = new Date(startDate);
    const end = new Date(endDate);
    const now = new Date();
    
    return start <= end && end <= now && start >= new Date('2017-01-01');
}

/**
 * Validates a crypto symbol (e.g. BTC/USDT, BTCUSDT)
 * @param {string} symbol - Symbol to validate
 * @returns {boolean}
 */
function validateCryptoSymbol(symbol) {
    const normalizedSymbol = symbol.replace('/', '').toUpperCase();
    return /^[A-Z]{3,10}USDT?$/.test(normalizedSymbol);
}

/**
 * Validates timeframes
 * @param {string[]} timeframes - Timeframes to validate
 * @returns {string[]}
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
 * Validates a percentage (0-100)
 * @param {string|number} value - Value to validate
 * @returns {boolean}
 */
function validatePercentage(value) {
    return validateAmount(value, 0, 100);
}

// ====================================
// CONVERSION AND FORMATTING
// ====================================

/**
 * Formats a number as currency (USDT)
 * @param {number} value - Value to format
 * @param {number} decimals - Number of decimals (default: 2)
 * @returns {string}
 */
function formatCurrency(value, decimals = 2) {
    if (isNaN(value)) return '0.00 USDT';
    return `${parseFloat(value).toFixed(decimals)} USDT`;
}

/**
 * Formats a percentage
 * @param {number} value - Value to format (e.g. 0.1234 = 12.34%)
 * @param {number} decimals - Number of decimals (default: 2)
 * @returns {string}
 */
function formatPercentage(value, decimals = 2) {
    if (isNaN(value)) return '0.00%';
    return `${(value * 100).toFixed(decimals)}%`;
}

/**
 * Formats a date in readable format
 * @param {string|Date} date - Date to format
 * @param {string} format - Format ('short', 'long', 'datetime')
 * @returns {string}
 */
function formatDate(date, format = 'short') {
    const d = new Date(date);
    
    switch (format) {
        case 'short':
            return d.toLocaleDateString('en-US');
        case 'long':
            return d.toLocaleDateString('en-US', { 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
            });
        case 'datetime':
            return d.toLocaleString('en-US');
        default:
            return d.toLocaleDateString('en-US');
    }
}

/**
 * Formats a number with thousand separators
 * @param {number} value - Value to format
 * @param {number} decimals - Number of decimals (default: 2)
 * @returns {string}
 */
function formatNumber(value, decimals = 2) {
    if (isNaN(value)) return '0';
    return new Intl.NumberFormat('en-US', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    }).format(value);
}

/**
 * Normalizes a crypto symbol (BTC/USDT -> BTCUSDT)
 * @param {string} symbol - Symbol to normalize
 * @returns {string}
 */
function normalizeSymbol(symbol) {
    return symbol.replace('/', '').toUpperCase();
}

/**
 * Converts a normalized symbol to readable format (BTCUSDT -> BTC/USDT)
 * @param {string} symbol - Symbol to convert
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
        timeframe = timeframe.replace('h', ' hours');
    } else if (timeframe.endsWith('d')) {
        timeframe = timeframe.replace('d', ' days');
    } else if (timeframe.endsWith('w')) {
        timeframe = timeframe.replace('w', ' weeks');
    } else if (timeframe.endsWith('M')) {
        timeframe = timeframe.replace('M', ' months');
    }
    return timeframe;
}

// ====================================
// UTILITY CALCULATIONS
// ====================================

/**
 * Calculates percentage change
 * @param {number} initialValue - Initial value
 * @param {number} finalValue - Final value
 * @returns {number} Percentage change (e.g. 0.1234 = 12.34%)
 */
function calculatePercentageChange(initialValue, finalValue) {
    if (initialValue === 0) return 0;
    return (finalValue - initialValue) / initialValue;
}

/**
 * Calculates Profit & Loss (PnL)
 * @param {number} entryPrice - Entry price
 * @param {number} exitPrice - Exit price
 * @param {number} quantity - Traded quantity
 * @param {number} commission - Commission (default: 0.001 = 0.1%)
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
 * Calculates position size based on risk
 * @param {number} capital - Available capital
 * @param {number} entryPrice - Entry price
 * @param {number} stopLoss - Stop-loss price
 * @param {number} riskPercent - Risk percentage (default: 0.02 = 2%)
 * @returns {number} Position size
 */
function calculatePositionSize(capital, entryPrice, stopLoss, riskPercent = 0.02) {
    const riskAmount = capital * riskPercent;
    const priceRisk = Math.abs(entryPrice - stopLoss);
    
    if (priceRisk === 0) return 0;
    
    return riskAmount / priceRisk;
}

// ====================================
// ERROR HANDLING
// ====================================

/**
 * Shows an error message in the interface
 * @param {string} message - Error message
 * @param {string} containerId - Container ID for the error
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
 * Hides an error message
 * @param {string} containerId - Error container ID
 */
function hideError(containerId = 'error-container') {
    const container = document.getElementById(containerId);
    if (container) {
        container.style.display = 'none';
        container.innerHTML = '';
    }
}

/**
 * Shows a success message
 * @param {string} message - Success message
 * @param {string} containerId - Container ID for the success
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
        
        // Auto-hide after 3 seconds
        setTimeout(() => hideSuccess(containerId), 3000);
    }
}

/**
 * Hides a success message
 * @param {string} containerId - Success container ID
 */
function hideSuccess(containerId = 'success-container') {
    const container = document.getElementById(containerId);
    if (container) {
        container.style.display = 'none';
        container.innerHTML = '';
    }
}

// ====================================
// LOADING HANDLING
// ====================================

/**
 * Shows a loading indicator
 * @param {string} containerId - Container ID
 * @param {string} message - Loading message
 */
function showLoading(containerId, message = 'Loading...') {
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
 * Hides a loading indicator
 * @param {string} containerId - Container ID
 */
function hideLoading(containerId) {
    const container = document.getElementById(containerId);
    if (container) {
        container.style.display = 'none';
        container.innerHTML = '';
    }
}

// ====================================
// MISCELLANEOUS UTILITIES
// ====================================

/**
 * Generates a unique ID
 * @returns {string}
 */
function generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
}

/**
 * Saves data to localStorage
 * @param {string} key - Storage key
 * @param {any} data - Data to save
 */
function saveToStorage(key, data) {
    try {
        localStorage.setItem(key, JSON.stringify(data));
    } catch (error) {
        console.error('Error saving to localStorage:', error);
    }
}

/**
 * Loads data from localStorage
 * @param {string} key - Storage key
 * @param {any} defaultValue - Default value
 * @returns {any}
 */
function loadFromStorage(key, defaultValue = null) {
    try {
        const item = localStorage.getItem(key);
        return item ? JSON.parse(item) : defaultValue;
    } catch (error) {
        console.error('Error reading from localStorage:', error);
        return defaultValue;
    }
}

/**
 * Debounces a function
 * @param {Function} func - Function to debounce
 * @param {number} wait - Delay in ms
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
 * Copies text to clipboard
 * @param {string} text - Text to copy
 * @returns {Promise<boolean>}
 */
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        return true;
    } catch (error) {
        console.error('Error copying to clipboard:', error);
        return false;
    }
}

// ====================================
// EXPORT FUNCTIONS
// ====================================

// Export for use in other files
window.Utils = {
    // Validation
    validateAmount,
    validateDateRange,
    validateCryptoSymbol,
    validateTimeframes,
    validateSymbols,
    validateStrategies,
    validatePercentage,
    
    // Formatting
    formatCurrency,
    formatPercentage,
    formatDate,
    formatNumber,
    normalizeSymbol,
    formatSymbol,
    formatTimeframe,
    
    // Calculations
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
    
    // Utilities
    generateId,
    saveToStorage,
    loadFromStorage,
    debounce,
    copyToClipboard
};