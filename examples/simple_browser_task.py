#!/usr/bin/env python3
"""Simple browser task example using Rabbit SDK.""" 
#Rabbit/examples/simple_browser_task.py

#!/usr/bin/env python3
"""Simple browser task example using Rabbit SDK."""
# Rabbit/examples/simple_browser_task.py

import sys
import os
import asyncio
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

from rabbit_sdk.agent import RabbitAgent
from rabbit_sdk.config import get_config

async def main():
    """Run a simple browser-based task with the agent."""
    config = get_config()
    agent = RabbitAgent(gemini_api_key=config["gemini_api_key"])
    
    research_task = """Analyze the sentiment around artificial intelligence safety concerns in recent tech publications.
1. Navigate to the provided URLs
2. Extract relevant content about AI safety
3. If extraction fails, try alternative selectors or navigation paths
4. Perform sentiment analysis on the extracted content
5. Identify major concerns, positive developments, and public sentiment
6. Summarize findings with key insights
Include all extracted data and analysis in your final report.
    """
    
    print("Starting research task...")
    result = await agent.run_task(
        research_task, 
        "session_id", 
        ["https://www.utoronto.ca/news/risks-artificial-intelligence-must-be-considered-technology-evolves-geoffrey-hinton", 
         "https://www.technologyreview.com/topic/artificial-intelligence/", 
         "https://builtin.com/artificial-intelligence/artificial-intelligence-future", 
         "https://www.gsb.stanford.edu/insights/what-point-do-we-decide-ais-risks-outweigh-its-promise"]
    )
    
    print("\nTask completed!")
    print("Results:", result)
    
    # Ensure browser is closed
    await agent.close_browser()

if __name__ == "__main__":
    asyncio.run(main())