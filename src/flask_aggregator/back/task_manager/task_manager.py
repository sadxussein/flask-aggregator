"""Task manager module."""

import queue
import threading
import time
import uuid
from typing import Dict, Any
from concurrent.futures import ThreadPoolExecutor
from flask_aggregator.back.task_manager.command import Command, State

# TODO: this import requires reconfiguration. There should be factory method
# or something like that. Maybe only interface/abstract class.
from flask_aggregator.back.task_manager.strategy import TaskRunStrategy

# TODO: this import requires attention. Perhaps, if there will be more
# observers, some other import/use of Observer pattern approach will be in
# order. Also, usage of Observer pattern here is questionable.
# from flask_aggregator.back.task_manager.observer import TaskState


class Task:
    """Abstract task class. Runs all operations."""

    def __init__(self, name: str, command: Command, strategy: TaskRunStrategy):
        self._uuid = uuid.uuid4()
        self._name = name
        self._command = command
        self._strategy = strategy

    @property
    def uuid(self):
        "Task UUID as string."
        return str(self._uuid)

    @property
    def name(self):
        "Task string name."
        return self._name

    def to_dict(self) -> dict[str, Any]:
        """JSON-friendly view of task.

        Returns:
            dict[str, Any]: Represents JSON view of task.
        """
        return {
            "uuid": str(self._uuid),
            "name": self._name,
            "last_run_time": self._strategy.last_run_time,
            "has_to_run": self._strategy.task_has_to_run,
            "state": self._command.state,
            "result": self._command.result,
            "error": self._command.error
        }

    def run(self):
        """Execute commands and mark time, when in was run (in epoch
        seconds)."""
        if self._strategy.task_has_to_run and not self._command.state in [
            State.RUNNING,
            State.FAILED,
        ]:
            self._strategy.mark_run_time()
            self._command.execute()


class TaskRegistry:
    """Holding tasks info."""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self._tasks: Dict[str, Any] = {}

    def get_tasks_uuid(self) -> list[str]:
        """List of tasks UUIDs.

        Returns:
            list[str]: UUID strings.
        """
        return list(self._tasks)

    # TODO: make sure that no task with same name exists.
    def add_task(self, task_uuid: str, task: Task):
        """Store result of task execution.

        Args:
            task_uuid (str): Task ID/name.
            result (Any): Preferably dict, but could be anything.
            error (str): Error string if there is any, None otherwise.
        """
        self._tasks[task_uuid] = task

    def get_task_by_uuid(self, task_uuid: str) -> Task:
        """Get task.

        Args:
            task_uuid (str): Desired task ID.

        Returns:
            Task: task instance.
        """
        return self._tasks[task_uuid]

    def get_task_by_name(self, task_name: str) -> Task:
        """Get task by name.

        Args:
            task_name (str): Desired task name.

        Returns:
            Task: task instance.
        """
        result = None
        for _, task in self._tasks.items():
            if task.name == task_name:
                result = task
        return result

    def delete_task(self, task_uuid: str):
        """Remore task from inventory.

        Args:
            task_uuid (str): Desired task ID/name.
        """
        self._tasks.pop(task_uuid)

    def clear(self):
        """Empty task inventory."""
        self._tasks.clear()


class TaskManager:
    """TM singleton class."""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, max_workers: int = 20):
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers, thread_name_prefix="fatm"
        )
        self._tasks = []
        self._registry = TaskRegistry()
        self._task_queue = queue.Queue()
        self._lock = threading.Lock()
        self._running = True
        self._futures = []

    def add_task(self, task: Task):
        """Add task to task queue."""
        self._task_queue.put(task)

    @property
    def registry(self):
        """Get task registry."""
        return self._registry

    def run(self, max_iterations: int = None):
        """Run tasks.

        Args:
            max_iterations (int, optional): Number of iterations main loop
                will be run. Debug option. Defaults to None.
        """
        iteration = 0  # DEBUG

        while self._running:
            self.__append_tasks_from_queue()
            self.__run_tasks()

            if max_iterations is not None:  # DEBUG
                iteration += 1
                if iteration > max_iterations:
                    break

            time.sleep(1)

        self.stop()

    def __append_tasks_from_queue(self):
        while not self._task_queue.empty():
            task = self._task_queue.get()
            with self._lock:
                self._registry.add_task(task.uuid, task)

    def __run_tasks(self):
        with self._lock:
            for uuid_ in self._registry.get_tasks_uuid():
                task = self._registry.get_task_by_uuid(uuid_)
                future = self._executor.submit(task.run)
                self._futures.append(future)

            # TODO: Periodic tasks might be still running when their next
            # iteration comes to running time. Need to check this.
            result = []
            for f in self._futures:
                result.append(f.result())

            for uuid_ in self._registry.get_tasks_uuid():
                task = self._registry.get_task_by_uuid(uuid_)

            self._futures = []

    def stop(self):
        """Shutdown all processes gracefully. Waiting for processes to
        finish."""
        self._running = False
        self._executor.shutdown(wait=True)
