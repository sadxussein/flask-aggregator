"""Task manager module."""

import queue
import signal
import threading
import time
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor


class Command(ABC):
    """Abstract class for all commands."""
    @property
    @abstractmethod
    def success(self) -> bool:
        """Test method."""

    @abstractmethod
    def execute(self):
        """Exectute real class commands."""


class CreateVMInOvirt(Command):
    """Dummy class for creating single VM."""

    def __init__(self, config: str):
        self._config = config

    @property
    def success(self) -> bool:
        return True  # DEBUG

    def execute(self) -> bool:
        print(f"Creating oVirt VM by config: {self._config}")
        return self.success


class GetVMsFromOvirt(Command):
    """Dummy class for getting VM list."""

    @property
    def success(self) -> bool:
        return False  # DEBUG

    def execute(self) -> bool:
        print("GetVMsFromOvirt", ["VM1", "VM2", "VM3"])
        return self.success


class CommandFactory:
    """So far only for tests."""
    @staticmethod
    def make_command(name: str, **kwargs) -> Command:
        if name == "get_vms_from_ovirt":
            return GetVMsFromOvirt()
        elif name == "create_vm_in_ovirt":
            return CreateVMInOvirt(kwargs["config"])
        else:
            raise ValueError("Unknown command.")


class TaskRunStrategy(ABC):
    """Abstract class for task run strategies."""
    @property
    @abstractmethod
    def task_has_to_run(self):
        """Make sure that task was run at least once."""

    @abstractmethod
    def update_times(self): # TODO: remove?
        """Necessary timestamps in epoch time: creation time, last run 
        time, next run time, etc."""


class OneTimeRun(TaskRunStrategy):
    """For tasks that have to be run once."""
    TASK_WAS_NOT_RUN_YET = -1

    def __init__(self):
        self._time_created = time.time()
        self._last_run_time = self.TASK_WAS_NOT_RUN_YET

    @property
    def last_run_time(self):
        """In epoch time."""
        return self._last_run_time

    @property
    def was_run_once(self):
        """If last run time is not -1, then task was run once."""
        return self._last_run_time != self.TASK_WAS_NOT_RUN_YET

    @property
    def task_has_to_run(self):
        return self._last_run_time == self.TASK_WAS_NOT_RUN_YET

    def update_times(self): # TODO: remove?
        self._last_run_time = time.time()

    def mark_now_as_last_run_time(self):
        """Set last run time for task."""
        self._last_run_time = time.time()


class IntervalRun(OneTimeRun):
    """For repeated tasks."""
    def __init__(self, interval: int = 60):
        if interval <= 0:
            raise ValueError("Time interval can not be equal or less than 0.")
        super().__init__()
        self._interval = interval
        self._next_run_time = self.TASK_WAS_NOT_RUN_YET
        self.__calc_next_run_time()

    def __calc_next_run_time(self):
        """Add interval time to last time run. Or, if it is empty, to time
        created."""
        if self._last_run_time == self.TASK_WAS_NOT_RUN_YET:
            self._next_run_time = self._time_created + self._interval
        else:
            self._next_run_time = self._last_run_time + self._interval

    def update_times(self): # TODO: remove?
        self._last_run_time = time.time()
        self.__calc_next_run_time()

    @property
    def task_has_to_run(self):
        if self._next_run_time <= time.time():
            return True
        return False


# TODO: consider necessity of this class.
class RetryRun(OneTimeRun):
    def __init__(self, max_retries: int = 3, retry_interval: int = 10):
        super().__init__()
        if max_retries < 1 or retry_interval < 1:
            raise ValueError("Max retries can not be less than 1.")
        self._max_retries = 3
        self._retry_interval = 10
        self._retry_count = 0
        self._was_last_run_successful = False

    @property
    def was_last_run_successful(self):
        return self._was_last_run_successful

    @was_last_run_successful.setter
    def was_last_run_successful(self, value: bool):
        self._was_last_run_successful = value

    def has_to_retry(self):
        if (
            not self._was_last_run_successful
            and self._retry_count < self._max_retries
        ):
            self._retry_count += 1
            return True
        return False


class Task:
    """Abstract task class. Runs all operations."""

    def __init__(self, command: Command, strategy: TaskRunStrategy):
        self._command = command
        self._strategy = strategy

    @property
    def was_last_run_successful(self):
        """For retries. If failed - retry a set number of times."""
        return self._command.success

    @property
    def is_periodic(self):
        """Should task be run with intervals?"""
        # TODO: this is temporary solution. Perhaps other ways of defining
        # whether task is periodic or not should be implemented.
        if isinstance(self._strategy, IntervalRun):
            return True
        return False

    @property
    def last_run_time(self):
        """When (in epoch time) was task last run?"""
        return self._strategy.last_run_time

    @property
    def has_to_run(self):
        """Should task be run?"""
        return self._strategy.task_has_to_run

    def run(self):
        """Execute commands and mark time, when in was run (in epoch
        seconds)."""
        self._strategy.update_times()
        self._command.execute()


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
        self._task_queue = queue.Queue()
        self._lock = threading.Lock()
        self._running = True
        self._futures = []

    def add_task(self, task: Task):
        """Add task to task queue."""
        self._task_queue.put(task)

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
                if iteration >= max_iterations:
                    break

            time.sleep(1)

    def __append_tasks_from_queue(self):
        while not self._task_queue.empty():
            task = self._task_queue.get()
            with self._lock:
                self._tasks.append(task)

    def __run_tasks(self):
        with self._lock:
            for i, task in enumerate(self._tasks):
                if task.has_to_run:
                    future = self._executor.submit(task.run)
                    self._tasks[i] = task
                    self._futures.append(future)
            # TODO: Periodic tasks might be still running when their next
            # iteration comes to running time. Need to check this.
            for f in self._futures:
                f.result()

    def stop(self):
        """Shutdown all processes gracefully. Waiting for processes to
        finish."""
        self._running = False
        self._executor.shutdown(wait=True)
