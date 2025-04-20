# Rabbit/rabbit_sdk/tools/browser_tools.py

"""Browser tools for interacting with web pages through the browser controller."""

from typing import Dict, List, Optional, Any, Union
import json
import time
import logging
from ..browser_controller import BrowserController

logger = logging.getLogger(__name__)

class BrowserTools:
    """Tools for interacting with web elements and browser functionality.""" 
    
    def __init__(self, browser_controller: BrowserController):
        """Initialize with a browser controller instance."""
        self.browser = browser_controller
        
    async def navigate(self, url: str) -> bool:
        """Navigate to the specified URL.
        
        Args:
            url: The URL to navigate to
            
        Returns:
            bool: Success status of the navigation
        """
        return await self.browser.navigate(url)
    
    async def get_current_url(self) -> str:
        """Get the current page URL.
        
        Returns:
            str: The current URL
        """
        return await self.browser.get_current_url()
    
    async def get_page_title(self) -> str:
        """Get the current page title.
        
        Returns:
            str: The page title
        """
        return await self.browser.get_page_title()
    
    async def get_page_content(self) -> str:
        """Get the HTML content of the current page.
        
        Returns:
            str: The page HTML content
        """
        return await self.browser.get_page_content()
    
    async def get_page_text(self) -> str:
        """Get the visible text content of the current page.
        
        Returns:
            str: The visible text content
        """
        return await self.browser.get_page_text()
    
    async def find_element(self, selector: str, by: str = "css") -> Optional[Dict[str, Any]]:
        """Find an element on the page.
        
        Args:
            selector: The selector string
            by: The selector type (css, xpath, id, etc.)
            
        Returns:
            Optional[Dict[str, Any]]: Element information or None if not found
        """
        return await self.browser.find_element(selector, by)
    
    async def find_elements(self, selector: str, by: str = "css") -> List[Dict[str, Any]]:
        """Find all elements matching the selector.
        
        Args:
            selector: The selector string
            by: The selector type (css, xpath, id, etc.)
            
        Returns:
            List[Dict[str, Any]]: List of elements
        """
        return await self.browser.find_elements(selector, by)
    
    async def extract_content(self, selector: str = None) -> Dict[str, Any]:
        """Extract content from the page for sentiment analysis.
        
        Args:
            selector: Optional selector to focus extraction (if None, extracts all content)
            
        Returns:
            Dict[str, Any]: Extracted content with structure
        """
        try:
            # If selector provided, try to extract those elements
            if selector:
                elements = await self.browser.extract_elements(selector)
                if elements and len(elements) > 0:
                    return {
                        "success": True,
                        "elements": elements,
                        "count": len(elements)
                    }
            
            # If no selector or no elements found, perform full content extraction
            result = await self.browser.analyze_page_sentiment()
            if result["success"]:
                return {
                    "success": True,
                    "title": result["title"],
                    "headings": result["headings"],
                    "paragraphs": result["paragraphs"],
                    "full_text": result["full_text"]
                }
            
            return result
        except Exception as e:
            logger.error(f"Error extracting content: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def click(self, selector: str, by: str = "css") -> bool:
        """Click on an element.
        
        Args:
            selector: The selector string
            by: The selector type (css, xpath, id, etc.)
            
        Returns:
            bool: Success status of the click
        """
        return await self.browser.click(selector, by)
    
    async def type_text(self, selector: str, text: str, by: str = "css") -> bool:
        """Type text into an input element.
        
        Args:
            selector: The selector for the input element
            text: The text to type
            by: The selector type (css, xpath, id, etc.)
            
        Returns:
            bool: Success status
        """
        return await self.browser.type_text(selector, text, by)
    
    async def wait_for_element(self, selector: str, by: str = "css", timeout: int = 10) -> bool:
        """Wait for an element to appear.
        
        Args:
            selector: The selector string
            by: The selector type (css, xpath, id, etc.)
            timeout: Maximum time to wait in seconds
            
        Returns:
            bool: True if element appears within timeout, False otherwise
        """
        return await self.browser.wait_for_content(self.browser.page, selector, timeout * 1000)
    
    async def take_screenshot(self, path: Optional[str] = None) -> Union[bytes, None]:
        """Take a screenshot of the current page.
        
        Args:
            path: File path to save the screenshot (optional)
            
        Returns:
            Union[bytes, None]: Screenshot bytes or None if saved to file
        """
        return await self.browser.take_screenshot(self.browser.page, path)