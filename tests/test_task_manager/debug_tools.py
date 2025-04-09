"""Debug classes for tests."""

import time
import flask_aggregator.back.task_manager.command as cmd


def mock_time_generator():
    """Simple +10 mock time generator."""
    counter = 0
    while True:
        yield counter
        counter += 10


def vm_name_generator():
    """Return some VM names."""
    i = 0
    vm_names = ["vm-name1", "vm-name2", "vm-name3"]
    while i < len(vm_names):
        yield vm_names[i]
        i += 1
    while True:
        yield "no-name-vm"


class AdditionProcess:
    """Imitation of real process that should be executed.
    
    In reality it should be some virtualization interaction, e.g. get vm list
    from oVirt.
    """
    def __init__(self, a, b):
        self._a = a
        self._b = b

    def process(self):
        """Real process imitation."""
        if not isinstance(self._a, int) or not isinstance(self._b, int):
            raise TypeError("Bad agruments. Exiting.")
        return self._a + self._b


class AdditionCommand(cmd.Command):
    """Some command, that incapulates process and its state check."""
    def __init__(self, a, b):
        super().__init__()
        self._a = a
        self._b = b

    def execute(self):
        try:
            self.state = cmd.State.RUNNING
            processor = AdditionProcess(self._a, self._b)
            self.result = processor.process()
            self.state = cmd.State.SUCCESS
        except TypeError as e:
            self.error = str(e)
            self.state = cmd.State.FAILED


class CumulativeAdditionProcess:
    """Imitation of real process that should be executed.
    
    In reality it should be some virtualization interaction, e.g. get vm list
    from oVirt.
    """
    def __init__(self, a, b, sleep=None):
        self._a = a
        self._b = b
        self._sleep = sleep
        self._result = 0
        self._elapsed_time = 0
        self._time_created = time.time()

    def process(self):
        """Real process imitation."""
        if not isinstance(self._a, int) or not isinstance(self._b, int):
            raise TypeError("Bad agruments. Exiting.")
        if self._sleep:
            time.sleep(self._sleep)
        # self._elapsed_time = time.time() - self._time_created
        self._result = self._result + self._a + self._b
        # print(self._result, self._elapsed_time)
        return self._result


class CumulativeAdditionCommand(cmd.Command):
    """Some command, that incapulates process and its state check."""
    def __init__(self, a, b, sleep=None):
        super().__init__()
        self._processor = CumulativeAdditionProcess(a, b, sleep)

    def execute(self):
        try:
            self.state = cmd.State.RUNNING
            self.result = self._processor.process()
            if self.state != cmd.State.CANCELLED:
                self.state = cmd.State.SUCCESS
        except TypeError as e:
            self.error = str(e)
            self.state = cmd.State.FAILED


class SleepProcess:
    """Imitation of long running process that should be executed as task."""
    def __init__(self, seconds: int):
        self._seconds = seconds

    def process(self):
        """Imitation of long-running task (longer than task manager update
        interval.)
        """
        if not isinstance(self._seconds, int):
            raise TypeError("Bad agruments. Exiting.")
        time.sleep(self._seconds)
        return f"has been waiting for {self._seconds} seconds"


class SleepCommand(cmd.Command):
    """Imitation of long running command."""
    def __init__(self, seconds):
        super().__init__()
        self._seconds = seconds

    def execute(self):
        try:
            self.state = cmd.State.RUNNING
            processor = SleepProcess(self._seconds)
            self.result = processor.process()
            self.state = cmd.State.SUCCESS
        except TypeError as e:
            self.error = str(e)
            self.state = cmd.State.FAILED


class GetVmNameCommand(cmd.Command):
    """Imitation of vm info."""
    def __init__(self):
        super().__init__()
        self._vm_name_gen = vm_name_generator()

    def execute(self):
        try:
            self.state = cmd.State.RUNNING
            self.result = next(self._vm_name_gen)
            self.state = cmd.State.SUCCESS
        except TypeError as e:
            self.error = str(e)
            self.state = cmd.State.FAILED
