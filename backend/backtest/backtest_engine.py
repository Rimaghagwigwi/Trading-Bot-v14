"""
Main backtest engine with enhanced portfolio management
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
    """Main engine to run backtests with advanced order types"""

    def __init__(self, initial_capital: float = 10000, commission_rate: float = 0.001, 
                 timeframe: str = '1h', pairs: list = []):
        self.portfolio = Portfolio(initial_capital, commission_rate, pairs)
        self.strategy = None
        self.timeframe = pd.to_timedelta(timeframe)

        logger.info("Backtest engine initialized")

    def set_strategy(self, strategy_params, strategy_class: str):
        """Set the trading strategy"""
        strategy_map = {
            'BuyAndHoldStrategy': BuyAndHoldStrategy,
            'RSIStrategy': RSIStrategy,
            'DCA_strategy': DCA_strategy
        }
        
        if strategy_class not in strategy_map:
            raise ValueError(f"Unknown strategy class: {strategy_class}")
            
        self.strategy = strategy_map[strategy_class]()
        self.strategy.set_params(strategy_params)

    def run_backtest(self, market_data: Dict[str, pd.DataFrame]) -> Dict:
        """Run a complete backtest"""
        if self.strategy is None:
            raise ValueError("No strategy configured")
        
        logger.info("Backtest started")
        self.portfolio.set_market_data(market_data)
        
        # Generate signals for all symbols
        signals = {}
        for symbol, data in market_data.items():
            try:
                symbol_signals = self.strategy.generate_signals(data)
                if not symbol_signals.empty:
                    symbol_signals['symbol'] = symbol
                    signals[symbol] = symbol_signals
            except Exception as e:
                logger.warning(f"Failed to generate signals for {symbol}: {e}")
                continue
        
        if not signals:
            logger.warning("No signals generated for any symbol")
            return self._create_empty_results()
        
        # Merge signals into a single DataFrame
        signals_df = pd.concat(signals.values(), ignore_index=False)
        signals_df = signals_df.sort_index()  # Sort by timestamp
        
        logger.info(f"{len(signals_df)} signals generated")

        # Execute backtest
        self._execute_backtest(signals_df, market_data)
        
        logger.info(f"{len(self.portfolio.trades)} trades executed")

        # Prepare results
        results = self._prepare_results()
        logger.info("Backtest finished")
        return results

    def _execute_backtest(self, signals_df: pd.DataFrame, market_data: Dict[str, pd.DataFrame]):
        """Execute the backtest with signals and market data"""
        # Get time range
        start_ts = min(data.index.min() for data in market_data.values())
        end_ts = max(data.index.max() for data in market_data.values())
        
        # Process each timestamp
        for ts in pd.date_range(start=start_ts, end=end_ts, freq=self.timeframe):
            # Update portfolio (this will process pending orders)
            self.portfolio.update_graph_data(ts)
            
            # Process new signals at this timestamp
            current_signals = signals_df[signals_df.index == ts]
            
            for _, signal_row in current_signals.iterrows():
                if 'signal' not in signal_row or not signal_row['signal']:
                    continue
                    
                trade = {
                    'type': signal_row['signal']['type'],
                    'symbol': signal_row['symbol'],
                    'timestamp': ts,
                    'params': signal_row['signal']['params'],
                }
                
                try:
                    self.portfolio.execute_trade(trade)
                except Exception as e:
                    logger.warning(f"Failed to execute trade at {ts}: {e}")
                    continue

    def _prepare_results(self) -> Dict:
        """Prepare final results for output"""
        # Convert graph data to proper format
        graph_data_dict = {}
        if self.portfolio.graph_data:
            for key, values in self.portfolio.graph_data.items():
                if key == 'timestamp':
                    graph_data_dict[key] = [ts.isoformat() for ts in values]
                else:
                    graph_data_dict[key] = values

        # Convert trades to serializable format
        trades_list = []
        for trade in self.portfolio.trades:
            trade_dict = trade.copy()
            if 'timestamp' in trade_dict:
                trade_dict['timestamp'] = trade_dict['timestamp'].isoformat()
            trades_list.append(trade_dict)

        return {
            'portfolio_summary': self.portfolio.get_summary(),
            'trades_history': trades_list,
            'graph_data': graph_data_dict,
        }

    def _create_empty_results(self) -> Dict:
        """Create empty results when no signals are generated"""
        return {
            'portfolio_summary': {
                'initial_capital': self.portfolio.initial_capital,
                'final_value': self.portfolio.initial_capital,
                'total_return': 0.0,
                'benchmark_return': 0.0,
                'cash': self.portfolio.cash,
                'total_position_value': 0.0,
                'positions': {},
                'position_values': {},
                'total_trades': 0,
                'total_commission': 0.0,
                'open_orders': 0
            },
            'trades_history': [],
            'graph_data': {
                'timestamp': [],
                'total_value': [],
                'benchmark': []
            },
        }