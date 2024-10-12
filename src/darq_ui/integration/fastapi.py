import pkgutil
import pathlib
import json

from darq.app import Darq
from fastapi import FastAPI, Depends
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from pydantic import BaseModel
from starlette.status import HTTP_404_NOT_FOUND

from darq_ui.utils import DARQ_APP, DARQ_UI_CONFIG, DarqUIConfig
from darq_ui.handlers import (
    get_tasks,
    run_task,
    drop_task,
    remove_task_from_droplist,
    join_url,
    error_response,
    ok_response,
    ErrorResult,
    TaskBody,
    TasksResponse,
    RunTaskResponse,
    DropTaskResponse,
    RemoveTaskFromDroplistResponse,
    Success,
    Failure,
)

from typing import Annotated


def get_darq_app(request: Request) -> Darq:
    return getattr(request.app, DARQ_APP)


class RunTask(BaseModel):
    task_name: str
    task_args: str | None = None
    task_kwargs: str | None = None


class DropTask(BaseModel):
    task_name: str
    reason: str


class RemoveTaskFromDroplist(BaseModel):
    task_name: str


api_router = APIRouter()
index_router = APIRouter()


@index_router.get("/")
async def index_handler(request: Request) -> HTMLResponse:
    try:
        page = pkgutil.get_data("darq_ui", "static/index.html")
    except FileNotFoundError as e:
        error = "No index.html found"
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=error,
        ) from e

    if not page:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="No index.html found",
        )

    ui_config: DarqUIConfig = getattr(request.app, DARQ_UI_CONFIG)
    base_static_path = join_url(ui_config.base_path, "/static")
    page = page.replace(
        b"{{CONFIG}}", json.dumps(ui_config.to_dict()).encode("utf-8")
    )
    page = page.replace(b"{{DYNAMIC_BASE}}", base_static_path.encode("utf-8"))

    return HTMLResponse(page.decode("utf-8"))


@api_router.get("/tasks")
async def get_tasks_handler(
    darq_app: Annotated[Darq, Depends(get_darq_app)],
) -> TasksResponse:
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


@api_router.post(
    "/tasks/run",
    responses={
        200: {"model": Success[RunTaskResponse]},
        400: {"model": Failure},
    },
)
async def run_task_handler(
    darq_app: Annotated[Darq, Depends(get_darq_app)], task: RunTask
) -> Success | Failure:
    result = await run_task(
        darq_app,
        task.task_name,
        task.task_args,
        task.task_kwargs,
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


@api_router.post(
    "/tasks/droplist/add",
    responses={
        200: {"model": Success[DropTaskResponse]},
        400: {"model": Failure},
    },
)
async def drop_task_handler(
    darq_app: Annotated[Darq, Depends(get_darq_app)],
    task: DropTask,
) -> Success | Failure:
    """Stop running task by name and add it to a droplist.
    It can not be run again until removed from droplist."""
    await drop_task(
        darq_app,
        task.task_name,
        task.reason,
    )

    return ok_response()


@api_router.post(
    "/tasks/droplist/remove",
    responses={
        200: {"model": Success[RemoveTaskFromDroplistResponse]},
        400: {"model": Failure},
    },
)
async def remove_task_from_droplist_handler(
    darq_app: Annotated[Darq, Depends(get_darq_app)],
    task: RemoveTaskFromDroplist,
) -> Success | Failure:
    await remove_task_from_droplist(
        darq_app,
        task.task_name,
    )

    return ok_response()


def setup(
    app: FastAPI,
    darq: Darq,
    base_path: str = "/darq",
    logs_url: str | None = None,
) -> None:
    app.include_router(api_router, prefix=join_url(base_path, "/api"))
    app.include_router(
        index_router, prefix="" if base_path == "/" else base_path
    )

    here = pathlib.Path(__file__).parents[1]

    app.mount(
        join_url(base_path, "/static"),
        StaticFiles(
            directory=here / "static",
            html=True,
            check_dir=True,
        ),
        name="static",
    )

    setattr(app, DARQ_APP, darq)
    setattr(
        app,
        DARQ_UI_CONFIG,
        DarqUIConfig(base_path=base_path, logs_url=logs_url),
    )
