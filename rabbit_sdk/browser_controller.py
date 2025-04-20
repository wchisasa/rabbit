# Rabbit/rabbit_sdk/browser_controller.py

"""
Browser controller module for managing browser instances and pages.
Handles multiple browser instances using Playwright with stealth options.
Includes retry logic and proper persistent context handling. 
"""

import asyncio
import logging
from typing import Optional, Dict, List, Any, Union
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BrowserController:
    def __init__(self, browser_type: str = "chromium", headless: bool = False, 
                 profile_dir: Optional[str] = None, keep_open: bool = False):
        """
        Initialize the browser controller.
        
        Args:
            browser_type (str): Type of browser to use ("chromium", "firefox", "webkit")
            headless (bool): Whether to run the browser in headless mode
            profile_dir (str, optional): Path to browser profile directory
            keep_open (bool): Whether to keep the browser open after completing tasks
        """
        self.browser_type = browser_type
        self.headless = headless
        self.profile_dir = profile_dir
        self.keep_open = keep_open
        self.browser = None
        self.playwright = None
        self.context = None
        self.page = None
        self.max_retries = 3
        self.retry_delay = 2  # seconds

    async def initialize_browser(self):
        """Initialize the browser instance with stealth settings."""
        try:
            self.playwright = await async_playwright().start()
            
            # Configure browser launch options
            browser_options = {
                "headless": self.headless,
                "args": [
                    "--disable-blink-features=AutomationControlled",
                    "--disable-features=IsolateOrigins,site-per-process",
                    "--disable-site-isolation-trials"
                ]
            }
            
            # Add user data directory if specified
            if self.profile_dir:
                browser_options["user_data_dir"] = self.profile_dir
                
            # Launch the specified browser type
            if self.browser_type.lower() == "chromium":
                self.browser = await self.playwright.chromium.launch(**browser_options)
            elif self.browser_type.lower() == "firefox":
                self.browser = await self.playwright.firefox.launch(**browser_options)
            elif self.browser_type.lower() == "webkit":
                self.browser = await self.playwright.webkit.launch(**browser_options)
            else:
                raise ValueError(f"Unsupported browser type: {self.browser_type}")
                
            # Create a new browser context
            context_options = {
                "viewport": {"width": 1280, "height": 800},
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            self.context = await self.browser.new_context(**context_options)
            
            # Apply stealth mode JavaScript to avoid detection
            await self._apply_stealth_mode()
            
            logger.debug(f"Browser initialized: {self.browser_type}")
            return self.context
            
        except Exception as e:
            logger.error(f"Error initializing browser: {str(e)}", exc_info=True)
            raise

    async def _apply_stealth_mode(self):
        """Apply stealth mode JavaScript to avoid detection."""
        if not self.context:
            logger.warning("Cannot apply stealth mode: browser context not initialized")
            return
            
        # Basic stealth script to evade bot detection
        stealth_js = """
        () => {
            // Override properties to avoid detection
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false,
            });
            
            // Remove automation-related properties
            delete navigator.__proto__.webdriver;
            
            // Hide automation artifacts
            window.chrome = { runtime: {} };
            window.navigator.chrome = { runtime: {} };
            
            // Pass basic bot tests
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
            );
        }
        """
        
        # Apply the stealth script to each new page
        await self.context.add_init_script(stealth_js)

    async def open_page(self, url: str) -> Page:
        """
        Open a new page with the specified URL with retry logic.
        
        Args:
            url (str): The URL to navigate to
            
        Returns:
            Page: The page object
        """
        if not self.browser:
            await self.initialize_browser()
            
        self.page = await self.context.new_page()
        
        # Set page timeout
        self.page.set_default_timeout(80000)  # 60 seconds
        
        # Enable JavaScript and cookies
        await self.page.context.clear_cookies()
        
        # Configure console message handling
        self.page.on("console", lambda msg: logger.debug(f"Console {msg.type}: {msg.text}"))
        
        # Apply retry logic for navigation
        retry_count = 0
        while retry_count < self.max_retries:
            try:
                response = await self.page.goto(
                    url, 
                    wait_until="domcontentloaded", 
                    timeout=70000
                )
                
                if response and response.ok:
                    # Wait for page to be fully loaded
                    await self.page.wait_for_load_state("networkidle", timeout=80000)
                    logger.debug(f"Successfully loaded page: {url}")
                    break
                else:
                    status = response.status if response else "unknown"
                    logger.warning(f"HTTP {status} when loading {url}, retrying...")
                    retry_count += 1
                    await asyncio.sleep(self.retry_delay)
                    
            except Exception as e:
                logger.warning(f"Error navigating to {url}: {e}, retry {retry_count+1}/{self.max_retries}")
                retry_count += 1
                await asyncio.sleep(self.retry_delay)
                
        if retry_count >= self.max_retries:
            logger.error(f"Failed to load {url} after {self.max_retries} attempts")
            
        return self.page
    
    async def execute_javascript(self, page: Page, script: str):
        """
        Execute JavaScript on the page.
        
        Args:
            page (Page): The page to execute script on
            script (str): JavaScript code to execute
            
        Returns:
            Any: Result of script execution
        """
        try:
            result = await page.evaluate(script)
            return result
        except Exception as e:
            logger.error(f"Error executing JavaScript: {str(e)}")
            return None
    
    async def wait_for_content(self, page: Page, selector: str, timeout: int = 70000):
        """
        Wait for content to load based on selector.
        
        Args:
            page (Page): The page to wait on
            selector (str): CSS selector to wait for
            timeout (int): Maximum time to wait in milliseconds
            
        Returns:
            bool: True if selector found, False if timeout
        """
        try:
            await page.wait_for_selector(selector, timeout=timeout)
            return True
        except Exception as e:
            logger.warning(f"Timeout waiting for selector {selector}: {e}")
            return False
    
    async def take_screenshot(self, page: Page, path: str = None):
        """
        Take a screenshot of the current page.
        
        Args:
            page (Page): The page to screenshot
            path (str, optional): Path to save the screenshot to
            
        Returns:
            bytes: Screenshot as bytes if path is None, otherwise None
        """
        try:
            if path:
                await page.screenshot(path=path, full_page=True)
                logger.debug(f"Screenshot saved to {path}")
                return None
            else:
                screenshot_bytes = await page.screenshot(full_page=True)
                return screenshot_bytes
        except Exception as e:
            logger.error(f"Error taking screenshot: {str(e)}")
            return None
    
    async def navigate(self, url: str) -> bool:
        """Navigate to the specified URL.
        
        Args:
            url: The URL to navigate to
            
        Returns:
            bool: Success status of the navigation
        """
        try:
            if not self.page:
                self.page = await self.open_page(url)
                return True
            
            response = await self.page.goto(url, wait_until="domcontentloaded", timeout=70000)
            await self.page.wait_for_load_state("networkidle", timeout=70000)
            return response and response.ok
        except Exception as e:
            logger.error(f"Error navigating to {url}: {str(e)}")
            return False
    
    async def get_current_url(self) -> str:
        """Get the current page URL."""
        return self.page.url if self.page else ""
    
    async def get_page_title(self) -> str:
        """Get the current page title."""
        return await self.page.title() if self.page else ""
    
    async def get_page_content(self) -> str:
        """Get the HTML content of the current page."""
        return await self.page.content() if self.page else ""
    
    async def get_page_text(self) -> str:
        """Get the visible text content of the current page."""
        if not self.page:
            return ""
        
        # Extract text using JavaScript for better reliability
        script = """
        () => {
            return document.body.innerText;
        }
        """
        return await self.page.evaluate(script)
    
    async def find_element(self, selector: str, by: str = "css") -> Optional[Dict[str, Any]]:
        """Find an element on the page."""
        if not self.page:
            return None
        
        try:
            if by.lower() == "css":
                element = await self.page.query_selector(selector)
            elif by.lower() == "xpath":
                element = await self.page.query_selector_all(f"xpath={selector}")
                element = element[0] if element else None
            else:
                logger.warning(f"Unsupported selector type: {by}")
                return None
                
            if not element:
                return None
                
            text = await element.inner_text()
            html = await element.inner_html()
            
            return {
                "text": text,
                "html": html,
                "exists": True
            }
        except Exception as e:
            logger.error(f"Error finding element {selector}: {str(e)}")
            return None
    
    async def find_elements(self, selector: str, by: str = "css") -> List[Dict[str, Any]]:
        """Find all elements matching the selector."""
        if not self.page:
            return []
        
        try:
            if by.lower() == "css":
                elements = await self.page.query_selector_all(selector)
            elif by.lower() == "xpath":
                elements = await self.page.query_selector_all(f"xpath={selector}")
            else:
                logger.warning(f"Unsupported selector type: {by}")
                return []
                
            result = []
            for element in elements:
                text = await element.inner_text()
                html = await element.inner_html()
                
                result.append({
                    "text": text,
                    "html": html,
                    "exists": True
                })
                
            return result
        except Exception as e:
            logger.error(f"Error finding elements {selector}: {str(e)}")
            return []
    
    async def extract_elements(self, selector: str) -> List[Dict[str, Any]]:
        """Extract elements with their text and attributes from the page.
        
        Args:
            selector (str): CSS selector
            
        Returns:
            List[Dict[str, Any]]: List of element data dictionaries
        """
        if not self.page:
            return []
        
        try:
            # Use JavaScript for more reliable extraction
            script = f"""
            () => {{
                const elements = Array.from(document.querySelectorAll('{selector}'));
                return elements.map(el => {{
                    // Get all attributes
                    const attributes = Array.from(el.attributes).reduce((acc, attr) => {{
                        acc[attr.name] = attr.value;
                        return acc;
                    }}, {{}});
                    
                    return {{
                        text: el.innerText,
                        html: el.innerHTML,
                        tagName: el.tagName.toLowerCase(),
                        attributes: attributes,
                        href: el.tagName.toLowerCase() === 'a' ? el.href : null
                    }};
                }});
            }}
            """
            
            elements = await self.page.evaluate(script)
            
            if not elements:
                # Try alternative selectors
                alternative_selectors = [
                    # Try broader article selectors
                    "article h2 a",
                    "article h3 a",
                    ".article h2 a",
                    ".article h3 a",
                    ".card a",
                    ".post a",
                    "article a",
                    # More specific for common news sites
                    "div[class*='article'] h2 a",
                    "div[class*='article'] h3 a",
                    "div[class*='post'] h2 a",
                    "div[class*='post'] h3 a",
                    "div[class*='card'] h2 a",
                    "div[class*='card'] h3 a",
                    # Fall back to any heading with link
                    "h2 a",
                    "h3 a"
                ]
                
                for alt_selector in alternative_selectors:
                    logger.debug(f"Trying alternative selector: {alt_selector}")
                    elements = await self.page.evaluate(f"""
                    () => {{
                        const elements = Array.from(document.querySelectorAll('{alt_selector}'));
                        return elements.map(el => {{
                            const attributes = Array.from(el.attributes).reduce((acc, attr) => {{
                                acc[attr.name] = attr.value;
                                return acc;
                            }}, {{}});
                            
                            return {{
                                text: el.innerText,
                                html: el.innerHTML,
                                tagName: el.tagName.toLowerCase(),
                                attributes: attributes,
                                href: el.tagName.toLowerCase() === 'a' ? el.href : null
                            }};
                        }});
                    }}
                    """)
                    
                    if elements and len(elements) > 0:
                        logger.debug(f"Found {len(elements)} elements with alternative selector {alt_selector}")
                        break
            
            return elements
        except Exception as e:
            logger.error(f"Error extracting elements {selector}: {str(e)}")
            return []
    
    async def click(self, selector: str, by: str = "css") -> bool:
        """Click on an element."""
        if not self.page:
            return False
        
        try:
            if by.lower() == "css":
                await self.page.click(selector)
            elif by.lower() == "xpath":
                await self.page.click(f"xpath={selector}")
            else:
                logger.warning(f"Unsupported selector type: {by}")
                return False
                
            return True
        except Exception as e:
            logger.error(f"Error clicking element {selector}: {str(e)}")
            return False
    
    async def type_text(self, selector: str, text: str, by: str = "css") -> bool:
        """Type text into an input element."""
        if not self.page:
            return False
        
        try:
            if by.lower() == "css":
                await self.page.fill(selector, text)
            elif by.lower() == "xpath":
                await self.page.fill(f"xpath={selector}", text)
            else:
                logger.warning(f"Unsupported selector type: {by}")
                return False
                
            return True
        except Exception as e:
            logger.error(f"Error typing text in element {selector}: {str(e)}")
            return False
    
    async def analyze_page_sentiment(self, keywords: List[str] = None) -> Dict[str, Any]:
        """
        Analyze page content to extract sentiment information.
        
        Args:
            keywords (List[str], optional): Keywords to focus on, if None analyzes all content
            
        Returns:
            Dict[str, Any]: Dictionary with sentiment analysis results
        """
        if not self.page:
            return {
                "success": False,
                "error": "No active page"
            }
            
        try:
            # Extract all text content from the page
            page_text = await self.get_page_text()
            
            # Extract article titles/headings
            headings_script = """
            () => {
                const headings = Array.from(document.querySelectorAll('h1, h2, h3'));
                return headings.map(h => h.innerText.trim()).filter(t => t.length > 0);
            }
            """
            headings = await self.page.evaluate(headings_script)
            
            # Extract article paragraphs
            paragraphs_script = """
            () => {
                const paragraphs = Array.from(document.querySelectorAll('p'));
                return paragraphs.map(p => p.innerText.trim()).filter(t => t.length > 0);
            }
            """
            paragraphs = await self.page.evaluate(paragraphs_script)
            
            return {
                "success": True,
                "url": self.page.url,
                "title": await self.page.title(),
                "headings": headings,
                "paragraphs": paragraphs,
                "full_text": page_text
            }
        except Exception as e:
            logger.error(f"Error analyzing page sentiment: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def close_browser(self):
        """Close the browser instance and cleanup resources."""
        try:
            if self.context:
                await self.context.close()
                self.context = None
                logger.debug("Browser context closed")
                
            if self.browser:
                await self.browser.close()
                self.browser = None
                logger.debug("Browser closed")
                
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
                logger.debug("Playwright stopped")
                
        except Exception as e:
            logger.error(f"Error closing browser resources: {str(e)}")