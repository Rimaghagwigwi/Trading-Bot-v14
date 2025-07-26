/**
 * main.js - Navigation management and application initialization
 * 
 * Features:
 * - Tab navigation (Backtest / Live Trading)
 * - Application initialization
 * - Connection status management
 * - Real-time clock
 * - Global event handling
 */

class MainApp {
    constructor() {
        this.currentTab = 'backtest';
        this.isInitialized = false;
        this.connectionCheckInterval = null;
        this.timeUpdateInterval = null;
        
        // DOM element references
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
     * Initializes the application
     */
    async init() {
        console.log('🚀 Initializing application...');
        
        try {
            // Initialize events
            this.setupEventListeners();
            
            // Initialize clock
            this.initClock();
            
            // Test backend connection
            await this.checkConnection();
            
            // Start intervals
            this.startIntervals();
            
            this.isInitialized = true;
            console.log('✅ Application initialized successfully');
            
            // Show welcome message
            this.showWelcomeMessage();
            
        } catch (error) {
            console.error('❌ Error during initialization:', error);
            window.Utils.showError('Error during application initialization');
        }
    }

    /**
     * Sets up keyboard shortcut event listeners
     */
    setupEventListeners() {
        // Tab navigation
        this.tabs.backtest.addEventListener('click', () => this.switchTab('backtest'));
        this.tabs.liveTrading.addEventListener('click', () => this.switchTab('liveTrading'));
        
        // Keyboard shortcuts
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
        
        // Window close handling
        window.addEventListener('beforeunload', (e) => {
            if (this.isLiveTradingActive()) {
                e.preventDefault();
                e.returnValue = 'The trading bot is active. Are you sure you want to leave?';
                return e.returnValue;
            }
        });
        
        // Resize handling
        window.addEventListener('resize', () => {
            this.handleResize();
        });
        
        // Page visibility handling
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.onPageHidden();
            } else {
                this.onPageVisible();
            }
        });
    }

    /**
     * Switches between tabs
     */
    switchTab(tabName) {
        if (this.currentTab === tabName) return;
        
        console.log(`🔄 Switching to tab: ${tabName}`);
        
        // Deactivate current tab
        this.tabs[this.currentTab].classList.remove('active');
        this.tabContents[this.currentTab].classList.remove('active');
        
        // Activate new tab
        this.currentTab = tabName;
        this.tabs[this.currentTab].classList.add('active');
        this.tabContents[this.currentTab].classList.add('active');
        
        // Notify tab change
        this.onTabChange(tabName);
        
        // Save preference
        window.Utils.saveToStorage('currentTab', tabName);
    }

    /**
     * Tab change handler
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
     * Refreshes the current tab
     */
    refreshCurrentTab() {
        console.log(`🔄 Refreshing tab: ${this.currentTab}`);
        
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
     * Checks backend connection
     */
    async checkConnection() {
        try {
            const isConnected = await window.API.testConnection();
            this.updateConnectionStatus(isConnected);
            return isConnected;
        } catch (error) {
            console.error('❌ Connection error:', error);
            this.updateConnectionStatus(false);
            return false;
        }
    }

    /**
     * Updates connection status
     */
    updateConnectionStatus(isConnected) {
        if (isConnected) {
            this.statusElements.icon.className = 'fas fa-circle text-success';
            this.statusElements.text.textContent = 'Connected';
            this.statusElements.container.className = 'connection-status connected';
        } else {
            this.statusElements.icon.className = 'fas fa-circle text-danger';
            this.statusElements.text.textContent = 'Disconnected';
            this.statusElements.container.className = 'connection-status disconnected';
        }
    }

    /**
     * Initializes the clock
     */
    initClock() {
        this.updateTime();
        this.timeUpdateInterval = setInterval(() => {
            this.updateTime();
        }, 1000);
    }

    /**
     * Updates displayed time
     */
    updateTime() {
        const now = new Date();
        const timeString = window.Utils.formatDate(now, 'datetime');
        this.timeElement.textContent = timeString;
    }


    /**
     * Starts intervals
     */
    startIntervals() {
        // Check connection every 30 seconds
        this.connectionCheckInterval = setInterval(() => {
            this.checkConnection();
        }, 30000);
    }

    /**
     * Stops intervals
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
     * Checks if live trading is active
     */
    isLiveTradingActive() {
        return window.LiveTradingManager && window.LiveTradingManager.isActive();
    }

    /**
     * Handles resize
     */
    handleResize() {
        // Notify chart managers
        if (window.ChartManager) {
            window.ChartManager.handleResize();
        }
    }

    /**
     * Page hidden
     */
    onPageHidden() {
        console.log('📱 Page hidden - Pausing updates');
        // Reduce update frequency
    }

    /**
     * Page visible
     */
    onPageVisible() {
        console.log('👁️ Page visible - Resuming updates');
        // Resume normal updates
        this.checkConnection();
    }

    /**
     * Shows welcome message
     */
    showWelcomeMessage() {
        window.Utils.showSuccess('Application initialized successfully!');
        
        // Hide message after 3 seconds
        setTimeout(() => {
            window.Utils.hideSuccess();
        }, 3000);
    }

    /**
     * Cleanup before destruction
     */
    destroy() {
        this.stopIntervals();
        
        // Cleanup event listeners
        document.removeEventListener('keydown', this.handleKeydown);
        window.removeEventListener('beforeunload', this.handleBeforeUnload);
        window.removeEventListener('resize', this.handleResize);
        document.removeEventListener('visibilitychange', this.handleVisibilityChange);
        
        console.log('🧹 Application cleaned up');
    }
}

// Global instance
window.MainApp = null;

// Initialization on DOM load
document.addEventListener('DOMContentLoaded', async () => {
    console.log('📄 DOM loaded - Initializing...');
    
    try {
        // Create main instance
        window.MainApp = new MainApp();
        
        // Wait for all scripts to load
        await window.MainApp.init();
        
    } catch (error) {
        console.error('❌ Fatal error during initialization:', error);
        
        // Show error message to user
        const errorDiv = document.createElement('div');
        errorDiv.className = 'fatal-error';
        errorDiv.innerHTML = `
            <h2>Initialization Error</h2>
            <p>A fatal error occurred while loading the application.</p>
            <p>Please check that the backend is running and reload the page.</p>
            <button onclick="location.reload()">Reload page</button>
        `;
        document.body.appendChild(errorDiv);
    }
});

// Cleanup before closing
window.addEventListener('beforeunload', () => {
    if (window.MainApp) {
        window.MainApp.destroy();
    }
});

// Global error handler
window.addEventListener('error', (event) => {
    console.error('❌ Global JavaScript error:', event.error);
    
    // Show error message to user
    if (window.Utils) {
        window.Utils.showError('An unexpected error occurred. Please reload the page.');
    }
    event.preventDefault();
    return true; // Prevent browser default error handling
});