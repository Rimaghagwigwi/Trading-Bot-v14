"""
Portfolio simulation for multi-pair backtesting
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime
from typing import Dict, List

logger = logging.getLogger(__name__)

class Portfolio:
    """Class to simulate a multi-pair trading portfolio"""
    
    def __init__(self, initial_capital: float = 10000, commission_rate: float = 0.001, pairs: List[str] = []):
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        
        # Portfolio state
        self.symbols = pairs
        self.cash = initial_capital
        self.positions: Dict[str, float] = {}  # {symbol: quantity}
        self.open_orders: Dict[str, Dict] = {}  # {symbol: order_details}
        
        # Benchmark
        self.benchmark_positions: Dict[str, float] = {}  # {symbol: quantity}

        # History
        self.trades: List[Dict] = []
        self.graph_data: Dict[str, List[float]] = {
            'timestamp': [],
            'total_value': [],
            'benchmark': []
        }
        self.total_commission = 0.0
        
        logger.info(f"Portfolio initialized: {initial_capital} USDT")
        
    def set_market_data(self, market_data: Dict[str, pd.DataFrame]):
        """Set market data for the portfolio"""
        self.market_data = market_data
        self.current_prices = {symbol: data['close'].iloc[-1] for symbol, data in market_data.items()}

        self.benchmark_positions = {symbol: self.initial_capital / data['close'].iloc[0] / len(self.symbols) for symbol, data in market_data.items()}

        logger.info(f"Market data set for {len(market_data)} symbols")

    def _get_total_usd_value(self, timestamp: pd.Timestamp) -> float:
        """Return the total USD value of the portfolio"""
        total_value = self.cash
        for symbol, quantity in self.positions.items():
            total_value += quantity * self.market_data[symbol].loc[timestamp]['close']
        return total_value
    
    def _get_benchmark_value(self, timestamp: pd.Timestamp) -> float:
        """Return the total benchmark value"""
        total_value = 0.0
        for symbol, quantity in self.benchmark_positions.items():
            total_value += quantity * self.market_data[symbol].loc[timestamp]['close']
        return total_value

    def execute_trade(self, trade: Dict) -> Dict:
        """Execute a trade on the portfolio

        Args:
            trade (Dict): Trade details to execute
            trade['symbol'] (str): Trading pair symbol
            trade['timestamp'] (datetime): Trade timestamp
            trade['type'] (str): Trade type ('buy_market', 'sell_market', etc.)
            trade['portion'] (float): Portion of the position to trade (0.1 for 10%, etc.)

        Returns:
            Dict: Result of the trade execution
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
        """Execute a market buy order for a symbol"""
        if 'portion' in trade['params']:
            usd_value = trade['params']['portion'] * self.cash
        elif 'usdc_value' in trade['params']:
            usd_value = trade['params']['usdc_value']
        else:
            usd_value = 0
        
        if self.cash <= 5 or self.cash < usd_value * (1 + self.commission_rate) or usd_value <= 5:
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
        """Execute a market sell order for a symbol""" 
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
        raise NotImplementedError("Limit buy order not implemented")
    
    def _sell_limit(self, trade: Dict) -> Dict:
        raise NotImplementedError("Limit sell order not implemented")
    
    def _oco(self, trade: Dict) -> Dict:
        raise NotImplementedError("OCO order not implemented")
    
    
    def get_summary(self) -> Dict:
        """Return a summary of the portfolio"""
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
        """Update portfolio graph data"""
        self.graph_data['timestamp'].append(timestamp)
        self.graph_data['total_value'].append(self._get_total_usd_value(timestamp))
        self.graph_data['benchmark'].append(self._get_benchmark_value(timestamp))
