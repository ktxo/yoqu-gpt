import json
import logging
import os.path

from typing import Any, List, Mapping, Optional

from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.llms.base import LLM
from langchain.prompts import PromptTemplate, ChatPromptTemplate, load_prompt
from ktxo.yoqu.client.api_client import APIWrapper
from ktxo.yoqu.common.exceptions import YoquException

logger = logging.getLogger("ktxo.yoqu.langchain")


def save_template(template, name:str):
    name = os.path.splitext(os.path.basename(name))[0]
    filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates", f"{name}.json")
    template.save(filename)
    return filename


def load_template(name:str):
    name = os.path.splitext(os.path.basename(name))[0]
    filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates", f"{name}.json")
    return load_prompt(filename)


def build_template(prompt:str):
    return PromptTemplate.from_template(prompt)


class YoquChatGPTLLM(LLM):
    resource:str = None
    host: str = "127.0.0.1"
    port: int = 8000
    client:Optional[APIWrapper] = None
    chat:dict = None

    def __init__(self, resource:str ):
        super(YoquChatGPTLLM, self).__init__()
        self.resource = resource
        self.client: APIWrapper = APIWrapper(self.host, self.port)
        logger.info(f"{self.__class__.__name__}")

    @property
    def _llm_type(self) -> str:
        return APIWrapper.__name__

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        if stop is not None:
            raise ValueError("stop kwargs are not permitted.")
        resource = kwargs.get("resource", self.resource)
        raw_text = kwargs.get("raw_text", False)
        chat_id = None
        if self.chat:
            chat_id = self.chat["chat_id"]

        if chat_id:
            self.chat = self.client.update_chat(chat_id, prompt, resource)
        else:
            self.chat = self.client.new_chat(prompt, resource, True)
        logger.debug(f"{self.chat}")
        if self.chat:
            logger.debug(f"Current chat {self.chat}")
            # Return last RESPONSE message
            if self.chat["messages"][-1]["type"] == "RESPONSE":
                if raw_text:
                    return self.chat["messages"][-1]["raw_text"]
                if len(self.chat["messages"][-1]["code_text"]) > 0:
                    # join all lines, code_text contains all lines returned by a "code" block in chatgpt, e.g.:
                    # {
                    #   "caption": "asasasas",
                    #   "summary": "sdasd",
                    #   "keywords": [1,1123,2]
                    # }
                    return "".join(self.chat["messages"][-1]["code_text"][-1]["lines"])
                else:
                    return self.chat["messages"][-1]["text"]
            logger.error(f"Current chat {self.chat}")
            raise YoquException(f"Error getting response from API")

    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        """Get the identifying parameters."""
        return {"host": self.host, "port": self.port, "resource": self.resource}



