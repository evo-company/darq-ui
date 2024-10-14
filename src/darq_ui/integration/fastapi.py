import pathlib
import dataclasses

from darq.app import Darq
from fastapi import FastAPI, Depends
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from pydantic import BaseModel
from starlette.status import HTTP_404_NOT_FOUND

from darq_ui.utils import DARQ_APP, DARQ_UI_CONFIG, DarqUIConfig, join_url
from darq_ui.handlers import (
    get_tasks,
    run_task,
    drop_task,
    remove_task_from_droplist,
    get_index_page,
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


def get_darq_ui_config(request: Request) -> DarqUIConfig:
    return getattr(request.app, DARQ_UI_CONFIG)


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


async def index_handler(
    ui_config: DarqUIConfig = Depends(get_darq_ui_config),
) -> HTMLResponse:
    content = get_index_page(ui_config)
    if not content:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="No index.html found",
        )
    return HTMLResponse(content)


async def embed_handler(
    ui_config: DarqUIConfig = Depends(get_darq_ui_config),
) -> HTMLResponse:
    content = get_index_page(dataclasses.replace(ui_config, embed=True))
    if not content:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="No index.html found",
        )
    return HTMLResponse(content)


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
    web_ui: bool = True,
    embed: bool = False,
) -> None:
    """Setup Darq UI in FastAPI application.

    :param app: FastAPI application
    :param darq: Darq instance
    :param base_path: base path for Darq UI.
        All api endpoints will be mounted under this path.
        Static files will be mounted under base_path + "/static".
    :param logs_url: URL to logs
    :param web_ui: enable web UI endpoint
    :param embed: enable /embed endpoint (for iframes)
    """
    if web_ui:
        index_router.add_api_route(base_path, endpoint=index_handler)
    if embed:
        index_router.add_api_route(
            join_url(base_path, "/embed"), endpoint=embed_handler
        )

    if index_router.routes:
        app.include_router(index_router)

    app.include_router(api_router, prefix=join_url(base_path, "/api"))

    if web_ui or embed:
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
