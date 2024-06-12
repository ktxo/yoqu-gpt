from contextlib import asynccontextmanager
import json
import logging.config

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from ktxo.yoqu.config import settings
from ktxo.yoqu.common.exceptions import YoquException
from ktxo.yoqu.api.rpa import init_rpa
from ktxo.yoqu.api.internal import api_admin
from ktxo.yoqu.api.routers import api_resource, api_db

# ----------------------------------------------------------------------
#
# with open("logging.json", 'r', encoding="utf-8") as fd:
#     logging.config.dictConfig(json.load(fd))

# ----------------------------------------------------------------------
tags_metadata = [
    {
        "name": "admin",
        "description": "Resources admin",
    },
    {
        "name": "api",
        "description": "Completions/Chats",
    },
]
api_description = """
### yoquGPT / w2uGPT / iwuGPT 

- **yoqu :** yo quiero usar
- **w2u :** want to use 
- **iwu :** I want to use

(Hacking ChatGPT, or just an use case to play for a while)
 
More details in repository [https://github.com/ktxo/yoqu-gpt](https://github.com/ktxo/yoqu-gpt)
"""

# ----------------------------------------------------------------------
logger = logging.getLogger("ktxo.yoqu")

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_rpa()
    yield
    # Cleanup
    logger.info(f"Lifespan end.")


app = FastAPI(title="Yoqu API", description=api_description, openapi_tags=tags_metadata, lifespan=lifespan)
app.include_router(api_admin.router)
app.include_router(api_resource.router)
app.include_router(api_db.router)


# ----------------------------------------------------------------------

@app.exception_handler(YoquException)
async def unicorn_exception_handler(request: Request, exc: YoquException):
    logger.error(f"Got {exc.__class__.__name__}: {exc}")
    return JSONResponse(status_code=500, content={"message": str(exc)}, )



if __name__ == "__main__":
    import uvicorn

    with open("logging.json", 'r', encoding="utf-8") as fd:
        logging.config.dictConfig(json.load(fd))

    uvicorn.run("main:app",
                host=settings.api_address,
                port=settings.api_port,
                reload=False,
                workers=1,
                use_colors=True,
                log_config="logging.json")