"""
Performance metrics calculation for backtests with enhanced order types
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime

class PerformanceMetrics:
    """Enhanced performance metrics calculator"""
    
    def __init__(self, results: Dict, market_data: Optional[Dict[str, pd.DataFrame]] = None):
        self.portfolio_summary = results.get('portfolio_summary', {})
        self.market_data = market_data
        
        # Convert graph data to DataFrame
        graph_data = results.get('graph_data', {})
        if graph_data and 'timestamp' in graph_data:
            self.graph_data = pd.DataFrame(graph_data)
            # Convert timestamp strings back to datetime if needed
            if len(self.graph_data) > 0 and isinstance(self.graph_data['timestamp'].iloc[0], str):
                self.graph_data['timestamp'] = pd.to_datetime(self.graph_data['timestamp'])
        else:
            self.graph_data = pd.DataFrame()
        
        # Convert trades history to DataFrame
        trades_data = results.get('trades_history', [])
        if trades_data:
            self.trades_history = pd.DataFrame(trades_data)
            # Convert timestamp strings back to datetime if needed
            if len(self.trades_history) > 0 and 'timestamp' in self.trades_history.columns:
                if isinstance(self.trades_history['timestamp'].iloc[0], str):
                    self.trades_history['timestamp'] = pd.to_datetime(self.trades_history['timestamp'])
        else:
            self.trades_history = pd.DataFrame()
        
    def calculate_all_metrics(self) -> Dict:
        """Calculates all performance metrics"""
        return_metrics = self._calculate_return_metrics()
        risk_metrics = self._calculate_risk_metrics()
        trade_metrics = self._calculate_trade_metrics()
        benchmark_metrics = self._calculate_benchmark_metrics()
        drawdown_metrics = self._calculate_drawdown_metrics()
        
        return {
            'return_metrics': return_metrics,
            'risk_metrics': risk_metrics,
            'trade_metrics': trade_metrics,
            'benchmark_metrics': benchmark_metrics,
            'drawdown_metrics': drawdown_metrics
        }
    
    def _calculate_return_metrics(self) -> Dict:
        """Calculates return metrics"""
        initial = self.portfolio_summary.get('initial_capital', 0)
        final = self.portfolio_summary.get('final_value', 0)
        
        if initial == 0:
            return {
                'total_return_pct': 0,
                'annualized_return_pct': 0,
                'cagr_pct': 0
            }
        
        total_return = (final - initial) / initial
        
        # Calculate annualized return based on actual time period
        annualized_return = 0
        cagr = 0
        
        if not self.graph_data.empty and len(self.graph_data) > 1:
            start_date = self.graph_data['timestamp'].iloc[0]
            end_date = self.graph_data['timestamp'].iloc[-1]
            days = (end_date - start_date).days
            
            if days > 0:
                years = days / 365.25
                # CAGR calculation
                cagr = ((final / initial) ** (1 / years) - 1) if years > 0 and final > 0 else 0
                # Simple annualized return
                annualized_return = total_return / years if years > 0 else 0
        
        return {
            'total_return_pct': total_return * 100,
            'annualized_return_pct': annualized_return * 100,
            'cagr_pct': cagr * 100
        }
    
    def _calculate_risk_metrics(self) -> Dict:
        """Calculates risk metrics"""
        if self.graph_data.empty or len(self.graph_data) < 2:
            return {
                'volatility_pct': 0, 
                'sharpe_ratio': 0,
                'sortino_ratio': 0,
                'calmar_ratio': 0
            }

        values = self.graph_data['total_value']
        returns = values.pct_change().dropna()
        
        if len(returns) == 0:
            return {
                'volatility_pct': 0, 
                'sharpe_ratio': 0,
                'sortino_ratio': 0,
                'calmar_ratio': 0
            }
        
        # Determine frequency for annualization
        time_diff = self.graph_data['timestamp'].iloc[1] - self.graph_data['timestamp'].iloc[0]
        if time_diff.total_seconds() <= 3600:  # Hourly or less
            periods_per_year = 24 * 365
        elif time_diff.total_seconds() <= 86400:  # Daily
            periods_per_year = 365
        else:  # Weekly or more
            periods_per_year = 52
        
        # Volatility (annualized)
        volatility = returns.std() * np.sqrt(periods_per_year) if len(returns) > 1 else 0
        
        # Mean return (annualized)
        mean_return = returns.mean() * periods_per_year
        
        # Sharpe ratio (assuming risk-free rate = 0)
        sharpe_ratio = mean_return / volatility if volatility > 0 else 0
        
        # Sortino ratio
        negative_returns = returns[returns < 0]
        if len(negative_returns) > 0:
            downside_deviation = negative_returns.std() * np.sqrt(periods_per_year)
            sortino_ratio = mean_return / downside_deviation if downside_deviation > 0 else 0
        else:
            sortino_ratio = sharpe_ratio  # No negative returns
        
        # Calmar ratio (CAGR / Max Drawdown)
        max_drawdown = self._calculate_max_drawdown()
        return_metrics = self._calculate_return_metrics()
        cagr = return_metrics['cagr_pct'] / 100
        calmar_ratio = abs(cagr / (max_drawdown / 100)) if max_drawdown != 0 else 0
        
        return {
            'volatility_pct': volatility * 100,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'calmar_ratio': calmar_ratio
        }
    
    def _calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown percentage"""
        if self.graph_data.empty:
            return 0
            
        values = self.graph_data['total_value']
        peak = values.cummax()
        drawdown = (values - peak) / peak * 100
        return drawdown.min()
    
    def _calculate_drawdown_metrics(self) -> Dict:
        """Calculate detailed drawdown metrics"""
        if self.graph_data.empty:
            return {
                'max_drawdown_pct': 0,
                'avg_drawdown_pct': 0,
                'max_drawdown_duration_days': 0,
                'recovery_factor': 0
            }
        
        values = self.graph_data['total_value']
        timestamps = self.graph_data['timestamp']
        peak = values.cummax()
        drawdown = (values - peak) / peak * 100
        
        max_drawdown = drawdown.min()
        
        # Average drawdown (only negative values)
        negative_drawdowns = drawdown[drawdown < 0]
        avg_drawdown = negative_drawdowns.mean() if len(negative_drawdowns) > 0 else 0
        
        # Maximum drawdown duration
        max_dd_duration = 0
        current_dd_start = None
        
        for i, dd in enumerate(drawdown):
            if dd < -0.01 and current_dd_start is None:  # Start of drawdown (>1%)
                current_dd_start = timestamps.iloc[i]
            elif dd >= -0.01 and current_dd_start is not None:  # End of drawdown
                duration = (timestamps.iloc[i] - current_dd_start).days
                max_dd_duration = max(max_dd_duration, duration)
                current_dd_start = None
        
        # Recovery factor
        total_return = self._calculate_return_metrics()['total_return_pct']
        recovery_factor = abs(total_return / max_drawdown) if max_drawdown != 0 else 0
        
        return {
            'max_drawdown_pct': max_drawdown,
            'avg_drawdown_pct': avg_drawdown,
            'max_drawdown_duration_days': max_dd_duration,
            'recovery_factor': recovery_factor
        }
    
    def _calculate_trade_metrics(self) -> Dict:
        """Calculates enhanced trading metrics"""
        if self.trades_history.empty:
            return {
                'total_trades': 0, 
                'buy_trades': 0,
                'sell_trades': 0,
                'win_rate_pct': 0, 
                'avg_trade_return_pct': 0,
                'profit_factor': 0,
                'avg_win_pct': 0,
                'avg_loss_pct': 0,
                'largest_win_pct': 0,
                'largest_loss_pct': 0,
                'total_commission': 0
            }
        
        executed_trades = self.trades_history[self.trades_history.get('executed', False) == True]
        
        if len(executed_trades) == 0:
            return {
                'total_trades': 0, 
                'buy_trades': 0,
                'sell_trades': 0,
                'win_rate_pct': 0, 
                'avg_trade_return_pct': 0,
                'profit_factor': 0,
                'avg_win_pct': 0,
                'avg_loss_pct': 0,
                'largest_win_pct': 0,
                'largest_loss_pct': 0,
                'total_commission': 0
            }
        
        total_trades = len(executed_trades)
        buy_trades = len(executed_trades[executed_trades['type'] == 'buy'])
        sell_trades = len(executed_trades[executed_trades['type'] == 'sell'])
        
        # Calculate trade returns (simplified approach)
        total_commission = executed_trades['commission'].sum() if 'commission' in executed_trades.columns else 0
        
        # For more detailed trade analysis, we would need to match buy/sell pairs
        # This is a simplified version
        
        return {
            'total_trades': total_trades,
            'buy_trades': buy_trades,
            'sell_trades': sell_trades,
            'win_rate_pct': 0,  # Would need paired trade analysis
            'avg_trade_return_pct': 0,  # Would need paired trade analysis
            'profit_factor': 0,  # Would need paired trade analysis
            'avg_win_pct': 0,
            'avg_loss_pct': 0,
            'largest_win_pct': 0,
            'largest_loss_pct': 0,
            'total_commission': total_commission
        }
    
    def _calculate_benchmark_metrics(self) -> Dict:
        """Calculates metrics vs benchmark (buy and hold)"""
        if self.graph_data.empty or 'benchmark' not in self.graph_data.columns:
            return {
                'benchmark_return_pct': 0,
                'excess_return_pct': 0,
                'tracking_error_pct': 0,
                'information_ratio': 0
            }
        
        # Benchmark return
        initial_benchmark = self.graph_data['benchmark'].iloc[0]
        final_benchmark = self.graph_data['benchmark'].iloc[-1]
        benchmark_return = ((final_benchmark - initial_benchmark) / initial_benchmark * 100 
                          if initial_benchmark != 0 else 0)

        # Strategy return
        return_metrics = self._calculate_return_metrics()
        strategy_return = return_metrics['total_return_pct']
        
        # Excess return
        excess_return = strategy_return - benchmark_return
        
        # Tracking error and information ratio
        if len(self.graph_data) > 1:
            strategy_returns = self.graph_data['total_value'].pct_change().dropna()
            benchmark_returns = self.graph_data['benchmark'].pct_change().dropna()
            
            if len(strategy_returns) == len(benchmark_returns) and len(strategy_returns) > 1:
                excess_returns = strategy_returns - benchmark_returns
                tracking_error = excess_returns.std() * np.sqrt(252) * 100  # Annualized
                information_ratio = (excess_returns.mean() * 252) / (excess_returns.std()) if excess_returns.std() > 0 else 0
            else:
                tracking_error = 0
                information_ratio = 0
        else:
            tracking_error = 0
            information_ratio = 0

        return {
            'benchmark_return_pct': benchmark_return,
            'excess_return_pct': excess_return,
            'tracking_error_pct': tracking_error,
            'information_ratio': information_ratio
        }
    
    def get_summary_report(self) -> str:
        """Generates a comprehensive summary report"""
        metrics = self.calculate_all_metrics()
        
        # Extract metrics safely with defaults
        return_m = metrics.get('return_metrics', {})
        risk_m = metrics.get('risk_metrics', {})
        trade_m = metrics.get('trade_metrics', {})
        benchmark_m = metrics.get('benchmark_metrics', {})
        drawdown_m = metrics.get('drawdown_metrics', {})
        
        total_return = return_m.get('total_return_pct', 0)
        cagr = return_m.get('cagr_pct', 0)
        
        benchmark_return = benchmark_m.get('benchmark_return_pct', 0)
        excess_return = benchmark_m.get('excess_return_pct', 0)
        
        sharpe_ratio = risk_m.get('sharpe_ratio', 0)
        sortino_ratio = risk_m.get('sortino_ratio', 0)
        calmar_ratio = risk_m.get('calmar_ratio', 0)
        max_drawdown = drawdown_m.get('max_drawdown_pct', 0)
        volatility = risk_m.get('volatility_pct', 0)
        
        total_trades = trade_m.get('total_trades', 0)
        buy_trades = trade_m.get('buy_trades', 0)
        sell_trades = trade_m.get('sell_trades', 0)
        total_commission = trade_m.get('total_commission', 0)
        
        max_dd_duration = drawdown_m.get('max_drawdown_duration_days', 0)
        recovery_factor = drawdown_m.get('recovery_factor', 0)
        
        return f"""
=== ENHANCED PERFORMANCE REPORT ===

💰 RETURNS:
- Total return: {total_return:.2f}%
- CAGR: {cagr:.2f}%

📊 BENCHMARK COMPARISON:
- Buy & Hold return: {benchmark_return:.2f}%
- Strategy outperformance: {excess_return:.2f}%

⚠️ RISK METRICS:
- Sharpe ratio: {sharpe_ratio:.2f}
- Sortino ratio: {sortino_ratio:.2f}
- Calmar ratio: {calmar_ratio:.2f}
- Volatility: {volatility:.2f}%

📉 DRAWDOWN ANALYSIS:
- Max drawdown: {max_drawdown:.2f}%
- Max drawdown duration: {max_dd_duration} days
- Recovery factor: {recovery_factor:.2f}

🔄 TRADING ACTIVITY:
- Total trades: {total_trades}
- Buy orders: {buy_trades}
- Sell orders: {sell_trades}
- Total commission paid: ${total_commission:.2f}

💼 PORTFOLIO STATUS:
- Final value: ${self.portfolio_summary.get('final_value', 0):.2f}
- Cash: ${self.portfolio_summary.get('cash', 0):.2f}
- Open orders: {self.portfolio_summary.get('open_orders', 0)}
"""
    
    def get_detailed_metrics(self) -> Dict:
        """Returns all metrics in a structured format for further analysis"""
        return self.calculate_all_metrics()
    
    def export_to_dict(self) -> Dict:
        """Export all data and metrics for JSON serialization"""
        metrics = self.calculate_all_metrics()
        
        return {
            'metrics': metrics,
            'portfolio_summary': self.portfolio_summary,
            'trade_count': len(self.trades_history),
            'data_points': len(self.graph_data),
            'timestamp_range': {
                'start': self.graph_data['timestamp'].iloc[0].isoformat() if not self.graph_data.empty else None,
                'end': self.graph_data['timestamp'].iloc[-1].isoformat() if not self.graph_data.empty else None
            }
        }