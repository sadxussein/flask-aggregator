"""Task manager module."""

import time
import signal
import queue
import threading
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor

class Task(ABC):
    """Abstract task class. Runs all operations."""
    def __init__(self, retries: int=1, retry_timeout: int=60, interval: int=None):
        self._retries = retries
        self._retry_timeout = retry_timeout
        self._was_last_run_successful = False
        self._interval = interval
        self._last_run_time = None

    @property
    def interval(self) -> int:
        """In seconds."""
        return self._interval

    @property
    def next_run_time(self):
        """In epoch time."""
        if self._last_run_time is None:
            self._last_run_time = time.time()
            return self._last_run_time
        return self._last_run_time + self._interval

    @property
    def was_last_run_successful(self):
        """For retries. If failed - retry a set number of times."""
        return self._was_last_run_successful

    def set_last_run_time(self):
        """In epuch time."""
        self._last_run_time = time.time()

    @abstractmethod
    def run(self):
        """Run task."""

class CreateVMInOvirt(Task):
    """Dummy class for creating single VM."""
    def run(self):
        print("Created VM in oVirt.")
        return "oVirt VM"

class GetVMsFromOvirt(Task):
    """Dummy class for getting VM list."""
    def run(self):
        print("Got VM list from oVirt.")
        return ["VM1", "VM2", "VM3"]

class TaskFactory:
    """Factory method class for tasks."""
    @staticmethod
    def make_task(task_name: str):
        """Get task object by string."""
        if task_name == "create_vm_in_ovirt":
            return CreateVMInOvirt()
        elif task_name == "get_vms_from_ovirt":
            return GetVMsFromOvirt(600)
        else:
            raise ValueError("Unknown task.")


class TaskManager:
    """TM singleton class."""
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, max_workers: int=20):
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="fatm")
        self._tasks = []
        self._task_queue = queue.Queue()
        self._lock = threading.Lock()
        self._running = True

    def add_task(self, task: Task):
        """Add task to task queue."""
        self._task_queue.put(task)

    def __append_tasks_from_queue(self):
        while not self._task_queue.empty():
            task = self._task_queue.get()
            with self._lock:
                self._tasks.append(task)

    def __run_tasks(self):
        now = time.time()
        with self._lock:
            for i, task in enumerate(self._tasks):
                print(now, task.next_run_time)
                if now >= task.next_run_time:
                    self._executor.submit(task)
                    task.set_last_run_time = now
                    self._tasks[i] = task

    def run(self, max_iterations: int=None):
        """Run tasks.

        Args:
            max_iterations (int, optional): Number of iterations main loop
                will be run. Debug option. Defaults to None.
        """
        iteration = 0   # DEBUG

        while self._running:
            self.__append_tasks_from_queue()
            self.__run_tasks()

            if max_iterations is not None:  # DEBUG
                iteration += 1
                if iteration >= max_iterations:
                    break

            time.sleep(1)

    def stop(self):
        """Shutdown all processes gracefully. Waiting for processes to
        finish."""
        self._running = False
        self._executor.shutdown(wait=True)















# class OneTimeTask(Task, ABC):
#     """One time task."""

# class PeriodicTask(Task, ABC):
#     """Task which should be executed within certain period of time continuously."""
#     def __init__(self, retries: int=1, interval: int=3600):
#         super().__init__(retries)
#         self._interval = interval
#         self._last_run_epoch_time = None

#     @property
#     def interval(self) -> int:
#         """In seconds."""
#         return self._interval

#     @property
#     def next_run_time(self):
#         """In epoch time."""
#         if self._last_run_epoch_time is None:
#             return time.time()
#         return self._last_run_epoch_time + self._interval