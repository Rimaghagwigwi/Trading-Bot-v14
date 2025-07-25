/**
 * ChartManager - Gestionnaire de graphiques pour bot de trading
 * Version corrigée pour TradingView Lightweight Charts v5
 */

class ChartManager {
    constructor() {
        this.charts = new Map();
        
        this.chartOptions = {
            height: 400,
            layout: {
                background: { color: '#1a1a1a' },
                textColor: '#d1d5db',
            },
            grid: {
                vertLines: { color: '#2d3748' },
                horzLines: { color: '#2d3748' },
            },
            crosshair: {
                mode: window.LightweightCharts.CrosshairMode.Normal,
            },
            rightPriceScale: {
                borderColor: '#485563',
            },
            timeScale: {
                borderColor: '#485563',
                timeVisible: true,
            }
        };

        this.seriesOptions = {
            portfolio: {
                color: '#10b981',
                lineWidth: 2,
                title: 'Portfolio'
            },
            benchmark: {
                color: '#f59e0b',
                lineWidth: 2,
                title: 'Buy & Hold'
            },
            candlestick: {
                upColor: '#10b981',
                downColor: '#ef4444',
                borderUpColor: '#10b981',
                borderDownColor: '#ef4444',
                wickUpColor: '#10b981',
                wickDownColor: '#ef4444',
            }
        };

    }

    /**
     * Crée un graphique de comparaison Portfolio vs Benchmark
     */
    async createComparisonChart(graphID, display_name, graph_data) {
        console.log(`🔄 Création graphique comparaison: ${graphID}`);

        const container = document.getElementById(graphID);

        // Nettoyer le conteneur
        container.innerHTML = '';

        // Créer le titre
        const titleDiv = document.createElement('div');
        titleDiv.className = 'chart-title';
        titleDiv.innerHTML = `<h3><i class="fas fa-chart-line"></i> ${display_name}</h3>`;
        container.appendChild(titleDiv);

        // Créer le conteneur graphique
        const chartContainer = document.createElement('div');
        chartContainer.className = 'chart-container';
        container.appendChild(chartContainer);

        // Créer le graphique
        const chart = window.LightweightCharts.createChart(chartContainer, this.chartOptions);

        // Préparer les données
        const portfolioData = this.prepareLineData(graph_data.timestamp, graph_data.total_value);
        const benchmarkData = this.prepareLineData(graph_data.timestamp, graph_data.benchmark);
        const intervals = Object.keys(portfolioData);
        console.log(`📊 Intervalles valides: ${intervals.join(', ')}`);

        // Créer les séries avec la nouvelle API v5
        const portfolioSeries = chart.addSeries(window.LightweightCharts.LineSeries, this.seriesOptions.portfolio);
        const benchmarkSeries = chart.addSeries(window.LightweightCharts.LineSeries, this.seriesOptions.benchmark);
        this.setSeriesTimeframe(portfolioSeries, portfolioData, intervals[0]);
        this.setSeriesTimeframe(benchmarkSeries, benchmarkData, intervals[0]);

        // Ajouter redimensionnement
        this.setupResizeObserver(chart, chartContainer);

        // Ajouter les boutons de contrôle
        this.addChartControls(container, chart);
        const controlsDiv = container.querySelector('.chart-controls');

        console.log(`🔄 Ajout des boutons d'intervalle: ${intervals}`);
        for (const interval of intervals) {
            const button = document.createElement('button');
            console.log(`🔘 Ajout bouton intervalle: ${interval}`);
            button.innerText = interval;
            button.className = 'btn btn-sm btn-secondary chart-timeframe-btn';
            button.addEventListener('click', () => {
                this.setSeriesTimeframe(portfolioSeries, portfolioData, interval);
                this.setSeriesTimeframe(benchmarkSeries, benchmarkData, interval);
                chart.timeScale().fitContent();
            });
            controlsDiv.appendChild(button);
        }

        console.log(`✅ Graphique comparaison ${graphID} créé`);
        this.charts.set(graphID, {'chart': chart, 'series': [portfolioSeries, benchmarkSeries]});
        return chart;
    }

    /**
     * Prepares downsampled line chart data for multiple valid timeframes based on input timestamps and values.
     * Filters and aligns data, determines valid timeframes according to data granularity, and downsamples accordingly.
     *
     * @param {Array<string>} timestamps - Array of string timestamps '2025-01-25 01:00:00'.
     * @param {Array<number>} values - Array of numeric values corresponding to each timestamp.
     * @returns {{interval: string, data: Array<{time: number, value: number}>}} Downsampled data for each valid timeframe.
     *
     * @example
     * const timestamps = ['2024-01-01 00:00:00', '2024-01-01 01:00:00', '2024-01-01 02:00:00', ...];
     * const values = [100, 105, 110, ...];
     * const data = prepareLineData(timestamps, values);
     * // Returns: {'1h': [{time: 1704067200, value: 100}, ...], '4h': [{time: 1704067200, value: 100}, ...], ...}
     */
    prepareLineData(timestamps, values) {
        // Input validation
        if (!Array.isArray(timestamps) || !Array.isArray(values)) {
            throw new Error('Both timestamps and values must be arrays');
        }
        
        if (timestamps.length !== values.length) {
            throw new Error('Timestamps and values arrays must have the same length');
        }
        
        if (timestamps.length === 0) {
            return {};
        }

        // Parse timestamps - pas besoin de trier car intervalle régulier
        const parsedData = timestamps.map((timestamp, index) => ({
            time: new Date(timestamp).getTime() / 1000,
            value: values[index]
        }));

        // Filtrer les données invalides
        const validData = parsedData.filter(item => !isNaN(item.time) && !isNaN(item.value));
        
        if (validData.length < 2) {
            return { 'raw': validData };
        }

        // Calculer l'intervalle source (régulier)
        const sourceInterval = validData[1].time - validData[0].time;
        const timeSpan = validData[validData.length - 1].time - validData[0].time;

        // Définir les timeframes disponibles
        const timeframes = {
            '1m': 60,
            '5m': 300,
            '15m': 900,
            '30m': 1800,
            '1h': 3600,
            '4h': 14400,
            '1d': 86400,
            '1w': 604800
        };

        // Sélectionner les timeframes valides
        const validTimeframes = Object.entries(timeframes).filter(([name, interval]) => {
            // Le timeframe doit être un multiple de l'intervalle source
            const isMultiple = interval % sourceInterval === 0 || interval >= sourceInterval;
            
            // Doit avoir au moins 5 points finaux pour être utile
            const hasEnoughFinalPoints = timeSpan / interval >= 4;
            
            // Le timeframe doit être plus grand que l'intervalle source
            const isLargerThanSource = interval >= sourceInterval;
            
            return isMultiple && hasEnoughFinalPoints && isLargerThanSource;
        });

        // Si aucun timeframe valide, retourner les données originales
        if (validTimeframes.length === 0) {
            return { 'raw': validData };
        }

        const results = {};

        // Traiter chaque timeframe valide
        validTimeframes.forEach(([intervalName, intervalSeconds]) => {
            // result[intervalName] = this.downsampleRegularData(validData, intervalSeconds, sourceInterval);

            const result = [];
            const pointsPerBucket = Math.round(intervalSeconds / sourceInterval);
            
            // Aligner le temps de départ sur une limite d'intervalle
            const startTime = validData[0].time;
            const alignedStartTime = Math.floor(startTime / intervalSeconds) * intervalSeconds;

            for (let i = 0; i < validData.length; i += pointsPerBucket) {
                // Récupérer les points pour ce bucket
                const bucketPoints = validData.slice(i, Math.min(i + pointsPerBucket, validData.length));
                
                if (bucketPoints.length === 0) continue;

                // Calculer la moyenne des valeurs
                const avgValue = bucketPoints.reduce((sum, point) => sum + point.value, 0) / bucketPoints.length;
                
                // Le temps du bucket est basé sur le premier point du bucket, aligné
                const bucketTime = alignedStartTime + Math.floor(i / pointsPerBucket) * intervalSeconds;

                result.push({
                    time: bucketTime,
                    value: Math.round(avgValue * 100) / 100
                });
            }
            results[intervalName] = result;
        });

        return results;
    }

    async createCandlestickChart(graphID, display_name, graph_data) {
        console.log(`🔄 Création graphique bougies: ${graphID}`);
        console.log(`📊 Données reçues:`, graph_data);
        const container = document.createElement('div');
        container.className = 'chart';
        container.id = graphID;

        document.getElementById('backtest-charts-container').appendChild(container);

        // Nettoyer le conteneur
        container.innerHTML = '';

        // Créer le titre
        const titleDiv = document.createElement('div');
        titleDiv.className = 'chart-title';
        titleDiv.innerHTML = `<h3><i class="fas fa-chart-line"></i> ${display_name}</h3>`;
        container.appendChild(titleDiv);

        // Créer le conteneur graphique
        const chartContainer = document.createElement('div');
        chartContainer.className = 'chart-container';
        container.appendChild(chartContainer);

        // Créer le graphique
        const chart = window.LightweightCharts.createChart(chartContainer, this.chartOptions);

        // Préparer les données
        const timestamps = graph_data.timestamp;
        const open = graph_data.open;
        const high = graph_data.high;
        const low = graph_data.low;
        const close = graph_data.close;

        const candlestickData = this.prepareCandlestickData(timestamps, open, high, low, close);
        const intervals = Object.keys(candlestickData);
        console.log(`📊 Intervalles valides: ${intervals.join(', ')}`);

        // Créer les séries avec la nouvelle API v5
        const candlestickSeries = chart.addSeries(window.LightweightCharts.CandlestickSeries, this.seriesOptions.candlestick);
        this.setSeriesTimeframe(candlestickSeries, candlestickData, intervals[0]);

        // Ajouter redimensionnement
        this.setupResizeObserver(chart, chartContainer);

        // Ajouter les boutons de contrôle
        this.addChartControls(container, chart);
        const controlsDiv = container.querySelector('.chart-controls');

        console.log(`🔄 Ajout des boutons d'intervalle: ${intervals}`);
        for (const interval of intervals) {
            const button = document.createElement('button');
            console.log(`🔘 Ajout bouton intervalle: ${interval}`);
            button.innerText = interval;
            button.className = 'btn btn-sm btn-secondary chart-timeframe-btn';
            button.addEventListener('click', () => {
                this.setSeriesTimeframe(candlestickSeries, candlestickData, interval);
                chart.timeScale().fitContent();
            });
            controlsDiv.appendChild(button);
        }

        console.log(`✅ Graphique chandeliers ${graphID} créé`);
        this.charts.set(graphID, {'chart': chart, 'series': [candlestickSeries]});
        return chart;
    }

    prepareCandlestickData(timestamps, open, high, low, close) {
        const rawCandlestickData = [];
        for (let i = 0; i < timestamps.length; i++) {
            rawCandlestickData.push({
                time: new Date(timestamps[i]).getTime() / 1000,
                open: open[i],
                high: high[i],
                low: low[i],
                close: close[i]
            });
        }

        // Calculer l'intervalle source (régulier)
        const sourceInterval = rawCandlestickData[1].time - rawCandlestickData[0].time;
        const timeSpan = rawCandlestickData[rawCandlestickData.length - 1].time - rawCandlestickData[0].time;

        // Définir les timeframes disponibles
        const timeframes = {
            '1m': 60,
            '5m': 300,
            '15m': 900,
            '30m': 1800,
            '1h': 3600,
            '4h': 14400,
            '1d': 86400,
            '1w': 604800
        };

        const candlestickData = {};
        // Sélectionner les timeframes valides
        const validTimeframes = Object.entries(timeframes).filter(([name, interval]) => {
            return timeSpan / interval >= 4 && interval >= sourceInterval;
        });

        validTimeframes.forEach(([name, interval]) => {
            const pointsPerBucket = Math.round(interval / sourceInterval);
            const result = [];

            for (let i = 0; i < rawCandlestickData.length; i += pointsPerBucket) {
                const bucket = rawCandlestickData.slice(i, i + pointsPerBucket);
                if (bucket.length === 0) continue;

                const open = bucket[0].open;
                const close = bucket[bucket.length - 1].close;
                const high = Math.max(...bucket.map(b => b.high));
                const low = Math.min(...bucket.map(b => b.low));

                result.push({ time: bucket[0].time, open, close, high, low });
            }

            candlestickData[name] = result;
        });

        return candlestickData;
    }

    addSignalsToChart(graphID, signals) {
        const chart = this.charts.get(graphID);
        if (!chart) return;
        console.log(`🔄 Ajout des signaux au graphique: ${graphID}`)

        const markers = [];
        signals.forEach(signal => {
            console.log(`🔘 Ajout signal: ${signal.type} à ${signal.timestamp}`);
            markers.push({
                time: new Date(signal.timestamp).getTime() / 1000,
                position: signal.type === 'buy' ? 'belowBar' : 'aboveBar',
                color: signal.type === 'buy' ? 'green' : 'red',
                shape: signal.type === 'buy' ? 'arrowUp' : 'arrowDown',
                text: signal.type === 'buy' ? 'BUY' : 'SELL',
            });
        });
        console.log(`📊 Nombre de signaux ajoutés: ${markers.length}`);
        console.log('Séries avant ajout des marqueurs:', chart['series'][0]);
        window.LightweightCharts.createSeriesMarkers(chart['series'][0], markers);
    }

    setSeriesTimeframe(series, data, timeframe) {
        if (!series || !timeframe || !data) return;
        const filteredData = data[timeframe];
        series.setData(filteredData);
    }

    /**
     * Configure l'observateur de redimensionnement
     */
    setupResizeObserver(chart, container) {
        if (!window.ResizeObserver) {
            console.log('⚠️ ResizeObserver non supporté');
            return;
        }

        const resizeObserver = new ResizeObserver(entries => {
            for (let entry of entries) {
                const { width, height } = entry.contentRect;
                if (width > 0 && height > 0) {
                    chart.applyOptions({ width, height });
                }
            }
        });

        resizeObserver.observe(container);
    }

    /**
     * Ajoute les contrôles du graphique
     */
    addChartControls(container, chart) {
        const controlsDiv = document.createElement('div');
        controlsDiv.className = 'chart-controls';

        // Bouton pour ajuster le graphique
        const fitButton = document.createElement('button');
        fitButton.innerHTML = `<i class="fas fa-expand-arrows-alt"></i> Ajuster`;
        fitButton.className = 'btn btn-sm btn-secondary chart-control-btn';
        fitButton.addEventListener('click', () => chart.timeScale().fitContent());
        controlsDiv.appendChild(fitButton);

        // Bouton pour réinitialiser le zoom
        const scrollButton = document.createElement('button');
        scrollButton.className = 'btn btn-sm btn-secondary chart-control-btn';
        scrollButton.innerHTML = `<i class="fas fa-fast-forward"></i> Temps réel`;
        scrollButton.addEventListener('click', () => chart.timeScale().scrollToRealTime());
        controlsDiv.appendChild(scrollButton);

        container.appendChild(controlsDiv);
    }

    /**
     * Supprime un graphique
     */
    removeChart(graphID) {
        console.log(`🗑️ Suppression graphique: ${graphID}`);
        
        const chart = this.charts.get(graphID);
        if (chart?.remove) {
            chart.remove();
        }
        
        this.charts.delete(graphID);
        this.chartData.delete(graphID);
        this.chartSeries.delete(graphID);
        
        const container = document.getElementById(graphID);
        if (container) {
            container.innerHTML = '';
        }
        
        console.log(`✅ Graphique ${graphID} supprimé`);
        return true;
    }
}

// Initialisation
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.chartManager = new ChartManager();
    });
} else {
    window.chartManager = new ChartManager();
}