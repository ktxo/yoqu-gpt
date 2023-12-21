import dataclasses
from dataclasses import field
from datetime import datetime
from enum import Enum
from pydantic import BaseModel
from pydantic.dataclasses import dataclass
from typing import Literal, Optional
import uuid
from sqlmodel import SQLModel, Field



@dataclass
class YoquBase():
    def asdict(self) -> dict:
        return {k: str(v) for k, v in dataclasses.asdict(self).items()}


@dataclass
class YoquStatRequests(YoquBase):
    total:int = 0
    ok:int = 0
    ko:int = 0
    errors:int = 0
    ok_last:datetime = None
    ko_last: datetime = None


@dataclass
class YoquStats(YoquBase):
    status: str = ""
    elapsed: float = 0
    context:dict = field(default_factory=dict)
    requests:YoquStatRequests = field(default_factory=YoquStatRequests)
    dt: datetime = datetime.utcnow()


class YoquStatus(Enum):
    OK = 1
    KO = 2
    UNKNOWN = 3



@dataclass
class RPAMessageCode(YoquBase):
    type:str
    lines:list[str] = field(default_factory=list)

@dataclass
class RPAMessage(YoquBase):
    id: str = str(uuid.uuid4())
    text: str = ""
    raw_text: str = ""
    code_text:list[RPAMessageCode] = field(default_factory=list)
    type: Literal["REQUEST", "RESPONSE", "ANY"] = "REQUEST"


# @dataclass
# class RPAResponeMessage(RPAMessage):
#     type_ = "RESPONSE"
#
# @dataclass
# class RPARequestMessage(RPAMessage):
#     type_ = "REQUEST"
#     responses: list[RPAResponeMessage] = field(default_factory=RPAResponeMessage)
#
# @dataclass
# class RPAChatMessage(YoquBase):
#     id: str
#     requests: list[RPARequestMessage] = field(default_factory=RPARequestMessage)
#
#     def get_requests(self):
#         return [r.text for r in self.requests]
#
#     def get_responses(self):
#         return [[res.text for res in req.responses] for req in self.requests]
#
#

@dataclass
class RPAChat(YoquBase):
    name: str
    messages: list[RPAMessage]|list[list[RPAMessage]] = field(default_factory=list)
    type:str = None
    resource:str = None
    #messages: list[RPAChatMessage] = dataclasses.field(default_factory=list)
    chat_id: str = str(uuid.uuid4())
    online:bool = False
    dt: datetime = datetime.utcnow()

    def __str__(self) -> str:
        return f"RPAChat(name='{self.name}' chat_id={self.chat_id} num_messages={len(self.messages)})"

    def get_requests(self):
        return [message.text for message in self.messages if message.type == "REQUEST"]

    def get_responses(self):
        messages = []
        for message in self.messages:
            if isinstance(message, list):
                messages += [m.text for m in message if m.type == "RESPONSE"]
            else:
                if message.type == "RESPONSE":
                    messages.append(message.text)



#
class Messages(SQLModel, table=True):
    __tablename__ = "messages"
    id: Optional[str] = Field(default=str(uuid.uuid4()), primary_key=True)
    message_id: str
    name:Optional[str] = None
    resource:str = "default"
    type:Optional[str] = "chatgpt"
    messages:str
    online:Optional[bool] = True
    tags:Optional[str] = None
    created:datetime = Field(default=datetime.utcnow())
    updated: datetime = Field(default=datetime.utcnow())

    def asdict(self) -> dict:
        return {k: str(v) for k, v in dataclasses.asdict(self).items()}


# API
class CompletionRequest(BaseModel):
    chat_id:Optional[str] = None
    prompt:Optional[str] = None
    name:Optional[str] = None
    resource_name:Optional[str] = None