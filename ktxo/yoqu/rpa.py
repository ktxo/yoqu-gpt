#
# RPA to manage Browsers with Selenium (only Chrome for now :-/)
#
import copy
import logging
import random
import subprocess
import time

from retry import retry
from retry.api import retry_call

from selenium import webdriver
from selenium.webdriver import chrome
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
# message.Keys.chord(Keys.SHIFT, Keys.ENTER)
from selenium.common.exceptions import WebDriverException

import undetected_chromedriver as uc

from ktxo.yoqu.common.exceptions import YoquException
from ktxo.yoqu.common.helper import ProcessHelper, build_filename, normalize_url


logger = logging.getLogger("ktxo.yoqu")

# Dummy copy to avoid reference to Selenium
class BY(object):
    """
    Copy of selenium.webdriver.common.by.By
    """
    ID = "id"
    XPATH = "xpath"
    LINK_TEXT = "link text"
    PARTIAL_LINK_TEXT = "partial link text"
    NAME = "name"
    TAG_NAME = "tag name"
    CLASS_NAME = "class name"
    CSS_SELECTOR = "css selector"

class RPAChrome():
    def __init__(self, config: dict):
        self.config = copy.deepcopy(config)
        self.debug = self.config.get("debug", False)
        self.url = self.config["url"]
        self.url_title = self.config.get("url_title", None)
        self.command: list[str] = self.config["command"] + [self.url]
        self.process = None
        self.process_pid = -1
        self.sleep_range:list[int] = self.config.get("sleep_range", [1, 5])
        self.driver: webdriver.Chrome = None

        self.options = webdriver.ChromeOptions()
        for o in self.config.get("options",[]):
            self.options.add_argument(o)
        for o in self.config.get("options_experimental",[]):
            if isinstance(o, list):
                self.options.add_experimental_option(*o)
            else:
                self.options.add_experimental_option(o)
        # self.options.add_experimental_option('excludeSwitches', ['enable-logging'])
        self.driver = None  #

    def sleep(self, t:int|list[int] = None):
        if not t:
            time.sleep(random.randint(*self.sleep_range))
        elif isinstance(t, int):
            time.sleep(t)
        elif isinstance(t, list):
            time.sleep(random.randint(*self.sleep_range))
        else:
            time.sleep(random.randint(*self.sleep_range))

    def _connect(self):
        try:
            if not self.is_alive():
                self.driver = uc.Chrome(options=self.options, **self.config["uc_options"])
                self.process_pid = self.driver.browser_pid
            else:
                logger.info(f"Browser pid={self.process_pid} already started, ignoring")
        except WebDriverException as we:
            logger.error(f"Cannot connect to process")
            raise YoquException(we.msg)
        return self.driver

    def start(self):
        self.driver = self._connect()
        self.go2url(self.config["url"])
        self.sleep()

        if self.url_title and self.driver.title != self.url_title:
            logger.error(f"Cannot go to {self.url}, current is '{self.driver.current_url}' ({self.driver.title})")
            if self.debug:
                self.save_screenshot()
            raise YoquException(f"Cannot go to {self.url}")
        logger.info(f"Browser started, pid={self.process_pid}")

    def go2url(self, url:str):
        self.driver.get(url)

    def save_screenshot(self, url) -> str:
        filename = f"{normalize_url(url)}.png"
        filename = build_filename(filename, "dump", False, True, False)
        self.driver.save_screenshot(filename)
        return filename

    def _quit(self):
        try:
            if self.driver:
                self.driver.quit()
                self.process_pid = -1
        except Exception as e:
            logger.warning(f"Ignoring {e}")

    def stop(self):
        if not self.is_alive():
            logger.warning(f"Process not exist, ignoring")
        else:
            logger.info(f"Stopping process command='{self.command} pid={self.process_pid}")
            self._quit()


    def restart(self):
        self.stop()
        self.start()
        return self.process

    def is_alive(self):
        if not self.driver:
            return False
        if self.driver.service.process.poll() is None and self.driver.window_handles != []:
            return True
        return False

    def status(self):
        return {"pid": self.process_pid, "command": self.command, "alive": self.is_alive()}

    def refresh(self):
        if self.driver:
            self.driver.refresh()

    def info(self) -> dict:
        return {"pid": self.process_pid, "command": self.command, "alive": self.is_alive()}

    @retry()
    def find_element(self, by, value):
        return self.driver.find_element(by, value)


    def find_elements(self, by, value):
        return self.driver.find_elements(by, value)

    def click(self, by, value):
        elem = self.driver.find_element(by, value)
        elem.click()
        return elem

    def send_keys(self, by, value, text):
        elem = self.driver.find_element(by, value)
        for part in text.split('\n'):
            elem.send_keys(part)
            (ActionChains(self.driver)
             .key_down(Keys.SHIFT).key_down(Keys.ENTER)
             .key_up(Keys.SHIFT).key_up(Keys.ENTER)
             .perform()
             )
        self.driver.execute_script('arguments[0].value=arguments[1]', elem, text)
        #elem.send_keys(text)
        return elem

    def go_2_top_of_page(self):
        ActionChains(self.driver).send_keys(Keys.CONTROL).send_keys(Keys.HOME).perform()

    def go_2_end_of_page(self):
        ActionChains(self.driver).send_keys(Keys.CONTROL).send_keys(Keys.END).perform()

    def current_url(self) -> str:
        return self.driver.current_url