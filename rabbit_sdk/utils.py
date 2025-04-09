#Rabbit/rabbit_sdk/utils.py
"""
Utility functions for the Rabbit Agent.
"""
import asyncio

async def extract_text_from_page(page):
    """
    Extract the HTML content from a page.
    
    Args:
        page: The playwright page object.
        
    Returns:
        str: The HTML content of the page.
    """
    try:
        # Get the HTML content of the page
        content = await page.content()
        return content
    except Exception as e:
        print(f"Error extracting text from page: {e}")
        return ""
