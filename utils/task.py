from asyncio import Task, create_task, sleep
from inspect import signature
from time import time
from typing import Any, Awaitable, Callable, Dict, Self

from pydantic import BaseModel

from utils.log import logger

log = logger(__name__)


# ----------------------------------------------------------------------------------------------------
# * Task reference
# ----------------------------------------------------------------------------------------------------
class TaskRef(BaseModel):
    id: Any
    callback: Callable[[Self | None], Awaitable[None]] | None = None
    delay: float = 0.0
    loop: bool = False
    _task: Task | None = None
    _start_at: float = 0.0
    _end_at: float = 0.0

    def model_post_init(self, __context):
        self._start_at = time()
        self._end_at = self._start_at + self.delay
        self._task = create_task(self._execute_loop() if self.loop else self._execute())

    @property
    def time_left(self):
        return max(0, round(self._end_at - time()))

    def cancel(self):
        if self._task:
            self._task.cancel()

    async def _execute_loop(self):
        while True:
            await self._execute()

    async def _execute(self):
        if self.delay > 0:
            await sleep(self.delay)
        if self.callback:
            try:
                params_count = len(signature(self.callback).parameters)
                if params_count == 0:
                    await self.callback()  # type: ignore
                elif params_count == 1:
                    await self.callback(self)
                else:
                    raise ValueError("Callback must have 0 or 1 parameter.")
            except Exception as e:
                log.exception(f"Task '{id}' error: {e}")

    def on_done(self, fn: Callable[[Task], object]):
        if self._task:
            self._task.add_done_callback(fn)


# ----------------------------------------------------------------------------------------------------
# * Act Task Manager
# ----------------------------------------------------------------------------------------------------
class ActTaskManager:
    """Manage concurrent tasks."""

    def __init__(self):
        self._tasks: Dict[Any, TaskRef] = {}

    # ----------------------------------------------------------------------------------------------------

    def schedule(
        self,
        id: Any,
        callback: Callable[[TaskRef | None], Awaitable[None]] | None = None,
        delay: float = 0,
        loop: bool = False,
    ) -> bool:
        """Schedule a task for asynchronous execution.
        Args:
            id: Unique identifier for the scheduled task.
            callback: Asynchronous callback function that accepts a **TaskRef** parameter.
            delay: Time delay before execution in _seconds_.
            loop: Whether the task should execute repeatedly.
        Returns:
            bool: True if scheduling succeed, False if task already exists.
        """
        if id in self._tasks:
            log.exception(f"Task '{id}' already exists.")
            return False
        task_ref = self._tasks[id] = TaskRef(
            id=id, callback=callback, delay=delay, loop=loop
        )
        task_ref.on_done(lambda _: self.remove(id))
        return True

    # ----------------------------------------------------------------------------------------------------

    def task_ref(self, id: Any) -> TaskRef | None:
        self._tasks.get(id)

    def remove(self, task_id: Any) -> None:
        """Remove task from the task manager."""
        if task_id in self._tasks:
            del self._tasks[task_id]

    def cancel(self, id: Any) -> bool:
        """Cancel and remove task of given id. If non-existent get False."""
        if id in self._tasks:
            self._tasks[id].cancel()
            del self._tasks[id]
            return True
        return False

    def cancel_all(self):
        """Cancel all tasks."""
        for id in list(self._tasks.keys()):
            self._tasks[id].cancel()
            del self._tasks[id]

    def time_left(self, id: Any) -> float | None:
        """Get remaining time for task of given id. If non-existent get None."""
        if id in self._tasks:
            return self._tasks[id].time_left
        return None

    def is_running(self, id: Any) -> bool:
        """Check if task of given id is running."""
        return id in self._tasks
