import os
import time
import pandas as pd
import requests

class DataManager:
    """
    Gestionnaire des données historiques avec stockage CSV.
    Récupère les données depuis Binance et les stocke localement.
    """
    
    def __init__(self):
        self.data_dir = "backend/data/historical"
        # Créer le dossier de données s'il n'existe pas
        os.makedirs(self.data_dir, exist_ok=True)

    def get_historical_data(self, symbol: str, start_date: pd.Timestamp, end_date: pd.Timestamp, timeframe: str) -> pd.DataFrame:
        """
        Récupère les données historiques OHLCV pour un symbol et timeframe donné.
        
        Args:
            symbol: Symbole de trading (ex: "BTCUSDT")
            start_date: Date de début
            end_date: Date de fin
            timeframe: Intervalle de temps (ex: "1m", "5m", "1h", etc.)
            
        Returns:
            DataFrame avec colonnes: timestamp, open, high, low, close, volume
        """
        
        filename = f"{symbol}_{timeframe}.csv"
        filepath = os.path.join(self.data_dir, filename)
        
        # Normaliser les dates d'entrée (enlever timezone si présente)
        start_date = start_date.tz_localize(None) if start_date.tz is not None else start_date
        end_date = end_date.tz_localize(None) if end_date.tz is not None else end_date
        
        # Charger les données existantes ou créer un DataFrame vide
        if os.path.exists(filepath):
            df = pd.read_csv(filepath)
            df['timestamp'] = pd.to_datetime(df['timestamp']).dt.tz_localize(None)  # Enlever timezone
            df = df.sort_values('timestamp')
        else:
            df = pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # Vérifier si on a besoin de récupérer des données manquantes
        missing_ranges = self._find_missing_ranges(df, start_date, end_date, timeframe)
        
        # Récupérer les données manquantes depuis Binance
        for range_start, range_end in missing_ranges:
            new_data = self._fetch_from_binance(symbol, range_start, range_end, timeframe)
            print("New data fetched:", new_data)
            if not new_data.empty:
                df = pd.concat([df, new_data], ignore_index=True)
                print("Data concatenated:", df)
        
        # Nettoyer et sauvegarder
        if not df.empty:
            df = df.drop_duplicates(subset=['timestamp']).sort_values('timestamp')
            df.to_csv(filepath, index=False)
        
        # Retourner uniquement les données dans la plage demandée
        return df[(df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)].copy()

    def _find_missing_ranges(self, df: pd.DataFrame, start_date: pd.Timestamp, end_date: pd.Timestamp, timeframe: str) -> list:
        """Trouve les plages de données manquantes."""
        missing_ranges = []
        
        if df.empty:
            return [(start_date, end_date)]
        
        # Vérifier avant le premier timestamp
        first_ts = df['timestamp'].min()
        if start_date < first_ts:
            # Calculer correctement la fin de la plage manquante
            timeframe_delta = pd.Timedelta(timeframe)
            missing_ranges.append((start_date, first_ts - timeframe_delta))
        
        # Vérifier après le dernier timestamp
        last_ts = df['timestamp'].max()
        if end_date > last_ts:
            timeframe_delta = pd.Timedelta(timeframe)
            missing_ranges.append((last_ts + timeframe_delta, end_date))
        
        # Vérifier les trous dans les données
        df_in_range = df[(df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)]
        if len(df_in_range) > 1:
            expected_timestamps = pd.date_range(start=df_in_range['timestamp'].min(), 
                                              end=df_in_range['timestamp'].max(), 
                                              freq=timeframe)
            actual_timestamps = set(df_in_range['timestamp'])
            
            gap_start = None
            for ts in expected_timestamps:
                if ts not in actual_timestamps:
                    if gap_start is None:
                        gap_start = ts
                else:
                    if gap_start is not None:
                        timeframe_delta = pd.Timedelta(timeframe)
                        missing_ranges.append((gap_start, ts - timeframe_delta))
                        gap_start = None
            
            # Gérer un trou qui va jusqu'à la fin
            if gap_start is not None:
                missing_ranges.append((gap_start, df_in_range['timestamp'].max()))
        
        return missing_ranges

    def _fetch_from_binance(self, symbol: str, start_date: pd.Timestamp, end_date: pd.Timestamp, interval: str) -> pd.DataFrame:
        """Récupère les données depuis l'API Binance."""
        base_url = "https://api.binance.com/api/v3/klines"
        
        print(f"Récupération des données de {symbol} de {start_date} à {end_date} avec intervalle {interval}")
        start_ms = int(start_date.timestamp() * 1000)
        end_ms = int(end_date.timestamp() * 1000)

        params = {
            'symbol': symbol,
            'interval': interval,
            'startTime': start_ms,
            'endTime': end_ms,
            'limit': 1000
        }
        
        all_data = []
        
        while start_ms < end_ms:
            params['startTime'] = start_ms
            
            try:
                response = requests.get(base_url, params=params)
                response.raise_for_status()
                data = response.json()
                
                if not data:
                    break
                
                for kline in data:
                    all_data.append({
                        'timestamp': pd.to_datetime(kline[0], unit='ms').tz_localize(None),  # Enlever timezone
                        'open': float(kline[1]),
                        'high': float(kline[2]),
                        'low': float(kline[3]),
                        'close': float(kline[4]),
                        'volume': float(kline[5])
                    })
                
                # Mettre à jour le timestamp de départ pour la prochaine requête
                start_ms = data[-1][0] + 1
                
                if start_ms < end_ms:
                    time.sleep(1)
            except requests.exceptions.RequestException as e:
                print(f"Erreur lors de la récupération des données: {e}")
                break

        return pd.DataFrame(all_data)