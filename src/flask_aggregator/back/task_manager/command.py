"""Commands and its factory module."""

from enum import Enum
from typing import Any
from abc import ABC, abstractmethod


class State(Enum):
    """Command states."""
    NEW = 1
    RUNNING = 2
    SUCCESS = 3
    FAILED = 4
    CANCELLED = 5


class Command(ABC):
    """Abstract class for all commands."""
    def __init__(self):
        self.result: Any = None
        self.error: str = None
        self.state: State = State.NEW

    @abstractmethod
    def execute(self):
        """Exectute real class commands."""
        # TODO: need to incorporate decorator for this method. It is
        # unappropriable for client code to be required `State` enum manual
        # incorporation every time `execute` is implemented.


# class CommandFactory:
#     """So far only for tests."""
#     @staticmethod
#     def make_command(name: str, **kwargs) -> Command:
#         """Factory method for commands.

#         Args:
#             name (str): Command name.

#         Raises:
#             ValueError: For unknown commands.

#         Returns:
#             Command: command class instance.
#         """
#         raise ValueError("Unknown command.")
