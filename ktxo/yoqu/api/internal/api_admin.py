import logging

from fastapi import APIRouter, Depends

from ktxo.yoqu.api.rpa import get_manager, valid_resource


logger = logging.getLogger("ktxo.yoqu")

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/")
async def list_resources(manager=Depends(get_manager)) -> list[str]:
    return list(manager.rpas.keys())


@router.get("/{resource_name}", dependencies=[Depends(valid_resource)])
async def get_info(resource_name: str, manager=Depends(get_manager)) -> dict:
    return manager.rpas[resource_name].info()


@router.get("/status/", summary="Status for all resources")
async def get_status(manager=Depends(get_manager)) -> dict[str, bool]:
    rc = {}
    for name, rpa in manager.rpas.items():
        rc[name] = manager.status(name)
    return rc


@router.get("/status/{resource_name}")
async def get_status(resource_name: str, manager=Depends(get_manager), ok=Depends(valid_resource)) -> dict[str, bool]:
    return {resource_name: manager.status(resource_name)}


@router.post("/refresh/{resource_name}", dependencies=[Depends(valid_resource)])
async def refresh(resource_name: str, manager=Depends(get_manager)):
    async with manager.get_resource(resource_name) as rpa:
        print(f"Returning {rpa}")
        rpa.refresh()
        return rpa.info()


@router.post("/start/{resource_name}", dependencies=[Depends(valid_resource)])
async def start(resource_name: str, manager=Depends(get_manager)):
    async with manager.get_resource(resource_name) as rpa:
        print(f"Returning {rpa}")
        rpa.start()
        return rpa.info()


@router.post("/stop/{resource_name}", dependencies=[Depends(valid_resource)])
async def stop(resource_name: str, manager=Depends(get_manager)):
    async with manager.get_resource(resource_name) as rpa:
        rpa.stop()
    return {"stop": "TODO", "resource": resource_name}


@router.post("/restart/{resource_name}", dependencies=[Depends(valid_resource)])
async def restart(resource_name: str, manager=Depends(get_manager)):
    return {"restart": "TODO", "resource": resource_name}


@router.get("/stats/{resource_name}")
async def get_stats(resource_name: str, manager=Depends(get_manager), ok=Depends(valid_resource)) -> dict:
    return manager.stats(resource_name)
