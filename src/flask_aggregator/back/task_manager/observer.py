"""For updating info about task progress/status."""

from abc import ABC, abstractmethod
from typing import Any


class Observer(ABC):
    """Abstract class for task observers."""
    def __init__(self):
        self._data = None

    @property
    def data(self):
        """State of task."""
        return self._data

    @abstractmethod
    def update(self, data: Any):
        """Update task current state."""


class TaskState(Observer):
    """Concrete class for task registry observer."""
    def update(self, data: dict[str, Any]):
        self._data = (
            f'name: {data["name"]} result: {data["result"]}'
            f'error: {data["error"]}'
            f'last_run_time: {int(data["last_run_time"])}'
        )
