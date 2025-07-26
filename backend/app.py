"""
Main Flask Application - API for the trading bot
"""

import json
import traceback
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import logging
import os
from datetime import datetime

import pandas as pd

from backend.strategies.DCA_strategy import DCA_strategy
from backend.strategies.RSI_strategy import RSIStrategy
from backend.strategies.buy_and_hold import BuyAndHoldStrategy

from .backtest.performance_metrics import PerformanceMetrics
from .backtest.backtest_engine import BacktestEngine
from .data.data_manager import DataManager

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    """Factory to create the Flask application"""
    FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))
    app = Flask(__name__, static_folder=None)
    
    # CORS configuration to allow requests from the frontend
    CORS(app)
    
    # Application configuration
    app.config['DEBUG'] = True
    app.config['TESTING'] = False
    
    data_manager = DataManager()
    
    # Route to serve index.html
    @app.route("/")
    def serve_index():
        return send_from_directory(FRONTEND_DIR, "index.html")

    # Route to serve static files (JS, CSS, etc.)
    @app.route("/<path:path>")
    def serve_static(path):
        return send_from_directory(FRONTEND_DIR, path)
    
    
    @app.route('/health')
    def health():
        """Health endpoint"""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'services': {
                'binance_api': 'connected',
                'backtest_engine': 'ready'
            }
        })
    
    @app.route('/api/market-data')
    def get_market_data():
        """Fetches market data"""
        try:
            # Request parameters
            symbol = request.args.get('symbol', 'BTCUSDC')
            timeframe = request.args.get('timeframe', '1h')
            start_ts = request.args.get('start_date')
            end_ts = request.args.get('end_date')
            
            # Fetch data
            data = data_manager.get_historical_data(
                symbol=symbol,
                start_date=start_ts,
                end_date=end_ts,
                timeframe=timeframe
            )

            if data.empty:
                return jsonify({'error': 'No data available'}), 404
            
            # Convert for API
            data_dict = data.to_dict('records')
            
            # Format timestamps
            for record in data_dict:
                record['timestamp'] = record['timestamp'].isoformat()
            
            return jsonify({
                'symbol': symbol,
                'timeframe': timeframe,
                'start_date': start_ts,
                'end_date': end_ts,
                'data_points': len(data_dict),
                'data': data_dict
            })
            
        except Exception as e:
            logger.error(f"Error fetching data: {str(e)}")
            return jsonify({'error': 'Error fetching market data'}), 500
    
    @app.route('/api/backtest', methods=['POST'])
    def run_backtest():
        """Runs a backtest"""
        try:
            # Get parameters
            request_json = request.get_json()
            
            if not request_json:
                return jsonify({'error': 'JSON data required'}), 400
            else:
                logger.info(f"Parameters received for backtest: {request_json}")
                
            # Get historical data
            symbols = request_json.get('symbols', ['BTCUSDT'])
            timeframe = request_json.get('timeframe', '1h')
            start_ts = pd.Timestamp(request_json.get('start_date', datetime.now() - pd.Timedelta(days=90)))
            end_ts = pd.Timestamp(request_json.get('end_date', datetime.now()))

            market_data = {}
            for symbol in symbols:
                symbol_data = data_manager.get_historical_data(
                    symbol=symbol,
                    start_date=start_ts,
                    end_date=end_ts,
                    timeframe=timeframe
                )
                if symbol_data.empty:
                    return jsonify({'error': f'Unable to fetch market data for {symbol}'}), 500
                market_data[symbol] = symbol_data.set_index('timestamp', drop=True)

            strategy_name=request_json.get('strategy', 'buy_and_hold')
            logger.info(f"🚀 Starting backtest: {strategy_name} on {symbols}")

            # Create backtest engine
            backtest_engine = BacktestEngine(
                initial_capital=float(request_json.get('initial_capital', 10000)), 
                commission_rate=float(request_json.get('commission_rate', 0.001)),
                timeframe=timeframe,
                paires=symbols
            )
            
            logger.info(f"Initializing strategy: {request_json}")
            backtest_engine.set_strategy(request_json.get('strategy_params', {}), request_json.get('strategy_class', 'BuyAndHoldStrategy'))

            # Run backtest
            results = backtest_engine.run_backtest(market_data)
            
            if not results:
                return jsonify({'error': 'Backtest failed'}), 500
            
            logger.info(f"✅ Backtest finished: {strategy_name}")
            
            performance_metrics = PerformanceMetrics(results, market_data)
            metrics = performance_metrics.calculate_all_metrics()
            logger.info(f"📊 Performance metrics calculated")
            
            for symbol, data in market_data.items():
                market_data[symbol].index = data.index.strftime('%Y-%m-%d %H:%M:%S')
                market_data[symbol] = market_data[symbol].reset_index().to_dict('list')

            results['graph_data']['timestamp'] = [ts.strftime('%Y-%m-%d %H:%M:%S') for ts in results['graph_data']['timestamp']]
            print("Formatted market data:")
            print(market_data['BTCUSDC'].keys())

            return jsonify({
                'success': True,
                'backtest_id': f"{strategy_name}_{int(datetime.now().timestamp())}",
                'parameters': request_json,
                'results': results,
                'metrics': metrics,
                'market_data': market_data,
            })

        except Exception as e:
            error_traceback = traceback.format_exc()
            logger.error(f"Error during backtest:\n{error_traceback}")
            return jsonify({'error': f'Error during backtest: {str(e)}\n\nTraceback:\n{error_traceback}'}), 500

    @app.route('/api/config/defaults')
    def get_default_config():
        """Returns default configuration for backtest"""
        default_config = {
            'symbols': ['BTCUSDC'],
            'timeframe': '1h',
            'days': 90,
            'initial_capital': 10000,
            'commission_rate': 0.001,
            'strategy': 'buy_and_hold'
        }
        
        return jsonify(default_config)
    
    @app.route('/api/config/symbols')
    def get_symbols():
        """Returns a list of supported symbols"""
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        return jsonify({
            'symbols': config.get('trading_pairs', []),
        })
        
    @app.route('/api/config/timeframes')
    def get_timeframes():
        """Returns available timeframes"""
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        return jsonify({
            'timeframes': config.get('timeframes', []),
        })
        
    @app.route('/api/config/strategies')
    def get_strategies():
        """Returns the list of available strategies"""
        strategies = [
            {
            'name': 'buy_and_hold',
            'display_name': 'Buy & Hold',
            'description': 'Buy at the beginning and hold until the end',
            'class': 'BuyAndHoldStrategy',
            'parameters': BuyAndHoldStrategy.parameters
            },
            {
            'name': 'rsi_strategy',
            'display_name': 'RSI Strategy',
            'description': 'Buy on oversold, sell on overbought',
            'class': 'RSIStrategy',
            'parameters': RSIStrategy.parameters
            },
            {
            'name': 'DCA_strategy',
            'display_name': 'Dollar Cost Averaging',
            'description': 'Invest a fixed portion regularly',
            'class': 'DCA_strategy',
            'parameters': DCA_strategy.parameters
            }
        ]
        
        return jsonify({
            'strategies': strategies,
            'total': len(strategies)
        })
    
    @app.errorhandler(404)
    def not_found(error):
        """404 error handler"""
        return jsonify({'error': 'Endpoint not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """500 error handler"""
        return jsonify({'error': 'Internal server error'}), 500
    
    
    return app

