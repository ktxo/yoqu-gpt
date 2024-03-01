import logging
from typing import Any
import time

from retry import retry

from ktxo.yoqu.exceptions import YoquException
from ktxo.yoqu.model import RPAChat, RPAMessage, RPAMessageCode
from ktxo.yoqu.base import YoquRPAChat

from selenium.webdriver.common.by import By

logger = logging.getLogger("ktxo.yoqu.gpt")


class RPAChatGPTResource(YoquRPAChat):
    URL = "https://chat.openai.com"
    TITLE = "ChatGPT"

    def __init__(self, name: str, config: dict):
        super(RPAChatGPTResource, self).__init__(name, config)
        logger.debug(f"{self.config}")

    def init_resource(self, **kwargs) -> Any:
        pass

    def is_blocked(self):
        return len(self.browser.find_elements(By.CSS_SELECTOR, "div[id='challenge-stage']")) > 0

    def _create_chat(self, message: str, chat_name: str = None) -> RPAChat:
        elem = self.browser.find_elements(By.XPATH, "//div[text()='New chat']")
        if len(elem) > 0 and elem[0].text.lower() == "new chat":
            elem[0].click() # New Chat
            messages = self._send(message)
            self._load_chats() # Refresh current list
            chat = RPAChat(name=self.chats[0].name, messages=messages, chat_id=self.chats[0].chat_id)
            if chat_name:
                self.chats[0].name = self._rename_chat(chat.chat_id, chat_name)
            return chat

    def _extract_code(self, raw_text) -> list[RPAMessageCode]:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(raw_text, 'html.parser')
        # block = [e.text for e  in soup.find_all("pre")]
        blocks = [e for e in soup.find_all("pre")]
        code = []
        for block in blocks:
            type = block.find_all("span")[0].text
            lines = block.find_all("code")[0].text.split("\n")
            code.append(RPAMessageCode(type=type, lines=lines))
        return code

    def _load_chatsBS(self) -> list[RPAChat]:
        self.chats: list[RPAChat] = []
        #container = self.browser.find_elements(By.XPATH, "//*nav[aria-label='Chat history']")
        # Scroll to get all
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(self.browser.driver.page_source, 'html.parser')
        chats = soup.find_all("li")
        for i, chat in enumerate(chats):
            # Skip New CHat List
            if chat.text.lower() == "New chat".lower():
                continue
            # [[i,chat.find_all("a")] for i,chat in enumerate(chats)]
            a = chat.find_all("a")
            if len(a) > 0 and a[0].attrs["href"].startswith("/c/"):
                #print(a[0].text)
                # if chat.attrs.get("data-projection-id"):
                url = chat.find("a").attrs["href"]
                self.chats.append(RPAChat(chat_id=self.extract_id(url),
                                          name=chat.text,
                                          type=self.type,
                                          resource=self.name))
            else:
                pass
                #print("\t", i, chat.text)
        logger.debug(f"Found {len(chats)} chats")
        return self.chats

    def _load_chats(self) -> list[RPAChat]:
        return self._load_chatsBS()
        self.chats: list[RPAChat] = []
        # #container = self.browser.find_elements(By.XPATH, "//*nav[aria-label='Chat history']")
        # chats = self.browser.find_elements(By.TAG_NAME, "li")
        # chats = self.browser.find_elements(By.XPATH, "//li[@data-projection-id]")
        # for i, chat in enumerate(chats):
        #     if chat.get_attribute("data-projection-id"):
        #         url = chat.find_elements(By.TAG_NAME, "a")[0].get_attribute("href")
        #         self.chats.append(RPAChat(chat_id=self.extract_id(url),
        #                                   name=chat.text,
        #                                   type=self.type,
        #                                   resource=self.name))
        #
        # logger.debug(f"Found {len(chats)} chats")
        # return self.chats

    def _chat_exist(self, chat_id: str) -> bool:
        for chat in self.chats:
            if chat_id == chat.chat_id:
                return True
        return False

    def _get_responses(self) -> list[RPAMessage]:
        self._wait_response()
        obj = self.browser.find_element(By.CSS_SELECTOR, "div[role='presentation']")
        results = []
        self.browser.sleep()
        elems = obj.find_elements(By.XPATH, "//div[contains(@class,'w-full text-token-text-primary')]")
        for e in elems:
            message_id = e.find_element(By.XPATH, ".//div[@data-message-id]").get_attribute("data-message-id")
            who_text = e.find_element(By.CSS_SELECTOR, "div[class='font-semibold select-none']").text
            if who_text.lower() == "you":
                raw_text = ""
                code_text = []
            else:
                # Content Policy violation messages
                e_ = e.find_elements(By.XPATH, "//a[text()='content policy']")
                if len(e_) > 0:
                    raw_text = e.text
                    code_text= []
                else:
                    raw_text = e.find_element(By.CSS_SELECTOR, "div[class*='markdown']").get_attribute("innerHTML")
                    code_text= self._extract_code(raw_text)
            text = "\n".join(e.text.split("\n")[1:])

            if who_text.lower() == "you":
                type_ = "REQUEST"
            else:  # ChatGPT
                type_ = "RESPONSE"
            results.append(RPAMessage(id=message_id,
                                      text=text,
                                      type=type_,
                                      raw_text=raw_text,
                                      code_text= code_text))
        return results

    from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
    @retry((NoSuchElementException, StaleElementReferenceException), delay=2, tries=3)
    def _wait_response(self):
        stop = False
        counter = 0
        self.browser.sleep()
        t0 = time.time()
        while not stop:
            container = self.browser.find_elements(By.CSS_SELECTOR, "div[role='presentation']")
            if len(container):
                e = container[0].find_elements(By.XPATH,
                                          "//*[name()='path' and @d='M4.5 2.5C5.05228 2.5 5.5 2.94772 5.5 3.5V5.07196C7.19872 3.47759 9.48483 2.5 12 2.5C17.2467 2.5 21.5 6.75329 21.5 12C21.5 17.2467 17.2467 21.5 12 21.5C7.1307 21.5 3.11828 17.8375 2.565 13.1164C2.50071 12.5679 2.89327 12.0711 3.4418 12.0068C3.99033 11.9425 4.48712 12.3351 4.5514 12.8836C4.98798 16.6089 8.15708 19.5 12 19.5C16.1421 19.5 19.5 16.1421 19.5 12C19.5 7.85786 16.1421 4.5 12 4.5C9.7796 4.5 7.7836 5.46469 6.40954 7H9C9.55228 7 10 7.44772 10 8C10 8.55228 9.55228 9 9 9H4.5C3.96064 9 3.52101 8.57299 3.50073 8.03859C3.49983 8.01771 3.49958 7.99677 3.5 7.9758V3.5C3.5 2.94772 3.94771 2.5 4.5 2.5Z']")
                if len(e) >= 2:
                    stop = True
                else:
                    self.browser.sleep()
                    if (time.time() - t0) > 60:
                        raise YoquException(f"Timeout waiting response")
            else:
                raise YoquException(f"Cannot locate element. Please retry the operation")

    def chat_id_url(self, chat_id:str):
        return f"https://chat.openai.com/c/{chat_id}"

    def _select_chat(self, chat_id: str):
        chats = self.browser.find_elements(By.TAG_NAME, "li")
        found = False
        for chat in chats:
            # if chat.get_attribute("data-projection-id"):
            chat_id_element = chat.find_element(By.TAG_NAME, "a").get_attribute("href")
            #
            if chat_id in chat_id_element:
                # @TODO: is not working
                # Scrol to element
                #self.browser.driver.execute_script("arguments[0].scrollIntoView();", chat)
                self.browser.driver.get(self.chat_id_url(chat_id))
                #chat.click()
                found = True
                break
        # @ TODO wait for responses
        #self.browser.sleep()
        return found

    def _send(self, message: str) -> list[RPAMessage]:
        # Chat must be selected before execute this function
        self.browser.sleep()
        if not self.browser.send_keys(By.CSS_SELECTOR, "textarea[id='prompt-textarea']", message):
            raise YoquException(f"Cannot send message")

        self.browser.click(By.CSS_SELECTOR, "button[data-testid='send-button']")
        responses = self._get_responses()
        logger.debug(f"{len(responses)} messages. Last: '{responses[-1].text[0:30]}...'")
        return responses

    def _delete_chat(self, chat_id: str):
        # @TODO
        if self._select_chat(chat_id):
            pass

