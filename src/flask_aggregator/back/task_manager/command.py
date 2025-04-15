"""Commands and its factory module."""

from typing import Any
from abc import ABC, abstractmethod

from flask_aggregator.back.ovirt_helper import OvirtHelper

class State:
    """Command states."""
    NEW = "new"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


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


# TODO: think this through. We are close to making real oVirt interaction
# command. Need to think what to pass to command - user, pass, engine link
# etc. Perhaps OvirtCommand should be subclassed by real command classes.
# This one might be needed only for storing login credentials or urls.
class OvirtCommand(Command):
    """Base class for oVirt interactions."""
    def __init__(self):
        super().__init__()
        # TODO: below is just a test!
        self._helper = OvirtHelper(urls_list=["e15-test2"])

    def execute(self):
        self.result = self._helper.get_hosts()

class VMWareCommand(Command):
    pass

class RosplatformaCommand(Command):
    pass


class CommandFactory:
    """So far only for tests."""
    @staticmethod
    def make_command(name: str, **kwargs) -> Command:
        """Factory method for commands.

        Args:
            name (str): Command name.

        Raises:
            ValueError: For unknown commands.

        Returns:
            Command: command class instance.
        """
        raise ValueError("Unknown command.")
