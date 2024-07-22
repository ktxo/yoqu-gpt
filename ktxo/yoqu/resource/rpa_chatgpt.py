import logging
from typing import Any
import time

from retry import retry

from ktxo.yoqu.common.exceptions import YoquException
from ktxo.yoqu.common.model import RPAChat, RPAMessage, RPAMessageCode
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
        #elem = self.browser.find_elements(By.XPATH, "//div[text()='New chat']")
        # ChatGPT must be opened with sidebar expanded
        p = "button[class='h-10 rounded-lg px-2 text-token-text-secondary focus-visible:outline-0 hover:bg-token-sidebar-surface-secondary focus-visible:bg-token-sidebar-surface-secondary']"

        elem = self.browser.find_elements(By.CSS_SELECTOR, p)
        #if len(elem) > 0 and elem[0].text == "ChatGPT":
        if len(elem) > 0:
            #elem[0].click() # New Chat
            elem[1].click()  # New Chat
            messages = self._send(message)
            self._load_chats() # Refresh current list
            chat = RPAChat(name=self.chats[0].name, messages=messages, chat_id=self.chats[0].chat_id)
            if chat_name:
                self.chats[0].name = self._rename_chat(chat.chat_id, chat.name, chat_name)
            return chat
        return None

    def _extract_code(self, elem) -> list[RPAMessageCode]:
        blocks = elem.find_elements(By.TAG_NAME, "pre")
        code = []
        for block in blocks:
            type_, lines = "", []
            elems = block.find_elements(By.TAG_NAME, "span")
            if len(elems) > 0:
                type_ = elems[0].text
            elems = block.find_elements(By.TAG_NAME, "code")
            if len(elems) > 0:
                lines = elems[0].text.split("\n")
            code.append(RPAMessageCode(type_=type_, lines=lines))
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
        messages = obj.find_elements(By.XPATH, "//div[contains(@class, 'w-full text-token-text-primary')]")
        for m in messages:
            message_id = m.find_element(By.XPATH, ".//div[@data-message-id]").get_attribute("data-message-id")
            t = m.find_elements(By.XPATH, ".//div[contains(@class, 'gizmo-bot-avatar')]")
            type_ = "REQUEST"
            if len(t) > 0:
                type_ = "RESPONSE"
            raw_text = ""
            code_text = self._extract_code(m)
            text = "\n".join(m.text.split("\n"))

            results.append(RPAMessage(id=message_id,
                                      text=text,
                                      type=type_,
                                      raw_text=raw_text,
                                      code_text= code_text))
        return results

    def _wait_response(self):
        stop = False
        counter = 0
        self.browser.sleep()
        t0 = time.time()
        while not stop:
            # if self._continue_generating_regenerate():
            #     continue
            send_button = self._get_send_button()

            if send_button:
                print(send_button.text)
                stop = True
            else:
                self.browser.sleep()
                if (time.time() - t0) > 600:
                    raise YoquException(f"Timeout waiting response")

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

    def _get_send_button(self):
        """ChatGPT changed "send button"""
        # SVG data
        svg_d = "M15.192 8.906a1.143 1.143 0 0 1 1.616 0l5.143 5.143a1.143 1.143 0 0 1-1.616 1.616l-3.192-3.192v9.813a1.143 1.143 0 0 1-2.286 0v-9.813l-3.192 3.192a1.143 1.143 0 1 1-1.616-1.616z"
        e = self.browser.find_elements(By.XPATH, f"//*[name()='path' and @d='{svg_d}']")
        if len(e) > 0:
            return e[0]
        else:
            return None


    def _send(self, message: str) -> list[RPAMessage]:
        # Chat must be selected before execute this function
        self.browser.sleep()
        if not self.browser.send_keys(By.CSS_SELECTOR, "textarea[id='prompt-textarea']", message):
            raise YoquException(f"Cannot send message")

        b = self._get_send_button()
        if b is None:
            raise YoquException("Cannot send message (send button not found)")
        b.click()
        responses = self._get_responses()
        logger.debug(f"{len(responses)} messages. Last: '{responses[-1].text[0:30]}...'")
        return responses

    def _delete_chat(self, chat_id: str):
        #chat = self._select_chat(chat_id)
        if chat_id:
            logger.debug(f"Deleting {chat_id}")
            # Restriction: only first item
            self.browser.sleep([0.5, 2])
            elem = self.browser.find_elements(By.CSS_SELECTOR, "button[data-state='closed']")
            if len(elem) > 0:
                self.browser.sleep([1.2, 2])
                elem[0].click()
                # Share, Rename, Delete
                self.browser.find_elements(By.CSS_SELECTOR, "div[role='menuitem']")[2].click()
                elem = self.browser.find_elements(By.CSS_SELECTOR, "button[class='btn relative btn-danger']")
                if len(elem) > 0:
                    self.browser.sleep([1, 2])
                    elem[0].click()
