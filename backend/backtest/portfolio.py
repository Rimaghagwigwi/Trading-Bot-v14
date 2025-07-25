"""
Simulation du portefeuille pour les backtests multi-paires
"""

from os import times
import pandas as pd
import numpy as np
import logging
from datetime import datetime
from typing import Dict, List

logger = logging.getLogger(__name__)

class Portfolio:
    """Classe pour simuler un portefeuille de trading multi-paires"""
    
    def __init__(self, initial_capital: float = 10000, commission_rate: float = 0.001, paires: List[str] = []):
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        
        # État du portefeuille
        self.symbols = paires
        self.cash = initial_capital
        self.positions: Dict[str, float] = {}  # {symbol: quantity}
        self.open_orders: Dict[str, Dict] = {}  # {symbol: order_details}
        
        # Benchmark
        self.benchmark_positions: Dict[str, float] = {}  # {symbol: quantity}

        # Historique
        self.trades: List[Dict] = []
        self.graph_data: Dict[str, List[float]] = {
            'timestamp': [],
            'total_value': [],
            'benchmark': []
        }
        self.total_commission = 0.0
        
        logger.info(f"Portfolio initialisé: {initial_capital} USDT")
        
    def set_market_data(self, market_data: Dict[str, pd.DataFrame]):
        """Configure les données de marché pour le portefeuille"""
        self.market_data = market_data
        self.current_prices = {symbol: data['close'].iloc[-1] for symbol, data in market_data.items()}

        self.benchmark_positions = {symbol: self.initial_capital / data['close'].iloc[0] / len(self.symbols) for symbol, data in market_data.items()}

        logger.info(f"Données de marché configurées pour {len(market_data)} symboles")

    def _get_total_usd_value(self, timestamp: pd.Timestamp) -> float:
        """Retourne la valeur totale en USD du portefeuille"""
        total_value = self.cash
        for symbol, quantity in self.positions.items():
            total_value += quantity * self.market_data[symbol].loc[timestamp]['close']
        return total_value
    
    def _get_benchmark_value(self, timestamp: pd.Timestamp) -> float:
        """Retourne la valeur totale du benchmark"""
        total_value = 0.0
        for symbol, quantity in self.benchmark_positions.items():
            total_value += quantity * self.market_data[symbol].loc[timestamp]['close']
        return total_value

    def execute_trade(self, trade: Dict) -> Dict:
        """Exécute un trade sur le portefeuille

        Args:
            trade (Dict): Détails du trade à exécuter
            trade['symbol'] (str): Symbole de la paire de trading
            trade['timestamp'] (datetime): Timestamp du trade
            trade['type'] (str): Type de trade ('buy_market', 'sell_market', etc.)
            trade['portion'] (float): Portion de la position à trader (0.1 pour 10%, etc.)

        Returns:
            Dict: Résultat de l'exécution du trade
        """
        trade['executed'] = False
        if trade['type'] == "buy_market":
            trade = self._buy_market(trade)
        elif trade['type'] == "sell_market":
            trade = self._sell_market(trade)
        elif trade['type'] == "buy_limit":
            trade = self._buy_limit(trade)
        elif trade['type'] == "sell_limit":
            trade = self._sell_limit(trade)
        elif trade['type'] == "oco":
            trade = self._oco(trade)

        if trade['executed']:
            self.trades.append(trade)

        return trade

    def _buy_market(self, trade: Dict) -> Dict:
        """Exécute un ordre d'achat au prix du marché pour un symbole"""
        if 'portion' in trade['params']:
            usd_value = trade['params']['portion'] * self.cash
        elif 'usdc_value' in trade['params']:
            usd_value = trade['params']['usdc_value']
        else:
            usd_value = 0
        
        if self.cash <= 5 or self.cash < usd_value * (1 + self.commission_rate) or usd_value <= 5:
            # Mets un emoji rouge pour indiquer un problème
            return trade
        
        price = self.market_data[trade['symbol']].loc[trade['timestamp']]['close']
        self.cash -= usd_value * (1 + self.commission_rate)
        quantity = usd_value / price
        commission = usd_value * self.commission_rate

        if trade['symbol'] not in self.positions:
            self.positions[trade['symbol']] = 0
            
        self.positions[trade['symbol']] += quantity
        self.total_commission += commission

        return {
            'timestamp': trade['timestamp'],
            'symbol': trade['symbol'],
            'type': 'buy',
            'price': price,
            'usd_value': usd_value,
            'commission': commission,
            'executed': True
        }

    def _sell_market(self, trade: Dict) -> Dict:
        """Exécute un ordre de vente au prix du marché pour un symbole""" 
        price = self.market_data[trade['symbol']].loc[trade['timestamp']]['close']
        if trade['symbol'] not in self.positions:
            self.positions[trade['symbol']] = 0

        quantity = self.positions[trade['symbol']] * trade['params']['portion']
        usd_value = quantity * price
        if self.positions[trade['symbol']] < quantity or usd_value <= 5:
            return trade
        
        commission = usd_value * self.commission_rate
        self.total_commission += commission

        self.cash += usd_value / (1 + self.commission_rate)
        self.positions[trade['symbol']] -= quantity

        return {
            'timestamp': trade['timestamp'],
            'symbol': trade['symbol'],
            'type': 'sell',
            'price': price,
            'usd_value': usd_value,
            'commission': commission,
            'executed': True
        }

    def _buy_limit(self, trade: Dict) -> Dict:
        raise NotImplementedError("L'ordre d'achat limite n'est pas implémenté")
    
    def _sell_limit(self, trade: Dict) -> Dict:
        raise NotImplementedError("L'ordre de vente limite n'est pas implémenté")
    
    def _oco(self, trade: Dict) -> Dict:
        raise NotImplementedError("L'ordre OCO n'est pas implémenté")
    
    
    def get_summary(self) -> Dict:
        """Retourne un résumé du portefeuille"""
        active_positions = {k: v for k, v in self.positions.items() if v > 0}
        
        position_values = {}
        total_position_value = 0
        for symbol, quantity in active_positions.items():
            if symbol in self.current_prices:
                value = quantity * self.current_prices[symbol]
                position_values[symbol] = value
                total_position_value += value
        
        return {
            'initial_capital': self.initial_capital,
            'final_value': self._get_total_usd_value(self.market_data[list(self.market_data.keys())[0]].index[-1]),
            'cash': self.cash,
            'total_position_value': total_position_value,
            'positions': active_positions,
            'position_values': position_values,
            'total_trades': len(self.trades),
            'total_commission': self.total_commission
        }
        
    def update_graph_data(self, timestamp: datetime):
        """Met à jour les données du graphique du portefeuille"""
        self.graph_data['timestamp'].append(timestamp)
        self.graph_data['total_value'].append(self._get_total_usd_value(timestamp))
        self.graph_data['benchmark'].append(self._get_benchmark_value(timestamp))