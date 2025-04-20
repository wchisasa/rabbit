# Rabbit/rabbit_sdk/planner.py
"""
Task planner that uses Gemini LLM to determine next actions.
Determines whether to reuse, redo, or skip a task and plans next steps.
""" 

import logging
import json
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Planner:
    """Plans task execution using LLM."""
    
    def __init__(self, llm_manager):
        """
        Initialize the planner.
        
        Args:
            llm_manager: LLM manager instance for text generation
        """
        self.llm_manager = llm_manager
        
    async def create_initial_plan(self, task: str, urls: List[str]) -> Dict[str, Any]:
        """
        Create an initial plan for executing a task on given URLs.
        
        Args:
            task (str): Task description
            urls (list): URLs to process
            
        Returns:
            dict: Initial plan with ordered steps
        """
        try:
            if not self.llm_manager.gemini_model:
                # Fallback plan when LLM is not available
                return {
                    "task": task,
                    "steps": [
                        {"type": "visit", "url": url, "actions": [{"type": "extract", "what": "content"}]}
                        for url in urls
                    ],
                    "strategy": "sequential"
                }
                
            # Generate plan using LLM
            prompt = f"""
            Create a detailed plan for the following web automation task:
            
            Task: {task}
            
            URLs to process: {urls}
            
            For each URL, what actions should be taken? Consider:
            1. What information needs to be extracted?
            2. Are there forms that need to be filled?
            3. Are there buttons or links to click?
            4. Does the task require logging in or other authentication?
            
            Format your response as a JSON object with:
            - An overview of the approach
            - A list of ordered steps for each URL
            - Any potential challenges to watch out for
            
            The JSON should follow this structure:
            {{
                "task": "task_description",
                "approach": "brief_description_of_approach",
                "steps": [
                    {{
                        "url": "url1",
                        "actions": [
                            {{"type": "action_type", "details": "action_details"}}
                        ]
                    }}
                ],
                "challenges": ["challenge1", "challenge2"]
            }}
            
            Where action_type can be: extract, click, fill_form, navigate, etc.
            """
                
            response = await self.llm_manager.generate_text(prompt, temperature=0.2)
            
            try:
                # Extract JSON from response
                if '{' in response and '}' in response:
                    start = response.find('{')
                    end = response.rfind('}') + 1
                    json_str = response[start:end]
                    plan = json.loads(json_str)
                else:
                    # Fallback plan
                    plan = {
                        "task": task,
                        "steps": [
                            {"type": "visit", "url": url, "actions": [{"type": "extract", "what": "content"}]}
                            for url in urls
                        ],
                        "strategy": "sequential"
                    }
            except json.JSONDecodeError:
                # Fallback plan
                plan = {
                    "task": task,
                    "steps": [
                        {"type": "visit", "url": url, "actions": [{"type": "extract", "what": "content"}]}
                        for url in urls
                    ],
                    "strategy": "sequential"
                }
                
            return plan
                
        except Exception as e:
            logger.error(f"Error creating initial plan: {str(e)}")
            # Fallback plan
            return {
                "task": task,
                "steps": [
                    {"type": "visit", "url": url, "actions": [{"type": "extract", "what": "content"}]}
                    for url in urls
                ],
                "strategy": "sequential"
            }
    
    async def should_reuse_result(self, task: str, url: str, cached_result: str) -> bool:
        """
        Determine if a cached result should be reused.
        
        Args:
            task (str): Task description
            url (str): URL of the page
            cached_result (str): Cached result data
            
        Returns:
            bool: Whether to reuse the cached result
        """
        try:
            if not self.llm_manager.gemini_model:
                # Default to not reusing when LLM is unavailable
                return False
                
            # Truncate cached result if too long
            truncated_result = cached_result[:500] + "..." if len(cached_result) > 500 else cached_result
                
            prompt = f"""
            For the task: "{task}"
            
            I have a cached result from URL: {url}
            
            Here is the beginning of the cached result:
            {truncated_result}
            
            Should I reuse this cached result or should I refresh the data?
            Consider:
            1. Does this task likely need fresh data?
            2. Does the URL suggest frequently changing content?
            3. Is the cached result relevant to the current task?
            
            Answer with only "yes" if I should reuse the cached result, or "no" if I should refresh the data.
            """
                
            response = await self.llm_manager.generate_text(prompt, temperature=0.1)
            
            # Parse response for yes/no
            response_lower = response.lower().strip()
            if "yes" in response_lower:
                logger.info(f"Decision: Reuse cached result for {url}")
                return True
            else:
                logger.info(f"Decision: Refresh data for {url}")
                return False
                
        except Exception as e:
            logger.error(f"Error deciding whether to reuse result: {str(e)}")
            return False  # Default to not reusing on error
    
    async def plan_next_action(self, task: str, url: str, page_content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Plan the next action based on the current page content and task.
        
        Args:
            task (str): Task description
            url (str): Current URL
            page_content (str): Content of the current page
            context (dict): Session context with history
            
        Returns:
            dict: Next action plan
        """
        try:
            if not self.llm_manager.gemini_model:
                # Default action when LLM is unavailable
                return {"type": "no_action", "reason": "LLM not available"}
                
            # Truncate page content if too long
            truncated_content = page_content[:2000] + "..." if len(page_content) > 2000 else page_content
                
            # Get previous actions from context
            previous_actions = context.get("actions_performed", [])
            previous_actions_text = ""
            if previous_actions:
                previous_actions_text = "Previous actions taken:\n" + "\n".join([
                    f"- URL: {a.get('url', 'unknown')}, Action: {a.get('action', {}).get('type', 'unknown')}"
                    for a in previous_actions[-3:]  # Show last 3 actions
                ])
                
            prompt = f"""
            Task: {task}
            
            Current URL: {url}
            
            {previous_actions_text}
            
            Current page content (truncated):
            {truncated_content}
            
            Based on the task and current page, determine the most appropriate next action.
            Consider options like:
            - Extracting specific information
            - Clicking on a button or link
            - Filling out a form
            - Navigating to a different URL
            - No action (if task is complete for this URL)
            
            Format your response as a JSON object with:
            - action_type: The type of action to take (extract, click, fill_form, navigate, no_action)
            - details: Specific details for the action (e.g., what to extract, which button to click)
            - selectors: CSS or XPath selectors for elements to interact with (if applicable)
            - reason: Brief explanation of why this action was chosen
            
            The JSON should follow this structure:
            {{
                "type": "action_type",
                "selector": "CSS_selector",  # for click, extract actions
                "form_data": {{             # for fill_form actions
                    "selector1": "value1",
                    "selector2": "value2"
                }},
                "submit_selector": "submit_button_selector",  # for fill_form actions
                "url": "url_to_navigate",   # for navigate actions
                "reason": "explanation"
            }}
            """
                
            response = await self.llm_manager.generate_text(prompt, temperature=0.2)
            
            try:
                # Extract JSON from response
                if '{' in response and '}' in response:
                    start = response.find('{')
                    end = response.rfind('}') + 1
                    json_str = response[start:end]
                    action_plan = json.loads(json_str)
                else:
                    # Default to no action
                    action_plan = {
                        "type": "no_action",
                        "reason": "Could not determine appropriate action"
                    }
            except json.JSONDecodeError:
                # Default to no action
                action_plan = {
                    "type": "no_action",
                    "reason": "Could not parse action plan"
                }
                
            return action_plan
                
        except Exception as e:
            logger.error(f"Error planning next action: {str(e)}")
            return {"type": "no_action", "reason": f"Error: {str(e)}"}
    
    async def plan_search(self, query: str) -> Dict[str, Any]:
        """
        Plan a search strategy for a given query.
        
        Args:
            query (str): Search query
            
        Returns:
            dict: Search strategy including URL and selectors
        """
        try:
            # Get search strategy from LLM manager
            search_plan = await self.llm_manager.plan_search_strategy(query)
            
            # Add default selectors for common search engines
            search_engine = search_plan.get("search_engine", "google").lower()
            
            if search_engine == "google":
                search_plan["selectors"] = [".g", "div.yuRUbf > a", "h3.LC20lb"]
            elif search_engine == "bing":
                search_plan["selectors"] = [".b_algo", "h2 a", ".b_caption"]
            elif search_engine == "duckduckgo":
                search_plan["selectors"] = [".result", "h2 a", ".result__snippet"]
            else:
                search_plan["selectors"] = [".g", "div.yuRUbf > a", "h3.LC20lb"]  # Default to Google
                
            return search_plan
                
        except Exception as e:
            logger.error(f"Error planning search: {str(e)}")
            return {
                "url": f"https://www.google.com/search?q={query}",
                "selectors": [".g", "div.yuRUbf > a", "h3.LC20lb"]
            }