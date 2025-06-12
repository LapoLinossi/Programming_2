# reporting.py - Cloud Version with Gemini API
import pandas as pd
import matplotlib.pyplot as plt
import logging
import os 
from datetime import datetime
from llm_reporter import LLMReporter

class Reporter:
    def __init__(self, chart_dir="charts", llm_reporter=None, report_dir="reports"):
        """Initialize reporter with optional LLM integration."""
        self.chart_dir = chart_dir
        self.llm_reporter = llm_reporter
        self.logger = logging.getLogger(__name__)
        self.report_dir = report_dir
        
        os.makedirs(chart_dir, exist_ok=True)
        os.makedirs(self.report_dir, exist_ok=True)
        
        self.logger.info(f"Reporter initialized - Chart dir: {chart_dir}, Report dir: {self.report_dir}")
        
        if self.llm_reporter:
            self.logger.info(f"LLM reporter available: {getattr(self.llm_reporter, 'available', False)}")
        else:
            self.logger.info("No LLM reporter provided")
    
    def generate_trade_summary(self, trade_data, market_data=None, save=True):
        """
        Generate a summary for a single trade, using LLM if available.
        """
        self.logger.info(f"=== Starting trade summary generation for {trade_data.get('symbol', 'UNKNOWN')} ===")
        summary = ""
        
        try:
            action = trade_data.get('action', 'UNKNOWN')
            symbol = trade_data.get('symbol', 'UNKNOWN')
            llm_available = (self.llm_reporter is not None and self.llm_reporter.available)
            
            if llm_available:
                self.logger.info("Attempting to use Gemini API for trade summary generation")
                try:
                    summary = self.llm_reporter.generate_trade_summary(trade_data, market_data)
                    
                    if not summary or not summary.strip():
                        self.logger.warning("LLM returned empty/whitespace summary, falling back to basic")
                        summary = self._generate_basic_summary(trade_data, market_data)
                    else:
                        summary = summary.strip()
                        self.logger.info(f"Using LLM summary: '{summary}'")
                        
                except Exception as llm_error:
                    self.logger.error(f"LLM generation failed: {llm_error}", exc_info=True)
                    summary = self._generate_basic_summary(trade_data, market_data)
            else:
                self.logger.info("Using basic trade summary generation (LLM not available)")
                summary = self._generate_basic_summary(trade_data, market_data)

            if not summary or not summary.strip():
                self.logger.error("Final summary is empty! This should not happen.")
                summary = f"Trade executed: {action} {trade_data.get('qty', 0)} {symbol} @ ${trade_data.get('price', 0):.2f}"
            
            self.logger.info(f"Final summary: '{summary}'")
            
            if save and summary:
                summary_file = self.save_trade_summary(summary, symbol, action)
                if summary_file:
                    self.logger.info(f"Trade summary saved to {summary_file}")
                else:
                    self.logger.error("Failed to save trade summary")
            
            self.logger.info(f"=== Completed trade summary generation ===")
            return summary
            
        except Exception as e:
            self.logger.error(f"Error in generate_trade_summary: {e}", exc_info=True)
            return f"Trade executed (summary generation failed)"

    def _generate_basic_summary(self, trade_data, market_data=None):
        """Generate a basic trade summary without LLM."""
        self.logger.info("Generating basic summary")
        
        try:
            action = trade_data.get('action', 'UNKNOWN')
            qty = trade_data.get('qty', 0)
            symbol = trade_data.get('symbol', 'UNKNOWN')
            price = trade_data.get('price', 0)
            
            summary = f"{action} {qty} {symbol} @ ${price:.2f}"
            
            reason = trade_data.get('reason', '')
            if reason:
                summary += f" - {reason}"
            
            if market_data:
                context_parts = []
                if 'rsi' in market_data and market_data['rsi'] is not None:
                    context_parts.append(f"RSI: {market_data['rsi']:.1f}")
                if 'sma' in market_data and market_data['sma'] is not None:
                    sma = market_data['sma']
                    if market_data.get('price_above_sma'):
                        context_parts.append(f"price above SMA (${sma:.2f})")
                    else:
                        context_parts.append(f"price below SMA (${sma:.2f})")
                if context_parts:
                    summary += f" [{', '.join(context_parts)}]"

            summary += f" at {datetime.now().strftime('%H:%M:%S')}"
            
            self.logger.info(f"Generated basic summary: '{summary}'")
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating basic summary: {e}", exc_info=True)
            return f"Trade summary generation failed: {e}"
    
    def save_trade_summary(self, summary, symbol, action=None):
        """Save the trade summary to a text file."""
        try:
            self.logger.info(f"Saving trade summary for {symbol}")
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            action_suffix = f"_{action}" if action else ""
            filename = os.path.join(self.report_dir, f"{symbol.lower()}{action_suffix}_{timestamp}.txt")
            
            report_content = f"Trade Summary - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            report_content += "=" * 50 + "\n\n"
            report_content += summary + "\n\n"
            report_content += "=" * 50 + "\n"
            
            with open(filename, 'w') as f:
                f.write(report_content)
            
            self.logger.info(f"Trade summary successfully saved to: {filename}")
            return filename
            
        except Exception as e:
            self.logger.error(f"Error saving trade summary to file: {e}", exc_info=True)
            return None

    def create_chart(self, data, symbol, signals=None, save=True):
        """Create and save a chart for the given symbol with price and indicators."""
        try:
            self.logger.info(f"Creating chart for {symbol}")
            plt.figure(figsize=(12, 8))
            
            ax1 = plt.subplot(2, 1, 1)
            ax1.plot(data.index, data['close'], label='Close', color='black')
            if 'sma' in data.columns:
                ax1.plot(data.index, data['sma'], label="SMA", color='blue')
            
            if signals:
                if 'buy' in signals:
                    for timestamp in signals['buy']:
                        if timestamp in data.index:
                            ax1.plot(timestamp, data.loc[timestamp, 'close'], '^', color='green', markersize=10)
                if 'sell' in signals:
                    for timestamp in signals['sell']:
                        if timestamp in data.index:
                            ax1.plot(timestamp, data.loc[timestamp, 'close'], 'v', color='red', markersize=10)
            
            ax1.set_title(f"{symbol} Price and Indicators")
            ax1.set_ylabel('Price')
            ax1.grid(True)
            ax1.legend()

            if 'rsi' in data.columns:
                ax2 = plt.subplot(2, 1, 2, sharex=ax1)
                ax2.plot(data.index, data['rsi'], label='RSI', color='purple')
                ax2.axhline(y=70, color='r', linestyle='--')
                ax2.axhline(y=30, color='g', linestyle='--')
                ax2.set_title('RSI')
                ax2.set_ylabel('RSI')
                ax2.grid(True)
                ax2.legend()
            
            plt.tight_layout()
            
            if save:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = os.path.join(self.chart_dir, f"{symbol.lower()}_{timestamp}.png")
                plt.savefig(filename)
                self.logger.info(f"Chart saved to {filename}")
                plt.close()
                return filename
            else:
                plt.close()
                return None
                
        except Exception as e:
            self.logger.error(f"Error creating chart: {e}", exc_info=True)
            plt.close()
            return None