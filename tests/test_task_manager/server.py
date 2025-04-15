"""Test task manager and task monitor."""

import time
from concurrent.futures import ThreadPoolExecutor

import flask_aggregator.back.task_manager.strategy as strat
import flask_aggregator.back.task_manager.monitor as mon
import flask_aggregator.back.task_manager.command as cmd
import flask_aggregator.back.task_manager.task_manager as tm
import tests.test_task_manager.debug_tools as dc


class TaskManagerWithMonitor:
    """Interactive testing for task manager and related classes."""
    def __init__(self):
        self._tm = tm.TaskManager()
        self._mon = mon.Server()
        self._tm.attach_monitor(self._mon.observer_callback)
        self._task = tm.Task(
            "e15-test2 hosts",
            cmd.OvirtCommand(),
            strat.IntervalRun(60)
        )
        self._running = True

    def __stop(self):
        self._running = False
        self._mon.stop()
        self._tm.stop()

    def __interact(self):
        user_input = input("Select option: ")
        if user_input == "add interval":
            self.__add_cumulative_addition_task(is_interval=True)
        elif user_input == "add onetime":
            self.__add_cumulative_addition_task(is_interval=False)
        elif user_input == "e":
            self.__stop()
        else:
            print("unknown command")

    def __add_cumulative_addition_task(self, is_interval=True):
        print("Adding simple addition task.")
        name = input("name: ")
        a = input("a: ")
        b = input("b: ")
        sleep = input("sleep: ")
        interval = input("interval: ") if is_interval else None
        strategy = (
            strat.IntervalRun(int(interval)) if is_interval
            else strat.OneTimeRun()
        )
        self._tm.add_task(tm.Task(
            name,
            dc.CumulativeAdditionCommand(int(a), int(b), int(sleep)),
            strategy=strategy
        ))

    def run(self):
        """Simple task manager run."""
        with ThreadPoolExecutor() as e:
            tm_future = e.submit(self._tm.run)
            tm_monitor = e.submit(self._mon.run)

            self._tm.add_task(self._task)

            while self._running:
                self.__interact()
                time.sleep(0.1)

            tm_future.result()
            tm_monitor.result()


if __name__ == "__main__":
    app = TaskManagerWithMonitor()
    app.run()
