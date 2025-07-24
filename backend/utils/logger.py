import logging
import os
from datetime import datetime
from typing import Optional

class TradingBotLogger:
    """
    Configuration du système de logging pour le bot de trading.
    """
    
    def __init__(self, log_dir: str = "data/logs"):
        self.log_dir = log_dir
        self.setup_logging()
    
    def setup_logging(self):
        """
        Configure le système de logging avec fichiers et console.
        """
        # Créer le dossier de logs s'il n'existe pas
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Configuration du format des logs
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        date_format = '%Y-%m-%d %H:%M:%S'
        
        # Configuration du logger principal
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        
        # Nettoyer les handlers existants
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Handler pour la console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(log_format, date_format)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # Handler pour le fichier principal
        today = datetime.now().strftime('%Y-%m-%d')
        main_log_file = os.path.join(self.log_dir, f"trading_bot_{today}.log")
        file_handler = logging.FileHandler(main_log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter(log_format, date_format)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        # Handler pour les erreurs (fichier séparé)
        error_log_file = os.path.join(self.log_dir, f"errors_{today}.log")
        error_handler = logging.FileHandler(error_log_file, encoding='utf-8')
        error_handler.setLevel(logging.ERROR)
        error_formatter = logging.Formatter(log_format, date_format)
        error_handler.setFormatter(error_formatter)
        logger.addHandler(error_handler)
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        Récupère un logger avec un nom spécifique.
        
        Args:
            name: Nom du logger (généralement __name__)
            
        Returns:
            Logger configuré
        """
        return logging.getLogger(name)
    
    def log_backtest_start(self, symbol: str, strategy: str, 
                          start_date: str, end_date: str):
        """
        Log le début d'un backtest.
        
        Args:
            symbol: Symbole testé
            strategy: Nom de la stratégie
            start_date: Date de début
            end_date: Date de fin
        """
        logger = self.get_logger("backtest")
        logger.info(f"=== DÉBUT BACKTEST ===")
        logger.info(f"Symbole: {symbol}")
        logger.info(f"Stratégie: {strategy}")
        logger.info(f"Période: {start_date} à {end_date}")
        logger.info(f"========================")
    
    def log_backtest_end(self, symbol: str, strategy: str, 
                        performance: dict):
        """
        Log la fin d'un backtest avec les résultats.
        
        Args:
            symbol: Symbole testé
            strategy: Nom de la stratégie
            performance: Dictionnaire avec les métriques de performance
        """
        logger = self.get_logger("backtest")
        logger.info(f"=== FIN BACKTEST ===")
        logger.info(f"Symbole: {symbol}")
        logger.info(f"Stratégie: {strategy}")
        
        # Log des métriques principales
        if 'total_return' in performance:
            logger.info(f"Rendement total: {performance['total_return']:.2%}")
        if 'sharpe_ratio' in performance:
            logger.info(f"Ratio de Sharpe: {performance['sharpe_ratio']:.2f}")
        if 'max_drawdown' in performance:
            logger.info(f"Drawdown max: {performance['max_drawdown']:.2%}")
        if 'win_rate' in performance:
            logger.info(f"Taux de réussite: {performance['win_rate']:.2%}")
        if 'total_trades' in performance:
            logger.info(f"Nombre de trades: {performance['total_trades']}")
        
        logger.info(f"====================")
    
    def log_trade_signal(self, symbol: str, signal_type: str, 
                        price: float, reason: str, timestamp: str):
        """
        Log un signal de trading.
        
        Args:
            symbol: Symbole concerné
            signal_type: Type de signal ('BUY', 'SELL', 'HOLD')
            price: Prix au moment du signal
            reason: Raison du signal
            timestamp: Timestamp du signal
        """
        logger = self.get_logger("signals")
        logger.info(f"SIGNAL {signal_type} - {symbol} @ {price:.4f} - {reason} - {timestamp}")
    
    def log_trade_execution(self, symbol: str, action: str, 
                           quantity: float, price: float, 
                           commission: float, timestamp: str):
        """
        Log l'exécution d'un trade.
        
        Args:
            symbol: Symbole tradé
            action: Action ('BUY' ou 'SELL')
            quantity: Quantité
            price: Prix d'exécution
            commission: Commission payée
            timestamp: Timestamp d'exécution
        """
        logger = self.get_logger("trades")
        logger.info(f"TRADE {action} - {symbol} - Qty: {quantity:.6f} @ {price:.4f} - Commission: {commission:.4f} - {timestamp}")
    
    def log_portfolio_update(self, balance: float, positions: dict, 
                           total_value: float, timestamp: str):
        """
        Log la mise à jour du portefeuille.
        
        Args:
            balance: Solde en cash
            positions: Positions actuelles
            total_value: Valeur totale du portefeuille
            timestamp: Timestamp de la mise à jour
        """
        logger = self.get_logger("portfolio")
        logger.info(f"PORTFOLIO UPDATE - Balance: {balance:.2f} - Total: {total_value:.2f} - {timestamp}")
        
        for symbol, position in positions.items():
            if position['quantity'] > 0:
                logger.info(f"  Position {symbol}: {position['quantity']:.6f} @ {position['avg_price']:.4f}")
    
    def log_error(self, module: str, error_type: str, message: str, 
                 exception: Exception = None):
        """
        Log une erreur avec contexte.
        
        Args:
            module: Module où l'erreur s'est produite
            error_type: Type d'erreur
            message: Message d'erreur
            exception: Exception Python (optionnel)
        """
        logger = self.get_logger(module)
        error_msg = f"ERROR [{error_type}]: {message}"
        
        if exception:
            error_msg += f" - Exception: {str(exception)}"
        
        logger.error(error_msg)
        
        # Log la stack trace si exception fournie
        if exception:
            logger.error(f"Stack trace:", exc_info=True)
    
    def log_data_update(self, symbol: str, timeframe: str, 
                       records_count: int, source: str):
        """
        Log la mise à jour des données.
        
        Args:
            symbol: Symbole mis à jour
            timeframe: Timeframe
            records_count: Nombre d'enregistrements
            source: Source des données ('binance', 'cache', etc.)
        """
        logger = self.get_logger("data")
        logger.info(f"DATA UPDATE - {symbol} {timeframe} - {records_count} records from {source}")
    
    def log_strategy_performance(self, strategy_name: str, 
                               performance_metrics: dict):
        """
        Log les performances d'une stratégie.
        
        Args:
            strategy_name: Nom de la stratégie
            performance_metrics: Métriques de performance
        """
        logger = self.get_logger("strategy")
        logger.info(f"STRATEGY PERFORMANCE - {strategy_name}")
        
        for metric, value in performance_metrics.items():
            if isinstance(value, float):
                if 'rate' in metric.lower() or 'ratio' in metric.lower():
                    logger.info(f"  {metric}: {value:.4f}")
                elif 'return' in metric.lower() or 'drawdown' in metric.lower():
                    logger.info(f"  {metric}: {value:.2%}")
                else:
                    logger.info(f"  {metric}: {value:.2f}")
            else:
                logger.info(f"  {metric}: {value}")
    
    def set_log_level(self, level: str):
        """
        Change le niveau de logging.
        
        Args:
            level: Niveau ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        """
        numeric_level = getattr(logging, level.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError(f'Invalid log level: {level}')
        
        logger = logging.getLogger()
        logger.setLevel(numeric_level)
        
        # Mettre à jour tous les handlers
        for handler in logger.handlers:
            handler.setLevel(numeric_level)
    
    def cleanup_old_logs(self, days_to_keep: int = 30):
        """
        Nettoie les anciens fichiers de logs.
        
        Args:
            days_to_keep: Nombre de jours à conserver
        """
        import glob
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        # Trouver tous les fichiers de logs
        log_files = glob.glob(os.path.join(self.log_dir, "*.log"))
        
        for log_file in log_files:
            try:
                # Récupérer la date de modification du fichier
                file_time = datetime.fromtimestamp(os.path.getmtime(log_file))
                
                if file_time < cutoff_date:
                    os.remove(log_file)
                    print(f"Supprimé ancien fichier de log: {log_file}")
            
            except Exception as e:
                print(f"Erreur lors de la suppression de {log_file}: {e}")

# Instance globale du logger
_logger_instance = None

def get_logger(name: str = None) -> logging.Logger:
    """
    Fonction utilitaire pour récupérer un logger.
    
    Args:
        name: Nom du logger (optionnel)
        
    Returns:
        Logger configuré
    """
    global _logger_instance
    
    if _logger_instance is None:
        _logger_instance = TradingBotLogger()
    
    if name:
        return _logger_instance.get_logger(name)
    else:
        return _logger_instance.get_logger(__name__)

def setup_logging(log_dir: str = "data/logs"):
    """
    Fonction pour initialiser le système de logging.
    
    Args:
        log_dir: Répertoire pour les fichiers de logs
    """
    global _logger_instance
    _logger_instance = TradingBotLogger(log_dir)

# Fonctions utilitaires pour les logs spécifiques
def log_backtest_start(symbol: str, strategy: str, start_date: str, end_date: str):
    """Log le début d'un backtest."""
    if _logger_instance:
        _logger_instance.log_backtest_start(symbol, strategy, start_date, end_date)

def log_backtest_end(symbol: str, strategy: str, performance: dict):
    """Log la fin d'un backtest."""
    if _logger_instance:
        _logger_instance.log_backtest_end(symbol, strategy, performance)

def log_trade_signal(symbol: str, signal_type: str, price: float, reason: str, timestamp: str):
    """Log un signal de trading."""
    if _logger_instance:
        _logger_instance.log_trade_signal(symbol, signal_type, price, reason, timestamp)

def log_trade_execution(symbol: str, action: str, quantity: float, price: float, commission: float, timestamp: str):
    """Log l'exécution d'un trade."""
    if _logger_instance:
        _logger_instance.log_trade_execution(symbol, action, quantity, price, commission, timestamp)

def log_error(module: str, error_type: str, message: str, exception: Exception = None):
    """Log une erreur."""
    if _logger_instance:
        _logger_instance.log_error(module, error_type, message, exception)