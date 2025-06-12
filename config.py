
"Purpose: Configuration settings for the trading bot"
# config.py
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
IB_HOST = "127.0.0.1"
IB_PORT = 4002 # Paper trading port (use 7496 for live)
IB_CLIENT_ID = 1

# Symbols to trade - Blue Chips
SYMBOLS = ['NET']  # Apple, Microsoft, Visa, Johnson & Johnson

# Strategy Parameters
MA_PERIOD = 50  # 50-day SMA as mentioned in the plan
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30

# Position Sizing
DEFAULT_POSITION_SIZE = 10# Shares per trade

# Risk Management
USE_STOP_LOSS = True
STOP_LOSS_PCT = 0.05  # 5% below entry price
USE_TAKE_PROFIT = True
TAKE_PROFIT_PCT = 0.10  # 10% above entry price

# Execution Settings
ORDER_TYPE = "AZN"  # Limit order
LIMIT_PRICE_OFFSET = 0.02  # 2% offset for limit price

# Logging and Reporting
LOG_LEVEL = "INFO"
SAVE_CHARTS = True
CHART_DIR = "charts"
REPORT_DIR= "reports"