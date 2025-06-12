# troubleshoot.py 
import time
import logging
import pandas as pd
import sys
import os

# Import required modules
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("troubleshoot")

# Import configuration
from config import *

# Test 1: Check imports and environment
def test_imports():
    logger.info("===== Test 1: Testing imports =====")
    try:
        logger.info(f"Python version: {sys.version}")
        logger.info(f"pandas version: {pd.__version__}")
        logger.info(f"Current working directory: {os.getcwd()}")
        logger.info("EClient available: Yes")
        logger.info("EWrapper available: Yes")
        logger.info("Contract available: Yes")
        logger.info("Configuration loaded successfully")
        logger.info("All imports verified successfully")
        return True
    except Exception as e:
        logger.error(f"Import test failed: {e}")
        return False

# Test 2: Test IB API connection
class TestApiWrapper(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.connection_confirmed = False
        self.next_order_id = None
        self.error_received = False
        
    def nextValidId(self, orderId):
        super().nextValidId(orderId)
        self.next_order_id = orderId
        self.connection_confirmed = True
        logger.info(f"Connection confirmed! Next valid order ID: {orderId}")
    
    def error(self, reqId, errorCode, errorString):
        super().error(reqId, errorCode, errorString)
        
        # Some error codes are just informational
        if errorCode in [2104, 2106, 2158]:
            logger.info(f"IB API Info: {errorCode} - {errorString}")
        else:
            logger.error(f"IB API Error {reqId} {errorCode} {errorString}")
            self.error_received = True

def test_connection():
    logger.info("===== Test 2: Testing IB API connection =====")
    
    logger.info(f"Attempting to connect to IB API at {IB_HOST}:{IB_PORT} (Client ID: {IB_CLIENT_ID})")
    
    # Create API wrapper
    api = TestApiWrapper()
    
    # Connect to IB
    try:
        api.connect(IB_HOST, IB_PORT, IB_CLIENT_ID)
        logger.info("Connect method called successfully")
        
        # Wait for connection confirmation 
        timeout = 15
        start_time = time.time()
        
        while not api.connection_confirmed and time.time() - start_time < timeout:
            logger.info("Waiting for connection confirmation...")
            time.sleep(1)
            
        if api.connection_confirmed:
            logger.info("✅ Connection test successful!")
            # Disconnect
            api.disconnect()
            return True
        else:
            logger.error("❌ Connection test failed - timed out waiting for confirmation")
            return False
            
    except Exception as e:
        logger.error(f"❌ Connection test failed with exception: {e}")
        return False

# Test 3: Test data fetching
from fetch_data import DataFetcher
from indicators import calculate_sma, calculate_rsi
from signals import SignalGenerator

def test_signal_generation():
    logger.info("===== Test 3: Testing signal generation =====")
    
    # Create sample data
    logger.info("Creating sample price data...")
    index = pd.date_range(start='2023-01-01', periods=100, freq='D')
    
    # Create uptrend followed by downtrend
    close_prices = [100 + i*0.5 for i in range(80)] + [140 - i*0.5 for i in range(20)]
    
    # Create DataFrame
    df = pd.DataFrame({
        'close': close_prices,
        'open': [p - 0.5 for p in close_prices],
        'high': [p + 1 for p in close_prices],
        'low': [p - 1 for p in close_prices],
        'volume': [1000 + i*10 for i in range(100)]
    }, index=index)
    
    logger.info(f"Sample data created with {len(df)} records")
    
    # Create signal generator
    signal_gen = SignalGenerator(
        ma_period=MA_PERIOD,
        rsi_period=RSI_PERIOD,
        rsi_overbought=RSI_OVERBOUGHT
    )
    
    # Generate signals
    logger.info("Generating trading signals...")
    try:
        signals_df = signal_gen.generate_signals(df)
        
        if signals_df is not None:
            # Check for buy signals
            buy_signals = signals_df[signals_df['buy_signal'] == True]
            sell_signals = signals_df[signals_df['sell_signal'] == True]
            
            logger.info(f"Analysis complete. Found {len(buy_signals)} buy signals and {len(sell_signals)} sell signals")
            
            # Show some example signals
            if not buy_signals.empty:
                logger.info("Sample buy signal:")
                sample = buy_signals.iloc[0]
                logger.info(f"Date: {sample.name}, Close: {sample['close']}, SMA: {sample['sma']}, RSI: {sample['rsi']}")
            
            if not sell_signals.empty:
                logger.info("Sample sell signal:")
                sample = sell_signals.iloc[0]
                logger.info(f"Date: {sample.name}, Close: {sample['close']}, SMA: {sample['sma']}, RSI: {sample['rsi']}")
            
            return True
        else:
            logger.error("❌ Signal generation test failed - no signals generated")
            return False
    except Exception as e:
        logger.error(f"❌ Signal generation test failed with exception: {e}")
        return False

# Test 4: Test order creation
from order import OrderManager

def test_order_creation():
    logger.info("===== Test 4: Testing order creation =====")
    
    # Create a mock API client
    class MockApiClient:
        def __init__(self):
            self.nextValidOrderId = 100
            self.orders = []
            
        def placeOrder(self, orderId, contract, order):
            self.orders.append({
                'orderId': orderId,
                'symbol': contract.symbol,
                'action': order.action,
                'quantity': order.totalQuantity,
                'price': order.lmtPrice
            })
            logger.info(f"Order placed: {orderId} - {contract.symbol} {order.action} {order.totalQuantity} @ {order.lmtPrice}")
            
    # Create mock config
    class MockConfig:
        LIMIT_PRICE_OFFSET = 0.02
        USE_STOP_LOSS = True
        STOP_LOSS_PCT = 0.05
        
    # Create OrderManager with mock API client and config
    mock_api = MockApiClient()
    mock_config = MockConfig()
    
    order_manager = OrderManager(mock_api, mock_config)
    
    # Test creating and placing an order
    try:
        logger.info("Testing buy order creation...")
        symbol = "AAPL"
        buy_order_id = order_manager.place_limit_order(
            symbol=symbol,
            action="BUY",
            quantity=100,
            current_price=150.0
        )
        
        if buy_order_id is not None:
            logger.info(f"✅ Buy order created successfully with ID {buy_order_id}")
        else:
            logger.error("❌ Buy order creation failed")
            return False
            
        logger.info("Testing sell order creation...")
        sell_order_id = order_manager.place_limit_order(
            symbol=symbol,
            action="SELL",
            quantity=100,
            current_price=150.0
        )
        
        if sell_order_id is not None:
            logger.info(f"✅ Sell order created successfully with ID {sell_order_id}")
            return True
        else:
            logger.error("❌ Sell order creation failed")
            return False
    
    except Exception as e:
        logger.error(f"❌ Order creation test failed with exception: {e}")
        return False

# Run all tests
if __name__ == "__main__":
    logger.info("Starting troubleshooting tests...")
    
    # Run tests and collect results
    import_result = test_imports()
    connection_result = test_connection() if import_result else False
    signal_result = test_signal_generation() if import_result else False
    order_result = test_order_creation() if import_result else False
    
    # Print summary
    logger.info("\n===== TEST RESULTS =====")
    logger.info(f"Import test: {'✅ PASSED' if import_result else '❌ FAILED'}")
    logger.info(f"Connection test: {'✅ PASSED' if connection_result else '❌ FAILED'}")
    logger.info(f"Signal generation test: {'✅ PASSED' if signal_result else '❌ FAILED'}")
    logger.info(f"Order creation test: {'✅ PASSED' if order_result else '❌ FAILED'}")
    
    # Overall result
    if all([import_result, connection_result, signal_result, order_result]):
        logger.info("✅ All tests passed! Your trading bot components are working correctly.")
        logger.info("If you're still not seeing trades execute, check that:")
        logger.info("1. Your TWS/IB Gateway is running and accepting API connections")
        logger.info("2. You've allowed API connections in TWS settings")
        logger.info("3. Your symbols are correctly configured")
        logger.info("4. Current market conditions actually trigger your trading signals")
    else:
        logger.info("❌ Some tests failed. Review the logs above to identify and fix issues.")