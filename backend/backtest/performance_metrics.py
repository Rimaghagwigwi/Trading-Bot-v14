"""
Performance metrics calculation for backtests
"""

import pandas as pd
import numpy as np
from typing import Dict, List

class PerformanceMetrics:
    """Performance metrics calculator"""
    
    def __init__(self, results: Dict, market_data: pd.DataFrame):
        self.portfolio_summary = results['portfolio_summary']
        self.graph_data = pd.DataFrame(results['graph_data']) if results['graph_data'] else pd.DataFrame()
        self.trades_history = pd.DataFrame(results['trades_history']) if results['trades_history'] else pd.DataFrame()
        self.market_data = market_data
        
    def calculate_all_metrics(self) -> Dict:
        """Calculates all performance metrics"""
        self.risk_metrics = self._calculate_risk_metrics()
        self.return_metrics = self._calculate_return_metrics()
        self.trade_metrics = self._calculate_trade_metrics()
        self.benchmark_metrics = self._calculate_benchmark_metrics()
        return {
            'return_metrics': self.return_metrics,
            'risk_metrics': self.risk_metrics,
            'trade_metrics': self.trade_metrics,
            'benchmark_metrics': self.benchmark_metrics
        }
    
    def _calculate_return_metrics(self) -> Dict:
        """Calculates return metrics"""
        initial = self.portfolio_summary['initial_capital']
        final = self.portfolio_summary['final_value']
        
        total_return = (final - initial) / initial
        # Annualized return (approximation)
        if not self.graph_data.empty: 
            days = (self.graph_data['timestamp'].max() - self.graph_data['timestamp'].min()).days
            print(f"Calculating annualized return over {days} days")
            annualized_return = (1 + total_return) ** (365 / days) - 1
            
        return {
            'total_return_pct': total_return * 100,
            'annualized_return_pct': annualized_return * 100
        }
    
    def _calculate_risk_metrics(self) -> Dict:
        """Calculates risk metrics"""
        if self.graph_data.empty:
            return {
                'volatility': 0, 
                'max_drawdown': 0, 
                'sharpe_ratio': 0,
                'sortino_ratio': 0
            }

        values = self.graph_data['total_value']
        returns = values.pct_change().dropna()
        
        # Volatility
        volatility = returns.std() * np.sqrt(252) if len(returns) > 1 else 0
        
        # Maximum drawdown
        peak = values.cummax()
        drawdown = (values - peak) / peak * 100
        max_drawdown = drawdown.min()
        
        # Sharpe ratio (approximation)
        if volatility > 0 and len(returns) > 0:
            sharpe_ratio = (returns.mean() * 252) / volatility
        else:
            sharpe_ratio = 0
        
        # Sortino ratio (approximation)
        negative_returns = returns[returns < 0]
        if len(negative_returns) > 0:
            downside_deviation = negative_returns.std() * np.sqrt(252)
            sortino_ratio = (returns.mean() * 252) / downside_deviation if downside_deviation > 0 else 0
        else:
            sortino_ratio = 0
        
        return {
            'volatility_pct': volatility * 100,
            'max_drawdown_pct': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio
        }
    
    def _calculate_trade_metrics(self) -> Dict:
        """Calculates trading metrics"""
        if self.trades_history.empty:
            return {'total_trades': 0, 'win_rate': 0, 'avg_trade_return': 0}
        
        trades = self.trades_history[self.trades_history['executed'] == True]
        
        if len(trades) == 0:
            return {'total_trades': 0, 'win_rate': 0, 'avg_trade_return': 0}
        
        total_trades = len(trades)
        
        # Win rate calculation
        # To implement
        
        return {
            'total_trades': total_trades,
            'win_rate_pct': 0,
            'avg_trade_return_pct': 0
        }
    
    def _calculate_benchmark_metrics(self) -> Dict:
        """Calculates metrics vs benchmark (buy and hold)"""
        
        # Benchmark return
        initial_value = self.graph_data.iloc[0]['benchmark']
        final_value = self.graph_data.iloc[-1]['benchmark']
        benchmark_return = (final_value - initial_value) / initial_value * 100 if initial_value != 0 else 0

        # Strategy return
        strategy_return = self.return_metrics['total_return_pct']

        return {
            'benchmark_return_pct': benchmark_return,
            'excess_return_pct': strategy_return - benchmark_return
        }
    
    def get_summary_report(self) -> str:
        """Generates a summary report"""
        metrics = self.calculate_all_metrics()
        
        # Extract values with access paths
        total_return = metrics['return_metrics']['total_return_pct']
        annualized_return = metrics['return_metrics']['annualized_return_pct']
        
        benchmark_return = metrics['benchmark_metrics']['benchmark_return_pct']
        excess_return = metrics['benchmark_metrics']['excess_return_pct']
        
        sharpe_ratio = metrics['risk_metrics']['sharpe_ratio']
        sortino_ratio = metrics['risk_metrics']['sortino_ratio']
        max_drawdown = metrics['risk_metrics']['max_drawdown_pct']
        volatility = metrics['risk_metrics']['volatility_pct']
        
        total_trades = metrics['trade_metrics']['total_trades']
        win_rate = metrics['trade_metrics']['win_rate_pct']
        
        return f"""
    
=== PERFORMANCE REPORT ===

Return:
- Total return: {total_return:.2f}%
- Annualized return: {annualized_return:.2f}%

Benchmark:
- Buy & Hold return: {benchmark_return:.2f}%
- Strategy outperformance: {excess_return:.2f}%

Risk:
- Sharpe ratio: {sharpe_ratio:.2f}
- Sortino ratio: {sortino_ratio:.2f}
- Max drawdown: {max_drawdown:.2f}%
- Volatility: {volatility:.2f}%

Trading:
- Number of trades: {total_trades}
- Win rate: {win_rate:.2f}%

"""