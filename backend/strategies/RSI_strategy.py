"""
Stratégie RSI (Relative Strength Index)
"""

import pandas as pd
import talib
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RSIStrategy():
    """Stratégie RSI - Acheter en survente, vendre en surachat"""
    
    parameters = {
        'rsi_period': {'display_name': 'Période RSI', 'default': 14},
        'rsi_oversold': {'display_name': 'Seuil de survente', 'default': 30},
        'rsi_overbought': {'display_name': 'Seuil de surachat', 'default': 70},
        'portion_buy': {'display_name': 'Portion à l\'achat', 'default': 0.5},
        'portion_sell': {'display_name': 'Portion à la vente', 'default': 0.5},
    }
    
    def __init__(self):
        self.name = 'rsi_strategy'
        
    def set_params(self, params):
        use_defaults = not all(k in params for k in self.parameters)
        if use_defaults:
            logger.info("Utilisation des paramètres par défaut pour la stratégie RSI")
        self.params = {k: v['default'] for k, v in self.parameters.items()} if use_defaults else params

    def generate_signals(self, market_data: pd.DataFrame) -> pd.DataFrame:
        """
        Génère les signaux de trading basés sur le RSI
        
        Args:
            market_data: DataFrame avec colonnes 'close' (obligatoire)
            
        Returns:
            DataFrame avec les signaux de trading
        """
        if 'close' not in market_data.columns:
            raise ValueError("Les données de marché doivent contenir une colonne 'close'")
            
        signal_df = market_data.copy()
        signal_df['signal'] = None
        
        # Calculer le RSI
        rsi = talib.RSI(signal_df['close'].values, timeperiod=self.params['rsi_period'])
        signal_df['rsi'] = rsi
        
        # Générer les signaux
        for i in range(1, len(signal_df)):
            current_rsi = signal_df['rsi'].iloc[i]
            previous_rsi = signal_df['rsi'].iloc[i-1]
            
            # Signal d'achat : RSI passe au-dessus du seuil de survente
            if (previous_rsi <= self.params['rsi_oversold'] and 
                current_rsi > self.params['rsi_oversold']):
                signal_df.at[signal_df.index[i], 'signal'] = {
                    'type': 'buy_market',
                    'params': {
                        'portion': self.params['portion_buy']
                    },
                }
            
            # Signal de vente : RSI passe en-dessous du seuil de surachat
            elif (previous_rsi >= self.params['rsi_overbought'] and 
                  current_rsi < self.params['rsi_overbought']):
                signal_df.at[signal_df.index[i], 'signal'] = {
                    'type': 'sell_market',
                    'params': {
                        'portion': self.params['portion_sell']
                    },
                }

        # Filtrer les signaux non nuls
        signals_only = signal_df[signal_df['signal'].notnull()]
        logger.info(f"Nombre total de signaux générés: {len(signals_only)}")
        
        return signals_only