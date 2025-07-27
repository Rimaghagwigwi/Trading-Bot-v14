/**
 * ChartManager - Chart manager for trading bot
 * Fixed version for TradingView Lightweight Charts v5
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
     * Creates a Portfolio vs Benchmark comparison chart
     */
    async createComparisonChart(graphID, display_name, graph_data) {
        console.log(`🔄 Creating comparison chart: ${graphID}`);

        const container = document.getElementById(graphID);

        // Clean container
        container.innerHTML = '';

        // Create title
        const titleDiv = document.createElement('div');
        titleDiv.className = 'chart-title';
        titleDiv.innerHTML = `<h3><i class="fas fa-chart-line"></i> ${display_name}</h3>`;
        container.appendChild(titleDiv);

        // Create chart container
        const chartContainer = document.createElement('div');
        chartContainer.className = 'chart-container';
        container.appendChild(chartContainer);

        // Create chart
        const chart = window.LightweightCharts.createChart(chartContainer, this.chartOptions);

        // Prepare data
        const portfolioData = this.prepareLineData(graph_data.timestamp, graph_data.total_value);
        const benchmarkData = this.prepareLineData(graph_data.timestamp, graph_data.benchmark);
        const intervals = Object.keys(portfolioData);
        console.log(`📊 Valid intervals: ${intervals.join(', ')}`);

        // Create series with new API v5
        const portfolioSeries = chart.addSeries(window.LightweightCharts.LineSeries, this.seriesOptions.portfolio);
        const benchmarkSeries = chart.addSeries(window.LightweightCharts.LineSeries, this.seriesOptions.benchmark);
        this.setSeriesTimeframe(portfolioSeries, portfolioData, intervals[0]);
        this.setSeriesTimeframe(benchmarkSeries, benchmarkData, intervals[0]);

        // Add resize observer
        this.setupResizeObserver(chart, chartContainer);

        // Add control buttons
        this.addChartControls(container, chart);
        const controlsDiv = container.querySelector('.chart-controls');

        console.log(`🔄 Adding interval buttons: ${intervals}`);
        for (const interval of intervals) {
            const button = document.createElement('button');
            console.log(`🔘 Adding interval button: ${interval}`);
            button.innerText = interval;
            button.className = 'btn btn-sm btn-secondary chart-timeframe-btn';
            button.addEventListener('click', () => {
                this.setSeriesTimeframe(portfolioSeries, portfolioData, interval);
                this.setSeriesTimeframe(benchmarkSeries, benchmarkData, interval);
                chart.timeScale().fitContent();
            });
            controlsDiv.appendChild(button);
        }

        console.log(`✅ Comparison chart ${graphID} created`);
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

        // Parse timestamps - no need to sort as interval is regular
        const parsedData = timestamps.map((timestamp, index) => ({
            time: new Date(timestamp).getTime() / 1000,
            value: values[index]
        }));

        // Filter invalid data
        const validData = parsedData.filter(item => !isNaN(item.time) && !isNaN(item.value));

        if (validData.length < 2) {
            return { 'raw': validData };
        }

        // Calculate source interval (regular)
        const sourceInterval = validData[1].time - validData[0].time;
        const timeSpan = validData[validData.length - 1].time - validData[0].time;

        // Define available timeframes
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

        // Select valid timeframes
        const validTimeframes = Object.entries(timeframes).filter(([name, interval]) => {
            // Timeframe must be a multiple of source interval
            const isMultiple = interval % sourceInterval === 0 || interval >= sourceInterval;

            // Must have at least 5 final points to be useful
            const hasEnoughFinalPoints = timeSpan / interval >= 4;

            // Timeframe must be larger than source interval
            const isLargerThanSource = interval >= sourceInterval;

            return isMultiple && hasEnoughFinalPoints && isLargerThanSource;
        });

        // If no valid timeframe, return original data
        if (validTimeframes.length === 0) {
            return { 'raw': validData };
        }

        const results = {};

        // Process each valid timeframe
        validTimeframes.forEach(([intervalName, intervalSeconds]) => {
            const result = [];
            const pointsPerBucket = Math.round(intervalSeconds / sourceInterval);

            // Align start time to interval boundary
            const startTime = validData[0].time;
            const alignedStartTime = Math.floor(startTime / intervalSeconds) * intervalSeconds;

            for (let i = 0; i < validData.length; i += pointsPerBucket) {
                // Get points for this bucket
                const bucketPoints = validData.slice(i, Math.min(i + pointsPerBucket, validData.length));

                if (bucketPoints.length === 0) continue;

                // Calculate average value
                const avgValue = bucketPoints.reduce((sum, point) => sum + point.value, 0) / bucketPoints.length;

                // Bucket time is based on first point of bucket, aligned
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
        console.log(`🔄 Creating candlestick chart: ${graphID}`);
        console.log(`📊 Data received:`, graph_data);
        const container = document.createElement('div');
        container.className = 'chart';
        container.id = graphID;

        document.getElementById('backtest-charts-container').appendChild(container);

        // Clean container
        container.innerHTML = '';

        // Create title
        const titleDiv = document.createElement('div');
        titleDiv.className = 'chart-title';
        titleDiv.innerHTML = `<h3><i class="fas fa-chart-line"></i> ${display_name}</h3>`;
        container.appendChild(titleDiv);

        // Create chart container
        const chartContainer = document.createElement('div');
        chartContainer.className = 'chart-container';
        container.appendChild(chartContainer);

        // Create chart
        const chart = window.LightweightCharts.createChart(chartContainer, this.chartOptions);

        // Prepare data
        const timestamps = graph_data.timestamps;
        const open = graph_data.open;
        const high = graph_data.high;
        const low = graph_data.low;
        const close = graph_data.close;

        const candlestickData = this.prepareCandlestickData(timestamps, open, high, low, close);
        const intervals = Object.keys(candlestickData);
        console.log(`📊 Valid intervals: ${intervals.join(', ')}`);

        // Create series with new API v5
        const candlestickSeries = chart.addSeries(window.LightweightCharts.CandlestickSeries, this.seriesOptions.candlestick);
        this.setSeriesTimeframe(candlestickSeries, candlestickData, intervals[0]);

        // Add resize observer
        this.setupResizeObserver(chart, chartContainer);

        // Add control buttons
        this.addChartControls(container, chart);
        const controlsDiv = container.querySelector('.chart-controls');

        console.log(`🔄 Adding interval buttons: ${intervals}`);
        for (const interval of intervals) {
            const button = document.createElement('button');
            console.log(`🔘 Adding interval button: ${interval}`);
            button.innerText = interval;
            button.className = 'btn btn-sm btn-secondary chart-timeframe-btn';
            button.addEventListener('click', () => {
                this.setSeriesTimeframe(candlestickSeries, candlestickData, interval);
                chart.timeScale().fitContent();
            });
            controlsDiv.appendChild(button);
        }

        console.log(`✅ Candlestick chart ${graphID} created`);
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

        // Calculate source interval (regular)
        const sourceInterval = rawCandlestickData[1].time - rawCandlestickData[0].time;
        const timeSpan = rawCandlestickData[rawCandlestickData.length - 1].time - rawCandlestickData[0].time;

        // Define available timeframes
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
        // Select valid timeframes
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
        console.log(`🔄 Adding signals to chart: ${graphID}`)

        const markers = [];
        signals.forEach(signal => {
            console.log(`🔘 Adding signal: ${signal.type} at ${signal.timestamp}`);
            markers.push({
                time: new Date(signal.timestamp).getTime() / 1000,
                position: signal.type === 'buy' ? 'belowBar' : 'aboveBar',
                color: signal.type === 'buy' ? 'green' : 'red',
                shape: signal.type === 'buy' ? 'arrowUp' : 'arrowDown',
                text: signal.type === 'buy' ? 'BUY' : 'SELL',
            });
        });
        console.log(`📊 Number of signals added: ${markers.length}`);
        console.log('Series before adding markers:', chart['series'][0]);
        window.LightweightCharts.createSeriesMarkers(chart['series'][0], markers);
    }

    setSeriesTimeframe(series, data, timeframe) {
        if (!series || !timeframe || !data) return;
        const filteredData = data[timeframe];
        series.setData(filteredData);
    }

    /**
     * Sets up resize observer
     */
    setupResizeObserver(chart, container) {
        if (!window.ResizeObserver) {
            console.log('⚠️ ResizeObserver not supported');
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
     * Adds chart controls
     */
    addChartControls(container, chart) {
        const controlsDiv = document.createElement('div');
        controlsDiv.className = 'chart-controls';

        // Button to fit chart
        const fitButton = document.createElement('button');
        fitButton.innerHTML = `<i class="fas fa-expand-arrows-alt"></i> Fit`;
        fitButton.className = 'btn btn-sm btn-secondary chart-control-btn';
        fitButton.addEventListener('click', () => chart.timeScale().fitContent());
        controlsDiv.appendChild(fitButton);

        // Button to reset zoom
        const scrollButton = document.createElement('button');
        scrollButton.className = 'btn btn-sm btn-secondary chart-control-btn';
        scrollButton.innerHTML = `<i class="fas fa-fast-forward"></i> Real time`;
        scrollButton.addEventListener('click', () => chart.timeScale().scrollToRealTime());
        controlsDiv.appendChild(scrollButton);

        container.appendChild(controlsDiv);
    }

    /**
     * Removes a chart
     */
    removeChart(graphID) {
        console.log(`🗑️ Removing chart: ${graphID}`);

        const chart = this.charts.get(graphID);
        if (chart?.remove) {
            chart.remove();
        }

        this.charts.delete(graphID);
        this.chartData?.delete?.(graphID);
        this.chartSeries?.delete?.(graphID);

        const container = document.getElementById(graphID);
        if (container) {
            container.innerHTML = '';
        }

        console.log(`✅ Chart ${graphID} removed`);
        return true;
    }
}

// Initialization
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.chartManager = new ChartManager();
    });
} else {
    window.chartManager = new ChartManager();
}
