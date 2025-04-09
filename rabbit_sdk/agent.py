# Rabbit/rabbit_sdk/agent.py (refactored)

""" 
Calls planner before acting.

After executing:

Logs summary content.

Stores results in memory using the same task:{task}:{url} key.

Updates a general last_action key (you can expand on this later). 
"""

import asyncio
from .browser_controller import BrowserController
from .memory_manager import MemoryManager
from .planner import plan_next_action
from .utils import extract_text_from_page

class RabbitAgent:
    def __init__(self, browser_type="chromium", headless=False, profile_dir=None, keep_open=False):
        self.browser_controller = BrowserController(browser_type=browser_type, headless=headless, profile_dir=profile_dir, keep_open=keep_open)
        self.memory_manager = MemoryManager()
        self.keep_open = keep_open
        self.browser_initialized = False

    async def run_task(self, task, session_id, urls):
        """
        Perform a task using the provided URLs.

        Args:
            task (str): Description of the task.
            session_id (str): Unique session identifier.
            urls (list): List of URLs to visit and perform actions on.

        Returns:
            dict: Structured result containing the status, summary, and data.
        """
        try:
            # Ensure that the URLs are passed correctly
            if not isinstance(urls, list):
                raise ValueError("URLs must be a list.")

            # Initialize browser if not already initialized
            if not self.browser_initialized:
                await self.browser_controller.initialize_browser()
                self.browser_initialized = True

            result_data = []
            for url in urls:
                # Perform the task for each URL
                page = await self.browser_controller.open_page(url)
                content = await page.content()

                # Process page content or perform scraping tasks here
                extracted_data = await extract_text_from_page(page)
                
                # Truncate data if it's too large to prevent memory issues
                if len(extracted_data) > 1000:
                    displayed_data = extracted_data[:1000] + "..."
                else:
                    displayed_data = extracted_data
                    
                result_data.append({
                    "url": url,
                    "data": displayed_data
                })

                # Save summary to memory
                memory_summary = f"Visited {url}, found content of length {len(extracted_data)}."
                self.memory_manager.save(session_id, f"visited_{url}", memory_summary)
                
                # Plan next action if needed (placeholder)
                # next_action = await plan_next_action(task, url, extracted_data)
                # Implement the next action logic here if needed

            # Construct the result as structured JSON
            result = {
                "status": "success",
                "summary": f"Visited {len(urls)} URLs",
                "data": result_data
            }
            return result

        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def close_browser(self):
        """Close the browser regardless of keep_open flag when the application exits."""
        if self.browser_initialized:
            try:
                await self.browser_controller.close_browser()
                self.browser_initialized = False
            except Exception as e:
                print(f"Error closing browser: {e}")