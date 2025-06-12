# indicators.py
import pandas as pd
import numpy as np

def calculate_sma(data, period=50):
    """
    Calculate Simple Moving Average
    
    Parameters:
    -----------
    data : pandas.DataFrame or Series
        Price data with 'close' column
    period : int
        Moving average period
        
    Returns:
    --------
    pandas.Series
        Moving average values
    """
    if isinstance(data, pd.DataFrame):
        if 'close' in data.columns:
            return data['close'].rolling(window=period).mean()
        else:
            raise ValueError("DataFrame must contain 'close' column")
    else:
        return data.rolling(window=period).mean()

def calculate_rsi(data, period=14):
    """
    Calculate Relative Strength Index
    
    Parameters:
    -----------
    data : pandas.DataFrame or Series
        Price data with 'close' column
    period : int
        RSI calculation period
        
    Returns:
    --------
    pandas.Series
        RSI values
    """
    if isinstance(data, pd.DataFrame):
        if 'close' in data.columns:
            series = data['close']
        else:
            raise ValueError("DataFrame must contain 'close' column")
    else:
        series = data
    
    # Calculate price changes
    delta = series.diff()
    
    # Separate gains and losses
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    # Calculate average gain and loss
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    
    # Calculate RS and RSI
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi