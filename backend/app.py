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
                if isinstance(record['timestamp'], pd.Timestamp):
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
            
            logger.info(f"Parameters received for backtest: {request_json}")
                
            # Get historical data
            symbols = request_json.get('symbols', ['BTCUSDT'])
            timeframe = request_json.get('timeframe', '1h')
            
            # Handle date parameters more robustly
            try:
                if 'start_date' in request_json:
                    start_ts = pd.Timestamp(request_json['start_date'])
                else:
                    start_ts = pd.Timestamp(datetime.now() - pd.Timedelta(days=90))
                    
                if 'end_date' in request_json:
                    end_ts = pd.Timestamp(request_json['end_date'])
                else:
                    end_ts = pd.Timestamp(datetime.now())
            except Exception as e:
                logger.error(f"Error parsing dates: {e}")
                return jsonify({'error': 'Invalid date format'}), 400

            # Fetch market data for all symbols
            market_data = {}
            for symbol in symbols:
                try:
                    symbol_data = data_manager.get_historical_data(
                        symbol=symbol,
                        start_date=start_ts,
                        end_date=end_ts,
                        timeframe=timeframe
                    )
                    if symbol_data.empty:
                        return jsonify({'error': f'No market data available for {symbol}'}), 500
                    
                    # Set timestamp as index
                    symbol_data = symbol_data.set_index('timestamp', drop=True)
                    market_data[symbol] = symbol_data
                    
                except Exception as e:
                    logger.error(f"Error fetching data for {symbol}: {e}")
                    return jsonify({'error': f'Unable to fetch market data for {symbol}'}), 500

            strategy_name = request_json.get('strategy', 'buy_and_hold')
            logger.info(f"🚀 Starting backtest: {strategy_name} on {symbols}")

            # Create backtest engine
            backtest_engine = BacktestEngine(
                initial_capital=float(request_json.get('initial_capital', 10000)), 
                commission_rate=float(request_json.get('commission_rate', 0.001)),
                timeframe=timeframe,
                pairs=symbols
            )
            
            # Set strategy with proper error handling
            try:
                strategy_params = request_json.get('strategy_params', {})
                strategy_class = request_json.get('strategy_class', 'BuyAndHoldStrategy')
                
                logger.info(f"Initializing strategy: {strategy_class} with params: {strategy_params}")
                backtest_engine.set_strategy(strategy_params, strategy_class)
            except Exception as e:
                logger.error(f"Error setting strategy: {e}")
                return jsonify({'error': f'Invalid strategy configuration: {str(e)}'}), 400

            # Run backtest
            results = backtest_engine.run_backtest(market_data)
            
            if not results:
                return jsonify({'error': 'Backtest failed to produce results'}), 500
            
            logger.info(f"✅ Backtest finished: {strategy_name}")
            
            # Calculate performance metrics
            try:
                performance_metrics = PerformanceMetrics(results, market_data)
                metrics = performance_metrics.calculate_all_metrics()
                logger.info(f"📊 Performance metrics calculated")
            except Exception as e:
                logger.warning(f"Error calculating metrics: {e}")
                metrics = {}
            
            # Prepare market data for response (convert to serializable format)
            market_data_response = {}
            for symbol, data in market_data.items():
                # Reset index to get timestamp as column
                data_reset = data.reset_index()
                
                # Convert timestamps to strings
                if 'timestamp' in data_reset.columns:
                    data_reset['timestamp'] = data_reset['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
                
                # Convert to list format for JSON serialization
                market_data_response[symbol] = {
                    'timestamps': data_reset['timestamp'].tolist(),
                    'open': data_reset['open'].tolist(),
                    'high': data_reset['high'].tolist(), 
                    'low': data_reset['low'].tolist(),
                    'close': data_reset['close'].tolist(),
                    'volume': data_reset['volume'].tolist() if 'volume' in data_reset.columns else []
                }

            # Ensure graph data timestamps are properly formatted
            if 'graph_data' in results and 'timestamp' in results['graph_data']:
                # Handle case where timestamps might already be strings
                formatted_timestamps = []
                for ts in results['graph_data']['timestamp']:
                    if isinstance(ts, str):
                        formatted_timestamps.append(ts)
                    else:
                        formatted_timestamps.append(ts.strftime('%Y-%m-%d %H:%M:%S'))
                results['graph_data']['timestamp'] = formatted_timestamps

            logger.info(f"📤 Sending response with {len(results.get('trades_history', []))} trades")

            return jsonify({
                'success': True,
                'backtest_id': f"{strategy_name}_{int(datetime.now().timestamp())}",
                'parameters': request_json,
                'results': results,
                'metrics': metrics,
                'market_data': market_data_response,
            })

        except Exception as e:
            error_traceback = traceback.format_exc()
            logger.error(f"Error during backtest:\n{error_traceback}")
            return jsonify({
                'error': f'Error during backtest: {str(e)}',
                'traceback': error_traceback if app.config['DEBUG'] else None
            }), 500

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
        try:
            config_path = os.path.join(os.path.dirname(__file__), 'config.json')
            
            if not os.path.exists(config_path):
                # Return default symbols if config file doesn't exist
                return jsonify({
                    'symbols': ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'DOTUSDT', 'LINKUSDT'],
                })
            
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            return jsonify({
                'symbols': config.get('trading_pairs', ['BTCUSDT', 'ETHUSDT']),
            })
        except Exception as e:
            logger.error(f"Error reading symbols config: {e}")
            return jsonify({
                'symbols': ['BTCUSDT', 'ETHUSDT', 'ADAUSDT'],
            })
        
    @app.route('/api/config/timeframes')
    def get_timeframes():
        """Returns available timeframes"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), 'config.json')
            
            if not os.path.exists(config_path):
                # Return default timeframes if config file doesn't exist
                return jsonify({
                    'timeframes': ['1m', '5m', '15m', '1h', '4h', '1d'],
                })
            
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            return jsonify({
                'timeframes': config.get('timeframes', ['1h', '4h', '1d']),
            })
        except Exception as e:
            logger.error(f"Error reading timeframes config: {e}")
            return jsonify({
                'timeframes': ['1m', '5m', '15m', '1h', '4h', '1d'],
            })
        
    @app.route('/api/config/strategies')
    def get_strategies():
        """Returns the list of available strategies"""
        try:
            strategies = [
                {
                    'name': 'buy_and_hold',
                    'display_name': 'Buy & Hold',
                    'description': 'Buy at the beginning and hold until the end',
                    'class': 'BuyAndHoldStrategy',
                    'parameters': getattr(BuyAndHoldStrategy, 'parameters', {}),
                    'risk_parameters': getattr(BuyAndHoldStrategy, 'risk_parameters', {})
                },
                {
                    'name': 'rsi_strategy',
                    'display_name': 'RSI Strategy',
                    'description': 'Buy on oversold, sell on overbought',
                    'class': 'RSIStrategy',
                    'parameters': getattr(RSIStrategy, 'parameters', {}),
                    'risk_parameters': getattr(RSIStrategy, 'risk_parameters', {})
                },
                {
                    'name': 'DCA_strategy',
                    'display_name': 'Dollar Cost Averaging',
                    'description': 'Invest a fixed portion regularly',
                    'class': 'DCA_strategy',
                    'parameters': getattr(DCA_strategy, 'parameters', {}),
                    'risk_parameters': getattr(DCA_strategy, 'risk_parameters', {})
                }
            ]
            
            return jsonify({
                'strategies': strategies,
                'total': len(strategies)
            })
        except Exception as e:
            logger.error(f"Error getting strategies: {e}")
            return jsonify({
                'strategies': [],
                'total': 0,
                'error': 'Failed to load strategies'
            })
    
    @app.errorhandler(404)
    def not_found(error):
        """404 error handler"""
        return jsonify({'error': 'Endpoint not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """500 error handler"""
        logger.error(f"Internal server error: {error}")
        return jsonify({'error': 'Internal server error'}), 500
    
    return app