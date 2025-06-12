# fetch_data.py - 
import pandas as pd
import logging
from datetime import datetime, timedelta
import time

class DataFetcher:
    def __init__(self, api_client):
        """Initialize with IB API client"""
        self.api_client = api_client
        self.logger = logging.getLogger(__name__)
    
    def get_historical_data(self, symbol, duration="60 D", bar_size="1 day", timeout=30):
        """
        Fetch historical data for a symbol
        
        Parameters:
        -----------
        symbol : str
            Stock symbol
        duration : str
            Duration string (e.g., "60 D" for 60 days)
        bar_size : str
            Bar size setting (e.g., "1 day")
        timeout : int
            Timeout in seconds to wait for data
            
        Returns:
        --------
        pandas.DataFrame or None
        """
        self.logger.info(f"Fetching historical data for {symbol}")
        
        try:
            # Check if API client is connected
            if not self.api_client.isConnected():
                self.logger.error(f"API client not connected, cannot fetch data for {symbol}")
                return None
                
            # Reset historical data in the API client
            self.api_client.historical_data = []
            self.api_client.historical_data_end = False
            
            # Create contract for the symbol
            contract = self._create_contract(symbol)
            
            # Request historical data
            req_id = 1  # Request ID
            
            # Format end datetime in the correct format expected by IB API
            # Use Eastern time as IB's default reference
            end_datetime = datetime.now().strftime("%Y%m%d-%H:%M:%S") 
            
            self.logger.debug(f"Requesting historical data for {symbol} with end time {end_datetime}")
            
            self.api_client.reqHistoricalData(
                reqId=req_id,
                contract=contract,
                endDateTime=end_datetime,
                durationStr=duration,
                barSizeSetting=bar_size,
                whatToShow='TRADES',
                useRTH=1,
                formatDate=1,
                keepUpToDate=False,
                chartOptions=[]
            )
            
            # Wait for data to be received with timeout
            start_time = time.time()
            while not self.api_client.historical_data_end and (time.time() - start_time) < timeout:
                time.sleep(0.1)  # Small sleep to prevent CPU overload
            
            # Check if we hit the timeout
            if not self.api_client.historical_data_end:
                self.logger.warning(f"Historical data request for {symbol} timed out after {timeout} seconds")
            
            # Process the data if we received any
            if len(self.api_client.historical_data) > 0:
                self.logger.info(f"Received {len(self.api_client.historical_data)} data points for {symbol}")
                
                # Convert to DataFrame
                df = pd.DataFrame(self.api_client.historical_data)
                
                # Set the datetime as index
                if 'datetime' in df.columns:
                    df.set_index('datetime', inplace=True)
                    # Sort by datetime to ensure chronological order
                    df.sort_index(inplace=True)
                    
                    self.logger.info(f"Successfully processed historical data for {symbol}: {len(df)} bars")
                    return df
                else:
                    self.logger.error(f"No datetime column in data for {symbol}")
                    return None
            else:
                self.logger.error(f"No historical data received for {symbol}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error fetching historical data for {symbol}: {str(e)}", exc_info=True)
            return None
    
    def _create_contract(self, symbol, sec_type="STK", exchange="SMART", currency="USD"):
        """Create a contract object for IB API"""
        from ibapi.contract import Contract
        contract = Contract()
        contract.symbol = symbol
        contract.secType = sec_type
        contract.exchange = exchange
        contract.currency = currency
        return contract
        
    def get_real_time_price(self, symbol):
        """
        Get real-time price for a symbol
        
        Parameters:
        -----------
        symbol : str
            Stock symbol
            
        Returns:
        --------
        float or None
            Current price if available, None otherwise
        """
        self.logger.info(f"Fetching real-time price for {symbol}")
        
        try:
            # This is a placeholder - in a real implementation
            # you would use reqMktData to get real-time price
            # For now we'll simulate by getting recent historical data
            
            # Get last 1 minute data
            df = self.get_historical_data(
                symbol=symbol,
                duration="1 D",  # 1 day
                bar_size="1 min",  # 1 minute bars
                timeout=10        # Shorter timeout for real-time data
            )
            
            if df is not None and not df.empty:
                # Return the last close price
                price = df['close'].iloc[-1]
                self.logger.info(f"Real-time price for {symbol}: {price}")
                return price
            else:
                self.logger.warning(f"Could not fetch real-time price for {symbol}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error fetching real-time price for {symbol}: {str(e)}")
            return None