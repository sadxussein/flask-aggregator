"""Task class test module."""

import time
import uuid
import unittest
from unittest.mock import patch, MagicMock
from concurrent.futures import ThreadPoolExecutor

import flask_aggregator.back.task_manager.strategy as strat
import flask_aggregator.back.task_manager.command as cmd
import flask_aggregator.back.task_manager.task_manager as tm
import tests.test_task_manager.debug_tools as dc


# pylint: disable=protected-access

class TestTask(unittest.TestCase):
    """Test cases for Task."""

    @patch("uuid.uuid4")
    def test_uuid(self, mock_uuid4):
        """Make sure that UUID returns string."""
        mock_uuid4.return_value = uuid.UUID("6ba7b811-9dad-11d1-80b4-00c04fd430c8")
        t = tm.Task("t", dc.AdditionCommand(1, 2), strat.OneTimeRun())
        self.assertEqual(t.uuid, "6ba7b811-9dad-11d1-80b4-00c04fd430c8")


    def test_to_dict(self):
        """Make sure that certain keys are present in task JSON-friendly
        view.
        """
        one_time_addition_task = tm.Task("one_time_addition_task", dc.AdditionCommand(1, 3), strat.OneTimeRun())
        interval_addition_task = tm.Task("interval_addition_task", dc.AdditionCommand(4, 2), strat.IntervalRun(10))
        task1_keys = list(one_time_addition_task.to_dict().keys())
        task2_keys = list(interval_addition_task.to_dict().keys())

        self.assertListEqual(
            task1_keys,
            [
                "uuid",
                "name",
                "last_run_time",
                "has_to_run",
                "state",
                "result",
                "error",
            ],
        )
        self.assertListEqual(
            task2_keys,
            [
                "uuid",
                "name",
                "last_run_time",
                "has_to_run",
                "state",
                "result",
                "error",
            ],
        )

    # Task.run function requires several variants of tests:
    # 1. Simple one-time-run task. Executed almost immediately.
    # 2. One-time-run task, but its execution time exceeds task manager
    #    default task run interval. For instance, such task will be ran 10
    #    seconds, while task manager interval is 5 seconds.
    # 3. Simple interval task. Executed almost immediately (faster that TM run
    #    polling). Must be executed with pre-defined intervals.
    # 4. Interval task, but like one-time-run sleep task (2). Same issues
    #    should be checked. There should be a guarantee, that such task will
    #    not be ran another time, while previous is still running.

    @patch("time.time")
    def test_run_one_time_addition_task_success(self, mock_time):
        """Test case for successful execution of one-time-run task."""
        mock_time_gen = dc.mock_time_generator()

        # time.time() = 0
        mock_time.return_value = next(mock_time_gen)
        one_time_addition_task = tm.Task("one_time_addition_task", dc.AdditionCommand(1, 3), strat.OneTimeRun())

        # time.time() = 10
        mock_time.return_value = next(mock_time_gen)
        self.assertEqual(one_time_addition_task._strategy.task_has_to_run, True)
        self.assertEqual(one_time_addition_task._strategy.last_run_time, -1)
        self.assertEqual(one_time_addition_task._command.result, None)
        self.assertEqual(one_time_addition_task._command.error, None)
        self.assertEqual(one_time_addition_task._command.state, cmd.State.NEW)

        one_time_addition_task.run()

        self.assertEqual(one_time_addition_task._strategy.task_has_to_run, False)
        self.assertEqual(one_time_addition_task._strategy.last_run_time, 10)
        self.assertEqual(one_time_addition_task._command.result, 4)
        self.assertEqual(one_time_addition_task._command.error, None)
        self.assertEqual(one_time_addition_task._command.state, cmd.State.SUCCESS)

        # time.time() = 20
        mock_time.return_value = next(mock_time_gen)
        self.assertEqual(one_time_addition_task._strategy.task_has_to_run, False)
        self.assertEqual(one_time_addition_task._strategy.last_run_time, 10)
        self.assertEqual(one_time_addition_task._command.result, 4)
        self.assertEqual(one_time_addition_task._command.error, None)
        self.assertEqual(one_time_addition_task._command.state, cmd.State.SUCCESS)

    def test_run_one_time_sleep_task_success(self):
        """Test case for successful execution of one-time-run long executed
        task.
        
        Primarily this test checks that state of task (its command, to be
        precise) changes.
        """
        one_time_sleep_task = tm.Task("one_time_sleep_task", dc.SleepCommand(15), strat.OneTimeRun())

        self.assertEqual(one_time_sleep_task._strategy.task_has_to_run, True)
        self.assertEqual(one_time_sleep_task._command.error, None)
        self.assertEqual(one_time_sleep_task._command.result, None)
        self.assertEqual(one_time_sleep_task._command.state, cmd.State.NEW)

        with ThreadPoolExecutor() as e:
            future = e.submit(one_time_sleep_task.run)

            self.assertEqual(one_time_sleep_task._strategy.task_has_to_run, False)
            self.assertEqual(one_time_sleep_task._command.error, None)
            self.assertEqual(one_time_sleep_task._command.result, None)
            self.assertEqual(one_time_sleep_task._command.state, cmd.State.RUNNING)

            future.result()

            self.assertEqual(one_time_sleep_task._strategy.task_has_to_run, False)
            self.assertEqual(one_time_sleep_task._command.error, None)
            self.assertEqual(one_time_sleep_task._command.result, "has been waiting for 15 seconds")
            self.assertEqual(one_time_sleep_task._command.state, cmd.State.SUCCESS)

    @patch("time.time")
    def test_run_interval_task_success(self, mock_time):
        """Test case for successful execution of interval task."""
        mock_time_gen = dc.mock_time_generator()

        # time.time() = 0
        mock_time.return_value = next(mock_time_gen)
        interval_addition_task = tm.Task(
            "interval_addition_task",
            dc.CumulativeAdditionCommand(4, 2),
            strat.IntervalRun(15)
        )

        # time.time() = 10
        mock_time.return_value = next(mock_time_gen)
        self.assertEqual(interval_addition_task._strategy.task_has_to_run, True)
        self.assertEqual(interval_addition_task._strategy.last_run_time, -1)
        self.assertEqual(interval_addition_task._strategy._next_run_time, 0)
        self.assertEqual(interval_addition_task._command.error, None)
        self.assertEqual(interval_addition_task._command.result, None)
        self.assertEqual(interval_addition_task._command.state, cmd.State.NEW)

        interval_addition_task.run()

        # time.time() = 20
        mock_time.return_value = next(mock_time_gen)
        self.assertEqual(interval_addition_task._strategy.task_has_to_run, False)
        self.assertEqual(interval_addition_task._strategy.last_run_time, 10)
        self.assertEqual(interval_addition_task._strategy._next_run_time, 25)
        self.assertEqual(interval_addition_task._command.error, None)
        self.assertEqual(interval_addition_task._command.result, 6)
        self.assertEqual(interval_addition_task._command.state, cmd.State.SUCCESS)

        # time.time() = 30
        mock_time.return_value = next(mock_time_gen)
        self.assertEqual(interval_addition_task._strategy.task_has_to_run, True)
        self.assertEqual(interval_addition_task._strategy.last_run_time, 10)
        self.assertEqual(interval_addition_task._strategy._next_run_time, 25)
        self.assertEqual(interval_addition_task._command.error, None)
        self.assertEqual(interval_addition_task._command.result, 6)
        self.assertEqual(interval_addition_task._command.state, cmd.State.SUCCESS)

        interval_addition_task.run()

        # time.time() = 40
        mock_time.return_value = next(mock_time_gen)
        self.assertEqual(interval_addition_task._strategy.task_has_to_run, False)
        self.assertEqual(interval_addition_task._strategy.last_run_time, 30)
        self.assertEqual(interval_addition_task._strategy._next_run_time, 45)
        self.assertEqual(interval_addition_task._command.error, None)
        self.assertEqual(interval_addition_task._command.result, 12)
        self.assertEqual(interval_addition_task._command.state, cmd.State.SUCCESS)

        # time.time() = 50
        mock_time.return_value = next(mock_time_gen)
        self.assertEqual(interval_addition_task._strategy.task_has_to_run, True)
        self.assertEqual(interval_addition_task._strategy.last_run_time, 30)
        self.assertEqual(interval_addition_task._strategy._next_run_time, 45)
        self.assertEqual(interval_addition_task._command.error, None)
        self.assertEqual(interval_addition_task._command.result, 12)
        self.assertEqual(interval_addition_task._command.state, cmd.State.SUCCESS)

    # @patch("time.time")
    def test_run_interval_sleep_task_success(self):
        """Test case for sleep interval task.
        
        It is important, that if long-executed task is already running not to
        start it again.
        """
        # mock_time_gen = dc.mock_time_generator()

        # mock_time.return_value = next(mock_time_gen)    # time.time() = 0
        mock_command = MagicMock()
        mock_command.state = cmd.State.NEW
        mock_command.result = None
        mock_command.error = None

        mock_strategy = MagicMock()
        mock_strategy.task_has_to_run = True
        mock_strategy.last_run_time = None

        task = tm.Task(
            "interval_task",
            mock_command,
            mock_strategy
        )
        self.assertEqual(task._command.state, cmd.State.NEW)

        with ThreadPoolExecutor() as e:
            future1 = e.submit(task.run)

            time.sleep(1)

            # self.assertEqual(task._command.state, cmd.State.RUNNING)

            time.sleep(5)

            mock_strategy.task_has_to_run = False
            future2 = e.submit(task.run)

            time.sleep(5)

            # self.assertEqual(task._command.state, cmd.State.SUCCESS)
            self.assertEqual(mock_command.execute.call_count, 1)

            future1.result()
            future2.result()


    def test_run_one_time_task_failure(self):
        """In case if one-time task failed."""
        # Passing bad argument into class constructor.
        one_time_addition_task = tm.Task(
            "one_time_addition_task",
            dc.AdditionCommand(1, "some_bad_arg"),
            strat.OneTimeRun()
        )

        one_time_addition_task.run()

        self.assertEqual(one_time_addition_task._strategy.task_has_to_run, False)
        self.assertNotEqual(one_time_addition_task._command.error, None)
        self.assertEqual(one_time_addition_task._command.result, None)
        self.assertEqual(one_time_addition_task._command.state, cmd.State.FAILED)

    def test_run_interval_task_failure(self):
        """In case if interval task failed."""
        interval_addition_task = tm.Task(
            "interval_addition_task",
            dc.AdditionCommand(4, "some_bad_arg"),
            strat.IntervalRun(10)
        )

        interval_addition_task.run()

        self.assertEqual(interval_addition_task._strategy.task_has_to_run, False)
        self.assertNotEqual(interval_addition_task._command.error, None)
        self.assertEqual(interval_addition_task._command.result, None)
        self.assertEqual(interval_addition_task._command.state, cmd.State.FAILED)

        time.sleep(10)

        self.assertEqual(interval_addition_task._strategy.task_has_to_run, True)
        self.assertNotEqual(interval_addition_task._command.error, None)
        self.assertEqual(interval_addition_task._command.result, None)
        self.assertEqual(interval_addition_task._command.state, cmd.State.FAILED)


class TestTaskManager(unittest.TestCase):
    """Test cases for TaskManager."""
    def test_run_single_interval_task_success(self):
        """Use single task in TM which runs successfully."""
        task_manager = tm.TaskManager()
        task_manager.add_task(tm.Task(
            "get_vm_name_task", dc.GetVmNameCommand(), strat.IntervalRun(5)
        ))
        task_manager.add_task(tm.Task(
            "initial_interval_cumulative_addition_task",
            dc.CumulativeAdditionCommand(4, 3),
            strat.IntervalRun(5)
        ))

        with ThreadPoolExecutor() as e:
            future = e.submit(task_manager.run, 20)

            task_registry = task_manager.registry

            self.assertEqual(len(task_registry.get_tasks_uuid()), 2)

            time.sleep(5)

            task_manager.add_task(tm.Task(
                "one_time_addition_task",
                dc.AdditionCommand(4, 2),
                strat.OneTimeRun()
            ))

            time.sleep(5)

            task_manager.add_task(tm.Task(
                "late_interval_cumulative_addition_task",
                dc.CumulativeAdditionCommand(1, 2),
                strat.IntervalRun(5)
            ))

            # Give some time for threads to start in system.
            time.sleep(1)

            self.assertEqual(len(task_registry.get_tasks_uuid()), 4)
            
            future.result()

        for uuid_ in task_registry.get_tasks_uuid():
            task = task_registry.get_task_by_uuid(uuid_)
            task_dict = task.to_dict()
            if task.name == "get_vm_name_task":
                self.assertEqual(task_dict["result"], "no-name-vm")
                self.assertEqual(task_dict["state"], cmd.State.SUCCESS)
            elif task.name == "one_time_addition_task":
                self.assertEqual(task_dict["result"], 6)
                self.assertEqual(task_dict["state"], cmd.State.SUCCESS)
            elif task.name == "late_interval_cumulative_addition_task":
                self.assertEqual(task_dict["result"], 9)
                self.assertEqual(task_dict["state"], cmd.State.SUCCESS)
            elif task.name == "initial_interval_cumulative_addition_task":
                self.assertEqual(task_dict["result"], 35)
                self.assertEqual(task_dict["state"], cmd.State.SUCCESS)
