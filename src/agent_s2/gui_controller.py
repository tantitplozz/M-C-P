"""
GOD-TIER AUTOBUY STACK - Agent-S2 GUI Controller
Production-ready browser automation with stealth capabilities
"""

import asyncio
import json
import logging
import random
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
import base64

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from playwright.async_api import async_playwright, Browser, Page, BrowserContext
import undetected_chromedriver as uc
from fake_useragent import UserAgent
import cv2
import numpy as np
from PIL import Image

class StealthMode:
    """Stealth capabilities for browser automation"""

    @staticmethod
    def get_random_user_agent() -> str:
        """Get random user agent"""
        ua = UserAgent()
        return ua.random

    @staticmethod
    def get_chrome_stealth_options() -> ChromeOptions:
        """Get Chrome options with stealth settings"""
        options = ChromeOptions()

        # Basic stealth settings
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-images")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-first-run")
        options.add_argument("--no-default-browser-check")
        options.add_argument("--disable-default-apps")

        # Advanced stealth
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument(f"--user-agent={StealthMode.get_random_user_agent()}")

        # Randomize window size
        width = random.randint(1024, 1920)
        height = random.randint(768, 1080)
        options.add_argument(f"--window-size={width},{height}")

        return options

    @staticmethod
    def human_like_delay(min_delay: float = 0.5, max_delay: float = 2.0) -> float:
        """Generate human-like delay"""
        return random.uniform(min_delay, max_delay)

    @staticmethod
    def human_like_typing_speed() -> float:
        """Generate human-like typing speed"""
        return random.uniform(0.05, 0.15)

class BrowserAutomation:
    """Browser automation wrapper"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.driver = None
        self.playwright = None
        self.browser = None
        self.page = None
        self.context = None

        # Stealth settings
        self.stealth_mode = config.get('agent_s2', {}).get('stealth_mode', True)
        self.human_like_delays = config.get('agent_s2', {}).get('automation', {}).get('human_like_delays', True)
        self.min_delay = config.get('agent_s2', {}).get('automation', {}).get('min_delay', 0.5)
        self.max_delay = config.get('agent_s2', {}).get('automation', {}).get('max_delay', 2.0)

    async def initialize_selenium(self) -> webdriver.Chrome:
        """Initialize Selenium WebDriver"""
        try:
            if self.stealth_mode:
                # Use undetected Chrome driver
                options = StealthMode.get_chrome_stealth_options()
                self.driver = uc.Chrome(options=options)

                # Execute stealth JavaScript
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            else:
                # Regular Chrome driver
                options = ChromeOptions()
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")

                self.driver = webdriver.Chrome(options=options)

            # Set timeouts
            self.driver.implicitly_wait(10)
            self.driver.set_page_load_timeout(30)

            self.logger.info("Selenium WebDriver initialized successfully")
            return self.driver

        except Exception as e:
            self.logger.error(f"Selenium initialization failed: {e}")
            raise

    async def initialize_playwright(self) -> Tuple[Browser, Page]:
        """Initialize Playwright browser"""
        try:
            self.playwright = await async_playwright().start()

            # Launch browser with stealth settings
            if self.stealth_mode:
                self.browser = await self.playwright.chromium.launch(
                    headless=False,
                    args=[
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-blink-features=AutomationControlled",
                        "--disable-extensions",
                        f"--user-agent={StealthMode.get_random_user_agent()}"
                    ]
                )
            else:
                self.browser = await self.playwright.chromium.launch(
                    headless=False,
                    args=["--no-sandbox", "--disable-dev-shm-usage"]
                )

            # Create context
            self.context = await self.browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent=StealthMode.get_random_user_agent() if self.stealth_mode else None
            )

            # Create page
            self.page = await self.context.new_page()

            # Add stealth scripts
            if self.stealth_mode:
                await self.page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined,
                    });

                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5],
                    });

                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['en-US', 'en'],
                    });
                """)

            self.logger.info("Playwright browser initialized successfully")
            return self.browser, self.page

        except Exception as e:
            self.logger.error(f"Playwright initialization failed: {e}")
            raise

    async def navigate_to_url(self, url: str) -> bool:
        """Navigate to URL"""
        try:
            if self.human_like_delays:
                await asyncio.sleep(StealthMode.human_like_delay(self.min_delay, self.max_delay))

            if self.page:
                await self.page.goto(url, wait_until="networkidle")
            else:
                self.driver.get(url)

            self.logger.info(f"Navigated to: {url}")
            return True

        except Exception as e:
            self.logger.error(f"Navigation failed: {e}")
            return False

    async def find_element(self, selector: str, timeout: int = 10) -> Optional[Any]:
        """Find element by CSS selector"""
        try:
            if self.page:
                element = await self.page.wait_for_selector(selector, timeout=timeout * 1000)
                return element
            else:
                wait = WebDriverWait(self.driver, timeout)
                element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                return element

        except Exception as e:
            self.logger.warning(f"Element not found: {selector} - {e}")
            return None

    async def click_element(self, selector: str, timeout: int = 10) -> bool:
        """Click element"""
        try:
            element = await self.find_element(selector, timeout)
            if not element:
                return False

            if self.human_like_delays:
                await asyncio.sleep(StealthMode.human_like_delay(self.min_delay, self.max_delay))

            if self.page:
                await element.click()
            else:
                element.click()

            self.logger.info(f"Clicked element: {selector}")
            return True

        except Exception as e:
            self.logger.error(f"Click failed: {e}")
            return False

    async def type_text(self, selector: str, text: str, timeout: int = 10) -> bool:
        """Type text into element"""
        try:
            element = await self.find_element(selector, timeout)
            if not element:
                return False

            if self.human_like_delays:
                await asyncio.sleep(StealthMode.human_like_delay(self.min_delay, self.max_delay))

            if self.page:
                await element.clear()
                await element.type(text, delay=StealthMode.human_like_typing_speed() * 1000)
            else:
                element.clear()
                for char in text:
                    element.send_keys(char)
                    if self.human_like_delays:
                        time.sleep(StealthMode.human_like_typing_speed())

            self.logger.info(f"Typed text into: {selector}")
            return True

        except Exception as e:
            self.logger.error(f"Type failed: {e}")
            return False

    async def get_text(self, selector: str, timeout: int = 10) -> Optional[str]:
        """Get text from element"""
        try:
            element = await self.find_element(selector, timeout)
            if not element:
                return None

            if self.page:
                text = await element.text_content()
            else:
                text = element.text

            return text.strip() if text else None

        except Exception as e:
            self.logger.error(f"Get text failed: {e}")
            return None

    async def take_screenshot(self, path: str = None) -> Optional[str]:
        """Take screenshot"""
        try:
            if not path:
                path = f"data/screenshots/screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

            Path(path).parent.mkdir(parents=True, exist_ok=True)

            if self.page:
                await self.page.screenshot(path=path)
            else:
                self.driver.save_screenshot(path)

            self.logger.info(f"Screenshot saved: {path}")
            return path

        except Exception as e:
            self.logger.error(f"Screenshot failed: {e}")
            return None

    async def close(self):
        """Close browser"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            if self.driver:
                self.driver.quit()

            self.logger.info("Browser closed successfully")

        except Exception as e:
            self.logger.error(f"Browser close failed: {e}")

class ProductDetection:
    """Product detection and price extraction"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)

    async def detect_product(self, page_content: str, product_name: str) -> Dict[str, Any]:
        """Detect product on page"""
        try:
            # Simple keyword matching (can be enhanced with ML)
            keywords = product_name.lower().split()
            content_lower = page_content.lower()

            matches = sum(1 for keyword in keywords if keyword in content_lower)
            confidence = matches / len(keywords) if keywords else 0

            return {
                "found": confidence > 0.5,
                "confidence": confidence,
                "matches": matches,
                "total_keywords": len(keywords)
            }

        except Exception as e:
            self.logger.error(f"Product detection failed: {e}")
            return {"found": False, "confidence": 0, "error": str(e)}

    async def extract_price(self, browser: BrowserAutomation, price_selectors: List[str]) -> Optional[float]:
        """Extract price from page"""
        try:
            for selector in price_selectors:
                price_text = await browser.get_text(selector)
                if price_text:
                    # Extract numeric value
                    import re
                    price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
                    if price_match:
                        return float(price_match.group())

            return None

        except Exception as e:
            self.logger.error(f"Price extraction failed: {e}")
            return None

class AgentS2Controller:
    """
    Production-ready Agent-S2 GUI Controller
    Advanced browser automation with stealth capabilities
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.browser = BrowserAutomation(config)
        self.product_detector = ProductDetection(config)

        # Website configurations
        self.website_configs = config.get('websites', {})

        # Active sessions
        self.active_sessions: Dict[str, Dict[str, Any]] = {}

        self.logger.info("Agent-S2 Controller initialized")

    async def initialize(self):
        """Initialize the GUI controller"""
        try:
            # Initialize browser (prefer Playwright for production)
            await self.browser.initialize_playwright()

            # Create screenshots directory
            Path("data/screenshots").mkdir(parents=True, exist_ok=True)

            self.logger.info("Agent-S2 Controller initialized successfully")

        except Exception as e:
            self.logger.error(f"Agent-S2 initialization failed: {e}")
            raise

    async def execute_autobuy(self, plan: Dict[str, Any], website: str, product_name: str, max_price: float) -> Dict[str, Any]:
        """Execute autobuy plan"""
        session_id = f"autobuy_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        try:
            # Initialize session
            self.active_sessions[session_id] = {
                "website": website,
                "product_name": product_name,
                "max_price": max_price,
                "plan": plan,
                "started_at": datetime.now(),
                "status": "running",
                "steps_completed": 0,
                "screenshots": []
            }

            session = self.active_sessions[session_id]

            # Get website configuration
            site_config = self.website_configs.get(website, self.website_configs.get('default', {}))

            # Execute plan steps
            for step in plan.get('steps', []):
                self.logger.info(f"Executing step: {step.get('action', 'unknown')}")

                result = await self._execute_step(session, step, site_config)

                if not result.get('success', False):
                    session['status'] = 'failed'
                    session['error'] = result.get('error', 'Step failed')
                    break

                session['steps_completed'] += 1

                # Take screenshot after each step
                screenshot_path = await self.browser.take_screenshot()
                if screenshot_path:
                    session['screenshots'].append(screenshot_path)

            # Final validation
            if session['status'] == 'running':
                session['status'] = 'completed'
                session['completed_at'] = datetime.now()

            return {
                "session_id": session_id,
                "status": session['status'],
                "steps_completed": session['steps_completed'],
                "total_steps": len(plan.get('steps', [])),
                "screenshots": session['screenshots'],
                "execution_time": (session.get('completed_at', datetime.now()) - session['started_at']).total_seconds()
            }

        except Exception as e:
            self.logger.error(f"AutoBuy execution failed: {e}")
            if session_id in self.active_sessions:
                self.active_sessions[session_id]['status'] = 'failed'
                self.active_sessions[session_id]['error'] = str(e)

            return {
                "session_id": session_id,
                "status": "failed",
                "error": str(e)
            }

    async def _execute_step(self, session: Dict[str, Any], step: Dict[str, Any], site_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single step"""
        action = step.get('action', 'unknown')

        try:
            if action == "navigate_to_website":
                return await self._navigate_to_website(session, step, site_config)
            elif action == "search_product":
                return await self._search_product(session, step, site_config)
            elif action == "verify_price":
                return await self._verify_price(session, step, site_config)
            elif action == "add_to_cart":
                return await self._add_to_cart(session, step, site_config)
            elif action == "proceed_to_checkout":
                return await self._proceed_to_checkout(session, step, site_config)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            self.logger.error(f"Step execution failed: {e}")
            return {"success": False, "error": str(e)}

    async def _navigate_to_website(self, session: Dict[str, Any], step: Dict[str, Any], site_config: Dict[str, Any]) -> Dict[str, Any]:
        """Navigate to website"""
        try:
            website = session['website']
            base_url = site_config.get('base_url', f"https://{website}")

            success = await self.browser.navigate_to_url(base_url)

            if success:
                # Wait for page to load
                await asyncio.sleep(3)
                return {"success": True, "url": base_url}
            else:
                return {"success": False, "error": "Navigation failed"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _search_product(self, session: Dict[str, Any], step: Dict[str, Any], site_config: Dict[str, Any]) -> Dict[str, Any]:
        """Search for product"""
        try:
            product_name = session['product_name']

            # Get search selectors
            search_selectors = site_config.get('selectors', {})
            search_box = search_selectors.get('search_box', '#search')
            search_button = search_selectors.get('search_button', 'button[type="submit"]')

            # Type in search box
            type_success = await self.browser.type_text(search_box, product_name)
            if not type_success:
                return {"success": False, "error": "Could not type in search box"}

            # Click search button
            click_success = await self.browser.click_element(search_button)
            if not click_success:
                return {"success": False, "error": "Could not click search button"}

            # Wait for results
            await asyncio.sleep(3)

            return {"success": True, "search_term": product_name}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _verify_price(self, session: Dict[str, Any], step: Dict[str, Any], site_config: Dict[str, Any]) -> Dict[str, Any]:
        """Verify product price"""
        try:
            max_price = session['max_price']

            # Common price selectors
            price_selectors = [
                ".price",
                ".product-price",
                "[data-testid='price']",
                ".a-price .a-offscreen",  # Amazon
                ".shopee-price",  # Shopee
                ".price-current"
            ]

            # Extract price
            current_price = await self.product_detector.extract_price(self.browser, price_selectors)

            if current_price is None:
                return {"success": False, "error": "Could not extract price"}

            # Check if price is within budget
            if current_price <= max_price:
                return {
                    "success": True,
                    "current_price": current_price,
                    "max_price": max_price,
                    "within_budget": True
                }
            else:
                return {
                    "success": False,
                    "error": f"Price too high: {current_price} > {max_price}",
                    "current_price": current_price,
                    "max_price": max_price,
                    "within_budget": False
                }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _add_to_cart(self, session: Dict[str, Any], step: Dict[str, Any], site_config: Dict[str, Any]) -> Dict[str, Any]:
        """Add product to cart"""
        try:
            # Get add to cart selectors
            cart_selectors = site_config.get('selectors', {})
            add_to_cart = cart_selectors.get('add_to_cart', 'button[data-testid="add-to-cart"]')

            # Click add to cart
            click_success = await self.browser.click_element(add_to_cart)
            if not click_success:
                return {"success": False, "error": "Could not click add to cart"}

            # Wait for cart update
            await asyncio.sleep(2)

            return {"success": True, "message": "Product added to cart"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _proceed_to_checkout(self, session: Dict[str, Any], step: Dict[str, Any], site_config: Dict[str, Any]) -> Dict[str, Any]:
        """Proceed to checkout"""
        try:
            # Common checkout selectors
            checkout_selectors = [
                'a[href*="checkout"]',
                'button[data-testid="checkout"]',
                '.checkout-button',
                '#checkout-btn'
            ]

            # Try to find and click checkout button
            for selector in checkout_selectors:
                click_success = await self.browser.click_element(selector, timeout=5)
                if click_success:
                    await asyncio.sleep(2)
                    return {"success": True, "message": "Proceeded to checkout"}

            return {"success": False, "error": "Could not find checkout button"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session status"""
        return self.active_sessions.get(session_id)

    async def cancel_session(self, session_id: str) -> bool:
        """Cancel active session"""
        if session_id in self.active_sessions:
            self.active_sessions[session_id]['status'] = 'cancelled'
            self.active_sessions[session_id]['cancelled_at'] = datetime.now()
            return True
        return False

    async def cleanup(self):
        """Cleanup resources"""
        try:
            await self.browser.close()
            self.logger.info("Agent-S2 Controller cleaned up successfully")
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")
