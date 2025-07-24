# Projet Bot Trading Crypto

## 🎯 Résumé du contexte

**Objectif** : Créer un bot de trading crypto local avec interface à deux modes : Backtest et Live Trading.

**Spécifications définies** :

- Usage local uniquement (pas de déploiement)
- Interface : Navigation par onglets (Backtest / Live Trading)
- Timeframes : 15m, 30m, 1h
- Gestion des risques : Oui (stop-loss, take-profit)
- Graphiques : Comparaison stratégie vs buy&hold
- Stockage : Fichiers CSV

**Configuration par défaut** :

- Capital initial : 1000 USDT
- Commissions : 0.1% par trade
- Période par défaut : 30 jours
- Crypto par défaut : BTC/USDT
- Timeframe par défaut : 1h

## 🏗️ Structure des fichiers (Simplifiée)

trading-bot/
├── frontend/
│   ├── index.html                 # Page principale avec navigation onglets
│   ├── css/
│   │   └── styles.css            # Styles globaux + navigation
│   ├── js/
│   │   ├── main.js               # Navigation onglets + initialisation
│   │   ├── backtest.js           # Logique page backtest
│   │   ├── live-trading.js       # Logique page live trading
│   │   ├── charts.js             # Graphiques Chart.js (partagé)
│   │   ├── api.js                # Communication backend (partagé)
│   │   └── utils.js              # Utilitaires (partagé)
├── backend/
│   ├── config.json               # Config timeframes et symbols
│   ├── app.py                    # Serveur Flask (routes backtest + live)
│   ├── strategies/
│   │   └── buy_and_hold.py
│   ├── data/
│   │   ├── historical/           # Données ohlcv en csv
│   │   └── data_manager.py       # Gestion données + stockage csv
│   ├── backtest/
│   │   ├── backtest_engine.py    # Moteur backtest
│   │   ├── portfolio.py          # Simulation portefeuille
│   │   ├── performance_metrics.py # Métriques performance
│   ├── trading/
│   │   └──                       # A IMPLEMENTER
│   └── utils/
│       ├── logger.py             # Logs
│       ├── validators.py         # Validation
│       └── helpers.py            # Utilitaires
├── requirements.txt              # Dépendances
├── README.md                     # Documentation
└── run.py                        # Script lancement

## 📋 Plan de développement par phases

### ✅ Phase 1 - Backend Core (TERMINÉE)

- [x] Backend Flask opérationnel
- [x] API REST avec endpoints principaux
- [x] Moteur de backtest complet (BacktestEngine)
- [x] Metriques de performance (PerformanceMetrics)
- [x] Portfolio Simulé (Portfolio)
- [x] Stratégie buy&hold implémentée
- [x] Client Binance pour données historiques
- [x] Stockage CSV fonctionnel

### 🎯 Phase 2 - Frontend avec interface Backtest et Live Trading (EN COURS)

#### 2.1 Préparation

- [x] **utils.js** : Ensemble de fonctions de validations, converstion, formatage
- [x] **api.js** : Communication avec le backend
- [x] **charts.js** : Gestion des graphiques

#### 2.2 Interface principale

- [x] **index.html** : Ajouter navigation par onglets
- [x] **main.js** : Logique de navigation entre onglets
- [x] **styles.css** : Styles pour navigation + structure générale

#### 2.3 Séparation des interfaces

- [x] **backtest.js** : Logique isolée du backtest
- [ ] **live_trading.js** : Logique du live trading (interface préliminaire)

### 🔮 Phase 3 - Stratégies Avancées

- [ ] **simple_ma_cross.py** : Stratégie croisement moyennes
- [x] **rsi_strategy.py** : Stratégie RSI complète
- [ ] **custom_strategy.py** : Template pour nouvelles stratégies
- [ ] Interface pour créer des stratégies personnalisées

### 🔮 Phase 4 - Live Trading Complet

- [ ] **live_trader.py** : Système de trading en temps réel
- [ ] **risk_manager.py** : Gestion des risques avancée
- [ ] **order_executor.py** : Exécution ordres Binance
- [ ] Interface de monitoring en temps réel
- [ ] Système d'alertes et notifications

### Onglet Live Trading (À développer)

- [ ] **Statut du bot** : ON/OFF, stratégie active
- [ ] **Portefeuille actuel** : Soldes, positions ouvertes
- [ ] **Graphique temps réel** : Prix + signaux de trading
- [ ] **Historique des trades** : Trades récents avec PnL
- [ ] **Paramètres de risque** : Stop-loss, take-profit
- [ ] **Logs en temps réel** : Activité du bot

## 📊 API Backend (Endpoints requis)

### Endpoints Backtest (✅ Existants)

- `GET /api/strategies` - Liste des stratégies
- `POST /api/backtest` - Lancer un backtest
- `GET /api/market-data` - Données historiques
- `GET /health` - Statut du système

### Endpoints Live Trading (🔮 À développer)

- `GET /api/live/status` - Statut du bot
- `POST /api/live/start` - Démarrer le bot
- `POST /api/live/stop` - Arrêter le bot
- `GET /api/live/portfolio` - État du portefeuille
- `GET /api/live/trades` - Historique des trades
- `GET /api/live/logs` - Logs en temps réel

## 🛠️ Technologies utilisées

- **Backend** : Python, Flask, python-binance
- **Frontend** : HTML5, CSS3, JavaScript, Chart.js
- **Stockage** : CSV files (simple et efficace)
- **API** : Binance REST API
- **Architecture** : Single Page Application (SPA) simple
