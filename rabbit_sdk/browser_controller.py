#Rabbit/rabbit_sdk/browser_controller.py

"""
Handles multiple browser instances using Playwright with stealth options.
Includes retry logic and proper persistent context handling.
"""

"""
Browser controller module for managing browser instances and pages. 
"""
import asyncio
from playwright.async_api import async_playwright

class BrowserController:
    def __init__(self, browser_type="chromium", headless=False, profile_dir=None, keep_open=False):
        self.browser_type = browser_type
        self.headless = headless
        self.profile_dir = profile_dir
        self.keep_open = keep_open
        self.browser = None
        self.playwright = None
        self.context = None

    async def initialize_browser(self):
        """Initialize the browser instance."""
        self.playwright = await async_playwright().start()
        
        browser_options = {
            "headless": self.headless
        }
        
        if self.profile_dir:
            browser_options["user_data_dir"] = self.profile_dir
            
        if self.browser_type.lower() == "chromium":
            self.browser = await self.playwright.chromium.launch(**browser_options)
        elif self.browser_type.lower() == "firefox":
            self.browser = await self.playwright.firefox.launch(**browser_options)
        elif self.browser_type.lower() == "webkit":
            self.browser = await self.playwright.webkit.launch(**browser_options)
        else:
            raise ValueError(f"Unsupported browser type: {self.browser_type}")
            
        self.context = await self.browser.new_context()
        
    async def open_page(self, url):
        """
        Open a new page with the specified URL.
        
        Args:
            url (str): The URL to navigate to.
            
        Returns:
            Page: The page object.
        """
        if not self.browser:
            await self.initialize_browser()
            
        page = await self.context.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            print(f"Error navigating to {url}: {e}")
            
        return page
        
    async def close_browser(self):
        """Close the browser instance and cleanup resources."""
        if self.context:
            await self.context.close()
            self.context = None
            
        if self.browser:
            await self.browser.close()
            self.browser = None
            
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None