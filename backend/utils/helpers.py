"""
Fonctions utilitaires pour le bot de trading
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import json
import os
import hashlib
from decimal import Decimal, ROUND_DOWN

def timestamp_to_datetime(timestamp: int) -> datetime:
    """Convertit un timestamp en datetime"""
    return datetime.fromtimestamp(timestamp / 1000)

def datetime_to_timestamp(dt: datetime) -> int:
    """Convertit un datetime en timestamp"""
    return int(dt.timestamp() * 1000)

def format_datetime(dt: datetime) -> str:
    """Formate un datetime en string lisible"""
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def parse_datetime(dt_str: str) -> datetime:
    """Parse une string datetime"""
    return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")

def calculate_timeframe_minutes(timeframe: str) -> int:
    """Calcule le nombre de minutes dans un timeframe"""
    timeframe_minutes = {
        '1m': 1, '3m': 3, '5m': 5, '15m': 15, '30m': 30,
        '1h': 60, '2h': 120, '4h': 240, '6h': 360, '8h': 480, '12h': 720,
        '1d': 1440, '3d': 4320, '1w': 10080, '1M': 43200
    }
    return timeframe_minutes.get(timeframe, 60)

def calculate_periods_needed(days: int, timeframe: str) -> int:
    """Calcule le nombre de périodes nécessaires pour X jours"""
    minutes_per_day = 24 * 60
    timeframe_minutes = calculate_timeframe_minutes(timeframe)
    return int((days * minutes_per_day) / timeframe_minutes)

def round_down_to_precision(value: float, precision: int) -> float:
    """Arrondit une valeur vers le bas avec une précision donnée"""
    if precision <= 0:
        return float(int(value))
    
    decimal_value = Decimal(str(value))
    precision_str = '0.' + '0' * (precision - 1) + '1'
    return float(decimal_value.quantize(Decimal(precision_str), rounding=ROUND_DOWN))

def calculate_position_size(capital: float, risk_per_trade: float, 
                          entry_price: float, stop_loss: float) -> float:
    """Calcule la taille de position basée sur le risque"""
    if stop_loss == 0 or entry_price == stop_loss:
        return 0.0
    
    risk_amount = capital * risk_per_trade
    price_diff = abs(entry_price - stop_loss)
    
    if price_diff == 0:
        return 0.0
    
    return risk_amount / price_diff

def calculate_commission(quantity: float, price: float, commission_rate: float) -> float:
    """Calcule la commission sur un trade"""
    trade_value = quantity * price
    return trade_value * commission_rate

def calculate_pnl(entry_price: float, exit_price: float, quantity: float, 
                  side: str, commission_rate: float = 0.001) -> Tuple[float, float]:
    """
    Calcule le PnL d'un trade
    
    Returns:
        Tuple[float, float]: (pnl_net, total_fees)
    """
    if side.lower() == 'long':
        pnl_gross = (exit_price - entry_price) * quantity
    else:  # short
        pnl_gross = (entry_price - exit_price) * quantity
    
    # Calculer les frais (entrée + sortie)
    entry_fee = calculate_commission(quantity, entry_price, commission_rate)
    exit_fee = calculate_commission(quantity, exit_price, commission_rate)
    total_fees = entry_fee + exit_fee
    
    pnl_net = pnl_gross - total_fees
    
    return pnl_net, total_fees

def calculate_drawdown(values: List[float]) -> List[float]:
    """Calcule le drawdown pour une série de valeurs"""
    if not values:
        return []
    
    drawdowns = []
    peak = values[0]
    
    for value in values:
        if value > peak:
            peak = value
        
        drawdown = (peak - value) / peak if peak > 0 else 0
        drawdowns.append(drawdown)
    
    return drawdowns

def calculate_returns(values: List[float]) -> List[float]:
    """Calcule les retours pour une série de valeurs"""
    if len(values) < 2:
        return []
    
    returns = []
    for i in range(1, len(values)):
        if values[i-1] > 0:
            returns.append((values[i] - values[i-1]) / values[i-1])
        else:
            returns.append(0.0)
    
    return returns


def validate_ohlcv_data(data: List[Dict]) -> bool:
    """Valide les données OHLCV"""
    if not data:
        return False
    
    required_fields = ['open', 'high', 'low', 'close', 'volume', 'timestamp']
    
    for candle in data:
        if not all(field in candle for field in required_fields):
            return False
        
        # Vérifier la cohérence OHLC
        if not (candle['low'] <= candle['open'] <= candle['high'] and
                candle['low'] <= candle['close'] <= candle['high']):
            return False
    
    return True

def generate_hash(data: str) -> str:
    """Génère un hash MD5 pour les données"""
    return hashlib.md5(data.encode()).hexdigest()

def safe_float(value: Any, default: float = 0.0) -> float:
    """Convertit une valeur en float de manière sécurisée"""
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default

def safe_int(value: Any, default: int = 0) -> int:
    """Convertit une valeur en int de manière sécurisée"""
    try:
        return int(value) if value is not None else default
    except (ValueError, TypeError):
        return default

def create_directories(paths: List[str]) -> None:
    """Crée les répertoires s'ils n'existent pas"""
    for path in paths:
        os.makedirs(path, exist_ok=True)

def save_json(data: Dict, filepath: str) -> bool:
    """Sauvegarde des données JSON"""
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        return True
    except Exception as e:
        print(f"Erreur sauvegarde JSON: {e}")
        return False

def load_json(filepath: str) -> Optional[Dict]:
    """Charge des données JSON"""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Erreur chargement JSON: {e}")
        return None

def format_number(value: float, decimals: int = 2) -> str:
    """Formate un nombre avec des séparateurs"""
    return f"{value:,.{decimals}f}"

def format_percentage(value: float, decimals: int = 2) -> str:
    """Formate un pourcentage"""
    return f"{value * 100:.{decimals}f}%"

def format_currency(value: float, symbol: str = "$") -> str:
    """Formate une devise"""
    return f"{symbol}{value:,.2f}"

def time_ago(timestamp: int) -> str:
    """Retourne le temps écoulé depuis un timestamp"""
    now = datetime.now()
    past = timestamp_to_datetime(timestamp)
    diff = now - past
    
    if diff.days > 0:
        return f"{diff.days} jour{'s' if diff.days > 1 else ''}"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} heure{'s' if hours > 1 else ''}"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''}"
    else:
        return "À l'instant"

def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """Divise une liste en chunks"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def merge_ohlcv_data(data1: List[Dict], data2: List[Dict]) -> List[Dict]:
    """Fusionne deux listes de données OHLCV en évitant les doublons"""
    if not data1:
        return data2
    if not data2:
        return data1
    
    # Créer un dictionnaire basé sur les timestamps
    merged = {}
    
    for candle in data1 + data2:
        timestamp = candle['timestamp']
        merged[timestamp] = candle
    
    # Retourner les données triées par timestamp
    return sorted(merged.values(), key=lambda x: x['timestamp'])

def calculate_correlation(values1: List[float], values2: List[float]) -> float:
    """Calcule la corrélation entre deux séries"""
    if len(values1) != len(values2) or len(values1) < 2:
        return 0.0
    
    return np.corrcoef(values1, values2)[0, 1]

def is_market_hours(timestamp: int, market_open: int = 9, market_close: int = 17) -> bool:
    """Vérifie si un timestamp est pendant les heures de marché"""
    dt = timestamp_to_datetime(timestamp)
    return market_open <= dt.hour < market_close

def get_next_timeframe_timestamp(current_timestamp: int, timeframe: str) -> int:
    """Calcule le prochain timestamp pour un timeframe donné"""
    minutes = calculate_timeframe_minutes(timeframe)
    return current_timestamp + (minutes * 60 * 1000)

def validate_symbol_format(symbol: str) -> bool:
    """Valide le format d'un symbole crypto"""
    return len(symbol) >= 6 and symbol.isupper() and symbol.endswith('USDT')

def clean_symbol(symbol: str) -> str:
    """Nettoie un symbole crypto"""
    return symbol.upper().replace('/', '').replace('-', '')

def get_base_asset(symbol: str) -> str:
    """Extrait l'asset de base d'un symbole"""
    if symbol.endswith('USDT'):
        return symbol[:-4]
    elif symbol.endswith('BTC'):
        return symbol[:-3]
    elif symbol.endswith('ETH'):
        return symbol[:-3]
    else:
        return symbol[:-4]  # Par défaut
    
def convert_numpy_types(obj):
    """
    Convertit les types numpy/pandas en types Python natifs pour la sérialisation JSON
    
    Args:
        obj: Objet à convertir
        
    Returns:
        Objet converti en types Python natifs
    """
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    elif isinstance(obj, pd.DataFrame):
        return obj.to_dict('records')
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    else:
        return obj