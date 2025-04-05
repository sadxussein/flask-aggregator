"""For updating info about task progress/status."""

from abc import ABC, abstractmethod

class Observer(ABC):
    """Abstract class for task observers."""
    def __init__(self):
        self._state = None

    @property
    def state(self):
        """State of task."""
        return self._state

    @abstractmethod
    def update(self, state: str):
        """Update task current state."""


class State(Observer):
    """Concrete class for keeping entity status up-to-date result."""
    def update(self, state):
        self._state = state


class TaskState(Observer):
    """Concrete class for keeping task status up-to-date."""
    def update(self, state):
        self._state = state


class CommandState(Observer):
    """Concrete class for keeping command status up-to-date."""
    def update(self, state):
        self._state = state
