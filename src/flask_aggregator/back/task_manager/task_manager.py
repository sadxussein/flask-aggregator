"""Task manager module."""

import time
import signal
import queue
import threading
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor

class Command(ABC):
    @abstractmethod
    def execute(self):
        pass


class CreateVMInOvirt(Command):
    """Dummy class for creating single VM."""
    def __init__(self, config: str):
        self._config = config

    def execute(self):
        print(f"Creating oVirt VM by config: {self._config}")


class GetVMsFromOvirt(Command):
    """Dummy class for getting VM list."""
    def execute(self):
        print("GetVMsFromOvirt", ["VM1", "VM2", "VM3"])


class CommandFactory:
    @staticmethod
    def make_command(name: str, **kwargs) -> Command:
        if name == "get_vms_from_ovirt":
            return GetVMsFromOvirt()
        elif name == "create_vm_in_ovirt":
            return CreateVMInOvirt(kwargs["config"])
        else:
            raise ValueError("Unknown command.")


class TaskRunStrategy(ABC):
    pass


class OneTimeRun(TaskRunStrategy):
    def __init__(self, max_retries: int=3, retry_interval: int=10):
        if max_retries < 1 or retry_interval < 1:
            raise ValueError("Max retries can not be less than 1.")
        self._max_retries = 3
        self._retry_interval = 10
        self._retry_count = 0
        self._last_run_time = time.time()
        self._was_last_run_successful = False

    @property
    def last_run_time(self):
        """In epoch time."""
        return self._last_run_time
    
    @last_run_time.setter
    def last_run_time(self):
        self._last_run_time = time.time()

    @property
    def was_last_run_successful(self):
        return self._was_last_run_successful
    
    @was_last_run_successful.setter
    def was_last_run_successful(self, value: bool):
        self._was_last_run_successful = value

    def has_to_retry(self):
        if not self._was_last_run_successful and self._retry_count < self._max_retries:
            self._retry_count += 1
            return True
        return False


class IntervalRun(OneTimeRun):
    def __init__(self, interval: int=60):
        self._interval = interval
        self._next_run_time = self._last_run_time + interval

    def calc_next_run_time(self):
        """Add interval time to last time run."""
        self._next_run_time = self._last_run_time + self._interval

    @property
    def next_run_time(self) -> int:
        """_summary_

        Returns:
            int: Time (in epoch) when task should be ran next.
        """
        if self._next_run_time > time.now():
            return self._next_run_time
        self._next_run_time = self._last_run_time + self._interval

    @next_run_time.setter
    def next_run_time(self):
        pass

class Task:
    """Abstract task class. Runs all operations."""
    def __init__(self, command: Command, strategy: TaskRunStrategy):
        self._command = command
        self._strategy = strategy
        self._was_last_run_successful = False

    @property
    def was_last_run_successful(self):
        """For retries. If failed - retry a set number of times."""
        return self._was_last_run_successful

    def run(self):
        self._command.execute()

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
        self._futures = []

    def add_task(self, task: Task):
        """Add task to task queue."""
        self._task_queue.put(task)

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

    def __append_tasks_from_queue(self):
        while not self._task_queue.empty():
            task = self._task_queue.get()
            with self._lock:
                self._tasks.append(task)

    def __run_tasks(self):
        now = time.time()
        with self._lock:
            for i, task in enumerate(self._tasks):
                if now >= task.next_run_time:
                    future = self._executor.submit(task.run)
                    task.set_last_run_time = now
                    self._tasks[i] = task
                    self._futures.append(future)
            
            for f in self._futures:
                print(f.result())

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