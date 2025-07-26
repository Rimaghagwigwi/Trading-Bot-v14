# Crypto Trading Bot Project

## 🎯 Project Overview

**Goal:** Build a local crypto trading bot with a dual-mode interface: Backtest and Live Trading.

**Key Specifications:**

- Local use only (no deployment)
- Interface: Tab navigation (Backtest / Live Trading)
- Supported timeframes: 15m, 30m, 1h
- Risk management: Yes (stop-loss, take-profit)
- Charts: Strategy vs buy & hold comparison
- Data storage: CSV files

**Default Configuration:**

- Initial capital: 1000 USDT
- Trading fee: 0.1% per trade
- Default period: 30 days
- Default crypto: BTC/USDT
- Default timeframe: 1h

## 🏗️ Simplified File Structure

```
trading-bot/
├── frontend/
│   ├── index.html                 # Main page with tab navigation
│   ├── css/
│   │   ├── chart.js               # Chart styles
│   │   └── styles.css             # Global + navigation styles
│   ├── js/
│   │   ├── main.js                # Tab navigation + initialization
│   │   ├── backtest.js            # Backtest page logic
│   │   ├── live-trading.js        # Live trading page logic
│   │   ├── charts.js              # Shared Chart.js logic
│   │   ├── api.js                 # Shared backend communication
│   │   └── utils.js               # Shared utilities
├── backend/
│   ├── config.json                # Timeframes and symbols config
│   ├── app.py                     # Flask server (backtest + live routes)
│   ├── strategies/
│   │   ├── DCA_strategy.py 
│   │   ├── RSI_strategy.py
│   │   └── buy_and_hold.py
│   ├── data/
│   │   ├── historical/            # OHLCV data in CSV
│   │   └── data_manager.py        # Data handling + CSV storage
│   ├── backtest/
│   │   ├── backtest_engine.py     # Backtest engine
│   │   ├── portfolio.py           # Portfolio simulation
│   │   ├── performance_metrics.py # Performance metrics
│   ├── trading/
│   │   └──                       # TO BE IMPLEMENTED
│   └── utils/
│       ├── logger.py              # Logging
│       ├── validators.py          # Validation
│       └── helpers.py             # Utilities
├── requirements.txt               # Dependencies
├── README.md                      # Documentation
└── run.py                         # Launch script
```

## 📋 Development Roadmap

### ✅ Phase 1 - Backend Core (COMPLETED)

- [x] Operational Flask backend
- [x] REST API with main endpoints
- [x] Complete backtest engine
- [x] Performance metrics
- [x] Simulated portfolio
- [x] Buy & hold strategy implemented
- [x] Binance client for historical data
- [x] Functional CSV storage

### 🎯 Phase 2 - Frontend: Backtest & Live Trading Interface (IN PROGRESS)

#### 2.1 Preparation

- [x] **utils.js**: Validation, conversion, formatting functions
- [x] **api.js**: Backend communication
- [x] **charts.js**: Chart management

#### 2.2 Main Interface

- [x] **index.html**: Tab navigation
- [x] **main.js**: Tab switching logic
- [x] **styles.css**: Navigation + general styles

#### 2.3 Interface Separation

- [x] **backtest.js**: Isolated backtest logic
- [ ] **live_trading.js**: Live trading logic (preliminary interface)

### 🔮 Phase 3 - Advanced Strategies

- [ ] **simple_ma_cross.py**: Moving average crossover strategy
- [x] **rsi_strategy.py**: Complete RSI strategy
- [ ] **custom_strategy.py**: Template for new strategies
- [ ] Interface for custom strategy creation

### 🔮 Phase 4 - Full Live Trading

- [ ] **live_trader.py**: Real-time trading system
- [ ] **risk_manager.py**: Advanced risk management
- [ ] **order_executor.py**: Binance order execution
- [ ] Real-time monitoring interface
- [ ] Alerts and notifications system

### Live Trading Tab (To be developed)

- [ ] **Bot status**: ON/OFF, active strategy
- [ ] **Current portfolio**: Balances, open positions
- [ ] **Real-time chart**: Price + trading signals
- [ ] **Trade history**: Recent trades with PnL
- [ ] **Risk parameters**: Stop-loss, take-profit
- [ ] **Live logs**: Bot activity

## 📊 Backend API (Required Endpoints)

### Backtest Endpoints (✅ Implemented)

- `GET /api/strategies` - List strategies
- `POST /api/backtest` - Run backtest
- `GET /api/market-data` - Historical data
- `GET /health` - System status

### Live Trading Endpoints (🔮 To be developed)

- `GET /api/live/status` - Bot status
- `POST /api/live/start` - Start bot
- `POST /api/live/stop` - Stop bot
- `GET /api/live/portfolio` - Portfolio state
- `GET /api/live/trades` - Trade history
- `GET /api/live/logs` - Live logs

## 🛠️ Technologies Used

- **Backend:** Python, Flask, python-binance
- **Frontend:** HTML5, CSS3, JavaScript, Chart.js
- **Storage:** CSV files (simple and efficient)
- **API:** Binance REST API
- **Architecture:** Simple Single Page Application (SPA)
