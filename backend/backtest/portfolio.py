"""
Portfolio simulation for multi-pair backtesting with advanced order types
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class OrderType(Enum):
    BUY_MARKET = "buy_market"
    SELL_MARKET = "sell_market"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    TRAILING_STOP = "trailing_stop"
    OCO = "oco"  # One-Cancels-Other

@dataclass
class Order:
    """Class representing a trading order"""
    id: str
    symbol: str
    order_type: OrderType
    quantity: float
    timestamp_created: pd.Timestamp
    params: Dict
    is_active: bool = True
    
    # For stop loss / take profit
    trigger_price: Optional[float] = None
    
    # For trailing stop
    trail_amount: Optional[float] = None
    trail_percent: Optional[float] = None
    highest_price: Optional[float] = None
    
    # For OCO orders
    linked_order_id: Optional[str] = None
    
    # For time-based orders
    expiry_time: Optional[pd.Timestamp] = None

class Portfolio:
    """Class to simulate a multi-pair trading portfolio with advanced order types"""
    
    def __init__(self, initial_capital: float = 10000, commission_rate: float = 0.001, pairs: List[str] = []):
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        
        # Portfolio state
        self.symbols = pairs
        self.cash = initial_capital
        self.positions: Dict[str, float] = {}  # {symbol: quantity}
        self.open_orders: List[Order] = []  # List of open orders
        self._order_counter = 0

        # Benchmark
        self.benchmark_positions: Dict[str, float] = {}  # {symbol: quantity}

        # History
        self.trades: List[Dict] = []
        self.graph_data: Dict[str, List] = {
            'timestamp': [],
            'total_value': [],
            'benchmark': []
        }
        self.total_commission = 0.0
        self.market_data: Optional[Dict[str, pd.DataFrame]] = None
        self.current_prices: Dict[str, float] = {}
        
        logger.info(f"Portfolio initialized: {initial_capital} USDT")
        
    def set_market_data(self, market_data: Dict[str, pd.DataFrame]):
        """Set market data for the portfolio"""
        self.market_data = market_data
        self.current_prices = {symbol: data['close'].iloc[-1] for symbol, data in market_data.items()}
        
        # Initialize benchmark positions (equal weight buy and hold)
        symbols_count = len(self.symbols)
        if symbols_count > 0:
            capital_per_symbol = self.initial_capital / symbols_count
            self.benchmark_positions = {
                symbol: capital_per_symbol / data['close'].iloc[0] 
                for symbol, data in market_data.items()
            }

        logger.info(f"Market data set for {len(market_data)} symbols")

    def _generate_order_id(self) -> str:
        """Generate unique order ID"""
        self._order_counter += 1
        return f"order_{self._order_counter}"

    def _get_current_price(self, symbol: str, timestamp: pd.Timestamp) -> float:
        """Get current price for a symbol at timestamp"""
        if self.market_data and symbol in self.market_data:
            try:
                return self.market_data[symbol].loc[timestamp]['close']
            except KeyError:
                # If exact timestamp not found, get the nearest available price
                available_times = self.market_data[symbol].index
                nearest_time = available_times[available_times <= timestamp][-1] if len(available_times[available_times <= timestamp]) > 0 else available_times[0]
                return self.market_data[symbol].loc[nearest_time]['close']
        return 0.0

    def _get_total_usd_value(self, timestamp: pd.Timestamp) -> float:
        """Return the total USD value of the portfolio"""
        total_value = self.cash
        for symbol, quantity in self.positions.items():
            if quantity > 0:
                price = self._get_current_price(symbol, timestamp)
                total_value += quantity * price
        return total_value
    
    def _get_benchmark_value(self, timestamp: pd.Timestamp) -> float:
        """Return the total benchmark value"""
        total_value = 0.0
        for symbol, quantity in self.benchmark_positions.items():
            price = self._get_current_price(symbol, timestamp)
            total_value += quantity * price
        return total_value

    def execute_trade(self, trade: Dict) -> Dict:
        """Execute a trade on the portfolio"""
        trade_result = trade.copy()
        trade_result['executed'] = False
        
        if trade['type'] == "buy":
            trade_result = self._execute_buy_order(trade)
        elif trade['type'] == "sell":
            trade_result = self._execute_sell_order(trade)

        if trade_result['executed']:
            self.trades.append(trade_result)
            # Create stop loss / take profit orders if specified
            self._create_conditional_orders(trade_result)

        return trade_result

    def _execute_buy_order(self, trade: Dict) -> Dict:
        """Execute a market buy order"""
        params = trade['params']
        symbol = trade['symbol']
        timestamp = trade['timestamp']
        
        # Calculate USD value to spend
        if 'portion' in params:
            usd_value = params['portion'] * self.cash
        elif 'usdc_value' in params:
            usd_value = params['usdc_value']
        else:
            return trade
        
        # Check if we have enough cash
        total_cost = usd_value * (1 + self.commission_rate)
        if self.cash < total_cost or usd_value <= 5:
            return trade
        
        price = self._get_current_price(symbol, timestamp)
        if price <= 0:
            return trade
            
        quantity = usd_value / price
        commission = usd_value * self.commission_rate

        # Update portfolio
        self.cash -= total_cost
        if symbol not in self.positions:
            self.positions[symbol] = 0
        self.positions[symbol] += quantity
        self.total_commission += commission

        return {
            'timestamp': timestamp,
            'symbol': symbol,
            'type': 'buy',
            'price': price,
            'quantity': quantity,
            'usd_value': usd_value,
            'commission': commission,
            'executed': True,
            'params': params
        }

    def _execute_sell_order(self, trade: Dict) -> Dict:
        """Execute a market sell order"""
        params = trade['params']
        symbol = trade['symbol']
        timestamp = trade['timestamp']
        
        if symbol not in self.positions:
            self.positions[symbol] = 0

        quantity_to_sell = self.positions[symbol] * params.get('portion', 1.0)
        
        if self.positions[symbol] < quantity_to_sell:
            return trade
            
        price = self._get_current_price(symbol, timestamp)
        if price <= 0:
            return trade
            
        usd_value = quantity_to_sell * price
        if usd_value <= 5:
            return trade
            
        commission = usd_value * self.commission_rate
        net_proceeds = usd_value - commission

        # Update portfolio
        self.cash += net_proceeds
        self.positions[symbol] -= quantity_to_sell
        self.total_commission += commission

        return {
            'timestamp': timestamp,
            'symbol': symbol,
            'type': 'sell',
            'price': price,
            'quantity': quantity_to_sell,
            'usd_value': usd_value,
            'commission': commission,
            'executed': True,
            'params': params
        }

    def _create_conditional_orders(self, executed_trade: Dict):
        """Create stop loss, take profit, or other conditional orders after a trade"""
        if not executed_trade['executed'] or executed_trade['type'] != 'buy':
            return
            
        params = executed_trade['params']
        symbol = executed_trade['symbol']
        entry_price = executed_trade['price']
        quantity = executed_trade['quantity']
        
        # Create stop loss order
        if 'stop_loss' in params and params['stop_loss']:
            stop_price = entry_price * (1 - params['stop_loss'])
            
            stop_order = Order(
                id=self._generate_order_id(),
                symbol=symbol,
                order_type=OrderType.STOP_LOSS,
                quantity=quantity * params.get('portion_sell', 1.0),
                timestamp_created=executed_trade['timestamp'],
                trigger_price=stop_price,
                params={'portion': params.get('portion_sell', 1.0)},
                expiry_time=self._calculate_expiry_time(executed_trade['timestamp'], params)
            )
            self.open_orders.append(stop_order)
        
        # Create take profit order
        if 'take_profit' in params and params['take_profit']:
            tp_price = entry_price * (1 + params['take_profit'])
            
            tp_order = Order(
                id=self._generate_order_id(),
                symbol=symbol,
                order_type=OrderType.TAKE_PROFIT,
                quantity=quantity * params.get('portion_sell', 1.0),
                timestamp_created=executed_trade['timestamp'],
                trigger_price=tp_price,
                params={'portion': params.get('portion_sell', 1.0)},
                expiry_time=self._calculate_expiry_time(executed_trade['timestamp'], params)
            )
            self.open_orders.append(tp_order)
            
        # Create trailing stop order
        if 'trailing_stop' in params and params['trailing_stop']:
            trailing_order = Order(
                id=self._generate_order_id(),
                symbol=symbol,
                order_type=OrderType.TRAILING_STOP,
                quantity=quantity * params.get('portion_sell', 1.0),
                timestamp_created=executed_trade['timestamp'],
                trail_percent=params['trailing_stop'],
                highest_price=entry_price,
                params={'portion': params.get('portion_sell', 1.0)},
                expiry_time=self._calculate_expiry_time(executed_trade['timestamp'], params)
            )
            self.open_orders.append(trailing_order)

    def _calculate_expiry_time(self, timestamp: pd.Timestamp, params: Dict) -> Optional[pd.Timestamp]:
        """Calculate expiry time for an order based on duration parameter"""
        if 'duration' in params and params['duration']:
            return timestamp + pd.Timedelta(hours=params['duration'])
        return None

    def process_pending_orders(self, timestamp: pd.Timestamp):
        """Process all pending orders at the given timestamp"""
        orders_to_remove = []
        
        for order in self.open_orders:
            if not order.is_active:
                continue
                
            # Check if order has expired
            if order.expiry_time and timestamp >= order.expiry_time:
                order.is_active = False
                orders_to_remove.append(order)
                continue
                
            current_price = self._get_current_price(order.symbol, timestamp)
            if current_price <= 0:
                continue
            
            order_triggered = False
            
            if order.order_type == OrderType.STOP_LOSS:
                if current_price <= order.trigger_price:
                    order_triggered = True
                    
            elif order.order_type == OrderType.TAKE_PROFIT:
                if current_price >= order.trigger_price:
                    order_triggered = True
                    
            elif order.order_type == OrderType.TRAILING_STOP:
                # Update highest price
                if current_price > order.highest_price:
                    order.highest_price = current_price
                    # Update trigger price
                    order.trigger_price = order.highest_price * (1 - order.trail_percent)
                
                # Check if trailing stop triggered
                if current_price <= order.trigger_price:
                    order_triggered = True
            
            if order_triggered:
                # Execute the order as a market sell
                trade = {
                    'type': 'sell',
                    'symbol': order.symbol,
                    'timestamp': timestamp,
                    'params': order.params
                }
                
                result = self._execute_sell_order(trade)
                if result['executed']:
                    result['order_type'] = order.order_type.value
                    result['triggered_by'] = order.id
                    self.trades.append(result)
                    
                order.is_active = False
                orders_to_remove.append(order)
        
        # Remove inactive orders
        for order in orders_to_remove:
            if order in self.open_orders:
                self.open_orders.remove(order)

    def update_graph_data(self, timestamp: pd.Timestamp):
        """Update portfolio graph data and process pending orders"""
        # Process pending orders first
        self.process_pending_orders(timestamp)
        
        # Update graph data
        self.graph_data['timestamp'].append(timestamp)
        self.graph_data['total_value'].append(self._get_total_usd_value(timestamp))
        self.graph_data['benchmark'].append(self._get_benchmark_value(timestamp))

    def get_summary(self) -> Dict:
        """Return a summary of the portfolio"""
        if not self.market_data:
            return {}
            
        active_positions = {k: v for k, v in self.positions.items() if v > 0}
        
        position_values = {}
        total_position_value = 0
        for symbol, quantity in active_positions.items():
            if symbol in self.current_prices:
                value = quantity * self.current_prices[symbol]
                position_values[symbol] = value
                total_position_value += value
        
        # Calculate performance metrics
        final_timestamp = max(data.index[-1] for data in self.market_data.values())
        final_value = self._get_total_usd_value(final_timestamp)
        total_return = (final_value - self.initial_capital) / self.initial_capital
        
        benchmark_final = self._get_benchmark_value(final_timestamp)
        benchmark_return = (benchmark_final - self.initial_capital) / self.initial_capital
        
        return {
            'initial_capital': self.initial_capital,
            'final_value': final_value,
            'total_return': total_return,
            'benchmark_return': benchmark_return,
            'cash': self.cash,
            'total_position_value': total_position_value,
            'positions': active_positions,
            'position_values': position_values,
            'total_trades': len(self.trades),
            'total_commission': self.total_commission,
            'open_orders': len([o for o in self.open_orders if o.is_active])
        }