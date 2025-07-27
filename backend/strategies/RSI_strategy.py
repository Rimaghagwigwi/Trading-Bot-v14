"""
RSI (Relative Strength Index) Strategy
"""

import pandas as pd
import talib
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RSIStrategy():
    """RSI Strategy - Buy on oversold, sell on overbought"""
    
    parameters = {
        'rsi_period': {'display_name': 'RSI Period', 'default': 14},
        'rsi_oversold': {'display_name': 'Oversold Threshold', 'default': 30},
        'rsi_overbought': {'display_name': 'Overbought Threshold', 'default': 70},
    }
    
    risk_parameters = {
        'portion_buy': {'display_name': 'Buy Portion', 'default': 0.5},
        'portion_sell': {'display_name': 'Sell Portion', 'default': 0.5},
        'stop_loss': {'display_name': 'Stop Loss (fraction)', 'default': 0.05},
        'duration': {'display_name': 'Trade Duration (periods)', 'default': 4},
    }
    
    def __init__(self):
        self.name = 'rsi_strategy'
        
    def set_params(self, params):
        use_defaults = not all(k in params for k in self.parameters)
        if use_defaults:
            logger.info("Using default parameters for RSI strategy")
        self.params = {k: v['default'] for k, v in self.parameters.items() + self.risk_parameters.items()} if use_defaults else params

    def generate_signals(self, market_data: pd.DataFrame) -> pd.DataFrame:
        """
        Generates trading signals based on RSI
        
        Args:
            market_data: DataFrame with 'close' column (required)
            
        Returns:
            DataFrame with trading signals
        """
        if 'close' not in market_data.columns:
            raise ValueError("Market data must contain a 'close' column")
            
        signal_df = market_data.copy()
        signal_df['signal'] = None
        
        # Calculate RSI
        rsi = talib.RSI(signal_df['close'].values, timeperiod=self.params['rsi_period'])
        signal_df['rsi'] = rsi
        
        # Generate signals
        for i in range(1, len(signal_df)):
            current_rsi = signal_df['rsi'].iloc[i]

            # Buy signal: RSI is below the oversold threshold
            if current_rsi <= self.params['rsi_oversold']:
                signal_df.at[signal_df.index[i], 'signal'] = {
                    'type': 'buy',
                    'params': {
                        'portion': self.params['portion_buy'],
                        'stop_loss': self.params['stop_loss'],
                        'duration': self.params['duration'],
                        'close_anyway': False
                    },
                }
            
            # Sell signal: RSI is above the overbought threshold
            elif current_rsi >= self.params['rsi_overbought']:
                signal_df.at[signal_df.index[i], 'signal'] = {
                    'type': 'sell',
                    'params': {
                        'portion': self.params['portion_sell'],
                        'stop_loss': self.params['stop_loss'],
                        'duration': self.params['duration'],
                        'close_anyway': False
                    },
                }

        # Filter non-null signals
        signals_only = signal_df[signal_df['signal'].notnull()].drop(columns=['rsi'])
        logger.info(f"Total number of signals generated: {len(signals_only)}")
        
        return signals_only