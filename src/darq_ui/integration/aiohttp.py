import dataclasses
import pathlib
from json import JSONDecodeError
from typing import Any, Callable, Coroutine

from aiohttp import web
from aiohttp.web_exceptions import HTTPNotAcceptable
from aiohttp.web_response import json_response
from darq.app import Darq
from pydantic import BaseModel

from darq_ui.handlers import (
    ErrorResult,
    Failure,
    RunTaskResponse,
    Success,
    TaskBody,
    TasksResponse,
    drop_task,
    error_response,
    get_index_page,
    get_tasks,
    ok_response,
    remove_task_from_droplist,
    run_task,
)
from darq_ui.utils import (
    DARQ_APP,
    DARQ_UI_CONFIG,
    DEFAULT_QUEUES,
    DarqUIConfig,
    join_url,
)


def get_darq_app(request: web.Request) -> Darq:
    return request.app[DARQ_APP]


async def get_json(request: web.Request) -> dict:
    if request.content_type == "application/json":
        try:
            return await request.json()
        except JSONDecodeError:
            pass
    raise HTTPNotAcceptable(text="invalid json")


def response_adapter(
    func: Callable,
) -> Callable[[web.Request], Coroutine[Any, Any, web.Response]]:
    """Allows to return Success or Failure objects from handlers"""

    async def wrapper(request: web.Request) -> web.Response:
        response = await func(request)
        if isinstance(response, Failure):
            return json_response(response.model_dump(), status=400)
        elif isinstance(response, BaseModel):
            return json_response(response.model_dump())
        return response

    return wrapper


async def index_handler(request: web.Request) -> web.Response:
    ui_config: DarqUIConfig = request.app[DARQ_UI_CONFIG]
    content = get_index_page(ui_config)
    if not content:
        return web.Response(text="not found", status=404)

    return web.Response(body=content, content_type="text/html")


async def embed_handler(request: web.Request) -> web.Response:
    ui_config: DarqUIConfig = request.app[DARQ_UI_CONFIG]
    content = get_index_page(dataclasses.replace(ui_config, embed=True))
    if not content:
        return web.Response(text="not found", status=404)

    return web.Response(body=content, content_type="text/html")


@response_adapter
async def get_tasks_handler(request: web.Request) -> TasksResponse:
    darq_app = get_darq_app(request)
    ui_config: DarqUIConfig = request.app[DARQ_UI_CONFIG]
    tasks = await get_tasks(darq_app, ui_config.queues)

    return TasksResponse(
        tasks=[
            TaskBody(
                name=task.name,
                signature=task.signature,
                docstring=task.doc,
                status=task.status,
                queue=task.queue,
                dropped_reason=task.dropped_reason,
            )
            for task in tasks
        ]
    )


@response_adapter
async def run_task_handler(
    request: web.Request,
) -> Success | Failure:
    darq_app = get_darq_app(request)
    data = await get_json(request)

    task_name = data.get("task_name")
    task_args = data.get("task_args")
    task_kwargs = data.get("task_kwargs")

    if not task_name:
        return error_response(error="task_name is required")

    if not task_args:
        return error_response(error="task_args is required")

    if not task_kwargs:
        return error_response(error="task_kwargs is required")

    result = await run_task(
        darq_app,
        task_name,
        task_args,
        task_kwargs,
    )

    if isinstance(result, ErrorResult):
        return error_response(
            error=result.error,
        )

    return ok_response(
        payload=RunTaskResponse(
            task_id=result.task_id,
        )
    )


@response_adapter
async def drop_task_handler(request: web.Request) -> Success | Failure:
    darq_app = get_darq_app(request)
    data = await get_json(request)

    task_name = data.get("task_name")
    reason = data.get("reason")

    if not task_name:
        return error_response(error="task_name is required")

    if not reason:
        return error_response(error="reason is required")

    await drop_task(
        darq_app,
        task_name,
        reason,
    )

    return ok_response()


@response_adapter
async def remove_task_from_droplist_handler(
    request: web.Request,
) -> Success | Failure:
    darq_app = get_darq_app(request)
    data = await get_json(request)

    task_name = data.get("task_name")

    if not task_name:
        return error_response(error="task_name is required")

    await remove_task_from_droplist(
        darq_app,
        task_name,
    )

    return ok_response()


def setup(
    app: web.Application,
    darq: Darq,
    base_path: str = "/darq",
    logs_url: str | None = None,
    web_ui: bool = True,
    embed: bool = False,
    queues: list[str] | None = None,
) -> None:
    """Setup Darq UI in aiohttp application.

    :param app: aiohttp application
    :param darq: Darq instance
    :param base_path: base path for Darq UI
    :param logs_url: URL to logs
    :param web_ui: enable web UI endpoint
    :param embed: enable /embed endpoint (for iframes)
    :param queues: list of queues to monitor
    """
    if web_ui:
        app.router.add_get(base_path, index_handler)
    if embed:
        app.router.add_get(join_url(base_path, "/embed"), embed_handler)

    app.router.add_get(join_url(base_path, "/api/tasks"), get_tasks_handler)
    app.router.add_post(join_url(base_path, "/api/tasks/run"), run_task_handler)
    app.router.add_post(
        join_url(base_path, "/api/tasks/droplist/add"), drop_task_handler
    )
    app.router.add_post(
        join_url(base_path, "/api/tasks/droplist/remove"),
        remove_task_from_droplist_handler,
    )

    if web_ui or embed:
        here = pathlib.Path(__file__).parents[1]
        app.router.add_routes(
            [web.static(join_url(base_path, "/static"), here / "static")]
        )

    if queues is None:
        queues = DEFAULT_QUEUES

    app[DARQ_APP] = darq
    app[DARQ_UI_CONFIG] = DarqUIConfig(
        base_path=base_path,
        logs_url=logs_url,
        queues=queues,
    )
