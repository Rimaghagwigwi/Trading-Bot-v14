"""
Main backtest engine
"""

from typing import Dict
import pandas as pd
import numpy as np
import logging
from datetime import datetime
from .portfolio import Portfolio
from ..strategies.buy_and_hold import BuyAndHoldStrategy
from ..strategies.RSI_strategy import RSIStrategy
from ..strategies.DCA_strategy import DCA_strategy

logger = logging.getLogger(__name__)

class BacktestEngine:
    """Main engine to run backtests"""

    def __init__(self, initial_capital: float = 10000, commission_rate: float = 0.001, timeframe: str = '1h', pairs: list = []):
        self.portfolio = Portfolio(initial_capital, commission_rate, pairs)
        self.strategy = None
        self.timeframe = pd.to_timedelta(timeframe)

        logger.info("Backtest engine initialized")

    def set_strategy(self, strategy_params, strategy_class: str):
        """Set the trading strategy"""
        self.strategy = globals()[strategy_class]()
        self.strategy.set_params(strategy_params)

    def run_backtest(self, market_data: Dict[str, pd.DataFrame]) -> Dict:
        """Run a complete backtest"""
        if self.strategy is None:
            raise ValueError("No strategy configured")
        
        logger.info("Backtest started")
        self.portfolio.set_market_data(market_data)
        
        # Generate trades
        signals = {symbol: self.strategy.generate_signals(data) for symbol, data in market_data.items()}
        for symbol, signal_df in signals.items():
            signal_df['symbol'] = symbol
        
        # Merge signals into a single DataFrame
        signals_df = pd.concat(signals.values(), ignore_index=False)
        print(signals_df)

        logger.info(f"{len(signals_df)} signals generated")

        # Execute trades
        start_ts = min(market_data[symbol].index.min() for symbol in market_data)
        end_ts = max(market_data[symbol].index.max() for symbol in market_data)
        
        for ts in pd.date_range(start=start_ts, end=end_ts, freq=self.timeframe):
            self.portfolio.update_graph_data(ts)
            to_process = signals_df[signals_df.index == ts]
            for _, row in to_process.iterrows():
                trade = {
                    'type': row['signal']['type'],
                    'symbol': row['symbol'],
                    'timestamp': ts,
                    'params': row['signal']['params'],
                }
                self.portfolio.execute_trade(trade)
            
        logger.info(f"{len(self.portfolio.trades)} trades executed")

        # Convert DataFrames to dicts for JSON serialization
        graph_data = self.portfolio.graph_data
        trades_history = self.portfolio.trades
        
        # Final results with JSON conversion
        results = {
            'portfolio_summary': self.portfolio.get_summary(),
            'trades_history': trades_history if trades_history else [],
            'graph_data': graph_data if graph_data else {},
        }

        logger.info("Backtest finished")
        return results
