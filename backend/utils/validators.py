from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import re

class ValidationError(Exception):
    """Exception levée lors d'une erreur de validation."""
    pass

class BacktestValidator:
    """
    Validateur pour les paramètres de backtest.
    """
    VALID_SYMBOLS = ['BTCUSDC', 'ETHUSDC', 'BNBUSDC', 'XRPUSDC', 'LTCUSDC']

    VALID_TIMEFRAMES = ['5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d']
    SUPPORTED_TIMEFRAMES = ['15m', '30m', '1h', '4h', '1d']  # Timeframes supportés par le bot
    
    @staticmethod
    def validate_symbol(symbol: str) -> bool:
        """
        Valide un symbole de trading.
        
        Args:
            symbol: Symbole à valider (ex: 'BTCUSDC')
            
        Returns:
            True si le symbole est valide
        """

        if not symbol:
            raise ValidationError("Le symbole ne peut pas être vide")

        return symbol in BacktestValidator.VALID_SYMBOLS

    @staticmethod
    def validate_timeframe(timeframe: str) -> bool:
        """
        Valide un timeframe.

        Args:
            timeframe: Timeframe à valider (ex: '1h')

        Returns:
            True si le timeframe est valide
        """
        
        if not timeframe:
            raise ValidationError("Le timeframe ne peut pas être vide")

        return timeframe in BacktestValidator.VALID_TIMEFRAMES
    
    @staticmethod
    def validate_date(date_str: str, field_name: str = "date") -> datetime:
        """
        Valide une date au format 'YYYY-MM-DD'.
        
        Args:
            date_str: Date à valider
            field_name: Nom du champ pour les erreurs
            
        Returns:
            Objet datetime
            
        Raises:
            ValidationError: Si la date n'est pas valide
        """
        if not date_str:
            raise ValidationError(f"La {field_name} ne peut pas être vide")
        
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            raise ValidationError(f"Format de {field_name} invalide: {date_str}. Format attendu: YYYY-MM-DD")
        
        return date_obj
    
    @staticmethod
    def validate_date_range(start_date: str, end_date: str) -> tuple:
        """
        Valide une plage de dates.
        
        Args:
            start_date: Date de début
            end_date: Date de fin
            
        Returns:
            Tuple (start_datetime, end_datetime)
            
        Raises:
            ValidationError: Si les dates ne sont pas valides
        """
        start_dt = BacktestValidator.validate_date(start_date, "date de début")
        end_dt = BacktestValidator.validate_date(end_date, "date de fin")
        
        # Vérifier que la date de début est antérieure à la date de fin
        if start_dt >= end_dt:
            raise ValidationError("La date de début doit être antérieure à la date de fin")
        
        # Vérifier que les dates ne sont pas dans le futur
        now = datetime.now()
        if start_dt > now:
            raise ValidationError("La date de début ne peut pas être dans le futur")
        if end_dt > now:
            raise ValidationError("La date de fin ne peut pas être dans le futur")
        
        # Vérifier que la période n'est pas trop longue (max 2 ans)
        if (end_dt - start_dt).days > 730:
            raise ValidationError("La période de backtest ne peut pas dépasser 2 ans")
        
        # Vérifier que la période n'est pas trop courte (min 1 jour)
        if (end_dt - start_dt).days < 1:
            raise ValidationError("La période de backtest doit être d'au moins 1 jour")
        
        return start_dt, end_dt
    
    @staticmethod
    def validate_initial_balance(balance: float) -> float:
        """
        Valide le solde initial.
        
        Args:
            balance: Solde à valider
            
        Returns:
            Solde validé
            
        Raises:
            ValidationError: Si le solde n'est pas valide
        """
        if balance <= 0:
            raise ValidationError("Le solde initial doit être positif")
        
        if balance < 10:
            raise ValidationError("Le solde initial doit être d'au moins 10 USDT")
        
        if balance > 1000000:
            raise ValidationError("Le solde initial ne peut pas dépasser 1,000,000 USDT")
        
        return float(balance)
    
    @staticmethod
    def validate_commission(commission: float) -> float:
        """
        Valide le taux de commission.
        
        Args:
            commission: Taux de commission à valider (en décimal, ex: 0.001 pour 0.1%)
            
        Returns:
            Taux de commission validé
            
        Raises:
            ValidationError: Si le taux n'est pas valide
        """
        if commission < 0:
            raise ValidationError("Le taux de commission ne peut pas être négatif")
        
        if commission > 0.1:  # 10% max
            raise ValidationError("Le taux de commission ne peut pas dépasser 10%")
        
        return float(commission)
    
    @staticmethod
    def validate_strategy_params(strategy_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valide les paramètres d'une stratégie.
        
        Args:
            strategy_name: Nom de la stratégie
            params: Paramètres à valider
            
        Returns:
            Paramètres validés
            
        Raises:
            ValidationError: Si les paramètres ne sont pas valides
        """
        if not isinstance(params, dict):
            raise ValidationError("Les paramètres doivent être un dictionnaire")
        
        validated_params = {}
        
        # Validation selon la stratégie
        if strategy_name == "buy_and_hold":
            # Pas de paramètres spécifiques
            pass
        
        elif strategy_name == "simple_ma_cross":
            # Validation des moyennes mobiles
            if 'short_window' not in params:
                raise ValidationError("Paramètre 'short_window' manquant")
            if 'long_window' not in params:
                raise ValidationError("Paramètre 'long_window' manquant")
            
            short_window = int(params['short_window'])
            long_window = int(params['long_window'])
            
            if short_window <= 0 or long_window <= 0:
                raise ValidationError("Les fenêtres de moyennes mobiles doivent être positives")
            
            if short_window >= long_window:
                raise ValidationError("La fenêtre courte doit être inférieure à la fenêtre longue")
            
            if short_window < 2 or long_window < 5:
                raise ValidationError("Fenêtres minimales: courte=2, longue=5")
            
            if short_window > 100 or long_window > 200:
                raise ValidationError("Fenêtres maximales: courte=100, longue=200")
            
            validated_params['short_window'] = short_window
            validated_params['long_window'] = long_window
        
        elif strategy_name == "rsi_strategy":
            # Validation RSI
            if 'rsi_period' not in params:
                raise ValidationError("Paramètre 'rsi_period' manquant")
            if 'rsi_overbought' not in params:
                raise ValidationError("Paramètre 'rsi_overbought' manquant")
            if 'rsi_oversold' not in params:
                raise ValidationError("Paramètre 'rsi_oversold' manquant")
            
            rsi_period = int(params['rsi_period'])
            rsi_overbought = float(params['rsi_overbought'])
            rsi_oversold = float(params['rsi_oversold'])
            
            if rsi_period < 5 or rsi_period > 50:
                raise ValidationError("La période RSI doit être entre 5 et 50")
            
            if rsi_overbought <= rsi_oversold:
                raise ValidationError("Le seuil de surachat doit être supérieur au seuil de survente")
            
            if rsi_oversold < 10 or rsi_overbought > 90:
                raise ValidationError("Seuils RSI: survente >= 10, surachat <= 90")
            
            validated_params['rsi_period'] = rsi_period
            validated_params['rsi_overbought'] = rsi_overbought
            validated_params['rsi_oversold'] = rsi_oversold
        
        return validated_params
    
    @staticmethod
    def validate_backtest_config(config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valide une configuration complète de backtest.
        
        Args:
            config: Configuration à valider
            
        Returns:
            Configuration validée
            
        Raises:
            ValidationError: Si la configuration n'est pas valide
        """
        validated_config = {}
        
        # Champs obligatoires
        required_fields = ['symbol', 'timeframe', 'start_date', 'end_date', 'strategy', 'initial_balance']
        
        for field in required_fields:
            if field not in config:
                raise ValidationError(f"Champ obligatoire manquant: {field}")
        
        # Validation individuelle des champs
        validated_config['symbol'] = BacktestValidator.validate_symbol(config['symbol'])
        validated_config['timeframe'] = BacktestValidator.validate_timeframe(config['timeframe'])

        start_dt, end_dt = BacktestValidator.validate_date_range(
            config['start_date'], config['end_date']
        )
        validated_config['start_date'] = start_dt.strftime('%Y-%m-%d')
        validated_config['end_date'] = end_dt.strftime('%Y-%m-%d')
        
        validated_config['strategy'] = config['strategy']
        validated_config['initial_balance'] = BacktestValidator.validate_initial_balance(
            float(config['initial_balance'])
        )
        
        # Champs optionnels
        if 'commission_rate' in config:
            validated_config['commission_rate'] = BacktestValidator.validate_commission(
                float(config['commission_rate'])
            )
        else:
            validated_config['commission_rate'] = 0.001  # 0.1% par défaut

        if 'strategy_params' in config:
            validated_config['strategy_params'] = BacktestValidator.validate_strategy_params(
                config['strategy'], config['strategy_params']
            )
        else:
            validated_config['strategy_params'] = {}
        
        return validated_config

class LiveTradingValidator:
    """
    Validateur pour les paramètres de trading en live.
    """
    
    @staticmethod
    def validate_api_keys(api_key: str, api_secret: str) -> tuple:
        """
        Valide les clés API Binance.
        
        Args:
            api_key: Clé API
            api_secret: Secret API
            
        Returns:
            Tuple (api_key, api_secret)
            
        Raises:
            ValidationError: Si les clés ne sont pas valides
        """
        if not api_key or not api_secret:
            raise ValidationError("Les clés API ne peuvent pas être vides")
        
        # Vérifier le format basique
        if len(api_key) < 20 or len(api_secret) < 20:
            raise ValidationError("Format de clés API invalide")
        
        return api_key.strip(), api_secret.strip()
    
    @staticmethod
    def validate_trade_amount(amount: float, balance: float, 
                             min_amount: float = 10.0) -> float:
        """
        Valide le montant d'un trade.
        
        Args:
            amount: Montant à trader
            balance: Solde disponible
            min_amount: Montant minimum
            
        Returns:
            Montant validé
            
        Raises:
            ValidationError: Si le montant n'est pas valide
        """
        if amount <= 0:
            raise ValidationError("Le montant doit être positif")
        
        if amount < min_amount:
            raise ValidationError(f"Le montant minimum est {min_amount} USDT")
        
        if amount > balance:
            raise ValidationError("Montant supérieur au solde disponible")
        
        return float(amount)
    
    @staticmethod
    def validate_stop_loss(stop_loss: float, current_price: float, 
                          trade_type: str) -> float:
        """
        Valide un stop-loss.
        
        Args:
            stop_loss: Prix de stop-loss
            current_price: Prix actuel
            trade_type: Type de trade ('BUY' ou 'SELL')
            
        Returns:
            Stop-loss validé
            
        Raises:
            ValidationError: Si le stop-loss n'est pas valide
        """
        if stop_loss <= 0:
            raise ValidationError("Le stop-loss doit être positif")
        
        if trade_type == 'BUY' and stop_loss >= current_price:
            raise ValidationError("Le stop-loss d'achat doit être inférieur au prix actuel")
        
        if trade_type == 'SELL' and stop_loss <= current_price:
            raise ValidationError("Le stop-loss de vente doit être supérieur au prix actuel")
        
        return float(stop_loss)
    
    @staticmethod
    def validate_take_profit(take_profit: float, current_price: float, 
                           trade_type: str) -> float:
        """
        Valide un take-profit.
        
        Args:
            take_profit: Prix de take-profit
            current_price: Prix actuel
            trade_type: Type de trade ('BUY' ou 'SELL')
            
        Returns:
            Take-profit validé
            
        Raises:
            ValidationError: Si le take-profit n'est pas valide
        """
        if take_profit <= 0:
            raise ValidationError("Le take-profit doit être positif")
        
        if trade_type == 'BUY' and take_profit <= current_price:
            raise ValidationError("Le take-profit d'achat doit être supérieur au prix actuel")
        
        if trade_type == 'SELL' and take_profit >= current_price:
            raise ValidationError("Le take-profit de vente doit être inférieur au prix actuel")
        
        return float(take_profit)