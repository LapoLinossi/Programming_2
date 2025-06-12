# Enhanced order.py with short selling orders
import logging
from datetime import datetime

class OrderManager:
    def __init__(self, api_client, config_module):
        """Initialize with IB API client and configuration"""
        self.api_client = api_client
        self.config = config_module
        self.logger = logging.getLogger(__name__)
        self.logger.info("OrderManager initialized with short selling capability")

    def create_contract(self, symbol):
        """Create contract object for a symbol"""
        from ibapi.contract import Contract
        contract = Contract()
        contract.symbol = symbol
        contract.secType = "STK"
        contract.exchange = "SMART"
        contract.currency = "USD"
        return contract
    
    def create_limit_order(self, action, quantity, limit_price):
        """Create limit order object"""
        from ibapi.order import Order
        order = Order()
        order.action = action  # "BUY", "SELL", "SSHORT"
        order.orderType = "LMT"
        order.totalQuantity = int(quantity)
        order.lmtPrice = limit_price
        order.tif = "DAY"
        order.transmit = True
        order.eTradeOnly = False
        order.firmQuoteOnly = False
        
        return order
    
    def place_short_order(self, symbol, quantity, current_price=None):
        """
        Place a short sell order
        
        Parameters:
        -----------
        symbol : str
            Stock symbol
        quantity : int
            Number of shares to short
        current_price : float, optional
            Current price for calculating limit price
            
        Returns:
        --------
        int or None
            Order ID if successful, None otherwise
        """
        try:
            self.logger.info(f"Attempting to place SHORT order for {symbol}")
            
            if current_price is None:
                self.logger.error("Current price must be provided")
                return None
            
            quantity = int(quantity)
            
            # Calculate limit price for short sale (slightly below current price)
            offset = getattr(self.config, 'LIMIT_PRICE_OFFSET', 0.02)
            limit_price = round(current_price * (1 - offset), 2)
            self.logger.info(f"Short limit price: {limit_price} (current: {current_price})")
            
            # Create contract and order
            contract = self.create_contract(symbol)
            order = self.create_limit_order("SSHORT", quantity, limit_price)  # SSHORT for short sale
            
            # Check if we have a valid order ID
            if not hasattr(self.api_client, 'nextValidOrderId') or self.api_client.nextValidOrderId is None:
                self.logger.error("No valid order ID available")
                return None
            
            # Place order
            order_id = self.api_client.nextValidOrderId
            self.api_client.placeOrder(order_id, contract, order)
            self.api_client.nextValidOrderId += 1
            
            self.logger.info(f"SHORT order placed for {quantity} shares of {symbol} at limit {limit_price} (Order ID: {order_id})")
            
            return order_id
            
        except Exception as e:
            self.logger.error(f"Error placing SHORT order for {symbol}: {e}", exc_info=True)
            return None
    
    def place_cover_order(self, symbol, quantity, current_price=None):
        """
        Place a buy-to-cover order
        
        Parameters:
        -----------
        symbol : str
            Stock symbol
        quantity : int
            Number of shares to cover
        current_price : float, optional
            Current price for calculating limit price
            
        Returns:
        --------
        int or None
            Order ID if successful, None otherwise
        """
        try:
            self.logger.info(f"Attempting to place COVER order for {symbol}")
            
            if current_price is None:
                self.logger.error("Current price must be provided")
                return None
            
            quantity = int(quantity)
            
            # Calculate limit price for cover (slightly above current price)
            offset = getattr(self.config, 'LIMIT_PRICE_OFFSET', 0.02)
            limit_price = round(current_price * (1 + offset), 2)
            self.logger.info(f"Cover limit price: {limit_price} (current: {current_price})")
            
            # Create contract and order
            contract = self.create_contract(symbol)
            order = self.create_limit_order("BUY", quantity, limit_price)
            
            # Check if we have a valid order ID
            if not hasattr(self.api_client, 'nextValidOrderId') or self.api_client.nextValidOrderId is None:
                self.logger.error("No valid order ID available")
                return None
            
            # Place order
            order_id = self.api_client.nextValidOrderId
            self.api_client.placeOrder(order_id, contract, order)
            self.api_client.nextValidOrderId += 1
            
            self.logger.info(f"COVER order placed for {quantity} shares of {symbol} at limit {limit_price} (Order ID: {order_id})")
            
            return order_id
            
        except Exception as e:
            self.logger.error(f"Error placing COVER order for {symbol}: {e}", exc_info=True)
            return None

    def place_limit_order(self, symbol, action, quantity, current_price=None):
        """
        Place a limit order (enhanced to support short selling)
        """
        if action == "SHORT":
            return self.place_short_order(symbol, quantity, current_price)
        elif action == "COVER":
            return self.place_cover_order(symbol, quantity, current_price)
        else:
            # Original logic for BUY/SELL
            try:
                self.logger.info(f"Attempting to place {action} order for {symbol}")
                
                if current_price is None:
                    self.logger.error("Current price must be provided")
                    return None
                
                quantity = int(quantity)
                
                # Calculate limit price
                offset = getattr(self.config, 'LIMIT_PRICE_OFFSET', 0.02)
                if action == "BUY":
                    limit_price = round(current_price * (1 + offset), 2)
                else:  # SELL
                    limit_price = round(current_price * (1 - offset), 2)
                
                # Create contract and order
                contract = self.create_contract(symbol)
                order = self.create_limit_order(action, quantity, limit_price)
                
                if not hasattr(self.api_client, 'nextValidOrderId') or self.api_client.nextValidOrderId is None:
                    self.logger.error("No valid order ID available")
                    return None
                
                # Place order
                order_id = self.api_client.nextValidOrderId
                self.api_client.placeOrder(order_id, contract, order)
                self.api_client.nextValidOrderId += 1
                
                self.logger.info(f"{action} order placed for {quantity} shares of {symbol} at limit {limit_price} (Order ID: {order_id})")
                
                return order_id
                
            except Exception as e:
                self.logger.error(f"Error placing {action} order for {symbol}: {e}", exc_info=True)
                return None