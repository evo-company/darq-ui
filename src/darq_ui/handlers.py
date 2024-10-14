import json
import logging
import pkgutil

from typing import Generic, TypeVar
from dataclasses import dataclass
from pydantic import BaseModel

from darq.app import Darq
from darq_ui.darq import Task, TaskStatus
from darq_ui.darq import DarqHelper
from darq_ui.utils import DarqUIConfig, join_url

log = logging.getLogger(__name__)

P = TypeVar("P", dict, BaseModel)


class Success(BaseModel, Generic[P]):
    payload: P | None = None
    error: None = None
    success: bool = True


class Failure(BaseModel, Generic[P]):
    payload: P | None = None
    error: str | None = None
    success: bool = False


def ok_response(
    payload: P | None = None,
) -> Success:
    return Success(
        error=None,
        payload=payload,
    )


def error_response(
    error: str | None = None,
) -> Failure:
    return Failure(
        error=error,
        payload=None,
    )


class TaskBody(BaseModel):
    name: str
    signature: str | None
    docstring: str | None
    status: TaskStatus | None
    dropped_reason: str | None

    class Config:
        use_enum_values = True


class TasksResponse(BaseModel):
    tasks: list[TaskBody]


class RunTaskResponse(BaseModel):
    task_id: str


class DropTaskResponse(BaseModel):
    task_name: str


class RemoveTaskFromDroplistResponse(BaseModel):
    task_name: str


@dataclass
class ErrorResult:
    error: str


@dataclass
class RunTaskResult:
    task_id: str


def get_index_page(ui_config: DarqUIConfig) -> str | None:
    try:
        page = pkgutil.get_data("darq_ui", "static/index.html")
    except FileNotFoundError:
        return None

    if not page:
        return None

    static_path = join_url(ui_config.base_path, "/static")
    config_str = json.dumps(ui_config.to_dict())

    page = page.replace(b"{{CONFIG}}", config_str.encode("utf-8"))
    page = page.replace(b"{{DYNAMIC_BASE}}", static_path.encode("utf-8"))

    return page.decode("utf-8")


async def get_tasks(darq_app: Darq) -> list[Task]:
    darq_helper = DarqHelper(darq_app)
    return await darq_helper.get_darq_tasks_for_admin()


async def run_task(
    darq_app: Darq,
    task_name: str,
    task_args: str | None = None,
    task_kwargs: str | None = None,
) -> ErrorResult | RunTaskResult:
    darq_helper = DarqHelper(darq_app)

    if await darq_helper.is_task_in_droplist(task_name):
        return ErrorResult(
            error="Task is in drop list and can not be run!",
        )

    try:
        t_args = json.loads(task_args or "[]")
    except json.JSONDecodeError:
        return ErrorResult(
            error="Failed to deserialize task args :(",
        )

    try:
        t_kwargs = json.loads(task_kwargs or "{}")
    except json.JSONDecodeError:
        return ErrorResult(
            error="Failed to deserialize task args :(",
        )

    darq_task = darq_helper.get_job_coro_by_name(task_name)

    if not darq_task:
        return ErrorResult(
            error=f'Task with name "{task_name}" does not exist!',
        )

    log.debug(
        "Run task %s with args %s and kwargs %s",
        task_name,
        t_args,
        t_kwargs,
    )

    job = await darq_task.delay(*t_args, **t_kwargs)

    if not job:
        return ErrorResult(
            error="Task failed to run",
        )

    return RunTaskResult(
        task_id=job.job_id,
    )


async def drop_task(darq_app: Darq, task_name: str, reason: str) -> None:
    """Stop running task by name and add it to a droplist.
    It can not be run again until removed from droplist."""
    darq_helper = DarqHelper(darq_app)
    await darq_helper.drop_add(task_name, reason)


async def remove_task_from_droplist(darq_app: Darq, task_name: str) -> None:
    darq_helper = DarqHelper(darq_app)
    await darq_helper.drop_remove(task_name)
