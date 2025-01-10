#!/usr/bin/env python3

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json

WAIT_TIMEOUT=30

class Authenticator:

    def __init__(self, amazon_url: str = "amazon.co.uk"):
        self.amazon_url = amazon_url


    def __del__(self):
        self._clear_driver()

    # ============================================================
    # Selenium


    def _setup_driver(self):
        user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"

        chrome_options = Options()
        chrome_options.add_argument("window-size=1366,768")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument(f"--user-agent={user_agent}")

        self.driver = webdriver.Chrome(options=chrome_options)
        self._selenium_get("https://www."+self.amazon_url, (By.TAG_NAME, 'body'))



    def _clear_driver(self):
        if hasattr(self, "driver"):
            self.driver.close()


    def _selenium_wait_element(self, element: tuple):
        WebDriverWait(self.driver, WAIT_TIMEOUT).until(EC.presence_of_element_located(element))


    def _selenium_wait_page_ready(self):
        WebDriverWait(self.driver, WAIT_TIMEOUT).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )


    def _selenium_get(self, url: str, wait_for_element: tuple=None, wait_for_page_load: bool=False):
        self.driver.get(url)

        if wait_for_element != None:
            self._selenium_wait_element(wait_for_element)

        if wait_for_page_load:
            self._selenium_wait_page_ready()


    def _get_session_data(self):
        return self.driver.get_cookies()


    # ============================================================
    # Perform authentication


    def run(self):
        print("\nTo authenticate with Amazon, you need to login via the browser")
        self._setup_driver()
        session = self._get_session_data()
        #TODO: Return session json

    # ============================================================
