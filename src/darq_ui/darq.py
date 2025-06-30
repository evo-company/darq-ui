import asyncio
import inspect
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import cast

from darq.app import Darq
from darq.jobs import DeserializationError, JobDef
from darq.types import DarqTask
from darq.worker import Task as WorkerTask

from darq_ui.utils import DEFAULT_QUEUES

log = logging.getLogger(__name__)


DROP_TASKS_KEY = "darq:drop_tasks"
PAUSE_TASKS_KEY = "darq:pause_tasks"


class DarqTaskDroppedError(Exception):
    pass


@dataclass
class TaskInfo:
    signature: str
    doc: str


@dataclass
class JobDefWithQueue:
    queue: str
    job: JobDef


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
    queue: str | None = None
    dropped_reason: str | None = None


class DarqHelper:
    def __init__(self, darq_app: Darq) -> None:
        self.darq_app = darq_app

    async def get_drop_tasks(self) -> dict[str, str]:
        """Get all tasks that are in drop list.

        Returns a dictionary where key is task name and value is reason why task
        """
        assert self.darq_app.redis_pool
        raw_drop_tasks = await self.darq_app.redis_pool.hgetall(DROP_TASKS_KEY)
        return dict(raw_drop_tasks.items())

    def get_all_registered_jobs(self) -> list[str]:
        assert self.darq_app.redis_pool
        return sorted(self.darq_app.registry.keys())

    def get_darq_job_by_name(self, job_name: str) -> WorkerTask | None:
        assert self.darq_app.redis_pool
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

    async def get_darq_tasks_for_admin(
        self,
        queues: list[str] | None = None,
    ) -> list[Task]:
        assert self.darq_app.redis_pool
        job_names = self.get_all_registered_jobs()

        if queues is None:
            queues = DEFAULT_QUEUES

        async def get_queued_jobs(queue: str) -> list[JobDefWithQueue]:
            try:
                jobs = await self.darq_app.redis_pool.queued_jobs(
                    queue_name=queue
                )
                return [JobDefWithQueue(queue, j) for j in jobs]
            except DeserializationError:
                log.exception(
                    "Can not get darq queued jobs for queue %s",
                    queue,
                )
                return []

        queued_jobs = await asyncio.gather(
            *[get_queued_jobs(q) for q in queues],
            return_exceptions=True,
        )

        queued_jobs_map: dict[str, JobDefWithQueue] = {}
        for res in queued_jobs:
            if isinstance(res, BaseException):
                raise res

            for j in res:
                queued_jobs_map[j.job.function] = j

        tasks_info = self.get_darq_tasks_info()
        dropped_tasks = await self.get_drop_tasks()

        tasks = []
        for job_name in job_names:
            job_def: JobDef | None = None
            queue: str | None = None
            if j := queued_jobs_map.get(job_name):
                job_def = j.job
                queue = j.queue

            task_info = tasks_info[job_name]

            status = None
            if job_def:
                status = TaskStatus.RUNNING

            if job_name in dropped_tasks:
                status = TaskStatus.DROPPED

            task = Task(
                name=job_name,
                status=status,
                enqueue_time=(
                    job_def.enqueue_time.isoformat() if job_def else None
                ),
                signature=task_info.signature,
                doc=task_info.doc,
                queue=queue,
                dropped_reason=dropped_tasks.get(job_name),
            )
            tasks.append(task)

        return tasks

    async def is_task_in_droplist(self, task_name: str) -> bool:
        assert self.darq_app.redis_pool
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
        assert self.darq_app.redis_pool
        add_date = datetime.now().strftime("%d.%m.%y %H:%M")
        reason = f"added to drop list by '{user}' on '{add_date}' because of '{reason}'"
        await self.darq_app.redis_pool.hset(DROP_TASKS_KEY, task_name, reason)

    async def drop_remove(self, task_name: str) -> None:
        """Remove task from drop list. After this operation a task can be
        started again."""
        assert self.darq_app.redis_pool
        await self.darq_app.redis_pool.hdel(DROP_TASKS_KEY, task_name)

    async def maybe_drop_task(self, task_name: str) -> None:
        """Check if task is in drop list and raise exception if it is.

        This function should be called before worker starts processing task.
        """
        assert self.darq_app.redis_pool
        if await self.is_task_in_droplist(task_name):
            reason = await self.darq_app.redis_pool.hget(
                DROP_TASKS_KEY, task_name
            )
            raise DarqTaskDroppedError(f"Task dropped: {reason}")


async def maybe_drop_task(darq: Darq, task_name: str) -> None:
    darq_helper = DarqHelper(darq)
    await darq_helper.maybe_drop_task(task_name)
