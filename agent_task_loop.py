# Rabbit/agent_task_loop.py 
"""
Persistent memory-based agent loop.
Interactive persistent loop that takes in:

session_id

task

url

Runs the full [Recall ➝ Plan ➝ Act ➝ Save ➝ Repeat] loop. 
""" 
import asyncio
from rabbit_sdk.agent import RabbitAgent

async def task_loop():
    """
    Runs the task loop for Rabbit Agent. Prompts the user for task details and processes the URLs.
    """
    # Prompt the user for task details
    task = input("Enter the task description (e.g., 'Find top companies'): ")
    session_id = input("Enter the session ID: ")
    urls_input = input("Enter the URLs (comma-separated): ")
    keep_open_input = input("Do you want to keep the browser open? (yes/no): ")

    # Parse URLs from input
    urls = [url.strip() for url in urls_input.split(",")]
    keep_open = keep_open_input.lower() == 'yes'

    # Initialize the RabbitAgent with the keep_open flag
    agent = RabbitAgent(browser_type="chromium", headless=False, keep_open=keep_open)

    try:
        # Run the task using the agent
        result = await agent.run_task(task=task, session_id=session_id, urls=urls)
        print(f"Task result: {result}")
    finally:
        # Ensure that the agent properly cleans up resources
        await agent.close_browser()

# Run the event loop using asyncio.run() to avoid event loop issues
if __name__ == "__main__":
    print("🧠 Rabbit Agent Task Loop (Ctrl+C to stop)")

    # Using asyncio.run() to properly handle the event loop
    asyncio.run(task_loop())