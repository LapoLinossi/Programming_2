import time
import logging
import threading
import pandas as pd
import os
from datetime import datetime, timedelta

# Import IB API
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import Order

# Import custom modules
from config import *
from fetch_data import DataFetcher
from signals import SignalGenerator
from order import OrderManager
from checks import TradingChecks
from portfolio import PortfolioManager
from logger import setup_logger
from reporting import Reporter
from llm_reporter import LLMReporter

from ib_insync import *

# Create custom IB API client class
class IBApiClient(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.nextValidOrderId = None
        self.historical_data = []
        self.historical_data_end = False
        self.position_data = {}
        self.order_status = {}
        
    def nextValidId(self, orderId):
        super().nextValidId(orderId)
        self.nextValidOrderId = orderId
        logging.info(f"Next Valid Order ID: {orderId}")
    
    def historicalData(self, reqId, bar):
        """Handle historical data bars"""
        from datetime import datetime
        
        try:
            dt = datetime.strptime(bar.date, "%Y%m%d %H:%M:%S")
        except ValueError:
            dt = datetime.strptime(bar.date, "%Y%m%d")
            
        self.historical_data.append({
            'datetime': dt,
            'open': bar.open,
            'high': bar.high,
            'low': bar.low,
            'close': bar.close,
            'volume': bar.volume
        })
        logging.debug(f"Received historical bar for {dt}: {bar.close}")
    
    def historicalDataEnd(self, reqId, start, end):
        """Signal that historical data request is complete"""
        super().historicalDataEnd(reqId, start, end)
        self.historical_data_end = True
        logging.info(f"Historical data download completed from {start} to {end}")
    
    def position(self, account, contract, position, avgCost):
        """Handle position updates"""
        super().position(account, contract, position, avgCost)
        symbol = contract.symbol
        self.position_data[symbol] = {
            'position': position,
            'avgCost': avgCost
        }
        logging.info(f"Current position for {symbol}: {position} shares at avg cost {avgCost}")
    
    def orderStatus(self, orderId, status, filled, remaining, avgFillPrice, 
                    permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):
        """Handle order status updates"""
        super().orderStatus(orderId, status, filled, remaining, avgFillPrice,
                           permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice)
        self.order_status[orderId] = {
            'status': status,
            'filled': filled,
            'remaining': remaining,
            'avgFillPrice': avgFillPrice
        }
        logging.info(f"Order {orderId} status: {status} - Filled: {filled}, Remaining: {remaining}")
    
    def error(self, reqId, errorCode, errorString):
        """Handle API error messages"""
        super().error(reqId, errorCode, errorString)
        if errorCode in [2104, 2106, 2158]:
            logging.info(f"IB API Info: {errorCode} - {errorString}")
        else:
            logging.error(f"IB API Error {reqId} {errorCode} {errorString}")

class TradingBot:
    def __init__(self):
        # Set up logging
        self.logger = setup_logger(log_level=LOG_LEVEL, log_to_file=True)
        
        # Initialize LLMReporter with OpenAI API key
        try:
            api_key = os.environ.get("OPENAI_API_KEY")
            self.llm_reporter = LLMReporter(api_key="AIzaSyCiMnRA5OYonL6a7x7xmX-RWr7OaBWZm6k")
            if self.llm_reporter.available:
                self.logger.info("LLM Reporter initialized successfully with OpenAI GPT-3.5-turbo")
            else:
                self.logger.warning("LLM Reporter initialized but not available, will use basic summaries")
        except Exception as e:
            self.logger.error(f"Failed to initialize LLMReporter: {e}")
            self.llm_reporter = None
        
        # Create IB API client
        self.api_client = IBApiClient()
        self.connect_to_ib()
        
        # Initialize components
        self.data_fetcher = DataFetcher(self.api_client)
        self.signal_generator = SignalGenerator(
            ma_period=MA_PERIOD,
            rsi_period=RSI_PERIOD,
            rsi_overbought=RSI_OVERBOUGHT,
            rsi_oversold=RSI_OVERSOLD)
        self.order_manager = OrderManager(self.api_client, config_module=globals())
        self.trading_checks = TradingChecks(self.api_client)
        self.portfolio = PortfolioManager()

        # Initialize Reporter with proper LLM reporter
        self.reporter = Reporter(chart_dir=CHART_DIR, report_dir=REPORT_DIR, llm_reporter=self.llm_reporter)
        self.logger.info(f"Reporter initialized with chart directory: {CHART_DIR}")
        
        # Set up symbols and status
        self.symbols = SYMBOLS
        self.active = False
        self.keep_running = True
    
    def connect_to_ib(self):
        """Connect to Interactive Brokers TWS/Gateway"""
        try:
            self.api_client.connect(IB_HOST, IB_PORT, IB_CLIENT_ID)
            self.api_thread = threading.Thread(target=self.run_loop, daemon=True)
            self.api_thread.start()
            wait_time = 0
            timeout = 15
            while self.api_client.nextValidOrderId is None and wait_time < timeout:
                time.sleep(0.1)
                wait_time += 0.1
            if self.api_client.nextValidOrderId is None:
                self.logger.error("Failed to connect to Interactive Brokers")
                return False
            self.logger.info(f"Connected to Interactive Brokers API (Port: {IB_PORT})")
            return True
        except Exception as e:
            self.logger.error(f"Error connecting to Interactive Brokers: {e}")
            return False
    
    def run_loop(self):
        """Run the socket loop"""
        try:
            self.api_client.run()
        except Exception as e:
            self.logger.error(f"API thread error: {e}")
    
    def run_strategy(self, symbol):
        """Run the strategy for a single symbol with short selling support"""
        self.logger.info(f"Running strategy for {symbol}")
        
        # Fetch historical data
        data = self.data_fetcher.get_historical_data(symbol, duration="60 D", bar_size="1 day")
        
        if data is None or data.empty:
            self.logger.warning(f"No data available for {symbol}")
            return
        
        # Generate signals (including short signals)
        signals_df = self.signal_generator.generate_signals(data)
        
        if signals_df is None:
            self.logger.warning(f"Could not generate signals for {symbol}")
            return
        
        # Generate and save chart for analysis
        if SAVE_CHARTS:
            chart_signals = {
                'buy': signals_df[signals_df['buy_signal'] == True].index.tolist(),
                'sell': signals_df[signals_df['sell_signal'] == True].index.tolist(),
                'short': signals_df[signals_df['short_signal'] == True].index.tolist(),
                'cover': signals_df[signals_df['cover_signal'] == True].index.tolist()
            }
            self.logger.info(f"Generating chart for {symbol}")
            self.reporter.create_chart(signals_df, symbol, chart_signals, save=True)
        
        # Check for signals in the latest data point
        latest = signals_df.iloc[-1]
        current_price = latest['close']
        
        self.logger.info(f"Signal analysis for {symbol}: Price {current_price}, SMA {latest.get('sma', 'N/A')}, RSI {latest.get('rsi', 'N/A')}")
        self.logger.info(f"Long signals - Buy: {latest.get('buy_signal', False)}, Sell: {latest.get('sell_signal', False)}")
        self.logger.info(f"Short signals - Short: {latest.get('short_signal', False)}, Cover: {latest.get('cover_signal', False)}")
        
        # Get current position
        position = self.trading_checks.get_current_position(symbol)
        is_short = self.portfolio.is_short_position(symbol)
        
        # Prepare market data for LLM reporting
        market_data = {
            'close': current_price,
            'sma': latest.get('sma', None),
            'rsi': latest.get('rsi', None),
            'price_above_sma': latest.get('price_above_sma', False)
        }
        
        # LONG POSITION LOGIC
        if position >= 0:  # No position or long position
            # Execute buy signal (open long position)
            if position == 0 and latest.get('buy_signal', False):
                self.logger.info(f"BUY SIGNAL TRIGGERED for {symbol}")
                order_value = current_price * DEFAULT_POSITION_SIZE
                if self.trading_checks.check_buying_power(order_value):
                    order_id = self.order_manager.place_limit_order(
                        symbol=symbol,
                        action="BUY",
                        quantity=DEFAULT_POSITION_SIZE,
                        current_price=current_price
                    )
                    
                    if order_id:
                        self.logger.info(f"BUY ORDER PLACED for {symbol}: Order ID {order_id}")
                        self.portfolio.update_position(
                            symbol=symbol,
                            quantity=DEFAULT_POSITION_SIZE,
                            price=current_price,
                            action="BUY",
                            order_id=order_id
                        )
                        
                        reason = self._build_trade_reason(latest, "BUY")
                        self._generate_trade_summary("BUY", symbol, DEFAULT_POSITION_SIZE, current_price, reason, market_data)
                        self._save_trade_chart(signals_df, symbol, order_id, "BUY")
                else:
                    self.logger.warning(f"Insufficient buying power for {symbol}")
            
            # Execute sell signal (close long position)
            elif position > 0 and latest.get('sell_signal', False):
                self.logger.info(f"SELL SIGNAL TRIGGERED for {symbol}")
                order_id = self.order_manager.place_limit_order(
                    symbol=symbol,
                    action="SELL",
                    quantity=position,
                    current_price=current_price
                )
                if order_id:
                    self.logger.info(f"SELL ORDER PLACED for {symbol}: Order ID {order_id}")
                    self.portfolio.update_position(
                        symbol=symbol,
                        quantity=position,
                        price=current_price,
                        action="SELL",
                        order_id=order_id
                    )
                    
                    reason = self._build_trade_reason(latest, "SELL")
                    self._generate_trade_summary("SELL", symbol, position, current_price, reason, market_data)
                    self._save_trade_chart(signals_df, symbol, order_id, "SELL")
            
            # Execute short signal (SELL SHORT when no position - this creates a negative position)
            elif position == 0 and latest.get('short_signal', False):
                self.logger.info(f"SHORT SELL SIGNAL TRIGGERED for {symbol} - Opening short position")
                if self.trading_checks.validate_short_order(symbol, DEFAULT_POSITION_SIZE):
                    order_id = self.order_manager.place_limit_order(
                        symbol=symbol,
                        action="SHORT",  # This is a "SELL SHORT" - selling shares you don't own
                        quantity=DEFAULT_POSITION_SIZE,
                        current_price=current_price
                    )
                    
                    if order_id:
                        self.logger.info(f"SHORT SELL ORDER PLACED for {symbol}: Order ID {order_id} - Now SHORT {DEFAULT_POSITION_SIZE} shares")
                        self.portfolio.update_position(
                            symbol=symbol,
                            quantity=DEFAULT_POSITION_SIZE,
                            price=current_price,
                            action="SHORT",
                            order_id=order_id
                        )
                        
                        reason = self._build_trade_reason(latest, "SHORT")
                        self._generate_trade_summary("SHORT", symbol, DEFAULT_POSITION_SIZE, current_price, reason, market_data)
                        self._save_trade_chart(signals_df, symbol, order_id, "SHORT")
                else:
                    self.logger.warning(f"Cannot short {symbol}: validation failed")
        
        # SHORT POSITION LOGIC
        elif position < 0:  # Short position
            # Execute cover signal (close short position)
            if latest.get('cover_signal', False):
                self.logger.info(f"COVER SIGNAL TRIGGERED for {symbol}")
                cover_quantity = abs(position)  # Convert negative position to positive quantity
                order_id = self.order_manager.place_limit_order(
                    symbol=symbol,
                    action="COVER",
                    quantity=cover_quantity,
                    current_price=current_price
                )
                
                if order_id:
                    self.logger.info(f"COVER ORDER PLACED for {symbol}: Order ID {order_id}")
                    self.portfolio.update_position(
                        symbol=symbol,
                        quantity=cover_quantity,
                        price=current_price,
                        action="COVER",
                        order_id=order_id
                    )
                    
                    reason = self._build_trade_reason(latest, "COVER")
                    self._generate_trade_summary("COVER", symbol, cover_quantity, current_price, reason, market_data)
                    self._save_trade_chart(signals_df, symbol, order_id, "COVER")
        
        # Log when no signals are present
        if not any([latest.get('buy_signal', False), latest.get('sell_signal', False), 
                   latest.get('short_signal', False), latest.get('cover_signal', False)]):
            self.logger.info(f"No trading signals for {symbol} at this time")
    
    def _build_trade_reason(self, latest, action):
        """Build a descriptive reason for the trade"""
        reason = ""
        if action in ["BUY", "COVER"]:
            if latest.get('price_cross_above_sma', False):
                reason = "Price crossed above SMA"
            if latest.get('rsi_below_threshold', False):
                rsi_val = latest.get('rsi', 0)
                reason += f" with RSI at {rsi_val:.1f} (below {RSI_OVERSOLD})"
        elif action in ["SELL", "SHORT"]:
            if latest.get('price_cross_below_sma', False):
                reason = "Price crossed below SMA"
            if latest.get('rsi_above_threshold', False):
                rsi_val = latest.get('rsi', 0)
                reason += f" with RSI at {rsi_val:.1f} (above {RSI_OVERBOUGHT})"
        
        return reason.strip()
    
    def _generate_trade_summary(self, action, symbol, quantity, price, reason, market_data):
        """Generate and log trade summary"""
        trade_data = {
            'action': action,
            'symbol': symbol,
            'qty': quantity,
            'price': price,
            'reason': reason
        }
        
        try:
            summary = self.reporter.generate_trade_summary(trade_data, market_data)
            self.logger.info(f"Trade summary: {summary}")
        except Exception as e:
            self.logger.error(f"Error generating trade summary: {e}")
    
    def _save_trade_chart(self, signals_df, symbol, order_id, action):
        """Save trade chart if enabled"""
        if SAVE_CHARTS:
            self.logger.info(f"Generating trade chart for {symbol} {action} order")
            order_signals = {'buy': [], 'sell': [], 'short': [], 'cover': []}
            order_signals[action.lower()] = [signals_df.index[-1]]
            self.reporter.create_chart(signals_df, f"{symbol}_{action}_{order_id}", order_signals, save=True)
    
    def generate_portfolio_report(self):
        """Generate a report of current portfolio positions and performance"""
        self.logger.info("Generating portfolio report")
        try:
            position_summary = self.portfolio.get_position_summary()
            
            if position_summary.empty:
                self.logger.info("No positions currently in portfolio")
                return
            
            self.logger.info("Current Portfolio Positions:")
            for symbol, position in position_summary.iterrows():
                current_price = self.data_fetcher.get_real_time_price(symbol)
                if current_price:
                    if position['qty'] > 0:  # Long position
                        pnl = (current_price - position['entry_price']) * position['qty']
                        pnl_pct = ((current_price / position['entry_price']) - 1) * 100
                        pos_type = "LONG"
                    else:  # Short position
                        pnl = (position['entry_price'] - current_price) * abs(position['qty'])
                        pnl_pct = ((position['entry_price'] / current_price) - 1) * 100
                        pos_type = "SHORT"
                    
                    self.logger.info(f"{symbol} ({pos_type}): {abs(position['qty'])} shares @ ${position['entry_price']:.2f} | Current: ${current_price:.2f} | P&L: ${pnl:.2f} ({pnl_pct:.2f}%)")
                else:
                    pos_type = "LONG" if position['qty'] > 0 else "SHORT"
                    self.logger.info(f"{symbol} ({pos_type}): {abs(position['qty'])} shares @ ${position['entry_price']:.2f}")
            
        except Exception as e:
            self.logger.error(f"Error generating portfolio report: {e}")
    
    def start_trading(self):
        """Start the trading bot"""
        if not self.api_client.nextValidOrderId:
            self.logger.error("Not connected to Interactive Brokers")
            return False
        
        self.logger.info("Starting trading bot with short selling capability")
        self.active = True
        
        try:
            self.api_client.reqPositions()
            while self.active and self.keep_running:
                for symbol in self.symbols:
                    try:
                        if self.reconnect_if_needed():
                            self.run_strategy(symbol)
                        time.sleep(1)
                    except Exception as e:
                        self.logger.error(f"Error running strategy for {symbol}: {e}")
                
                self.generate_portfolio_report()
                self.logger.info("Completed signal check for all symbols, waiting for next cycle...")
                time.sleep(1000)
                
        except KeyboardInterrupt:
            self.logger.info("Trading bot stopped by user")
        except Exception as e:
            self.logger.error(f"Error in trading bot: {e}")
        finally:
            self.stop_trading()
        
        return True
    
    def stop_trading(self):
        """Stop the trading bot"""
        self.active = False
        self.api_client.disconnect()
        self.logger.info("Trading bot stopped")
    
    def reconnect_if_needed(self):
        """Check connection and reconnect if needed"""
        if not self.api_client.isConnected():
            self.logger.info("Connection lost, attempting to reconnect...")
            return self.connect_to_ib()
        return True

if __name__ == "__main__":
    bot = TradingBot()
    bot.start_trading()