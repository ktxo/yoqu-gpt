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




from selenium.common.exceptions import WebDriverException, TimeoutException, NoSuchElementException, StaleElementReferenceException

from ktxo.yoqu.exceptions import YoquException
from ktxo.yoqu.helper import ProcessHelper, build_filename, normalize_url


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
        for o in self.config["options"]:
            self.options.add_argument(o)
        for o in self.config["options_experimental"]:
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
            #self.driver = webdriver.Chrome(executable_path=self.config["chromedriver"], options=self.options, service_log_path="log.txt")
            self.driver = webdriver.Chrome(service=Service(executable_path=self.config["chromedriver"]),
                                           options=self.options)
        except WebDriverException as we:
            logger.error(f"Cannot connect to process")
            raise YoquException(we.msg)
        return self.driver

    # def connect(self):
    #     self.driver = self._connect()
    #     self.driver.get(self.config["url"])
    #     self.sleep()
    #     if self.url_title and self.driver.title != self.url_title:
    #         logger.error(f"Cannot go to {self.url}, current is '{self.driver.current_url}' ({self.driver.title})")
    #         if self.debug:
    #             self.save_screenshot()
    #         raise Exception(f"Cannot go to {self.url}")
    #     logger.info(f"Process command='{self.command}' started, pid={self.process_pid}")
    def start(self):
        self.process_pid = ProcessHelper.process_exist(self.command, self.process_pid)
        if self.process_pid > 0:
            if not self.driver:
                self._connect()
            logger.warning(f"Process with pid={self.process_pid} exist, command='{self.command}', ignoring")
            return
        logger.info(f"Process command='{self.command}' not exist, starting")
        self.process_pid = ProcessHelper.start_process(self.command)
        if self.process_pid == -1:
            logger.error(f"Cannot start process command='{self.command}'")
            raise YoquException(f"Cannot start process command='{self.command}'")
        self.driver = self._connect()
        self.driver.get(self.config["url"])
        self.sleep()

        if self.url_title and self.driver.title != self.url_title:
            logger.error(f"Cannot go to {self.url}, current is '{self.driver.current_url}' ({self.driver.title})")
            if self.debug:
                self.save_screenshot()
            raise Exception(f"Cannot go to {self.url}")
        logger.info(f"Process command='{self.command}' started, pid={self.process_pid}")

    def save_screenshot(self, url) -> str:
        filename = f"{normalize_url(url)}.png"
        filename = build_filename(filename, "dump", False, True, False)
        self.driver.save_screenshot(filename)
        return filename

    def _quit(self, process):
        try:
            if self.driver:
                self.driver.quit()
        except Exception as e:
            logger.warning(f"Ignoring {e}")
        try:
            if self.process:
                self.process.terminate()
        except Exception as e:
            logger.warning(f"Ignoring {e}")

    def stop(self):
        self.process = ProcessHelper.get_process(self.command)
        if not self.process:
            self.process_pid = -1
            logger.warning(f"Process not exist, ignoring")
        else:
            self.process_pid = self.process.pid
            logger.info(f"Stopping process command='{self.command} pid={self.process_pid}")
        self._quit(self.process)
        self.process = None

    def restart(self):
        self.stop()
        self.start()
        return self.process
        pass

    def is_alive(self):
        self.process_pid = ProcessHelper.process_exist(self.command, self.process_pid)
        return self.process_pid != -1

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