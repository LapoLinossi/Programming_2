#!/usr/bin/env python3
"""
Test script to check Gemini API integration
"""

import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_gemini_llm_reporter():
    """Test Gemini-based LLMReporter class"""
    print("\n=== Testing Gemini LLMReporter ===")
    try:
        from llm_reporter import LLMReporter
        
        print("Initializing Gemini LLMReporter...")
        llm_reporter = LLMReporter()
        
        print(f"Available: {llm_reporter.available}")
        
        if llm_reporter.available:
            test_trade = {
                'symbol': 'AAPL',
                'action': 'BUY',
                'qty': 100,
                'price': 150.00,
                'reason': 'Test trade'
            }
            
            test_market = {
                'close': 150.00,
                'sma': 145.00,
                'rsi': 35.0
            }
            
            print("Testing trade summary generation...")
            result = llm_reporter.generate_trade_summary(test_trade, test_market)
            print(f"✅ Gemini LLMReporter works! Result: '{result}'")
            return True
        else:
            print("❌ Gemini LLMReporter not available")
            return False
            
    except ImportError:
        print("❌ gemini_llm_reporter module not found")
        return False
    except Exception as e:
        print(f"❌ Gemini LLMReporter error: {e}")
        import traceback
        traceback.print_exc()
        return False

def setup_instructions():
    """Print setup instructions"""
    print("\n=== SETUP INSTRUCTIONS ===")
    print("1. Install the Gemini API library:")
    print("   pip install google-generativeai")
    print()
    print("2. Get your API key from Google AI Studio:")
    print("   https://makersuite.google.com/app/apikey")
    print()
    print("3. Set your API key as an environment variable:")
    print("   export GEMINI_API_KEY='your-api-key-here'")
    print("   # or")
    print("   export GOOGLE_API_KEY='your-api-key-here'")
    print()
    print("4. Create the gemini_llm_reporter.py file (see artifact below)")

if __name__ == "__main__":
    print("Testing Gemini API integration...\n")
    
    reporter_works = test_gemini_llm_reporter()
    
    print("\n" + "="*50)
    print("SUMMARY:")
    print(f"Gemini LLMReporter: {'✅ WORKS' if reporter_works else '❌ FAILED'}")
    
    if not reporter_works:
        setup_instructions()
    else:
        print("\n✅ All tests passed! Your Gemini integration is working.")