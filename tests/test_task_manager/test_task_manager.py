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
                "time_created",
                "last_run_time",
                "start_run_time",
                "stop_run_time",
                "run_time",
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
                "time_created",
                "last_run_time",
                "start_run_time",
                "stop_run_time",
                "run_time",
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
        self.assertEqual(interval_addition_task._strategy.next_run_time, 0)
        self.assertEqual(interval_addition_task._command.error, None)
        self.assertEqual(interval_addition_task._command.result, None)
        self.assertEqual(interval_addition_task._command.state, cmd.State.NEW)

        interval_addition_task.run()

        # time.time() = 20
        mock_time.return_value = next(mock_time_gen)
        self.assertEqual(interval_addition_task._strategy.task_has_to_run, False)
        self.assertEqual(interval_addition_task._strategy.last_run_time, 10)
        self.assertEqual(interval_addition_task._strategy.next_run_time, 25)
        self.assertEqual(interval_addition_task._command.error, None)
        self.assertEqual(interval_addition_task._command.result, 6)
        self.assertEqual(interval_addition_task._command.state, cmd.State.SUCCESS)

        # time.time() = 30
        mock_time.return_value = next(mock_time_gen)
        self.assertEqual(interval_addition_task._strategy.task_has_to_run, True)
        self.assertEqual(interval_addition_task._strategy.last_run_time, 10)
        self.assertEqual(interval_addition_task._strategy.next_run_time, 25)
        self.assertEqual(interval_addition_task._command.error, None)
        self.assertEqual(interval_addition_task._command.result, 6)
        self.assertEqual(interval_addition_task._command.state, cmd.State.SUCCESS)

        interval_addition_task.run()

        # time.time() = 40
        mock_time.return_value = next(mock_time_gen)
        self.assertEqual(interval_addition_task._strategy.task_has_to_run, False)
        self.assertEqual(interval_addition_task._strategy.last_run_time, 30)
        self.assertEqual(interval_addition_task._strategy.next_run_time, 45)
        self.assertEqual(interval_addition_task._command.error, None)
        self.assertEqual(interval_addition_task._command.result, 12)
        self.assertEqual(interval_addition_task._command.state, cmd.State.SUCCESS)

        # time.time() = 50
        mock_time.return_value = next(mock_time_gen)
        self.assertEqual(interval_addition_task._strategy.task_has_to_run, True)
        self.assertEqual(interval_addition_task._strategy.last_run_time, 30)
        self.assertEqual(interval_addition_task._strategy.next_run_time, 45)
        self.assertEqual(interval_addition_task._command.error, None)
        self.assertEqual(interval_addition_task._command.result, 12)
        self.assertEqual(interval_addition_task._command.state, cmd.State.SUCCESS)

    def test_run_interval_long_task_success(self):
        """Test case for task, which execution time is longer than its
        interval.
        """
        task = tm.Task(
            "interval_long_add_task",
            dc.CumulativeAdditionCommand(1, 1, 20),
            strat.IntervalRun(10)
        )
        self.assertEqual(task.should_run(), True)
        self.assertEqual(task.can_be_cancelled(), True)

        with ThreadPoolExecutor() as e:
            future = e.submit(task.run)

            time.sleep(10)

            self.assertEqual(task.should_run(), False)
            self.assertEqual(task.can_be_cancelled(), True)

            time.sleep(10)

            # 1 second to wait for task to finish.
            time.sleep(1)

            self.assertEqual(task.should_run(), True)
            self.assertEqual(task.can_be_cancelled(), True)

            future.result()

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
    """Test cases for TaskManager.
    
    All tests are executed for 20 seconds.
    """
    def setUp(self):
        self.start_time = int(time.time())
        self.task_manager = tm.TaskManager(max_iterations=20)

        # These tasks should not be executed. They have to be set to FAILED
        # state.
        self.bad_onetime_task = tm.Task(
            "bad_onetime_task",
            dc.CumulativeAdditionCommand("bad_arg", 2),
            strat.OneTimeRun()
        )
        # Executes faster than its internal interval, but slower than TM
        # polling interval.
        self.bad_interval_task = tm.Task(
            "bad_interval_task",
            dc.CumulativeAdditionCommand("bad_arg", 2, 5),
            strat.IntervalRun(10)
        )
        # Executes even slower that its internal interval.
        self.bad_interval_long_sleep_task = tm.Task(
            "bad_interval_task",
            dc.CumulativeAdditionCommand(3, "bad_arg", 10),
            strat.IntervalRun(5)
        )

        # These are normal tasks. They will either have SUCCESS or CANCELLED
        # state.
        self.fast_onetime_task = tm.Task(
            "fast_onetime_task",
            dc.CumulativeAdditionCommand(1, 2),
            strat.OneTimeRun()
        )
        self.fast_interval_task = tm.Task(
            "fast_interval_task",
            dc.CumulativeAdditionCommand(2, 3),
            strat.IntervalRun(5)
        )
        self.slow_onetime_task = tm.Task(
            "slow_onetime_task",
            dc.CumulativeAdditionCommand(3, 4, sleep=5),
            strat.OneTimeRun()
        )

        # Executes faster than its internal interval, but slower than TM
        # polling interval.
        self.slow_interval_task = tm.Task(
            "slow_interval_task",
            dc.CumulativeAdditionCommand(4, 5, sleep=5),
            strat.IntervalRun(10)
        )

        # Executes even slower that its internal interval.
        self.slow_interval_task_long_sleep = tm.Task(
            "slow_interval_task_long_sleep",
            dc.CumulativeAdditionCommand(10, 5, sleep=9),
            strat.IntervalRun(5)
        )

        # Executes even slower that its internal interval. And the working
        # time is divisible by the interval of the task, e.g. sleep=10 and
        # TM max_iterations=20 (with polling interval at 1 second): 20/10 = 2.
        # If such task ends it might not end in required state.
        # TODO: check statement above.
        self.slow_interval_divisible_task_long_sleep = tm.Task(
            "slow_interval_divisible_task_long_sleep",
            dc.CumulativeAdditionCommand(10, 5, sleep=10),
            strat.IntervalRun(5)
        )

        self.tasks = {
            self.bad_onetime_task.name: self.bad_onetime_task,
            self.bad_interval_task.name: self.bad_interval_task,
            self.bad_interval_long_sleep_task.name: self.bad_interval_long_sleep_task,
            self.fast_onetime_task.name: self.fast_onetime_task,
            self.fast_interval_task.name: self.fast_interval_task,
            self.slow_onetime_task.name: self.slow_onetime_task,
            self.slow_interval_task.name: self.slow_interval_task,
            self.slow_interval_task_long_sleep.name: self.slow_interval_task_long_sleep,
            self.slow_interval_divisible_task_long_sleep.name: self.slow_interval_divisible_task_long_sleep
        }

    def test_run_multiple_tasks(self):
        """Basically, it is main test for TaskManager. Many tasks included.

        Imitation of many tasks running at once. Some added dynamically,
        while task manager is running. Some tasks are bad, will have errors.
        """
        self.task_manager.add_task(self.fast_onetime_task)
        self.task_manager.add_task(self.slow_interval_task)
        self.task_manager.add_task(self.slow_interval_task_long_sleep)
        self.task_manager.add_task(self.slow_interval_divisible_task_long_sleep)

        with ThreadPoolExecutor() as e:
            future = e.submit(self.task_manager.run)

            time.sleep(5)

            self.task_manager.add_task(self.bad_onetime_task)
            self.task_manager.add_task(self.bad_interval_task)
            self.task_manager.add_task(self.bad_interval_long_sleep_task)

            time.sleep(5)

            self.task_manager.add_task(self.fast_interval_task)
            self.task_manager.add_task(self.slow_onetime_task)

            time.sleep(10)

            time.sleep(1)

            future.result()


        # Checking results.
        for task in self.task_manager.registry.get_tasks():
            if task.name == "bad_onetime_task":
                task_dict = task.to_dict()
                self.assertEqual(task_dict["result"], None)
                self.assertEqual(task_dict["error"], "Bad agruments. Exiting.")
                self.assertEqual(task_dict["state"], cmd.State.FAILED)
                self.assertEqual(int(task_dict["last_run_time"]), self.start_time + 5)
                self.assertEqual(task.should_run(), False)
                self.assertEqual(task.can_be_cancelled(), False)
            elif task.name == "bad_interval_task":
                task_dict = task.to_dict()
                self.assertEqual(task_dict["result"], None)
                self.assertEqual(task_dict["error"], "Bad agruments. Exiting.")
                self.assertEqual(task_dict["state"], cmd.State.FAILED)
                self.assertEqual(int(task_dict["last_run_time"]), self.start_time + 5)
                self.assertEqual(task.should_run(), False)
                self.assertEqual(task.can_be_cancelled(), False)
            elif task.name == "bad_interval_long_sleep_task":
                task_dict = task.to_dict()
                self.assertEqual(task_dict["result"], None)
                self.assertEqual(task_dict["error"], "Bad agruments. Exiting.")
                self.assertEqual(task_dict["state"], cmd.State.FAILED)
                self.assertEqual(int(task_dict["last_run_time"]), self.start_time + 5)
                self.assertEqual(task.should_run(), False)
                self.assertEqual(task.can_be_cancelled(), False)
            elif task.name == "fast_onetime_task":
                task_dict = task.to_dict()
                self.assertEqual(task_dict["result"], 3)
                self.assertEqual(task_dict["error"], None)
                self.assertEqual(task_dict["state"], cmd.State.SUCCESS)
                self.assertEqual(int(task_dict["last_run_time"]), self.start_time)
                self.assertEqual(task.should_run(), False)
                self.assertEqual(task.can_be_cancelled(), False)
            elif task.name == "fast_interval_task":
                task_dict = task.to_dict()
                self.assertEqual(task_dict["result"], 10)
                self.assertEqual(task_dict["error"], None)
                self.assertEqual(task_dict["state"], cmd.State.CANCELLED)
                self.assertEqual(int(task_dict["last_run_time"]), self.start_time + 15)
                self.assertEqual(task.should_run(), False)
                self.assertEqual(task.can_be_cancelled(), False)
            elif task.name == "slow_onetime_task":
                task_dict = task.to_dict()
                self.assertEqual(task_dict["result"], 7)
                self.assertEqual(task_dict["error"], None)
                self.assertEqual(task_dict["state"], cmd.State.SUCCESS)
                self.assertEqual(int(task_dict["last_run_time"]), self.start_time + 10)
                self.assertEqual(task.should_run(), False)
                self.assertEqual(task.can_be_cancelled(), False)
            elif task.name == "slow_interval_task":
                task_dict = task.to_dict()
                self.assertEqual(task_dict["result"], 18)
                self.assertEqual(task_dict["error"], None)
                self.assertEqual(task_dict["state"], cmd.State.CANCELLED)
                self.assertEqual(int(task_dict["last_run_time"]), self.start_time + 10)
                self.assertEqual(task.should_run(), False)
                self.assertEqual(task.can_be_cancelled(), False)
            elif task.name == "slow_interval_task_long_sleep":
                task_dict = task.to_dict()
                self.assertEqual(task_dict["result"], 45)
                self.assertEqual(task_dict["error"], None)
                self.assertEqual(task_dict["state"], cmd.State.CANCELLED)
                self.assertEqual(int(task_dict["last_run_time"]), self.start_time + 18)
                self.assertEqual(task.should_run(), False)
                self.assertEqual(task.can_be_cancelled(), False)
            elif task.name == "slow_interval_divisible_task_long_sleep":
                task_dict = task.to_dict()
                self.assertEqual(task_dict["result"], 30)
                self.assertEqual(task_dict["error"], None)
                self.assertEqual(task_dict["state"], cmd.State.CANCELLED)
                self.assertEqual(int(task_dict["last_run_time"]), self.start_time + 10)
                self.assertEqual(task.should_run(), False)
                self.assertEqual(task.can_be_cancelled(), False)



    def test_run_single_interval_sleep_task_success(self):
        """Single task, which should be executed long. Longer than TM polling
        and when its internal execution time is longer than its execution
        interval.
        """
        task = self.slow_interval_task_long_sleep

        self.task_manager.add_task(task)

        with ThreadPoolExecutor() as e:
            future = e.submit(self.task_manager.run)

            future.result()

        # Task should be executed twice. Once at 0, at 9 seconds and at 18
        # seconds (15 + 15). At 20 seconds task will be terminated, since TM
        # run is set to 20 seconds of work time.
        task_dict = task.to_dict()
        self.assertEqual(task_dict["result"], 45)
        self.assertEqual(task_dict["error"], None)
        self.assertEqual(task_dict["state"], cmd.State.CANCELLED)
        self.assertEqual(int(task_dict["last_run_time"]), self.start_time + 10)
        self.assertEqual(task.should_run(), False)
        self.assertEqual(task.can_be_cancelled(), False)


    def test_run_single_interval_divisible_sleep_task_success(self):
        """Single task, which should be executed long. Longer than TM polling
        and when its internal execution time is longer than its execution
        interval. Also this tasks run interval is divisible by total time, 
        when TM is running, e.g. 20/10 = 2. 20 - TM run time in seconds, 10 -
        task run time in seconds.
        """
        task = self.slow_interval_divisible_task_long_sleep

        self.task_manager.add_task(task)

        with ThreadPoolExecutor() as e:
            future = e.submit(self.task_manager.run)

            future.result()

        # Task should be executed twice. Once at 0, then at 10 seconds (15 + 15).
        # At 20 seconds task will be terminated, since TM run is set to 20
        # seconds of work time.
        self.assertEqual(task._command.state, cmd.State.CANCELLED)
        self.assertEqual(task._command.result, 30)


if __name__ == "__main__":
    test = TestTaskManager(methodName="test_run_single_interval_sleep_task_success")
    test.setUp()
    test.test_run_single_interval_sleep_task_success()
    test.tearDown()
