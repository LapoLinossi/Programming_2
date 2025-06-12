# llm_reporter.py - Cloud Version with Gemini API
import logging
import os
from datetime import datetime
import google.generativeai as genai

class LLMReporter:
    """
    A class to generate individual trade summaries using Google's Gemini API.
    """

    def __init__(self, api_key="AIzaSyCiMnRA5OYonL6a7x7xmX-RWr7OaBWZm6k", max_tokens=200):
        """
        Initialize the LLMReporter with Gemini API.
        """
        self.logger = logging.getLogger(__name__)
        
        # Set API key
        api_key = api_key or os.environ.get("GEMINI_API_KEY")
        
        if not api_key:
            self.logger.error("No Gemini API key provided")
            self.available = False
            return
        
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel("gemini-1.5-flash")
            self.max_tokens = max_tokens
            self.available = True
            self.logger.info("Successfully initialized Gemini client")
        except Exception as e:
            self.logger.error(f"Failed to initialize Gemini client: {e}")
            self.available = False
            return
    
    def generate_trade_summary(self, trade_data, market_data=None):
        """
        Generate a detailed summary for a single trade using Gemini. This is a public method.
        """
        if not self.available:
            self.logger.warning("Gemini client not available, falling back to basic summary")
            return self._generate_basic_summary(trade_data)
        
        try:
            prompt = self._construct_trade_prompt(trade_data, market_data)
            self.logger.debug(f"Generated prompt: {prompt}")
            
            summary = self._run_cloud_llm(prompt)
            self.logger.debug(f"LLM raw result: '{summary}'")
            return summary

        except Exception as e:
            self.logger.error(f"Error generating trade summary with Gemini: {e}")
            return self._generate_basic_summary(trade_data)

    def _generate_basic_summary(self, trade_data):
        """
        Generate a fallback basic summary if LLM is unavailable.
        """
        action = trade_data['action']
        
        # Make the action more descriptive for basic summary
        if action == "SHORT":
            action_desc = "SHORT SELL"
        elif action == "COVER":
            action_desc = "COVER SHORT"
        elif action == "BUY":
            action_desc = "BUY LONG"
        elif action == "SELL":
            action_desc = "SELL LONG"
        else:
            action_desc = action
        
        summary = f"{action_desc} {trade_data['qty']} {trade_data['symbol']} @ ${trade_data['price']:.2f}"
        if 'reason' in trade_data and trade_data['reason']:
            summary += f": {trade_data['reason']}"
        
        summary += f" at {datetime.now().strftime('%H:%M:%S')}"
        
        self.logger.info(f"Generated basic summary: {summary}")
        return summary

    def _construct_trade_prompt(self, trade_data, market_data=None):
        """
        Construct a detailed prompt for a single trade summary with proper short sell terminology.
        """
        action = trade_data['action']
        symbol = trade_data['symbol']
        qty = trade_data['qty']
        price = trade_data['price']
        
        # Create more descriptive trade descriptions
        if action == "SHORT":
            trade_description = f"SHORT SELL (opening short position) {qty} shares of {symbol} at ${price:.2f}"
            trade_context = "This is a bearish trade betting that the stock price will decrease. The trader is borrowing shares to sell them, expecting to buy them back later at a lower price."
        elif action == "COVER":
            trade_description = f"COVER SHORT (closing short position) {qty} shares of {symbol} at ${price:.2f}"
            trade_context = "This closes an existing short position by buying back the previously borrowed shares."
        elif action == "BUY":
            trade_description = f"BUY LONG (opening long position) {qty} shares of {symbol} at ${price:.2f}"
            trade_context = "This is a bullish trade expecting the stock price to increase."
        elif action == "SELL":
            trade_description = f"SELL LONG (closing long position) {qty} shares of {symbol} at ${price:.2f}"
            trade_context = "This closes an existing long position by selling the owned shares."
        else:
            trade_description = f"{action} {qty} shares of {symbol} at ${price:.2f}"
            trade_context = ""

        prompt = f"""You are a financial analyst. Write a brief trading summary for this trade:

Trade: {trade_description}
{trade_context}
"""
        
        if 'reason' in trade_data and trade_data['reason']:
            prompt += f"Technical Reason: {trade_data['reason']}\n"

        if market_data:
            prompt += "Market Conditions:\n"
            if 'rsi' in market_data and market_data['rsi'] is not None:
                rsi_condition = "oversold" if market_data['rsi'] < 30 else "overbought" if market_data['rsi'] > 70 else "neutral"
                prompt += f"- RSI: {market_data['rsi']:.1f} ({rsi_condition})\n"
            if 'sma' in market_data and market_data['sma'] is not None:
                price_vs_sma = "above" if trade_data['price'] > market_data['sma'] else "below"
                prompt += f"- Price ${trade_data['price']:.2f} is {price_vs_sma} SMA ${market_data['sma']:.2f}\n"

        prompt += f"\nWrite a 2-3 sentence professional trading summary. Be clear about whether this is a LONG or SHORT position trade. Include the trade rationale and market context."
        
        return prompt

    def _run_cloud_llm(self, prompt):
        """
        Run the Gemini model with the provided prompt.
        """
        try:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "max_output_tokens": self.max_tokens,
                    "temperature": 0.7,
                    "top_p": 0.9
                }
            )
            
            result = response.text.strip()
            self.logger.debug(f"Gemini response: {response}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error running Gemini LLM: {e}")
            raise