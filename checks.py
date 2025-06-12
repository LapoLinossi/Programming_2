# Enhanced checks.py with short selling validation
import logging
from ib_insync import IB, Stock

class TradingChecks:
    def __init__(self, api_client):
        """Initialize with IB API client"""
        self.api_client = api_client
        self.logger = logging.getLogger(__name__)

    def check_buying_power(self, order_value):
        """Check if there's enough buying power for the order"""
        buying_power = 100000  # Simulated value
        if buying_power >= order_value:
            self.logger.info(f"Sufficient buying power: {buying_power} >= {order_value}")
            return True
        else:
            self.logger.warning(f"Insufficient buying power: {buying_power} < {order_value}")
            return False

    def check_shortable(self, symbol):
        """
        Check if the stock is shortable using Interactive Brokers data
        """
        try:
            ib = IB()
            ib.connect('127.0.0.1', 4002, clientId=2)  # Use different client ID
            
            contract = Stock(symbol, 'SMART', 'USD')
            ib.qualifyContracts(contract)
            
            # Request market data to get shortable shares info
            ticker = ib.reqMktData(contract, '', False, False)
            ib.sleep(2)  # Wait for data
            
            # Check if shortable shares are available
            shortable = hasattr(ticker, 'shortableShares') and ticker.shortableShares > 0
            
            ib.disconnect()
            self.logger.info(f"Shortable check for {symbol}: {shortable}")
            return shortable
            
        except Exception as e:
            self.logger.error(f"Error checking shortable status for {symbol}: {e}")
            return False

    def get_current_position(self, symbol):
        """Get current position for a symbol"""
        position = 0
        if hasattr(self.api_client, 'position_data') and symbol in self.api_client.position_data:
            position = self.api_client.position_data[symbol]['position']
        self.logger.info(f"Current position for {symbol}: {position}")
        return position

    def validate_short_order(self, symbol, quantity):
        """Validate if a short order can be placed"""
        # Check if stock is shortable
        if not self.check_shortable(symbol):
            self.logger.warning(f"Stock {symbol} is not shortable")
            return False
        
        # Check margin requirements (simplified)
        current_price = 100  # This should come from real-time data
        margin_required = current_price * quantity * 1.5  # 150% margin requirement
        
        if not self.check_buying_power(margin_required):
            self.logger.warning(f"Insufficient margin for short sale of {symbol}")
            return False
            
        return True
