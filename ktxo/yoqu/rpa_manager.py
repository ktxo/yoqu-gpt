import asyncio
from contextlib import asynccontextmanager
import copy
import json
import logging

import psutil
# Disable Selenium log
# from selenium.webdriver.remote.remote_connection import LOGGER
# from urllib3.connectionpool import log as urllibLogger
# urllibLogger.setLevel(logging.WARNING)
# LOGGER.setLevel(logging.WARNING)
# # ----------------------------------------------------------------------------
logger = logging.getLogger("ktxo.yoqu")

from ktxo.yoqu.base import YoquRPAChat, YoquStatus, YoquStats, YoquException, YoquNotFoundException
from ktxo.yoqu.resource.rpa_chatgpt import RPAChatGPTResource



class RPAManager():
    def __init__(self, config: dict|str):
        if isinstance(config, str):
            with open(config, "r", encoding="utf-8") as fd:
                self.config = json.load(fd)
        else:
            self.config = copy.deepcopy(config)

        self.rpas:dict[str, YoquRPAChat] = {}
        self.locks = {}
        logger.info(f"Starting....")

        for filename in self.config.get("rpas", []):
            try:
                if name:= self.add(filename):
                    logger.info(f"Added resource {name}, starting...")
                    self.rpas[name].init_resource()
                    self.rpas[name].start()
            except Exception as e:
                del self.rpas[name]
                logger.error(f"Cannot add resource from  {filename}", e)
        self.rpa_default = ""
        if self.rpas:
            self.rpa_default = list(self.rpas.keys())[0]
        logger.info(f"Started with {len(self.rpas)} rpas. Default '{self.rpa_default}'")
        self.concurrency_limit = asyncio.Semaphore(len(self.config))

    def add(self, config:str|dict):
        if isinstance(config, str):
            try:
                with open(config, "r") as fd:
                    config = json.load(fd)
            except Exception as e:
                logger.error(f"Ops, cannot open/reading configuration file '{config}' ({e})")
                return None
        if config["name"] in config:
            logger.warning(f"Resource {config['name']} already exists, ignoring")
            return None
        if config.get("type", None) == "chatgpt":
            self.rpas[config["name"]] = RPAChatGPTResource(config["name"], config)
            self.locks[config["name"]] = asyncio.Lock()
        else:
            logger.error(f"Resource type {config.get('type', '')} unknown, ignoring")
        return config["name"]

    def status(self, name:str) -> bool:
        rpa = self.rpas.get(name, None)
        if rpa is None:
            logger.warning(f"Resource {name} unknown, ignoring")
            return False
        return rpa.is_ok()

    def stats(self, name:str) -> dict:
        rpa = self.rpas.get(name, None)
        if rpa is None:
            logger.warning(f"Resource {name} unknown, ignoring")
            raise YoquException(f"Resource '{name}' not found")
        return rpa.info()

    async def get_manager(self, name) -> YoquRPAChat:
        async with self.concurrency_limit:
            if not name in self.config:
                #return None
                raise YoquException(f"Resource '{name}' not found")
            else:
                rpa = self.rpas.get(name)
                logger.info(f"Returning {rpa.name}")
                return rpa

    @asynccontextmanager
    async def get_resource(self, name) -> YoquRPAChat:
        if name not in self.locks:
            raise YoquException(f"Resource '{name}' not found")
        async with self.locks[name]:
            logger.info(f"Locking {name}")
            yield self.rpas[name]
            logger.info(f"Releasing {name}")


if __name__ == '__main__':
    import logging
    import logging.config
    LOG_LEVELS = {'I': logging.INFO, 'D': logging.DEBUG, 'W': logging.WARNING, 'E': logging.ERROR}
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    from selenium.webdriver.remote.remote_connection import LOGGER
    from urllib3.connectionpool import log as urllibLogger
    urllibLogger.setLevel(logging.WARNING)
    LOGGER.setLevel(logging.WARNING)


    # manager = RPAManager("rpa_manager.json")
    # print(manager.status("asasas"))
    # print(manager.status("chatgpt1"))