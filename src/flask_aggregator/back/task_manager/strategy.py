"""Task strategy module."""

import time
from abc import ABC, abstractmethod

class TaskRunStrategy(ABC):
    """Abstract class for task run strategies."""
    @property
    @abstractmethod
    def last_run_time(self):
        """In epoch time."""

    @property
    @abstractmethod
    def task_has_to_run(self):
        """Make sure that task was run at least once."""

    @abstractmethod
    def mark_run_time(self): # TODO: remove?
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

    # @property
    # def was_run_once(self):
    #     """If last run time is not -1, then task was run once."""
    #     return self._last_run_time != self.TASK_WAS_NOT_RUN_YET

    @property
    def task_has_to_run(self):
        return self._last_run_time == self.TASK_WAS_NOT_RUN_YET

    def mark_run_time(self): # TODO: remove?
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
            self._next_run_time = self._time_created
        else:
            self._next_run_time = self._last_run_time + self._interval

    def mark_run_time(self): # TODO: remove?
        self._last_run_time = time.time()
        self.__calc_next_run_time()

    @property
    def task_has_to_run(self):
        if self._next_run_time <= time.time():
            return True
        return False
