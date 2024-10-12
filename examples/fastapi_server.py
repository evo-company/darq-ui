import logging

import fastapi
import uvicorn

from fastapi import FastAPI

from darq.app import Darq
from darq.connections import RedisSettings

from darq_ui.integration.fastapi import setup

log = logging.getLogger(__name__)

darq = Darq(
    redis_settings=RedisSettings(
        host="localhost",
        port=6379,
        database=0,
    ),
    ctx={},
)


@darq.task
async def say_hello_task(name: str) -> None:
    log.info("Hello %s", name)


def create_app() -> FastAPI:
    app = FastAPI(
        debug=True,
        servers=[
            {"url": "http://localhost:3000", "description": "Dev environment"},
        ],
        openapi_tags=[
            {"name": "api", "description": "Darq-ui api"},
        ],
    )

    @app.on_event("startup")
    async def startup() -> None:
        await darq.connect()

    @app.on_event("shutdown")
    async def shutdown() -> None:
        await darq.disconnect()

    # In order for this to work, you need to run npm run build or npm run build-watch at least once
    setup(
        app,
        darq,
        base_path="/darq",
        logs_url="https://mylogserver.com/taskname=${taskName}",
    )

    log.info("Server api configured at http:0.0.0.0:3000/api endpoint")

    return app


def app_factory() -> fastapi.FastAPI:
    return create_app()


def main(reload: bool) -> None:
    uvicorn.run(
        "fastapi_server:app_factory",
        port=3000,
        host="0.0.0.0",
        reload=reload,
        factory=True,
    )


if __name__ == "__main__":
    main(reload=True)
