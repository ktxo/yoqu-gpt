import logging

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from ktxo.yoqu.config import settings
from ktxo.yoqu.db import get_session
from ktxo.yoqu.api.rpa import valid_resource

logger = logging.getLogger("ktxo.yoqu")

router = APIRouter(prefix="/yoqu/db", tags=["api"] )

templates = Jinja2Templates(directory=settings.api_template_folder)



@router.get("/completions/",
            summary="DB- List of Completions/chats from resource",
            dependencies=[Depends(valid_resource)],
            response_class=HTMLResponse)
async def get_completions(request: Request,
                          resource_name:str|None = None,
                          session: AsyncSession = Depends(get_session)):
    async with session:
        #from ktxo.yoqu.db import get_messages
        #rows = await get_messages()
        rows = []
        return templates.TemplateResponse("completions.html", {"request": request, "items": rows})
#
#
#
#
# @router.get("/completions/{chat_id}",
#             summary="Completion/Chat details",
#             dependencies=[Depends(valid_resource)])
# async def get_completion(chat_id:str,
#                          resource_name:str|None,
#                          manager=Depends(get_manager),
#                          session: AsyncSession = Depends(get_session)):
#     logger.debug(f"Getting {chat_id}")
#     async with manager.get_resource(resource_name) as rpa:
#         return rpa.get_chat(chat_id)
