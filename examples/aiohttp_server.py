import logging
from typing import AsyncIterator

from aiohttp import web

from darq.app import Darq
from darq.connections import RedisSettings

from darq_ui.integration.aiohttp import setup

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


async def lifecycle(app) -> AsyncIterator[None]:
    await darq.connect()
    yield
    await darq.disconnect()


def create_app() -> web.Application:
    app = web.Application()

    app.cleanup_ctx.append(lifecycle)

    # In order for this to work, you need to run npm run build or npm run build-watch at least once
    setup(
        app,
        darq,
        base_path="/",
        logs_url="https://mylogserver.com/taskname=${taskName}",
    )

    log.info("Server api configured at http:0.0.0.0:3000/api endpoint")

    return app


def main() -> None:
    app = create_app()

    log.info(
        "darq-ui example aiohttp server started: %s:%d",
        "localhost",
        3000,
    )

    web.run_app(app, host="localhost", port=3000)


if __name__ == "__main__":
    main()
