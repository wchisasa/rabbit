#!/usr/bin/env python3
"""Simplified workflow for cryptocurrency market analysis using Rabbit SDK."""

import sys
import os
import asyncio
import json
from datetime import datetime
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

from rabbit_sdk.agent import RabbitAgent
from rabbit_sdk.config import get_config
from rabbit_sdk.memory_manager import MemoryManager

async def analyze_cryptocurrencies(agent, crypto_list):
    """Analyze multiple cryptocurrencies in a single browser session."""
    print("Starting cryptocurrency analysis...")
    
    # Single consolidated task to analyze all cryptocurrencies
    crypto_names = ", ".join(crypto_list)
    task = f"""
    Navigate to CoinMarketCap and collect data for the following cryptocurrencies: {crypto_names}
    
    For each cryptocurrency:
    1. Go to its page on CoinMarketCap
    2. Collect the following data:
       - Current price
       - 24h change percentage
       - 7d change percentage
       - Market cap
       - 24h trading volume
       - Key recent news headlines (if available)
    
    Then navigate to TradingView's crypto market overview to assess general market sentiment.
    
    Finally, check Crypto Fear & Greed Index on alternative.me.
    
    Compile all findings into a comprehensive JSON report with the following structure:
    {{
        "market_overview": {{
            "sentiment": "...",
            "fear_greed_index": "..."
        }},
        "cryptocurrencies": {{
            "[crypto_name]": {{
                "price": "...",
                "24h_change": "...",
                "7d_change": "...",
                "market_cap": "...",
                "volume_24h": "...",
                "news": [...]
            }},
            ...
        }},
        "analysis": {{
            "top_performer": "...",
            "worst_performer": "...",
            "notable_trends": [...],
            "correlations": [...]
        }},
        "outlook": {{
            "short_term": "...",
            "medium_term": "..."
        }}
    }}
    """
    
    # Only open one browser session for all cryptocurrencies
    urls = [
        "https://coinmarketcap.com/",
        "https://www.tradingview.com/markets/cryptocurrencies/prices-all/",
        "https://alternative.me/crypto/fear-and-greed-index/"
    ]
    
    result = await agent.run_task(
        task,
        "consolidated_crypto_analysis",
        urls
    )
    
    return result

async def generate_insights(agent, analysis_data):
    """Generate trading insights based on the analysis without opening a browser."""
    print("Generating trading insights...")
    
    insights_task = f"""
    Based on the following cryptocurrency market analysis:
    
    {analysis_data}
    
    Generate a concise report with:
    
    1. Key market trends and patterns
    2. Notable correlations between cryptocurrencies
    3. Short-term outlook (24-48 hours)
    4. Medium-term outlook (1-2 weeks)
    5. Risk factors to monitor
    6. Top opportunities based on the data
    
    Focus on actionable insights rather than general information.
    """
    
    # No URLs needed as this uses the LLM without browser navigation
    insights = await agent.run_task(
        insights_task,
        "trading_insights",
        []
    )
    
    return insights

async def main():
    """Run a simplified cryptocurrency analysis workflow."""
    config = get_config()
    agent = RabbitAgent(gemini_api_key=config["gemini_api_key"])
    memory = MemoryManager()
    
    # List of cryptocurrencies to analyze - keep it small for resource efficiency
    crypto_list = ["bitcoin", "ethereum", "solana"]
    
    try:
        # Step 1: Single browser session for all crypto data collection
        crypto_analysis = await analyze_cryptocurrencies(agent, crypto_list)
        memory.save("crypto_analysis", "crypto_data", crypto_analysis)
        
        # Step 2: Generate insights without opening a browser
        insights = await generate_insights(agent, crypto_analysis)
        memory.save("crypto_analysis", "insights", insights)
        
        # Generate final report
        final_report = {
            "timestamp": datetime.now().isoformat(),
            "analysis": crypto_analysis,
            "insights": insights
        }
        
        # Save report
        report_filename = f"crypto_report_{datetime.now().strftime('%Y%m%d')}.json"
        with open(report_filename, "w") as f:
            json.dump(final_report, f, indent=2)
        
        print("\nAnalysis workflow completed!")
        print(f"Report saved as {report_filename}")
        
        return final_report
        
    except Exception as e:
        print(f"Error in workflow: {e}")
        raise
    finally:
        # Ensure browser is closed
        await agent.close_browser()

if __name__ == "__main__":
    asyncio.run(main())