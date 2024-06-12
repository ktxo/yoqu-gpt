import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ktxo.yoqu.db import get_session, add_message
from ktxo.yoqu.api.rpa import get_manager, valid_resource
from ktxo.yoqu.common.model import CompletionRequest, RPAChat

logger = logging.getLogger("ktxo.yoqu")

router = APIRouter(prefix="/yoqu", tags=["api"] )


@router.get("/completions/",
            summary="List of Completions/chats from resource",
            dependencies=[Depends(valid_resource)])
async def get_completions(resource_name:str|None = None,
                          manager=Depends(get_manager),
                          session: AsyncSession = Depends(get_session)) -> list[RPAChat]:
    async with manager.get_resource(resource_name) as rpa:
        # rpa = manager.rpas[resource_name]
        return rpa.list_chats()

@router.put("/completions/",
            summary="Update existing Completion/Chat",
            dependencies=[Depends(valid_resource)])
async def completion(completion:CompletionRequest,
                     manager=Depends(get_manager),
                     session: AsyncSession = Depends(get_session)) -> RPAChat:
    logger.debug(f"Updating {completion.chat_id}")
    async with manager.get_resource(completion.resource_name) as rpa:
        return rpa.send(completion.chat_id, completion.prompt)


@router.post("/completions/",
            summary="Create a Completion/Chat",
            dependencies=[Depends(valid_resource)])
async def completion(completion:CompletionRequest,
                     manager=Depends(get_manager),
                     session: AsyncSession = Depends(get_session)) -> RPAChat:
    logger.debug(f"Creating {completion.prompt[0:30]}...")
    async with manager.get_resource(completion.resource_name) as rpa:
        return rpa.create(completion.prompt, completion.name, completion.delete_after)

@router.get("/completions/{chat_id}",
            summary="Completion/Chat details",
            dependencies=[Depends(valid_resource)])
async def get_completion(chat_id:str,
                         resource_name:str|None = None,
                         manager=Depends(get_manager),
                         session: AsyncSession = Depends(get_session)) -> RPAChat:
    logger.debug(f"Getting {chat_id}")
    async with manager.get_resource(resource_name) as rpa:
        chat = rpa.get_chat(chat_id)
        #add_message(session, chat)
        return chat
