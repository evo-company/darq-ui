import inspect
import logging
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from typing import cast

from darq.app import Darq
from darq.jobs import (
    DeserializationError,
    JobDef,
)
from darq.types import DarqTask
from darq.worker import Task as WorkerTask


log = logging.getLogger(__name__)


DROP_TASKS_KEY = "darq:drop_tasks"
PAUSE_TASKS_KEY = "darq:pause_tasks"


@dataclass
class TaskInfo:
    signature: str
    doc: str


class TaskStatus(Enum):
    RUNNING = "running"
    DROPPED = "dropped"


@dataclass
class Task:
    name: str
    status: TaskStatus | None
    enqueue_time: str | None
    signature: str | None
    doc: str | None
    dropped_reason: str | None = None


class DarqHelper:
    def __init__(self, darq_app: Darq) -> None:
        self.darq_app = darq_app

    async def get_drop_tasks(self) -> dict[str, str]:
        """Get all tasks that are in drop list.

        Returns a dictionary where key is task name and value is reason why task
        """
        raw_drop_tasks = await self.darq_app.redis_pool.hgetall(DROP_TASKS_KEY)
        return dict(raw_drop_tasks.items())

    def get_all_registered_jobs(self) -> list[str]:
        return sorted(self.darq_app.registry.keys())

    def get_darq_job_by_name(self, job_name: str) -> WorkerTask | None:
        return self.darq_app.registry.get(job_name)

    def get_job_coro_by_name(self, job_name: str) -> DarqTask | None:
        arq_function = self.get_darq_job_by_name(job_name)
        if not arq_function:
            return None
        return cast(DarqTask, arq_function.coroutine)

    def get_darq_tasks_info(self) -> dict[str, TaskInfo]:
        job_names = self.get_all_registered_jobs()

        task_info = {}
        for job_name in job_names:
            job = self.get_job_coro_by_name(job_name)
            if not job:
                continue
            signature = inspect.signature(job).replace(
                return_annotation=inspect.Signature.empty
            )

            # TODO(m.kind): remove ctx param from signature
            task_info[job_name] = TaskInfo(
                str(signature),
                job.__doc__ or "",
            )

        return task_info

    async def get_darq_tasks_for_admin(self) -> list[Task]:
        job_names = self.get_all_registered_jobs()

        queued_jobs = []

        try:
            queued_jobs = await self.darq_app.redis_pool.queued_jobs()
        except DeserializationError:
            log.exception("Can not get darq queued jobs")

        queued_jobs_map = {job.function: job for job in queued_jobs}

        tasks_info = self.get_darq_tasks_info()
        dropped_tasks = await self.get_drop_tasks()

        tasks = []
        for job_name in job_names:
            job_def: JobDef | None = queued_jobs_map.get(job_name)
            task_info = tasks_info[job_name]

            status = None
            if job_def:
                status = TaskStatus.RUNNING

            if job_name in dropped_tasks:
                status = TaskStatus.DROPPED

            task = Task(
                name=job_name,
                status=status,
                enqueue_time=job_def.enqueue_time.isoformat()
                if job_def
                else None,
                signature=task_info.signature,
                doc=task_info.doc,
                dropped_reason=dropped_tasks.get(job_name),
            )
            tasks.append(task)

        return tasks

    async def is_task_in_droplist(self, task_name: str) -> bool:
        return await self.darq_app.redis_pool.hexists(DROP_TASKS_KEY, task_name)

    async def drop_add(
        self, task_name: str, reason: str, user: str = "unknown"
    ) -> None:
        """Add task to drop list with reason and user who dropped task.

        Being in drop list means that task will be skipped on start.

        WARNING: it does not stop tasks which are already running. It only works
        on tasks that are not started yet or that are working in batches
        and running itselves.
        """
        add_date = datetime.now().strftime("%d.%m.%y %H:%M")
        reason = f"added to drop list by '{user}' on '{add_date}' because of '{reason}'"
        await self.darq_app.redis_pool.hset(DROP_TASKS_KEY, task_name, reason)

    async def drop_remove(self, task_name: str) -> None:
        """Remove task from drop list. After this operation a task can be
        started again."""
        await self.darq_app.redis_pool.hdel(DROP_TASKS_KEY, task_name)
