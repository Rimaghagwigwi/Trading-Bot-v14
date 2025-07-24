"""
Stratégie Buy and Hold
"""

import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BuyAndHoldStrategy():
    """Stratégie Buy and Hold - Acheter au début et tenir jusqu'à la fin"""
    
    parameters = {
        'portion_buy': {'display_name': 'Portion à l\'achat', 'default': 0.5},  # Acheter 50% de la portion disponible
        'portion_sell': {'display_name': 'Portion à la vente', 'default': 1.0},  # Vendre 100% de la position
    }
    
    
    def __init__(self):
        self.name = 'buy_and_hold'
    def set_params(self, params):
        use_defaults = not all(k in params for k in self.parameters)
        if use_defaults:
            logger.info("Utilisation des paramètres par défaut pour la stratégie Buy and Hold")
        self.params = {k: v['default'] for k, v in self.parameters.items()} if use_defaults else params


    def generate_signals(self, market_data: pd.DataFrame) -> pd.DataFrame:
        signal_df = market_data.copy()
        signal_df['signal'] = None
        
        # Signal d'achat au premier point
        signal_df.at[signal_df.index[0], 'signal'] = {
            'type': 'buy_market',
            'params': {
                'portion': self.params['portion_buy']
                },
        }
        
        # Signal de vente au dernier point
        signal_df.at[signal_df.index[-1], 'signal'] = {
            'type': 'sell_market',
            'params': {
                'portion': self.params['portion_sell']
                },
        }

        # Filtrer les signaux non nuls
        return signal_df[signal_df['signal'].notnull()]