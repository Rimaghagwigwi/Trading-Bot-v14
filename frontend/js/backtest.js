/**
 * Gestion de l'interface Backtest
 * Gère la configuration, l'exécution et l'affichage des résultats de backtest
 */

class BacktestManager {
    constructor() {
        this.last_response = null;
        this.backtestHistory = [];
        this.charts = {};
        this.isRunning = false;
    }
    
    /**
     * Initialisation du gestionnaire backtest
     */
    async init() {

        console.log('🚀 Initialisation du BacktestManager...');
        
        // Récupération des symboles disponibles
        try {
            const response = await window.API.config.getSymbols();
            console.log('Symboles récupérés:', response.data.symbols);
            this.populateSymbolCheckboxes(response.data.symbols);
        } catch (error) {
            console.warn('⚠️ Impossible de récupérer les symboles:', error);
        }
        
        // Récupération des timeframes disponibles
        try {
            const response = await window.API.config.getTimeframes();
            console.log('Timeframes récupérés:', response.data.timeframes);
            this.populateTimeframeSelect(response.data.timeframes);
        } catch (error) {
            console.warn('⚠️ Impossible de récupérer les timeframes:', error);
        }
        
        // Récupération des stratégies disponibles
        try {
            const response = await window.API.config.getStrategies();
            this.strategies = response.data.strategies || [];
            console.log('Stratégies récupérées:', this.strategies);
            this.populateStrategySelect(this.strategies);
        } catch (error) {
            console.warn('⚠️ Impossible de récupérer les stratégies:', error);
        }
        
        // Récupération de la configuration par défaut
        try {
            const config = await window.API.config.getDefaults();
            console.log('Configuration par défaut récupérée:', config);
            this.applyDefaultConfig(config.data);
        } catch (error) {
            console.warn('⚠️ Impossible de récupérer la configuration par défaut:', error);
        }

        console.log('✅ BacktestManager initialisé avec succès');
    }

    // Peuple la selection des symboles
    populateSymbolCheckboxes(symbols) {
        const grid = document.getElementById('trading-pairs-grid');
        if (!grid || !symbols) {
            console.warn('⚠️ Impossible de peupler la sélection des symboles : élément ou données manquantes');
            return;
        }
        grid.innerHTML = '';

        symbols.forEach(symbol => {
            const pairItem = document.createElement('label');
            pairItem.className = 'checkbox';

            pairItem.innerHTML = `
                <input type="checkbox" name="trading-pairs" value="${symbol}">
                <div class="checkbox-card">
                    <span class="checkbox-name">${symbol}</span>
                </div>
            `;
            
            grid.appendChild(pairItem);
        });
    }

    // Peuple le select des timeframes
    populateTimeframeSelect(timeframes) {
        const timeframeSelect = document.getElementById('timeframe');
        if (!timeframeSelect || !timeframes) return;

        timeframeSelect.innerHTML = '';
        timeframes.forEach(timeframe => {
            const option = document.createElement('option');
            option.value = timeframe;
            option.textContent = window.Utils.formatTimeframe(timeframe);
            timeframeSelect.appendChild(option);
        });
    }

    // Peuple le select des stratégies
    populateStrategySelect(strategies) {
        const strategySelect = document.getElementById('strategy');
        if (!strategySelect || !strategies) return;

        strategySelect.innerHTML = '';
        strategies.forEach(strategy => {
            const option = document.createElement('option');
            option.value = strategy.name;
            option.textContent = strategy.display_name;
            strategySelect.appendChild(option);
        });

        this.setupStrategyChangeListener();
    }

    // Peuple les selects des paramètres de stratégie
    populateStrategyParams(strategy_name) {
        const paramsContainer = document.getElementById('strategy-params-grid');
        if (!paramsContainer) return;
        
        const strategy = this.strategies.find(s => s.name === strategy_name);
        const params = strategy ? strategy.parameters : null;
        console.log('Paramètres récupérés:', params);

        if (!params || Object.keys(params).length === 0) {
            return;
        }
        paramsContainer.style.display = 'grid';
        paramsContainer.innerHTML = ``;
   
        Object.entries(params).forEach(([key, value]) => {
            const paramItem = document.createElement('div');
            paramItem.className = 'form-group';
            paramItem.innerHTML = `
                <label class="form-label" for="${key}">${value.display_name}</label>
                <input class="form-input" type="number" id="${key}" value="${value.default}" step="any">
            `;
            paramsContainer.appendChild(paramItem);
        });
    }

    setupStrategyChangeListener() {
        const strategySelect = document.getElementById('strategy');
        if (!strategySelect) return;
        
        // Ajouter le nouvel event listener
        strategySelect.addEventListener('change', (event) => {
            this.populateStrategyParams(event.target.value);
        });
    }

    
    // Applique la configuration par défaut
    applyDefaultConfig(config) {
        if (!config) return;
        const timeframeSelect = document.getElementById('timeframe');   
        const strategySelect = document.getElementById('strategy');
        const initialCapitalInput = document.getElementById('initial-capital');
        const commissionInput = document.getElementById('commission');
        const startDate = document.querySelector('#start-date');
        const endDate = document.querySelector('#end-date');

        if (timeframeSelect && config.timeframe) {
            timeframeSelect.value = config.timeframe;
        }
        if (strategySelect && config.strategy) {
            strategySelect.value = config.strategy;
            this.populateStrategyParams(config.strategy);
        }
        if (initialCapitalInput && config.initial_capital) {
            initialCapitalInput.value = config.initial_capital;
        }
        if (commissionInput && config.commission_rate) {
            commissionInput.value = config.commission_rate * 100; // Convertit en pourcentage
        }
        if (startDate && endDate && config.days) {
            const start = new Date();
            start.setDate(start.getDate() - config.days);
            const end = new Date();
            const startValue = start.toISOString().split('T')[0];
            const endValue = end.toISOString().split('T')[0];
            console.log(`Dates par défaut appliquées: ${startValue} → ${endValue}`);
            startDate.value = startValue;
            endDate.value = endValue;
        }
    }

    //Récupère la configuration du backtest
    getBacktestConfig() {
        const symbols = Array.from(document.querySelectorAll('input[name="trading-pairs"]:checked')).map(input => input.value);
        const timeframe = document.getElementById('timeframe').value;
        const strategy_name = document.getElementById('strategy').value;
        const strategy_params = this.getStrategyParams(strategy_name);
        const initial_capital = document.getElementById('initial-capital').value || 10000;
        const start_date = document.getElementById('start-date').value;
        const end_date = document.getElementById('end-date').value;
        const commission = parseFloat(document.getElementById('commission').value) || 0.1;

        const class_name = this.strategies.find(s => s.name === strategy_name)?.class;

        return {
            'symbols': symbols,
            'timeframe': timeframe,
            'strategy': strategy_name,
            'strategy_class': class_name,
            'strategy_params': strategy_params,
            'initial_capital': initial_capital,
            'start_date': new Date(start_date),
            'end_date': new Date(end_date),
            'commission_rate': commission / 100 // Convertit en pourcentage
        };
    }

    getStrategyParams(strategy_name) {
        const strategy = this.strategies.find(s => s.name === strategy_name);
        console.log('Stratégie trouvée:', strategy);
        if (!strategy || !strategy.parameters) {
            console.warn('⚠️ Aucune stratégie ou paramètres trouvés pour:', strategy_name);
            return {};
        }
        const params = {};
        // Récupération des valeurs des paramètres
        Object.entries(strategy.parameters).forEach(([key, param]) => {
            const value = document.getElementById(key).value;
            params[key] = parseFloat(value) || param.default; // Utilise la valeur par défaut si la saisie est invalide
        });

        return params;
    }

    //Démarre le backtest
    startBacktest() {
        this.isRunning = true;
        console.log('✅ Démarrage du backtest...');
        // Logique pour démarrer le backtest
        const config = this.getBacktestConfig();
        if (!config.symbols || !config.timeframe || !config.strategy) {
            console.error('❌ Configuration du backtest manquante.');
            this.isRunning = false;
            return;
        }
        console.log('🔧 Configuration du backtest:', config)
        window.API.backtest.run(config)
            .then(response => {
                if (!response.success) {
                    console.error('❌ Erreur dans la réponse du backtest:', response);
                } else {
                    this.backtestHistory.push(response.data);
                    this.displayResults(response.data);
                }
                this.isRunning = false;
            })
            .catch(error => {
                console.error('❌ Erreur lors du backtest:', error);
                this.isRunning = false;
            });
    }

    /**
     * Affiche les résultats du backtest dans l'interface
     * @param {Object} data - Données de la réponse de l'API
     */
    displayResults(data) {
        console.log('📊 Affichage des résultats du backtest:', data);

        // Afficher la section des résultats
        const resultsSection = document.getElementById('backtest-results');
        resultsSection.style.display = 'block';

        // 1. Afficher les métriques de performance
        this.displayMetrics(data.metrics);

        // 2. Créer le graphique
        this.displayChart(data.results, data.market_data);

        // 3. Ajouter à l'historique des backtests
        this.addToBacktestHistory(data.parameters, data.results, data.metrics);

        // 4. Faire défiler vers les résultats
        resultsSection.scrollIntoView({ behavior: 'smooth' });

        // 5. Afficher un message de succès
        window.Utils.showSuccess('Backtest terminé avec succès !');

    }

    /**
     * Affiche les métriques de performance
     * @param {Object} metrics - Métriques calculées
     */
    displayMetrics(metrics) {
        try {
            const grid = document.getElementById('metrics-cards-grid');
            if (!grid) return;

            grid.innerHTML = ''; // Réinitialiser le contenu

            // Créer les éléments de métriques
            const METRICS_CARDS = {
                'Rendement': [
                    { id: 'total-return', label: 'Rendement total', value: metrics['return_metrics']['total_return_pct'].toFixed(2) + '%'},
                    { id: 'annualized-return', label: 'Rendement annualisé', value: metrics['return_metrics']['annualized_return_pct'].toFixed(2) + '%'}
                ],
                'Comparaison avec Buy and Hold': [
                    { id: 'benchmark-return', label: 'Rendement du benchmark', value: metrics['benchmark_metrics']['benchmark_return_pct'].toFixed(2) + '%'},
                    { id: 'outperformance', label: 'Surperformance', value: metrics['benchmark_metrics']['excess_return_pct'].toFixed(2) + '%'}
                ],
                'Risque': [
                    { id: 'sharpe-ratio', label: 'Ratio de Sharpe', value: metrics['risk_metrics']['sharpe_ratio'].toFixed(2)},
                    { id: 'sortino-ratio', label: 'Ratio de Sortino', value: metrics['risk_metrics']['sortino_ratio'].toFixed(2)},
                    { id: 'max-drawdown', label: 'Drawdown maximum', value: metrics['risk_metrics']['max_drawdown_pct'].toFixed(2) + '%'},
                    { id: 'volatility', label: 'Volatilité', value: metrics['risk_metrics']['volatility_pct'].toFixed(2) + '%'}
                ],
                'Trade': [
                    { id: 'total_trades', label: 'Total des trades', value: metrics['trade_metrics']['total_trades']},
                    { id: 'win-rate', label: 'Taux de victoire', value: metrics['trade_metrics']['win_rate_pct'].toFixed(2) + '%'},
                ]
            };
            
            // Fonction pour déterminer la couleur basée sur la valeur
            function getColorClass(value, metricId) {
            // Définition des seuils pour chaque métrique
            const thresholds = {
                'total-return': { win: 10, neutral: 0 },           // > 10% = win, 0-10% = neutral, < 0% = loss
                'annualized-return': { win: 15, neutral: 0 },      // > 15% = win
                'benchmark-return': { win: 8, neutral: 0 },        // > 8% = win
                'outperformance': { win: 5, neutral: 0 },          // > 5% = win
                'sharpe-ratio': { win: 1.5, neutral: 1 },          // > 1.5 = win, 1-1.5 = neutral, < 1 = loss
                'sortino-ratio': { win: 2, neutral: 1 },           // > 2 = win
                'max-drawdown': { win: -5, neutral: -10 },         // > -5% = win, -5% à -10% = neutral, < -10% = loss
                'volatility': { win: 15, neutral: 25 },            // < 15% = win, 15-25% = neutral, > 25% = loss
                'win-rate': { win: 60, neutral: 50 }               // > 60% = win, 50-60% = neutral, < 50% = loss
            };
            
            // Cas neutres (pas de coloration)
            const neutralMetrics = ['total_trades'];
            
            if (neutralMetrics.includes(metricId)) {
                return '';
            }
            
            const threshold = thresholds[metricId];
            if (!threshold) {
                return ''; // Pas de seuil défini
            }
            
            const numericValue = parseFloat(value.replace('%', ''));
            
            // Métriques où plus bas = mieux
            const lowerIsBetter = ['max-drawdown', 'volatility'];
            
            if (lowerIsBetter.includes(metricId)) {
                if (numericValue <= threshold.win) return 'win-color';
                if (numericValue <= threshold.neutral) return 'neutral-color';
                return 'loss-color';
            } else {
                if (numericValue >= threshold.win) return 'win-color';
                if (numericValue >= threshold.neutral) return 'neutral-color';
                return 'loss-color';
            }
        }


            //Creation des cartes de métriques
            Object.entries(METRICS_CARDS).forEach(([categoryTitle, metrics]) => {
            const card = document.createElement('div');
            card.className = 'card';
            
            const header = document.createElement('div');
            header.className = 'card-header';
            header.textContent = categoryTitle;
            card.appendChild(header);
            
            const cardBody = document.createElement('div');
            cardBody.className = 'card-body';

            metrics.forEach(metric => {
                const metricElement = document.createElement('div');
                metricElement.className = 'metric-item';
                
                const label = document.createElement('span');
                label.className = 'metric-label';
                label.textContent = metric.label;
                
                const value = document.createElement('span');
                value.className = 'metric-value';
                value.id = metric.id;
                value.textContent = metric.value;
                
                metricElement.appendChild(label);
                metricElement.appendChild(value);
                cardBody.appendChild(metricElement);

                // Appliquer la couleur selon la valeur
                const colorClass = getColorClass(metric.value, metric.id);
                if (colorClass) {
                    value.classList.add(colorClass);
                }
            });

            card.appendChild(cardBody);
            grid.appendChild(card);
        });

        } catch (error) {
            console.error('Erreur lors de l\'affichage des métriques:', error);
        }
    }

    displayChart(results, market_data) {
        const sectionID = document.getElementById('backtest-charts');
        sectionID.style.display = 'block';

        console.log(results)
        // Réinitialiser le conteneur des graphiques
        const chartsContainer = document.getElementById('backtest-charts-container');
        chartsContainer.innerHTML = `<div class="chart" id="comparison-chart"></div>`;

        // Graphique de comparaison
        chartManager.createComparisonChart('comparison-chart', 'Résultats backtest', results.graph_data);

        // Graphique de chaque crypto
        Object.entries(market_data).forEach(([symbol, data]) => {
            // resultats.trades_history = [{symbol: 'BTCUSDC', entry: 100, exit: 110, ...}, ...]
            chartManager.createCandlestickChart(`${symbol}-candle-chart`, `${symbol}`, data);
            chartManager.addSignalsToChart(`${symbol}-candle-chart`, results.trades_history.filter(trade => trade.symbol === symbol));
        });
    }

    /**
     * Ajoute les résultats à l'historique des backtests
     * @param {Object} results - Résultats du backtest
     */
    addToBacktestHistory(params, results, metrics) {
        const historyTable = document.getElementById('backtest-history').getElementsByTagName('tbody')[0];
        const newRow = historyTable.insertRow(0); // Insérer en première position

        // Formatage des données
        const currentDate = new Date().toLocaleString('fr-FR');
        const period = `${params.start_date.split('T')[0]} → ${params.end_date.split('T')[0]}`;
        const returnValue = metrics.return_metrics.total_return_pct.toFixed(2);
        const sharpeValue = metrics.risk_metrics.sharpe_ratio?.toFixed(2) || 'N/A';

        // Création des cellules
        newRow.innerHTML = `
            <td>${currentDate}</td>
            <td>${params.symbols}</td>
            <td>${params.strategy}</td>
            <td>${period}</td>
            <td class="${returnValue >= 0 ? 'positive' : 'negative'}">${returnValue}%</td>
            <td class="${sharpeValue >= 1 ? 'positive' : sharpeValue >= 0 ? 'neutral' : 'negative'}">${sharpeValue}</td>
        `;

        // Limiter l'historique à 10 entrées
        while (historyTable.rows.length > 10) {
            historyTable.deleteRow(historyTable.rows.length - 1);
        }
    }

    /**
     * Exporte les résultats en CSV
     * @param {string} symbol - Symbole de la crypto
     * @param {string} strategy - Nom de la stratégie
     */
    exportResults(symbol, strategy) {
        try {
            // Cette fonction devrait être appelée avec les résultats actuels
            // Pour l'instant, on affiche juste un message
            window.Utils.showSuccess(`Export des résultats pour ${symbol} - ${strategy} (à implémenter)`);
        } catch (error) {
            console.error('Erreur lors de l\'export:', error);
            window.Utils.showError('Erreur lors de l\'export des résultats');
        }
    }

    // Fonction utilitaire pour formater les pourcentages
    formatPercentage(value, decimals = 2) {
        return (value * 100).toFixed(decimals) + '%';
    }

    // Fonction utilitaire pour formater les devises
    formatCurrency(value, currency = 'USDT', decimals = 2) {
        return value.toFixed(decimals) + ' ' + currency;
    }
}

// Instance globale
window.BacktestManager = new BacktestManager();

// Écouteur pour le bouton de lancement du backtest
document.getElementById('run-backtest').addEventListener('click', async () => {
    if (window.BacktestManager.isRunning) { 
        alert('Un backtest est déjà en cours.');
        return;
    }   

    // Démarrer le backtest
    window.BacktestManager.startBacktest();
});

// Auto-initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', () => {
    window.BacktestManager.init();
});

// Export pour utilisation avec modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = BacktestManager;
}