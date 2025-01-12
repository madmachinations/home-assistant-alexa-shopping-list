#!/usr/bin/env python3

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import platform
import requests
import zipfile
import tarfile
import os
import tempfile
import stat
import subprocess

WAIT_TIMEOUT=30
CHROMIUM_REPO_BASE_URL = "https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/"

OS_SETTINGS = {
    "windows": {
        "repo_name": "Win_x64",
        "chrome_zip": "chrome-win.zip",
        "driver_zip": "chromedriver_win32.zip",
        "chrome_binary_path": "chrome.exe",
        "chromedriver_binary_path": "chromedriver.exe",
    },
    "linux": {
        "repo_name": "Linux_x64",
        "chrome_zip": "chrome-linux.zip",
        "driver_zip": "chromedriver_linux64.zip",
        "chrome_binary_path": "chrome",
        "chromedriver_binary_path": "chromedriver",
    },
    "mac": {
        "repo_name": "Mac",
        "chrome_zip": "chrome-mac.zip",
        "driver_zip": "chromedriver_mac64.zip",
        "chrome_binary_path": "Chromium.app/Contents/MacOS/Chromium",
        "chromedriver_binary_path": "chromedriver",
    },
    "mac-arm": {
        "repo_name": "Mac_Arm",
        "chrome_zip": "chrome-mac.zip",
        "driver_zip": "chromedriver_mac64.zip",
        "chrome_binary_path": "Chromium.app/Contents/MacOS/Chromium",
        "chromedriver_binary_path": "chromedriver",
    }
}

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
        chrome_options.binary_location = self._get_chromium_sub_path("chrome_binary_path")

        service = webdriver.ChromeService(executable_path=self._get_chromium_sub_path("chromedriver_binary_path"))
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
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
    # Config data


    def _get_os(self):
        os_name = platform.system()

        if os_name == "Windows":
            return "windows"
        elif os_name == "Darwin":
            cpu_arch = platform.machine()
            if cpu_arch == "arm64":
                return "mac-arm"
            elif cpu_arch == "x86_64":
                return "mac"
        elif os_name == "Linux":
            return "linux"
        
        raise Exception("Unable to detect OS and architecture")
    

    def _get_os_config_value(self, key):
        return OS_SETTINGS[self._get_os()][key]
    

    def _ensure_chromium_path(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        chromium_folder = os.path.join(script_dir, "chromium")
        if not os.path.exists(chromium_folder):
            os.makedirs(chromium_folder)
        return chromium_folder
    

    def _get_chromium_sub_path(self, os_setting):
        if os_setting == "chrome_binary_path":
            bridge = "chromium"
        else:
            bridge = "chromedriver"
        return os.path.join(self._ensure_chromium_path(), bridge, self._get_os_config_value(os_setting))

    # ============================================================
    # Chromium


    def _get_latest_chromium_version(self):
        response = requests.get(CHROMIUM_REPO_BASE_URL+self._get_os_config_value("repo_name")+"%2FLAST_CHANGE?alt=media")
        if response.status_code == 200:
            return response.text
        raise Exception("Failed to fetch latest Chromium version.")


    def _extract_chromium(self, file_name, extract_as):
        temp_dir = tempfile.mkdtemp()
        base_path = os.path.dirname(file_name)
        
        if self._get_os().startswith("mac"):
            subprocess.run(["unzip", "-q", file_name, "-d", temp_dir], check=True)
        else:
            with zipfile.ZipFile(file_name, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
        
        extracted_dir = next(os.path.join(temp_dir, d) for d in os.listdir(temp_dir) if os.path.isdir(os.path.join(temp_dir, d)))
        os.rename(extracted_dir, os.path.join(base_path, extract_as))
        os.rmdir(temp_dir)
        os.remove(file_name)
    
    
    def _download_chromium(self):
        repo_name = self._get_os_config_value("repo_name")
        version = self._get_latest_chromium_version()
        chrome_path = self._ensure_chromium_path()

        chrome_url = CHROMIUM_REPO_BASE_URL+repo_name+"%2F"+version+"%2F"+self._get_os_config_value("chrome_zip")+"?alt=media"
        driver_url = CHROMIUM_REPO_BASE_URL+repo_name+"%2F"+version+"%2F"+self._get_os_config_value("driver_zip")+"?alt=media"

        print(f"Downloading Chromium...")
        response = requests.get(chrome_url, stream=True)
        file_name = os.path.join(chrome_path, "chromium.zip")
        with open(file_name, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print("Extracting files...")
        self._extract_chromium(file_name, "chromium")

        if platform.system() == "Darwin":
            subprocess.run(["xattr", "-r", "-d", "com.apple.quarantine", chrome_path], check=False)
            subprocess.run(["chmod", "+x", self._get_chromium_sub_path("chrome_binary_path")], check=True)
            # subprocess.run(["chmod", "+x", os.path.join(self._get_chromium_sub_path("chrome_binary_path"), "Frameworks/Chromium Framework.framework/Versions/134.0.6952.0/Helpers/chrome_crashpad_handler")], check=True)
            # subprocess.run(["chmod", "+x", self._get_chromium_sub_path("chromedriver_binary_path")], check=True)

        print(f"Downloading Chrome Driver...")
        response = requests.get(driver_url, stream=True)
        file_name = os.path.join(chrome_path, "chrome-driver.zip")
        with open(file_name, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print("Extracting files...")
        self._extract_chromium(file_name, "chromedriver")

        driver_path = self._get_chromium_sub_path("chromedriver_binary_path")
        st = os.stat(driver_path)
        os.chmod(driver_path, st.st_mode | stat.S_IEXEC)
    

    def _reset_chromium(self):
        chromium_dir = self._ensure_chromium_path()
        if os.path.exists(chromium_dir):
            for root, dirs, files in os.walk(chromium_dir, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(chromium_dir)

    
    def _ensure_chromium(self):
        chrome_path = self._get_chromium_sub_path("chrome_binary_path")
        driver_path = self._get_chromium_sub_path("chromedriver_binary_path")

        if not os.path.exists(chrome_path) or not os.path.exists(driver_path):
            print("Chromium not found. Downloading...")
            self._reset_chromium()
            self._download_chromium()
        
        print("Chromium is ready")


    # ============================================================
    # Perform authentication


    def run(self):
        self._ensure_chromium()

        self._setup_driver()
        input("Press enter to continue")

        # self._setup_driver()
        # session = self._get_session_data()
        #TODO: Return session json

    # ============================================================
