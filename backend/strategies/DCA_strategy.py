"""
Buy and Hold Strategy
"""

import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DCA_strategy():
    """DCA Strategy: Dollar Cost Averaging - Invest a fixed portion regularly"""
    
    parameters = {
        'daily_investment': {'display_name': 'Daily Investment', 'default': 0},  # Invest 0 USDT each day
        'monthly_investment': {'display_name': 'Monthly Investment', 'default': 100},  # Invest 100 USDT each month
    }
    
    def __init__(self):
        self.name = 'DCA_strategy'
        
    def set_params(self, params):
        use_defaults = not all(k in params for k in self.parameters)
        if use_defaults:
            logger.info("Using default parameters for DCA strategy")
        self.params = {k: v['default'] for k, v in self.parameters.items()} if use_defaults else params

    def generate_signals(self, market_data: pd.DataFrame) -> pd.DataFrame:
        print(market_data)
        signal_df = market_data.copy()
        signal_df['signal'] = None
        
        for i in range(1, len(signal_df)):
            if signal_df.index[i].hour == 0 and signal_df.index[i].minute == 0:
                # Daily buy signal
                signal_df.at[signal_df.index[i], 'signal'] = {
                    'type': 'buy_market',
                    'params': {
                        'usdc_value': self.params['daily_investment']
                    },
                }
            
            if signal_df.index[i].day == 1 and signal_df.index[i].hour == 0 and signal_df.index[i].minute == 0:
                # Monthly buy signal
                signal_df.at[signal_df.index[i], 'signal'] = {
                    'type': 'buy_market',
                    'params': {
                        'usdc_value': self.params['monthly_investment']
                    },
                }
        
        # Filter non-null signals
        return signal_df[signal_df['signal'].notnull()]
