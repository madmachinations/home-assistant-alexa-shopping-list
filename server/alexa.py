#!/usr/bin/env python3

from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
import time
import json
import os

WAIT_TIMEOUT=30

class AlexaShoppingList:

    def __init__(self, amazon_url: str = "amazon.co.uk", cookies_path: str = ""):
        self.amazon_url = amazon_url
        self.cookies_path = cookies_path
        self._setup_driver()


    def __del__(self):
        self._clear_driver()

    # ============================================================
    # Helpers


    def _get_file_location(self):
        return os.path.dirname(os.path.realpath(__file__))

    def _is_debug_mode(self):
        return os.environ.get("ALEXA_SHOPPING_LIST_DEBUG", "0") == "1"

    # ============================================================
    # Selenium


    def _setup_driver(self):
        user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"

        chrome_options = Options()
        if(self._is_debug_mode() == False):
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("window-size=1366,768")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument(f"--user-agent={user_agent}")

        driver_path = os.environ.get("CHROME_DRIVER", "")
        if driver_path != "":
            service = webdriver.ChromeService(executable_path=driver_path)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
        else:
            self.driver = webdriver.Chrome(options=chrome_options)

        self.is_authenticated = False
        self._selenium_get("https://www."+self.amazon_url, (By.TAG_NAME, 'body'))
        self._load_cookies()

        if len(self.driver.find_elements(By.ID, 'nav-backup-backup')) > 0:
            # I don't know why this is, but random amazon displays some weird page instead of the usual home page.
            # This solution only works for versions of amazon in english, so would cause problems for other languages.
            # But this only happens rarely, so... whatever.
            self.driver.find_element(By.CLASS_NAME, "nav-bb-right").find_element(By.LINK_TEXT, "Your Account").click()
            time.sleep(5)

        if len(self.driver.find_elements(By.CLASS_NAME, 'nav-action-signin-button')) > 0:
            self.driver.find_element(By.ID, 'nav-link-accountList').click()
            time.sleep(5)
        else:
            self.is_authenticated = True



    def _clear_driver(self):
        if hasattr(self, "driver"):
            self.save_session()
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


    def _cookie_cache_path(self):
        if self.cookies_path != "":
            return os.path.join(self.cookies_path, "cookies.json")
        return os.path.join(self._get_file_location(), "cookies.json")


    def _load_cookies(self):
        if os.path.exists(self._cookie_cache_path()):

            with open(self._cookie_cache_path(), 'r') as file:
                cookies = json.load(file)

            for cookie in cookies:
                self.driver.add_cookie(cookie)

            self.driver.refresh()
            self._selenium_wait_element((By.ID, 'nav-link-accountList'))


    # ============================================================
    # Authentication


    def requires_login(self):
        if 'ap/signin' in self.driver.current_url:
            return True

        if len(self.driver.find_elements(By.CLASS_NAME, 'nav-action-signin-button')) > 0:
            return True

        if self.is_authenticated == False:
            return True

        return False
    

    def save_session(self):
        if self.is_authenticated:
            with open(self._cookie_cache_path(), 'w') as file:
                json.dump(self.driver.get_cookies(), file)

    # ============================================================
    # Alexa lists


    def _ensure_driver_is_on_alexa_list(self, refresh: bool = False):
        list_url = "https://www."+self.amazon_url+"/alexaquantum/sp/alexaShoppingList?ref=nav_asl"
        if self.driver.current_url != list_url:
            self._selenium_get(list_url, (By.CLASS_NAME, 'virtual-list'))
        elif refresh == True:
            self.driver.refresh()
            self._selenium_wait_element((By.CLASS_NAME, 'virtual-list'))


    def get_alexa_list(self, refresh: bool = True):
        self._ensure_driver_is_on_alexa_list(refresh)
        time.sleep(5)

        list_container = self.driver.find_element(By.CLASS_NAME, 'virtual-list')

        found = []
        last = None
        while True:
            list_items = list_container.find_elements(By.CLASS_NAME, 'item-title')
            for item in list_items:
                if item.get_attribute('innerText') not in found:
                    found.append(item.get_attribute('innerText'))
            if not list_items or last == list_items[-1]:
                # We've reached the end
                break
            last = list_items[-1]
            self.driver.execute_script("arguments[0].scrollIntoView();", last)
            time.sleep(1)

        if not refresh:
            # Now let's scroll back to the top
            first = None
            while True:
                list_items = list_container.find_elements(By.CLASS_NAME, 'item-title')
                if not list_items or first == list_items[0]:
                    # We've reached the top
                    break
                first = list_items[0]
                scroll_origin = ScrollOrigin.from_element(first)
                ActionChains(self.driver).scroll_from_origin(scroll_origin, 0, -1000).perform()

        return found


    def _get_alexa_list_item_element(self, item: str):
        self._ensure_driver_is_on_alexa_list(False)
        time.sleep(5)
        list_container = self.driver.find_element(By.CLASS_NAME, 'virtual-list')

        last = None
        while True:
            list_items = list_container.find_elements(By.CLASS_NAME, 'inner')
            for container in list_items:
                title_element = container.find_element(By.CLASS_NAME, 'item-title')
                if title_element.get_attribute('innerText') == item:
                    return container  # Return immediately when found

            if not list_items or last == list_items[-1]:
                # We've reached the top
                break

            last = list_items[-1]
            self.driver.execute_script("arguments[0].scrollIntoView();", last)
            time.sleep(1)

        return None


    def add_alexa_list_item(self, item: str):
        element = self._get_alexa_list_item_element(item)
        if element != None:
            return

        self.driver.find_element(By.CLASS_NAME, 'list-header').find_element(By.CLASS_NAME, 'add-symbol').click()

        textfield = self.driver.find_element(By.CLASS_NAME, 'list-header').find_element(By.CLASS_NAME, 'input-box').find_element(By.TAG_NAME, 'input')
        textfield.send_keys(item)

        submit = self.driver.find_element(By.CLASS_NAME, 'list-header').find_element(By.CLASS_NAME, 'add-to-list').find_element(By.TAG_NAME, 'button')
        submit.click()

        self.driver.find_element(By.CLASS_NAME, 'list-header').find_element(By.CLASS_NAME, 'cancel-input').click()
        time.sleep(1)

        return self.get_alexa_list(False)


    def update_alexa_list_item(self, old: str, new: str):
        element = self._get_alexa_list_item_element(old)
        if element == None:
            return

        element.find_element(By.CLASS_NAME, 'item-actions-1').find_element(By.TAG_NAME, 'button').click()

        textfield = element.find_element(By.CLASS_NAME, 'input-box').find_element(By.TAG_NAME, 'input')
        textfield.clear()
        textfield.send_keys(new)

        element.find_element(By.CLASS_NAME, 'item-actions-2').find_element(By.TAG_NAME, 'button').click()
        time.sleep(1)

        return self.get_alexa_list(False)


    def remove_alexa_list_item(self, item: str):
        # In large lists, items towards the end are sometimes not found on the first try
        # In cases like these, retry if the element is not found
        retries = 3
        while retries > 0:
            element = self._get_alexa_list_item_element(item)
            
            if element is None:
                return None
            
            try:
                # Find the delete button and click it
                delete_button = element.find_element(By.CLASS_NAME, 'item-actions-2').find_element(By.TAG_NAME, 'button')
                delete_button.click()
                break
            except StaleElementReferenceException:
                retries -= 1
                time.sleep(1)
            except Exception as e:
                return None
        
        time.sleep(1)  # Wait for the list to update
        return self.get_alexa_list(False)

    # ============================================================
