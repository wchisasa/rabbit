#!/usr/bin/env python3
#Rabbit/examples/complex_workflow.py
"""Complex workflow example using Rabbit SDK."""

import sys
import os
import json
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rabbit_sdk.agent import Agent
from rabbit_sdk.config import get_config
from rabbit_sdk.memory_manager import MemoryManager


def save_results(results, filename=None):
    """Save results to a JSON file."""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"workflow_results_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    print(f"Results saved to {filename}")


def main():
    """Run a complex multi-step workflow with the agent."""
    config = get_config()
    agent = Agent(config)
    memory = MemoryManager(config)
    
    # Example of a more complex task with multiple steps and reasoning
    task = """
    Complete the following research task:
    
    1. Navigate to https://news.ycombinator.com/
    2. Find the top 5 posts on the front page
    3. For each post:
       a. Extract the title, link, and points
       b. Navigate to the post's page
       c. Extract the first 3 comments
       d. Return to the main page
    4. Compile all the information into a structured report
    5. Save the report as JSON
    """
    
    print("Starting complex workflow...")
    print("This may take several minutes to complete.")
    
    # Set a longer timeout for complex tasks
    config["task_timeout"] = 600
    
    # Run the agent with memory persistence
    result = agent.run(task, memory=memory)
    
    # Save the final results
    save_results(result, "hacker_news_report.json")
    
    print("\nWorkflow completed!")
    print("Check 'hacker_news_report.json' for the results.")


if __name__ == "__main__":
    main()