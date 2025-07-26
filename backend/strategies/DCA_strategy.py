"""
Stratégie Buy and Hold
"""

import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DCA_strategy():
    """Stratégie DCA: Dollar Cost Averaging - Investir régulièrement une portion fixe"""
    
    parameters = {
        'daily_investment': {'display_name': 'Investissement quotidien', 'default': 0},  # Investir 0 USDT chaque jour
        'monthly_investment': {'display_name': 'Investissement mensuel', 'default': 100},  # Investir 100 USDT chaque mois
    }
    
    
    def __init__(self):
        self.name = 'DCA_strategy'
        
    def set_params(self, params):
        use_defaults = not all(k in params for k in self.parameters)
        if use_defaults:
            logger.info("Utilisation des paramètres par défaut pour la stratégie DCA")
        self.params = {k: v['default'] for k, v in self.parameters.items()} if use_defaults else params


    def generate_signals(self, market_data: pd.DataFrame) -> pd.DataFrame:
        print(market_data)
        signal_df = market_data.copy()
        signal_df['signal'] = None
        
        for i in range(1, len(signal_df)):
            if signal_df.index[i].hour == 0 and signal_df.index[i].minute == 0:
                # Signal d'achat quotidien
                signal_df.at[signal_df.index[i], 'signal'] = {
                    'type': 'buy_market',
                    'params': {
                        'usdc_value': self.params['daily_investment']
                    },
                }
            
            if signal_df.index[i].day == 1 and signal_df.index[i].hour == 0 and signal_df.index[i].minute == 0:
                # Signal d'achat mensuel
                signal_df.at[signal_df.index[i], 'signal'] = {
                    'type': 'buy_market',
                    'params': {
                        'usdc_value': self.params['monthly_investment']
                    },
                }
        
        # Filtrer les signaux non nuls
        return signal_df[signal_df['signal'].notnull()]