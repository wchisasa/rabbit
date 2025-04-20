# Rabbit/rabbit_sdk/agent.py (refactored)

""" 
Main agent class that orchestrates browser automation, planning, and execution.
Integrates Gemini LLM for intelligent decision making and planning. 
""" 

import asyncio
import logging
from typing import List, Dict, Any, Optional

from .browser_controller import BrowserController
from .memory_manager import MemoryManager
from .planner import Planner
from .llm_manager import LLMManager
from .utils import extract_text_from_page, sanitize_input

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RabbitAgent:
    def __init__(self, 
                 browser_type: str = "chromium", 
                 headless: bool = False, 
                 profile_dir: Optional[str] = None, 
                 keep_open: bool = False,
                 gemini_api_key: Optional[str] = None):
        """
        Initialize the Rabbit Agent with browser and LLM components.
        
        Args:
            browser_type (str): Type of browser to use ("chromium", "firefox", "webkit")
            headless (bool): Whether to run the browser in headless mode
            profile_dir (str, optional): Path to browser profile directory
            keep_open (bool): Whether to keep the browser open after completing tasks
            gemini_api_key (str, optional): API key for Google's Gemini LLM service
        """
        self.browser_controller = BrowserController(
            browser_type=browser_type, 
            headless=headless, 
            profile_dir=profile_dir, 
            keep_open=keep_open
        )
        self.memory_manager = MemoryManager()
        self.llm_manager = LLMManager(api_key=gemini_api_key)
        self.planner = Planner(self.llm_manager)
        self.keep_open = keep_open
        self.browser_initialized = False
        self.session_context = {}

    async def run_task(self, task: str, session_id: str, urls: List[str], max_steps: int = 5) -> Dict[str, Any]:
        """
        Perform a task using the provided URLs with intelligent planning.

        Args:
            task (str): Description of the task to perform
            session_id (str): Unique session identifier
            urls (list): List of URLs to visit and perform actions on
            max_steps (int): Maximum number of steps to perform

        Returns:
            dict: Structured result containing the status, summary, and data
        """
        try:
            # Validate input
            task = sanitize_input(task)
            if not isinstance(urls, list):
                raise ValueError("URLs must be a list.")
            
            # Initialize browser if not already initialized
            if not self.browser_initialized:
                await self.browser_controller.initialize_browser()
                self.browser_initialized = True
            
            # Initialize session context
            self.session_context[session_id] = {
                "task": task,
                "visited_urls": [],
                "extracted_data": {},
                "actions_performed": [],
            }

            # Generate initial plan using Gemini LLM
            initial_plan = await self.planner.create_initial_plan(task, urls)
            logger.info(f"Initial plan created: {initial_plan}")
            
            result_data = []
            for url in urls:
                # Check if we have relevant data in memory
                memory_key = f"task:{task}:{url}"
                cached_result = self.memory_manager.get(session_id, memory_key)
                
                if cached_result and await self.planner.should_reuse_result(task, url, cached_result):
                    logger.info(f"Reusing cached result for {url}")
                    result_data.append({
                        "url": url,
                        "data": cached_result,
                        "source": "cache"
                    })
                    continue
                
                # Execute the task for this URL
                page = await self.browser_controller.open_page(url)
                content = await page.content()
                
                # Extract data from page
                extracted_data = await extract_text_from_page(page)
                self.session_context[session_id]["extracted_data"][url] = extracted_data
                
                # Execute multiple steps based on max_steps
                current_data = extracted_data
                steps_executed = 0
                
                while steps_executed < max_steps:
                    # Decide next action based on page content and task
                    next_action = await self.planner.plan_next_action(
                        task, 
                        url, 
                        current_data,
                        self.session_context[session_id]
                    )
                    
                    # Break if no more actions needed
                    if next_action.get('type') == "no_action":
                        break
                        
                    # Execute planned action
                    action_result = await self._execute_action(page, next_action)
                    self.session_context[session_id]["actions_performed"].append({
                        "url": url,
                        "action": next_action,
                        "result": action_result
                    })
                    
                    # Update current data if action was successful
                    if action_result.get('status') == 'success':
                        if action_result.get('data'):
                            current_data = str(action_result.get('data'))
                        else:
                            # Re-extract data after action
                            current_data = await extract_text_from_page(page)
                            
                    steps_executed += 1
                
                # Process page content or perform scraping tasks here
                if len(current_data) > 1000:
                    displayed_data = current_data[:1000] + "..."
                else:
                    displayed_data = current_data
                    
                result_data.append({
                    "url": url,
                    "data": displayed_data,
                    "actions": next_action if steps_executed > 0 else {"type": "extract_content"},
                    "source": "browser"
                })

                # Save to memory 
                memory_summary = f"Visited {url}, performed {steps_executed} action(s). Content length: {len(current_data)}."
                self.memory_manager.save(session_id, memory_key, displayed_data)
                self.memory_manager.save(session_id, f"summary:{url}", memory_summary)
                
                # Add to visited URLs
                self.session_context[session_id]["visited_urls"].append(url)

            # Perform deep analysis on the collected data
            if "sentiment" in task.lower() or "analyze" in task.lower():
                analysis_result = await self.llm_manager.perform_analysis_task(
                    task,
                    result_data
                )
                if analysis_result.get("status") == "success":
                    analysis = analysis_result.get("analysis", {})
                else:
                    analysis = {"error": analysis_result.get("message", "Analysis failed")}
            else:
                analysis = {}

            # Generate final result summary using Gemini
            summary = await self.llm_manager.generate_summary(
                task, 
                self.session_context[session_id]
            )

            # Construct the result
            result = {
                "status": "success",
                "summary": summary,
                "data": result_data,
                "analysis": analysis,
                "actions_performed": self.session_context[session_id]["actions_performed"]
            }
            return result

        except Exception as e:
            logger.error(f"Error in run_task: {str(e)}", exc_info=True)
            return {"status": "error", "message": str(e)}

    async def _execute_action(self, page, action):
        """Execute a planned action on the page."""
        try:
            action_type = action.get("type", "no_action")
            
            if action_type == "click":
                selector = action.get("selector")
                if selector:
                    await page.click(selector)
                    return {"status": "success", "action": "click", "selector": selector}
                
            elif action_type == "fill_form":
                form_data = action.get("form_data", {})
                for selector, value in form_data.items():
                    await page.fill(selector, value)
                
                submit_selector = action.get("submit_selector")
                if submit_selector:
                    await page.click(submit_selector)
                
                return {"status": "success", "action": "fill_form", "form_data": form_data}
                
            elif action_type == "navigate":
                url = action.get("url")
                if url:
                    await page.goto(url)
                    return {"status": "success", "action": "navigate", "url": url}
                    
            elif action_type == "extract":
                selector = action.get("selector")
                if selector:
                    elements = await page.query_selector_all(selector)
                    texts = []
                    for element in elements:
                        text = await element.text_content()
                        texts.append(text)
                    return {"status": "success", "action": "extract", "data": texts}
            
            elif action_type == "no_action":
                return {"status": "success", "action": "no_action"}
                
            return {"status": "unknown_action", "action_requested": action_type}
            
        except Exception as e:
            logger.error(f"Error executing action: {str(e)}", exc_info=True)
            return {"status": "error", "message": str(e)}

    async def search_and_extract(self, query: str, session_id: str) -> Dict[str, Any]:
        """
        Perform a search query and extract relevant information.
        
        Args:
            query (str): Search query
            session_id (str): Session identifier
            
        Returns:
            dict: Search results and extracted information
        """
        try:
            if not self.browser_initialized:
                await self.browser_controller.initialize_browser()
                self.browser_initialized = True
                
            # Use planner to determine search strategy
            search_plan = await self.planner.plan_search(query)
            search_url = search_plan.get("url", f"https://www.google.com/search?q={query}")
            
            # Open search page
            page = await self.browser_controller.open_page(search_url)
            
            # Wait for results to load
            await page.wait_for_load_state("networkidle")
            
            # Extract search results based on the plan
            selectors = search_plan.get("selectors", [".g"])
            results = []
            
            for selector in selectors:
                elements = await page.query_selector_all(selector)
                for element in elements:
                    text_content = await element.text_content()
                    href = await element.get_attribute("href") or ""
                    results.append({
                        "text": text_content,
                        "link": href
                    })
            
            # Use LLM to summarize and analyze the results
            analysis = await self.llm_manager.analyze_search_results(query, results)
            
            # Save to memory
            memory_key = f"search:{query}"
            self.memory_manager.save(session_id, memory_key, str(results))
            
            return {
                "status": "success",
                "query": query,
                "results": results[:5],  # Limit to first 5 for display
                "analysis": analysis
            }
            
        except Exception as e:
            logger.error(f"Error in search_and_extract: {str(e)}", exc_info=True)
            return {"status": "error", "message": str(e)}
            
    async def analyze_content(self, task: str, session_id: str, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Perform deep analysis on collected content.
        
        Args:
            task (str): Description of the analysis task
            session_id (str): Session identifier
            data (list): Collected data to analyze
            
        Returns:
            dict: Analysis results
        """
        try:
            # Perform sentiment analysis or other advanced analysis
            analysis_result = await self.llm_manager.perform_analysis_task(task, data)
            
            # Save analysis to memory
            memory_key = f"analysis:{task}"
            if analysis_result.get("status") == "success":
                self.memory_manager.save(session_id, memory_key, str(analysis_result.get("analysis", {})))
            
            return analysis_result
        except Exception as e:
            logger.error(f"Error in analyze_content: {str(e)}", exc_info=True)
            return {"status": "error", "message": str(e)}

    async def close_browser(self):
        """Close the browser regardless of keep_open flag when the application exits."""
        if self.browser_initialized:
            try:
                await self.browser_controller.close_browser()
                self.browser_initialized = False
                logger.info("Browser closed successfully")
            except Exception as e:
                logger.error(f"Error closing browser: {e}")