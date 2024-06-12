import dataclasses
import re
from abc import ABC, abstractmethod
import copy
from datetime import datetime
import json
import logging
import os
from typing import Any

from ktxo.yoqu.common.exceptions import YoquException, YoquNotFoundException
from ktxo.yoqu.common.helper import build_filename, build_folders, write_json, write_binary
from ktxo.yoqu.common.model import YoquStatus, YoquStats, RPAChat, RPAMessage
from ktxo.yoqu.rpa import RPAChrome

logger = logging.getLogger("ktxo.yoqu")

class YoquResource(ABC):
    def __init__(self, name:str, config: dict | str):
        if isinstance(config, str):
            with open(config, "r", encoding="utf-8") as fd:
                self.config = json.load(fd)
        else:
            self.config = copy.deepcopy(config)
        self.name = name
        self.desc = self.config.get("desc", "")
        self.type = self.config.get("type", "UNKNOWN")
        self.resource_config = self.config.get("resource", {})
        self.dump = self.config.get("dump", False)
        self.dump_folder = self.config.get("dump_folder", None)
        self.stats = YoquStats()
        logger.info(f"Configuration {self.config}")
    
    @abstractmethod
    def init_resource(self, **kwargs) -> Any:
        pass

    @abstractmethod
    def invoke(self, **kwargs) -> Any:
        pass

    def install(self, **kwargs):
        pass

    def start(self, **kwargs):
        pass

    def stop(self, **kwargs):
        pass

    def restart(self, **kwargs):
        self.stop()
        if self.is_ok():
            self.start()
        else:
            self.start()

    def refresh(self, **kwargs):
        pass

    def is_ok(self) -> bool:
        return True

    def info(self) -> dict:
        import dataclasses
        return {"name": self.name, "type": self.type, "status": "Not defined", "stats": dataclasses.asdict(self.stats)}

    def update_stats(self, ok=None, ko:int = None, ok_dt:datetime = None, ko_dt:datetime = None, errors:int = None) -> YoquStats:
        if errors:
            self.stats.requests.errors +=1
        if ok:
            self.stats.requests.ok += 1
            if ok_dt:
                self.stats.requests.ok_last = ok_dt
            else:
                self.stats.requests.ok_last = datetime.utcnow()
        if ko:
            self.stats.requests.ko += 1
            if ko_dt:
                self.stats.requests.ko_last = ko_dt
            else:
                self.stats.requests.ko_last = datetime.utcnow()
        self.stats.requests.total = self.stats.requests.ok + self.stats.requests.ko
        return self.stats

    def status(self, **kwargs) -> YoquStatus:
        return YoquStatus.OK

    def dump_request(self, filename:str, data:dict|Any, infer_extension:bool = True):
        if self.dump:
            file_ext = ""
            if infer_extension:
                if isinstance(data, dict):
                    file_ext = ".json"
                else:
                    file_ext = ".xxx"
            filename = build_filename(f"{filename}{file_ext}", self.dump_folder, False, True, False)
            build_folders(os.path.dirname(filename))
            if isinstance(data, dict):
                filename_= write_json(data, filename)
            else:
                filename_ = write_binary(data, filename)
            logger.debug(f"Dump -> {filename}")

class YoquRPAChat(YoquResource):
    URL = "Ups, URL not defined"
    TITLE = "YoquRPAChat"
    VALID_OPERATIONS = ["create", "chat", "rename", "list", "get", "delete"]
    
    def __init__(self, name: str, config: dict):
        super(YoquRPAChat, self).__init__(name, config)
        self.dump = self.config.get("dump", False)
        self.dump_folder = self.config.get("dump_folder", None)
        self.browser: RPAChrome = RPAChrome(self.resource_config)
        self.sleep_range: list[int] = self.resource_config.get("sleep_range", [1, 5])
        self.is_local: bool = True # TODO
        self.chats: list[RPAChat] = []

    def is_blocked(self):
        return False

    def start(self, **kwargs):
        # Not used for UC
        # if self.browser.is_alive():
        #     logger.info(f"Browser is alive")
        # else:
        #     logger.info(f"Starting browser with '{self.browser.command}'")
        # Stop if exist, ignore messages
        # self.browser.stop()

        self.browser.start()

        if self.is_blocked():
            logger.warning(f"Being blocked")
        if not self.browser.is_alive():
            return False

    def stop(self, **kwargs):
        if self.browser:
            self.browser.stop()

    def refresh(self, **kwargs):
        if self.browser:
            self.browser.driver.get(self.browser.driver.current_url)
            self.browser.driver.refresh()

    def is_ok(self) -> bool:
        if self.browser:
            return self.browser.is_alive()
        else:
            return False

    def create(self, message: str, chat_name: str = None, delete_after=False) -> RPAChat:
        if not self.is_ok():
            raise YoquException(f"RPA '{self.name}' not running")
        return self.invoke(operation="create", name=chat_name, message=message, delete_after=delete_after)

    def send(self, chat_id: str, message: str) -> RPAChat:
        if not self.is_ok():
            raise YoquException(f"RPA '{self.name}' not running")
        return self.invoke(operation="chat", chat_id=chat_id, message=message)

    def list_chats(self) -> list[str]:
        if not self.is_ok():
            raise YoquException(f"RPA '{self.name}' not running")
        return self.invoke(operation="list")

    def get_chat(self, chat_id: str) -> RPAChat:
        if not self.is_ok():
            raise YoquException(f"RPA not running")
        return self.invoke(operation="get", chat_id=chat_id)

    def extract_id(self, url) -> str:
        # ChatGPT: https://chat.openai.com/c/48662ada-d46a-4abe-ae51-1bf892f22548
        # Claude:  https://claude.ai/chat/64259e9f-c94d-45b0-8e7d-ad9aa3048377
        groups = re.search(r"^(.*)/([A-z0-9]{8}-[A-z0-9]{4}-[A-z0-9]{4}-[A-z0-9]{4}-[A-z0-9]{12})(.*)", url)
        if groups:
            #return f"{self.type}___{groups.groups()[1]}"
            return f"{groups.groups()[1]}"
        else:
            return None

    def parse_id(self, id_):
        return id_
        #return id_.split("___")

    @abstractmethod
    def _create_chat(self, message:str, chat_name:str=None) -> RPAChat: pass
    @abstractmethod
    def _rename_chat(self, chat_id:str, chat_name: str, *args, **kwargs) -> RPAChat: pass
    @abstractmethod
    def _load_chats(self) -> list[RPAChat]: pass
    @abstractmethod
    def _chat_exist(self, chat_name: str) -> bool: pass
    @abstractmethod
    def _get_responses(self) -> list[RPAMessage]: pass
    @abstractmethod
    def _select_chat(self, chat_name: str): pass
    @abstractmethod
    def _send(self, message:str ) -> list[RPAMessage]: pass
    @abstractmethod
    def _delete_chat(self, chat_id: str): pass

    def invoke(self, **kwargs) -> Any:
        cmd = kwargs.get("operation", None)
        if not cmd or cmd not in self.VALID_OPERATIONS:
            raise YoquException(f"Unknown command '{cmd}'")

        chat_name = kwargs.get("name", None)
        chat_id = kwargs.get("chat_id", None)
        message = kwargs.get("message", None)
        delete_after = kwargs.get("delete_after", False)
        try:
            match cmd:
                case "create":
                    chat = self._create_chat(message, chat_name)
                    logger.debug(f"Created {chat}")
                    if delete_after:
                        self._delete_chat(chat.chat_id)
                        _ = self.chats.pop(0)
                        logger.info(f"Removing {chat}")
                        #self._load_chats() # Refreh
                    self.update_stats(ok=True)
                    return chat
                case "chat":
                    if not chat_id:
                        raise YoquException(f"Missing chat_id parameter")
                    if not message:
                        raise YoquException(f"Missing message parameter")
                    self._load_chats()
                    if not self._chat_exist(chat_id):
                        self.update_stats(ko=True)
                        raise YoquException(f"Unknown chat '{chat_id}'")
                    if not self._select_chat(chat_id):
                        self.update_stats(ko=True)
                        raise YoquNotFoundException(f"Cannot locate chat '{chat_id}'")
                    messages = self._send(message)
                    #self.dump_request(chat_id, {"chat": chat_name, "chat_id": chat_id,"messages":[d.asdict() for d in messages]})

                    self.update_stats(ok=True)
                    chat_name = [chat.name for chat in self.chats if chat.chat_id == chat_id][0]
                    chat = RPAChat(name=chat_name,
                                   messages=messages,
                                   type=self.type,
                                   resource=self.name,
                                   chat_id=self.extract_id(self.browser.current_url()))
                    self.dump_request(f"{self.type}_{chat_id}", chat.asdict())
                    logger.debug(f"Message sent to {chat}")
                    return chat
                case "rename":
                    # @TODO
                    return self._rename_chat(chat_id, chat_name)
                case "list":
                    return self._load_chats()
                case "get":
                    if not self._chat_exist(chat_id):
                        raise YoquNotFoundException(f"Unknown chat '{chat_id}'")
                    if not self._select_chat(chat_id):
                        raise YoquNotFoundException(f"Cannot locate chat '{chat_id}'")
                    messages = self._get_responses()
                    chat_name = [chat.name for chat in self.chats if chat.chat_id == chat_id][0]
                    chat = RPAChat(name=chat_name,
                                   chat_id=chat_id,
                                   messages=messages,
                                   type=self.type,
                                   resource=self.name )
                    logger.debug(f"Chat {chat}")
                    self.dump_request(chat_id, dataclasses.asdict(chat))
                    self.update_stats(ok=True)
                    return chat
                case "delete":
                    if not self._chat_exist(chat_id):
                        raise YoquNotFoundException(f"Unknown chat '{chat_id}'")
                    if not self._select_chat(chat_id):
                        raise YoquNotFoundException(f"Cannot locate chat '{chat_id}'")
                    self._delete_chat(chat_id)
                case _:
                        logger.warning(f"Unknown command '{cmd}'")
                        return None
        except YoquNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Got exception {type(e)}", e)
            raise YoquException(str(e))

    def _rename_chat(self, chat_id:str, chat_name: str, new_chat_name:str):
        pass

    def info(self) -> dict:
        return {"name": self.name,
                "type": self.type,
                "alive": self.browser.is_alive(),
                "pid": self.browser.process_pid,
                "stats": self.stats.asdict()
                }

    def dump_chat(self, chat: RPAChat):
        print(f"Title: {chat.name}")
        print(f"Id   : {chat.chat_id}")
        print("--- Messages ---")
        for i, m in enumerate(chat.messages, 1):
            nl = "\n"
            print(f"#{i:2d} {m.type}{nl}{m.text}")
            print("-" * 80)
