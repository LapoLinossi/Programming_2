#!/usr/bin/env python3
"""
Test script to check which LLM library works in your environment
"""

import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_gpt4all():
    """Test gpt4all library"""
    print("=== Testing gpt4all ===")
    try:
        import gpt4all
        
        model_path = "/Users/federico/Library/Application Support/nomic.ai/GPT4All/Meta-Llama-3-8B-Instruct.Q4_0.gguf"
        
        if not os.path.exists(model_path):
            print(f"❌ Model file not found: {model_path}")
            return False
            
        print("Loading model with gpt4all...")
        model = gpt4all.GPT4All(model_path)
        
        print("Testing generation...")
        result = model.generate("What is 2+2?", max_tokens=50)
        print(f"✅ gpt4all works! Result: '{result}'")
        return True
        
    except ImportError:
        print("❌ gpt4all not installed. Install with: pip install gpt4all")
        return False
    except Exception as e:
        print(f"❌ gpt4all error: {e}")
        return False

def test_llama_cpp():
    """Test llama_cpp library"""
    print("\n=== Testing llama_cpp ===")
    try:
        from llama_cpp import Llama
        
        model_path = "/Users/federico/Library/Application Support/nomic.ai/GPT4All/Meta-Llama-3-8B-Instruct.Q4_0.gguf"
        
        if not os.path.exists(model_path):
            print(f"❌ Model file not found: {model_path}")
            return False
            
        print("Loading model with llama_cpp...")
        model = Llama(
            model_path=model_path,
            n_ctx=2048,
            n_threads=4,
            verbose=False
        )
        
        print("Testing generation...")
        result = model("What is 2+2?", max_tokens=50)
        output_text = result["choices"][0]["text"]
        print(f"✅ llama_cpp works! Result: '{output_text}'")
        return True
        
    except ImportError:
        print("❌ llama_cpp not installed. Install with: pip install llama-cpp-python")
        return False
    except Exception as e:
        print(f"❌ llama_cpp error: {e}")
        return False

def test_your_current_llm_reporter():
    """Test your current LLMReporter class"""
    print("\n=== Testing your current LLMReporter ===")
    try:
        from llm_reporter import LLMReporter
        
        print("Initializing LLMReporter...")
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
            print(f"✅ LLMReporter works! Result: '{result}'")
            return True
        else:
            print("❌ LLMReporter not available")
            return False
            
    except Exception as e:
        print(f"❌ LLMReporter error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing LLM libraries in your environment...\n")
    
    gpt4all_works = test_gpt4all()
    llama_cpp_works = test_llama_cpp()
    current_works = test_your_current_llm_reporter()
    
    print("\n" + "="*50)
    print("SUMMARY:")
    print(f"gpt4all: {'✅ WORKS' if gpt4all_works else '❌ FAILED'}")
    print(f"llama_cpp: {'✅ WORKS' if llama_cpp_works else '❌ FAILED'}")
    print(f"Current LLMReporter: {'✅ WORKS' if current_works else '❌ FAILED'}")
    
    print("\nRECOMMENDAITONS:")
    if current_works:
        print("✅ Your current setup works! No changes needed.")
    elif gpt4all_works:
        print("🔧 Switch to gpt4all - replace your llm_reporter.py with the fixed version above")
    elif llama_cpp_works:
        print("🔧 Your llama_cpp setup should work - check for other issues")
    else:
        print("❌ Neither library works - check installations and model file")
        print("Try: pip install gpt4all")
        print("Or: pip install llama-cpp-python")