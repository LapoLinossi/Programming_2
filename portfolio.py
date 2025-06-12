# Enhanced portfolio.py with short position tracking
import pandas as pd
import logging
from datetime import datetime

class PortfolioManager:
    def __init__(self):
        """Initialize portfolio manager with short position support"""
        self.positions = {}  # Key: symbol, Value: {qty, entry_price, entry_time, position_type}
        self.trades = []  # List of all trades executed
        self.logger = logging.getLogger(__name__)
        
    def update_position(self, symbol, quantity, price, action, order_id=None):
        """
        Update portfolio with a new trade including short positions
        
        Parameters:
        -----------
        symbol : str
            Stock symbol
        quantity : int
            Number of shares (positive for long, negative for short)
        price : float
            Execution price
        action : str
            "BUY", "SELL", "SHORT", or "COVER"
        order_id : int, optional
            Order ID
        """
        timestamp = datetime.now()
        
        # Update positions dictionary
        if action == "BUY":
            if symbol in self.positions:
                old_qty = self.positions[symbol]['qty']
                old_price = self.positions[symbol]['entry_price']
                new_qty = old_qty + quantity
                # Calculate new average price
                if new_qty != 0:
                    self.positions[symbol]['entry_price'] = (old_qty * old_price + quantity * price) / new_qty
                    self.positions[symbol]['qty'] = new_qty
                else:
                    del self.positions[symbol]
            else:
                self.positions[symbol] = {
                    'qty': quantity,
                    'entry_price': price,
                    'entry_time': timestamp,
                    'position_type': 'LONG'
                }
                
        elif action == "SELL":
            if symbol in self.positions:
                current_qty = self.positions[symbol]['qty']
                new_qty = current_qty - quantity
                
                if new_qty <= 0:
                    # Position closed
                    del self.positions[symbol]
                else:
                    # Partial position closed
                    self.positions[symbol]['qty'] = new_qty
            else:
                self.logger.warning(f"Attempting to sell {symbol} which is not in portfolio")
                
        elif action == "SHORT":
            if symbol in self.positions:
                old_qty = self.positions[symbol]['qty']
                old_price = self.positions[symbol]['entry_price']
                new_qty = old_qty - quantity  # Short reduces position (negative)
                
                if new_qty == 0:
                    del self.positions[symbol]
                else:
                    # Calculate new average price for short position
                    self.positions[symbol]['entry_price'] = (old_qty * old_price - quantity * price) / new_qty
                    self.positions[symbol]['qty'] = new_qty
                    self.positions[symbol]['position_type'] = 'SHORT' if new_qty < 0 else 'LONG'
            else:
                # New short position
                self.positions[symbol] = {
                    'qty': -quantity,  # Negative quantity for short
                    'entry_price': price,
                    'entry_time': timestamp,
                    'position_type': 'SHORT'
                }
                
        elif action == "COVER":
            if symbol in self.positions and self.positions[symbol]['qty'] < 0:
                current_qty = self.positions[symbol]['qty']
                new_qty = current_qty + quantity  # Cover adds back to negative position
                
                if new_qty >= 0:
                    # Short position closed or flipped to long
                    if new_qty == 0:
                        del self.positions[symbol]
                    else:
                        self.positions[symbol]['qty'] = new_qty
                        self.positions[symbol]['position_type'] = 'LONG'
                        self.positions[symbol]['entry_price'] = price
                else:
                    # Partial cover
                    self.positions[symbol]['qty'] = new_qty
            else:
                self.logger.warning(f"Attempting to cover {symbol} which is not shorted")
        
        # Record the trade
        trade = {
            'symbol': symbol,
            'action': action,
            'qty': quantity,
            'price': price,
            'timestamp': timestamp,
            'order_id': order_id
        }
        self.trades.append(trade)
        
        self.logger.info(f"Portfolio updated: {action} {quantity} shares of {symbol} at ${price}")
    
    def get_position(self, symbol):
        """Get current position for a symbol"""
        if symbol in self.positions:
            return self.positions[symbol]['qty']
        return 0
    
    def is_short_position(self, symbol):
        """Check if current position is short"""
        if symbol in self.positions:
            return self.positions[symbol]['qty'] < 0
        return False
    
    def get_position_summary(self):
        """Get summary of current positions"""
        return pd.DataFrame.from_dict(self.positions, orient='index')
    
    def get_trade_history(self):
        """Get history of all trades"""
        return pd.DataFrame(self.trades)