"""Task strategy module."""

import time
from abc import ABC, abstractmethod


class TaskRunStrategy(ABC):
    """Abstract class for task run strategies."""
    TASK_WAS_NOT_RUN_YET = -1

    def __init__(self):
        self.time_created = time.time()
        # Perhaps start and last run times are redundand.
        self.start_run_time = self.TASK_WAS_NOT_RUN_YET
        self.stop_run_time = self.TASK_WAS_NOT_RUN_YET
        self.last_run_time = self.TASK_WAS_NOT_RUN_YET

    @property
    @abstractmethod
    def task_has_to_run(self):
        """Make sure that task was run at least once."""

    @property
    def run_time(self):
        """How long task was executed."""
        return self.stop_run_time - self.start_run_time

    def mark_start_time(self):
        """Necessary timestamps in epoch time: creation time, last run 
        time, next run time, etc."""
        self.last_run_time = time.time()
        self.start_run_time = time.time()

    def mark_stop_time(self):
        """Mark time when task ended."""
        self.stop_run_time = time.time()


class OneTimeRun(TaskRunStrategy):
    """For tasks that have to be run once."""
    @property
    def task_has_to_run(self):
        return self.start_run_time == self.TASK_WAS_NOT_RUN_YET


class IntervalRun(OneTimeRun):
    """For repeated tasks."""
    def __init__(self, interval: int = 60):
        if interval <= 0:
            raise ValueError("Time interval can not be equal or less than 0.")
        super().__init__()
        self.interval = interval
        self.next_run_time = self.TASK_WAS_NOT_RUN_YET
        self.__calc_next_run_time()

    def __calc_next_run_time(self):
        """Add interval time to last time run. Or, if it is empty, to time
        created.
        """
        if self.last_run_time == self.TASK_WAS_NOT_RUN_YET:
            self.next_run_time = self.time_created
        else:
            self.next_run_time = self.last_run_time + self.interval

    def mark_start_time(self): # TODO: remove?
        self.start_run_time = time.time()
        self.last_run_time = time.time()
        self.__calc_next_run_time()

    @property
    def task_has_to_run(self):
        if self.next_run_time <= time.time():
            return True
        return False
