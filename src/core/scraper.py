import undetected_chromedriver as uc
import random
import time
import logging
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from src.utils.helpers import clean_text


class AmazonScraper:
    def __init__(self, config):
        """Initializes the scraper with configurations and CSS selectors from config."""
        self.logger = logging.getLogger(__name__)
        self.driver = None
        self.config = config

        self.selectors = self.config.get('amazon', {})
        browser_cfg = self.config.get('browser', {})
        self.min_delay = browser_cfg.get('min_delay', 2)
        self.max_delay = browser_cfg.get('max_delay', 5)

    def init_driver(self):
        """
        Starts an undetected Chrome instance with stealth arguments.
        Raises an exception if the browser fails to launch so the caller
        is aware instead of silently receiving a None driver.
        """
        options = uc.ChromeOptions()
        options.add_argument('--incognito')
        options.add_argument('--start-maximized')
        options.add_argument('--disable-popup-blocking')
        options.add_argument('--lang=en-US')
        options.add_argument("--disable-notifications")
        try:
            self.driver = uc.Chrome(options=options)
            self.logger.info("Browser engine started successfully.")
        except Exception as e:
            self.logger.error(f"Failed to start browser engine: {e}")
            raise

    def get_multiple_pages(self, keyword, max_pages=3):
        """
        Iterates through the given number of search result pages,
        scraping product data from each one and returning a combined list.
        """
        all_results = []
        for current_page in range(1, max_pages + 1):
            self.logger.info(f"Processing page {current_page} of {max_pages}...")
            self.search(keyword, page=current_page)
            self._scroll_to_bottom()
            page_results = self.extract_products()
            all_results.extend(page_results)
            self.logger.info(f"Page {current_page} complete. Found {len(page_results)} items.")
        return all_results

    def search(self, keyword, page=1):
        """Constructs the Amazon search URL for the given keyword and page number, then navigates to it."""
        base = self.selectors.get('base_url', 'https://www.amazon.com.tr')
        endpoint = self.selectors.get('search_endpoint', '/s?k=')
        full_url = f"{base}{endpoint}{keyword.replace(' ', '+')}&page={page}"
        self.logger.info(f"Searching for '{keyword}' on page {page}...")
        return self.navigate_to_page(full_url)

    def navigate_to_page(self, url):
        """
        Navigates to the given URL, applies a human-like delay, clears
        overlays, handles the cookie dismiss button, and waits for product
        cards to appear in the DOM before returning the page source.
        """
        if not self.driver:
            self.init_driver()

        self.logger.info(f"Navigating to URL: {url}")
        self.driver.get(url)
        self._human_delay()

        self._clear_overlays()

        dismiss = self.selectors.get('dismiss_btn')
        if dismiss:
            try:
                wait = WebDriverWait(self.driver, 4)
                btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, str(dismiss))))
                btn.click()
                self.logger.info("Dismiss button clicked.")
            except Exception:
                self.logger.debug("Dismiss button not detected or already closed.")

        card_sel = self.selectors.get('product_card')
        if card_sel:
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, str(card_sel)))
                )
                self.logger.info("Product cards localized on page.")
            except TimeoutException:
                self.logger.warning("Timeout: No product cards found on this page.")

        return self.driver.page_source

    def extract_products(self):
        """
        Finds all product cards on the current page and extracts
        title, price, and rating from each one. Cards that fail to
        parse are skipped and logged at debug level.
        """
        product_list = []
        card_sel = self.selectors.get('product_card')
        title_sel = self.selectors.get('title')
        price_sel = self.selectors.get('price')
        rating_sel = self.selectors.get('rating')

        self.logger.info(f"Extracting products using selector: {card_sel}")
        cards = self.driver.find_elements(By.CSS_SELECTOR, str(card_sel))

        if not cards:
            return []

        for card in cards:
            try:
                try:
                    title_elem = card.find_element(By.CSS_SELECTOR, str(title_sel))
                    title = title_elem.get_attribute("innerText") or title_elem.text
                    title = clean_text(title)
                except Exception:
                    title = "Unknown Product"

                try:
                    price_element = card.find_element(By.CSS_SELECTOR, str(price_sel))
                    price = price_element.get_attribute("innerText") or price_element.text
                except Exception:
                    price = "0"

                try:
                    rating = card.find_element(By.CSS_SELECTOR, str(rating_sel)).get_attribute("innerText")
                except Exception:
                    rating = "0"

                if title != "Unknown Product":
                    product_list.append({
                        "title": title,
                        "price": price,
                        "rating": rating
                    })
            except Exception as e:
                self.logger.debug(f"Skipping card due to unexpected error: {e}")
                continue

        return product_list

    def _human_delay(self):
        """Pauses execution for a random duration between min and max delay to simulate human behavior."""
        wait_time = random.uniform(self.min_delay, self.max_delay)
        self.logger.info(f"Waiting for {wait_time:.2f}s...")
        time.sleep(wait_time)

    def _scroll_to_bottom(self):
        """Incrementally scrolls the page to trigger lazy-loaded content before extraction."""
        self.logger.info("Executing incremental scroll...")
        for i in range(1, 6):
            self.driver.execute_script(
                f"window.scrollTo(0, (document.body.scrollHeight - 2000) * {i / 5});"
            )
            time.sleep(random.uniform(0.7, 1.2))

    def _clear_overlays(self):
        """Sends an ESC keypress to the page body to dismiss translation bars or popup overlays."""
        try:
            self.logger.info("Clearing overlays via ESC key.")
            self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
            time.sleep(1)
        except Exception as e:
            self.logger.debug(f"Overlay cleanup skipped: {e}")

    def close_driver(self):
        """Safely quits the Chrome driver and releases the reference."""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
        except Exception as e:
            self.logger.warning(f"Driver could not be closed cleanly: {e}")
            self.driver = None