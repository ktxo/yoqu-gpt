import logging

from fastapi import Request, HTTPException

from ktxo.yoqu.config import settings
from ktxo.yoqu.rpa_manager import RPAManager

logger = logging.getLogger("ktxo.yoqu")


rpa_manager:RPAManager = None

def init_rpa():
    global rpa_manager
    rpa_manager = RPAManager(settings.rpa_config_file, settings.rpa_default_name)

async def get_manager():
    global rpa_manager
    return rpa_manager


async def valid_resource(request: Request):
    resource_name = request.path_params.get("resource_name", None)
    if not resource_name:
        return True
    manager = await get_manager()
    if not resource_name in manager.rpas :
        logger.error(f"Resource '{resource_name}' not found")
        raise HTTPException(status_code=404, detail=f"Resource '{resource_name}' not found")
    return True
