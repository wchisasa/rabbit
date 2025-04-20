#!/usr/bin/env python3
#Rabbit/agent_task_loop.py
"""Main execution loop for Rabbit Agent running tasks.""" 
import sys
import os
import argparse
import json
import time
import logging
import asyncio
from typing import Dict, List, Any, Optional
from rabbit_sdk.agent import RabbitAgent
from rabbit_sdk.config import get_config
from rabbit_sdk.memory_manager import MemoryManager

def setup_logging(config: Dict[str, Any]):
    """Set up logging based on configuration."""
    log_level = getattr(logging, config["log_level"])
    
    # Configure logging to file
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        filename=config["log_file"]
    )
    
    # Suppress stdout/stderr when not in debug mode
    if not config["debug_mode"]:
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')

def load_task(task_path: str) -> Dict[str, Any]:
    """Load task from a JSON file.
    
    Args:
        task_path: Path to the task JSON file
        
    Returns:
        Dict[str, Any]: Task configuration
    """
    with open(task_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_result(result: Dict[str, Any], output_path: Optional[str] = None):
    """Save task result to a file.
    
    Args:
        result: Task execution result
        output_path: Path to save the result
    """
    if output_path is None:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_path = f"result_{timestamp}.json"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    
    logging.info(f"Result saved to {output_path}")

async def run_task(agent: RabbitAgent, task_data: Dict[str, Any], memory: MemoryManager) -> Dict[str, Any]:
    """Run a task with content extraction and sentiment analysis.
    
    Args:
        agent: The agent instance
        task_data: Task configuration data
        memory: Memory manager instance
        
    Returns:
        Dict[str, Any]: Task execution result
    """
    instructions = task_data["instructions"]
    urls = task_data.get("parameters", {}).get("urls", [])
    
    logging.info(f"Running task with {len(urls)} URLs")
    
    # Run the main task
    result = await agent.run_task(
        instructions, 
        task_data.get("session_id", "default_session"),
        urls
    )
    
    # If no data was extracted, try alternative extraction method
    if not result or not result.get("data") or len(result.get("data", [])) == 0:
        logging.warning("No data extracted, trying alternative extraction method")
        
        browser_tools = agent.get_browser_tools()
        all_content = []
        
        # Process each URL
        for url in urls:
            logging.info(f"Processing URL: {url}")
            
            # Navigate to the URL
            success = await browser_tools.navigate(url)
            if not success:
                logging.error(f"Failed to navigate to {url}")
                continue
                
            # Wait for content to load
            await asyncio.sleep(2)
            
            # Try different selectors for article extraction
            selectors = [
                "article", 
                ".article",
                "div[class*='article']",
                "div[class*='post']",
                "div[class*='content']",
                "main"
            ]
            
            content = None
            for selector in selectors:
                content = await browser_tools.extract_content(selector)
                if content and content.get("success") and (
                    content.get("paragraphs") or 
                    content.get("headings") or 
                    content.get("elements")
                ):
                    logging.info(f"Content extracted with selector: {selector}")
                    break
            
            # If no content was found with specific selectors, extract all page content
            if not content or not content.get("success"):
                logging.info("Trying full page content extraction")
                content = await browser_tools.extract_content()
            
            if content and content.get("success"):
                all_content.append({
                    "url": url,
                    "title": content.get("title", ""),
                    "content": content
                })
        
        # Use LLM to analyze content if we have any
        if all_content:
            logging.info("Analyzing content with LLM")
            llm_manager = agent.get_llm_manager()
            
            # Format content for analysis
            content_text = ""
            for item in all_content:
                content_text += f"URL: {item['url']}\n"
                content_text += f"Title: {item['title']}\n"
                
                if "headings" in item["content"]:
                    content_text += "Headings:\n"
                    for heading in item["content"]["headings"][:10]:  # Limit to first 10
                        content_text += f"- {heading}\n"
                
                if "paragraphs" in item["content"]:
                    content_text += "Content excerpts:\n"
                    for para in item["content"]["paragraphs"][:15]:  # Limit to first 15
                        if len(para) > 50:  # Only include substantial paragraphs
                            content_text += f"{para[:300]}...\n\n"  # Truncate long paragraphs
            
            # Generate analysis prompt
            prompt = f"""
            Task: {instructions}
            
            Analyze the following content for sentiment regarding AI safety concerns:
            
            {content_text}
            
            Provide a detailed analysis covering:
            1. Major concerns identified
            2. Positive developments mentioned
            3. Overall sentiment (positive, negative, neutral, mixed)
            4. Key themes and insights
            5. Summary of findings
            """
            
            # Get analysis from LLM
            analysis = await llm_manager.generate_text(prompt)
            
            result = {
                "success": True,
                "message": "Content analyzed with alternative extraction method",
                "data": all_content,
                "analysis": analysis
            }
    
    return result

def main():
    """Main entry point for the task loop."""
    parser = argparse.ArgumentParser(description="Rabbit Agent Task Loop")
    parser.add_argument("--task", "-t", help="Path to task JSON file", required=True)
    parser.add_argument("--config", "-c", help="Path to config file")
    parser.add_argument("--output", "-o", help="Path to save the result")
    parser.add_argument("--debug", "-d", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    # Load configuration
    config = get_config(args.config)
    if args.debug:
        config["debug_mode"] = True
    
    # Setup logging
    setup_logging(config)
    
    # Load task
    try:
        task_data = load_task(args.task)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error(f"Error loading task: {e}")
        sys.exit(1)
    
    # Initialize agent and memory
    agent = RabbitAgent(
        gemini_api_key=config.get("gemini_api_key"),
        headless=not config.get("debug_mode", False)
    )
    memory = MemoryManager(config)
    
    # Run the task
    logging.info(f"Starting task: {task_data.get('name', 'Unnamed Task')}")
    try:
        start_time = time.time()
        
        # Run async task
        result = asyncio.run(run_task(agent, task_data, memory))
        
        execution_time = time.time() - start_time
        
        # Add metadata to result
        result_with_meta = {
            "task_name": task_data.get("name", "Unnamed Task"),
            "execution_time": execution_time,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "result": result
        }
        
        # Save result
        save_result(result_with_meta, args.output)
        logging.info(f"Task completed in {execution_time:.2f} seconds")
        
        # Close browser
        asyncio.run(agent.close_browser())
        
        return 0
    except Exception as e:
        logging.error(f"Task execution failed: {e}", exc_info=True)
        
        # Ensure browser is closed even on error
        try:
            asyncio.run(agent.close_browser())
        except:
            pass
            
        return 1

if __name__ == "__main__":
    sys.exit(main())