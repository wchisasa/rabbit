#!/usr/bin/env python3
#Rabbit/test_agent.py
"""Test script for RabbitAgent functionality."""

import asyncio
import os
import sys
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rabbit_sdk.agent import RabbitAgent
from rabbit_sdk.config import get_config
from rabbit_sdk.memory_manager import MemoryManager

async def test_simple_task():
    """Test a simple browser task."""
    print("Testing simple browser task...")
    
    config = get_config()
    agent = RabbitAgent(gemini_api_key=config["gemini_api_key"])
    
    try:
        # Simple task to test browser capabilities
        task = """
        Navigate to Wikipedia's homepage.
        1. Search for "Artificial Intelligence"
        2. Extract the first paragraph of the article
        3. Find and list 3 notable AI researchers mentioned in the article
        4. Return results in JSON format
        """
        
        result = await agent.run_task(
            task,
            "wiki_ai_search",
            ["https://www.wikipedia.org/"]
        )
        
        print("\nTask Results:")
        print(result)
        return result
        
    except Exception as e:
        print(f"Error in test task: {e}")
        raise
    finally:
        await agent.close_browser()

async def test_crypto_price_task():
    """Test cryptocurrency price checking task."""
    print("Testing crypto price checking task...")
    
    config = get_config()
    agent = RabbitAgent(gemini_api_key=config["gemini_api_key"])
    memory = MemoryManager()
    
    try:
        # Crypto price checking task
        task = """
        Navigate to CoinMarketCap and collect the following data for Bitcoin and Ethereum:
        1. Current price
        2. 24h change percentage
        3. Market cap
        4. Trading volume (24h)
        
        Format the extracted data as JSON.
        """
        
        result = await agent.run_task(
            task,
            "crypto_price_check",
            ["https://coinmarketcap.com/"]
        )
        
        # Store result in memory
        memory.save("test_results", "crypto_prices", result)
        
        print("\nCrypto Price Results:")
        print(result)
        return result
        
    except Exception as e:
        print(f"Error in crypto price task: {e}")
        raise
    finally:
        await agent.close_browser()

async def test_news_summary_task():
    """Test news summarization task."""
    print("Testing news summarization task...")
    
    config = get_config()
    agent = RabbitAgent(gemini_api_key=config["gemini_api_key"])
    
    try:
        # News summarization task
        task = """
        Navigate to The Verge tech news website.
        1. Identify the top 3 tech news stories
        2. For each story, provide:
           - Headline
           - Brief summary (2-3 sentences)
           - Author if available
           - Publication date
        3. Format the results in JSON
        """
        
        result = await agent.run_task(
            task,
            "tech_news_summary",
            ["https://www.theverge.com/"]
        )
        
        print("\nNews Summary Results:")
        print(result)
        return result
        
    except Exception as e:
        print(f"Error in news summary task: {e}")
        raise
    finally:
        await agent.close_browser()

async def test_sequential_tasks():
    """Test running multiple tasks in sequence."""
    print("Testing sequential tasks...")
    
    config = get_config()
    agent = RabbitAgent(gemini_api_key=config["gemini_api_key"])
    memory = MemoryManager()
    
    try:
        # Task 1: Weather check
        weather_task = """
        Navigate to Weather.com.
        1. Get the current temperature and conditions for New York City
        2. Get the 3-day forecast
        3. Return the data in JSON format
        """
        
        weather_result = await agent.run_task(
            weather_task,
            "weather_check",
            ["https://weather.com/weather/today/l/New+York+NY"]
        )
        
        memory.save("test_results", "weather", weather_result)
        
        # Task 2: Stock check
        stock_task = """
        Navigate to Yahoo Finance.
        1. Get the current price and daily change for AAPL, MSFT, and GOOGL
        2. Return the data in JSON format
        """
        
        stock_result = await agent.run_task(
            stock_task,
            "stock_check",
            ["https://finance.yahoo.com/"]
        )
        
        memory.save("test_results", "stocks", stock_result)
        
        # Combine results
        combined_results = {
            "timestamp": datetime.now().isoformat(),
            "weather": weather_result,
            "stocks": stock_result
        }
        
        print("\nSequential Tasks Results:")
        print(combined_results)
        return combined_results
        
    except Exception as e:
        print(f"Error in sequential tasks: {e}")
        raise
    finally:
        await agent.close_browser()

async def test_no_browser_task():
    """Test a task that doesn't require a browser."""
    print("Testing non-browser task...")
    
    config = get_config()
    agent = RabbitAgent(gemini_api_key=config["gemini_api_key"])
    
    try:
        # Task that uses LLM without browser
        task = """
        Create a brief analysis of potential use cases for AI agents in the following industries:
        1. Healthcare
        2. Finance
        3. Education
        
        For each industry, list 3 specific applications and the potential benefits.
        """
        
        result = await agent.run_task(
            task,
            "ai_use_cases",
            []  # Empty URL list indicates no browser needed
        )
        
        print("\nNon-Browser Task Results:")
        print(result)
        return result
        
    except Exception as e:
        print(f"Error in non-browser task: {e}")
        raise

async def main():
    """Run all test functions."""
    tests = [
        test_simple_task(),
        test_crypto_price_task(),
        test_news_summary_task(),
        test_sequential_tasks(),
        test_no_browser_task()
    ]
    
    for test in tests:
        try:
            await test
            print("\n" + "-"*50 + "\n")
        except Exception as e:
            print(f"Test failed: {e}")
            print("\n" + "-"*50 + "\n")

if __name__ == "__main__":
    asyncio.run(main())