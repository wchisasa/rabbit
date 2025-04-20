#Rabbit/rabbit_sdk/utils.py
"""
Utility functions for the Rabbit SDK.
Includes functions for text extraction, data sanitization, and other common operations.
"""

import os
import json
import logging
import time
import datetime
import hashlib
from typing import Dict, List, Any, Optional, Union

# Set up logging 
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='./logs/rabbit.log',  # Add a log file instead of console output
    filemode='a'

)
logger = logging.getLogger(__name__)

def setup_environment():
    """Set up necessary environment variables and paths."""
    # Create cache directory if it doesn't exist
    os.makedirs("./cache", exist_ok=True)
    os.makedirs("./logs", exist_ok=True)
    logger.info("Environment setup complete")

def generate_hash(data: str) -> str:
    """Generate a hash for caching or identification purposes."""
    return hashlib.md5(data.encode()).hexdigest()

def load_json(file_path: str) -> Dict:
    """Load JSON data from a file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Error loading JSON from {file_path}: {e}")
        return {}

def save_json(data: Dict, file_path: str) -> bool:
    """Save data to a JSON file."""
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving JSON to {file_path}: {e}")
        return False

def retry_with_exponential_backoff(func, max_retries: int = 3, base_delay: float = 1.0):
    """Decorator for retrying a function with exponential backoff."""
    def wrapper(*args, **kwargs):
        retries = 0
        while retries < max_retries:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                retries += 1
                if retries >= max_retries:
                    logger.error(f"Function {func.__name__} failed after {max_retries} retries: {e}")
                    raise
                wait_time = base_delay * (2 ** (retries - 1))
                logger.warning(f"Retry {retries}/{max_retries} for {func.__name__} in {wait_time:.2f}s: {e}")
                time.sleep(wait_time)
    return wrapper


def save_analysis_results(analysis_data: Dict[str, Any], task_id: Optional[str] = None) -> str:
    """
    Save analysis results to a JSON file in the results directory.
    
    Args:
        analysis_data: The analysis data to save
        task_id: Optional task identifier to include in the filename
        
    Returns:
        str: Path to the saved file
    """
    # Create results directory if it doesn't exist
    results_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sentiment_results")
    os.makedirs(results_dir, exist_ok=True)
    
    # Generate filename with timestamp or task_id
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"analysis_{task_id or timestamp}.json"
    filepath = os.path.join(results_dir, filename)
    
    # Write formatted JSON to file
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(analysis_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Analysis results saved to {filepath}")
    return filepath

def format_browser_content(content: Dict) -> str:
    """Format browser content for LLM processing."""
    if not content:
        return "No content available"
    
    formatted_content = []
    
    if 'title' in content:
        formatted_content.append(f"Page Title: {content['title']}")
    
    if 'url' in content:
        formatted_content.append(f"URL: {content['url']}")
    
    if 'text' in content:
        formatted_content.append("Content:")
        formatted_content.append(content['text'])
    
    if 'links' in content:
        formatted_content.append("Links:")
        for link in content['links'][:10]:  # Limit to first 10 links
            formatted_content.append(f"- {link.get('text', 'No text')}: {link.get('href', 'No URL')}")
    
    return "\n".join(formatted_content)

def extract_elements_from_page(page_content: Dict, element_type: str) -> List[Dict]:
    """Extract specific elements from page content."""
    elements = []
    
    if element_type == "links" and "links" in page_content:
        return page_content["links"]
    elif element_type == "forms" and "forms" in page_content:
        return page_content["forms"]
    elif element_type == "buttons" and "buttons" in page_content:
        return page_content["buttons"]
    elif element_type == "inputs" and "inputs" in page_content:
        return page_content["inputs"]
    
    return elements

async def extract_text_from_page(page):
    """Extract text content from a browser page.""" 
    try:
        text_content = await page.evaluate('() => document.body.innerText')
        return text_content
    except Exception as e:
        logger.error(f"Error extracting text from page: {e}")
        return ""

def sanitize_input(text: str) -> str:
    """Sanitize input to remove potentially harmful characters."""
    # Basic sanitization to prevent command injection
    return text.replace(';', '').replace('&', '').replace('|', '')

def parse_action_response(response: str) -> Dict:
    """Parse LLM response into a structured action format."""
    try:
        # Try to parse as JSON first
        if '{' in response and '}' in response:
            json_str = response[response.find('{'):response.rfind('}')+1]
            return json.loads(json_str)
        
        # Simple parsing for action:parameter format
        action_dict = {}
        lines = response.strip().split('\n')
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                action_dict[key.strip()] = value.strip()
        
        return action_dict
    except Exception as e:
        logger.error(f"Error parsing action response: {e}")
        return {"action": "error", "error": str(e)}
        

def cleanup_resources():
    """Clean up temporary files and resources."""
    try:
        # Clean up temporary files that are older than 1 day
        cache_dir = "./cache"
        if os.path.exists(cache_dir):
            current_time = time.time()
            for filename in os.listdir(cache_dir):
                file_path = os.path.join(cache_dir, filename)
                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getmtime(file_path)
                    if file_age > 86400:  # 24 hours in seconds
                        os.remove(file_path)
        logger.info("Resource cleanup complete")
        return True
    except Exception as e:
        logger.error(f"Error during resource cleanup: {e}")
        return False