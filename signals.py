# Enhanced signals.py with short selling logic
import pandas as pd
import numpy as np
import logging
from indicators import calculate_sma, calculate_rsi

class SignalGenerator:
    def __init__(self, ma_period=50, rsi_period=14, rsi_overbought=70, rsi_oversold=30):
        """
        Initialize signal generator with short selling capability
        
        Parameters:
        -----------
        ma_period : int
            Moving average period
        rsi_period : int
            RSI calculation period
        rsi_overbought : int
            RSI level considered overbought
        rsi_oversold : int
            RSI level considered oversold
        """
        self.ma_period = ma_period
        self.rsi_period = rsi_period
        self.rsi_overbought = rsi_overbought
        self.rsi_oversold = rsi_oversold
        self.logger = logging.getLogger(__name__)
    
    def generate_signals(self, data):
        """
        Generate trading signals including short selling signals
        
        Parameters:
        -----------
        data : pandas.DataFrame
            Price data with OHLCV columns
            
        Returns:
        --------
        pandas.DataFrame
            Price data with indicators and signals added
        """
        if data is None or len(data) < self.ma_period:
            self.logger.warning("Insufficient data for signal generation")
            return None
        
        # Make a copy to avoid modifying the original
        df = data.copy()
        
        # Calculate indicators
        df['sma'] = calculate_sma(df, self.ma_period)
        df['rsi'] = calculate_rsi(df, self.rsi_period)
        
        # Price position relative to SMA
        df['price_above_sma'] = df['close'] > df['sma']
        df['price_cross_above_sma'] = (df['price_above_sma'] & ~df['price_above_sma'].shift(1).fillna(False))
        df['price_cross_below_sma'] = (~df['price_above_sma'] & df['price_above_sma'].shift(1).fillna(False))
        
        # RSI conditions
        df['rsi_below_threshold'] = df['rsi'] < self.rsi_oversold
        df['rsi_above_threshold'] = df['rsi'] >= self.rsi_overbought
        
        # Long signals (original logic)
        df['buy_signal'] = df['price_cross_above_sma'] & df['rsi_below_threshold']
        df['sell_signal'] = df['price_cross_below_sma'] | df['rsi_above_threshold']
        
        # Short signals (new logic)
        # Short when price crosses below SMA AND RSI is above overbought
        df['short_signal'] = df['price_cross_below_sma'] | df['rsi_above_threshold']
        
        # Cover short when price crosses above SMA OR RSI below oversold
        df['cover_signal'] = df['price_cross_above_sma'] | df['rsi_below_threshold']
        
        return df