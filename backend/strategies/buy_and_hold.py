"""
Buy and Hold Strategy
"""

import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BuyAndHoldStrategy():
    """Buy and Hold Strategy - Buy at the beginning and hold until the end"""
    
    parameters = {
        'portion_buy': {'display_name': 'Buy Portion', 'default': 0.5},  # Buy 50% of available portion
        'portion_sell': {'display_name': 'Sell Portion', 'default': 1.0},  # Sell 100% of the position
    }
    
    def __init__(self):
        self.name = 'buy_and_hold'
    def set_params(self, params):
        use_defaults = not all(k in params for k in self.parameters)
        if use_defaults:
            logger.info("Using default parameters for Buy and Hold strategy")
        self.params = {k: v['default'] for k, v in self.parameters.items()} if use_defaults else params

    def generate_signals(self, market_data: pd.DataFrame) -> pd.DataFrame:
        signal_df = market_data.copy()
        signal_df['signal'] = None

        # Buy signal at the first point
        signal_df.at[signal_df.index[0], 'signal'] = {
            'type': 'buy',
            'params': {
                'portion': self.params['portion_buy']
                },
        }
        
        # Sell signal at the last point
        signal_df.at[signal_df.index[-1], 'signal'] = {
            'type': 'sell',
            'params': {
                'portion': self.params['portion_sell']
                },
        }

        # Filter non-null signals
        signals_only = signal_df[signal_df['signal'].notnull()]

        return signals_only
