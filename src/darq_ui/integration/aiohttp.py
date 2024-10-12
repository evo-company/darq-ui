import pkgutil
import pathlib
import json
from typing import Any, Callable, Coroutine

from darq.app import Darq

from aiohttp import web
from aiohttp.web_response import json_response

from json import JSONDecodeError
from aiohttp.web_exceptions import HTTPNotAcceptable
from pydantic import BaseModel

from darq_ui.utils import DARQ_APP, DARQ_UI_CONFIG, DarqUIConfig
from darq_ui.handlers import (
    get_tasks,
    run_task,
    error_response,
    ok_response,
    Success,
    Failure,
    drop_task,
    remove_task_from_droplist,
    join_url,
    ErrorResult,
    TaskBody,
    TasksResponse,
    RunTaskResponse,
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
    page = pkgutil.get_data("darq_ui", "static/index.html")

    if not page:
        return web.Response(text="not found", status=404)

    ui_config: DarqUIConfig = request.app[DARQ_UI_CONFIG]
    base_static_path = join_url(ui_config.base_path, "/static")
    page = page.replace(
        b"{{CONFIG}}", json.dumps(ui_config.to_dict()).encode("utf-8")
    )
    page = page.replace(b"{{DYNAMIC_BASE}}", base_static_path.encode("utf-8"))

    return web.Response(body=page.decode("utf-8"), content_type="text/html")


@response_adapter
async def get_tasks_handler(request: web.Request) -> TasksResponse:
    darq_app = get_darq_app(request)
    tasks = await get_tasks(darq_app)

    return TasksResponse(
        tasks=[
            TaskBody(
                name=task.name,
                signature=task.signature,
                docstring=task.doc,
                status=task.status,
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
) -> None:
    app.router.add_get(base_path, index_handler)
    app.router.add_get(join_url(base_path, "/api/tasks"), get_tasks_handler)
    app.router.add_post(join_url(base_path, "/api/tasks/run"), run_task_handler)
    app.router.add_post(
        join_url(base_path, "/api/tasks/droplist/add"), drop_task_handler
    )
    app.router.add_post(
        join_url(base_path, "/api/tasks/droplist/remove"),
        remove_task_from_droplist_handler,
    )

    here = pathlib.Path(__file__).parents[1]

    app.router.add_routes(
        [web.static(join_url(base_path, "/static"), here / "static")]
    )

    app[DARQ_APP] = darq
    app[DARQ_UI_CONFIG] = DarqUIConfig(base_path=base_path, logs_url=logs_url)
