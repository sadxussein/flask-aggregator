"""Task manager unittest."""

import unittest
from unittest.mock import MagicMock, patch

from task_manager.task_manager import (
    CommandFactory, CreateVMInOvirt, GetVMsFromOvirt, Task, TaskManager,
    OneTimeRun, IntervalRun, RetryRun
)


def mock_time_generator():
    """Simple +10 mock time generator."""
    counter = 0
    while True:
        yield counter
        counter += 10



class TestTaskManager(unittest.TestCase):
    """Task manager test cases."""

    # @patch("concurrent.futures.ThreadPoolExecutor.submit")
    # @patch("time.time")
    def test_run_single_task_single_iteration(self):
        """Test add task to queue."""
        # mock_time.side_effect = lambda: next(mock_time_gen)

        tm = TaskManager()
        c1 = CommandFactory.make_command(
            "create_vm_in_ovirt", config="some_config"
        )
        c2 = CommandFactory.make_command("get_vms_from_ovirt")
        t1 = Task(command=c1, strategy=OneTimeRun())
        t2 = Task(command=c2, strategy=IntervalRun(10))
        tm.add_task(t1)
        tm.add_task(t2)

        self.assertEqual(tm._task_queue.qsize(), 2)

        tm.run(max_iterations=3)

        self.assertEqual(len(tm._tasks), 2)


class TestOneTimeRun(unittest.TestCase):
    """One-time run task strategy test cases."""
    def setUp(self):
        self.mock_time_gen = mock_time_generator()

    @patch("time.time")
    def test_init(self, mock_time):
        """Success case."""
        mock_time.side_effect = lambda: next(self.mock_time_gen)

        run_strat = OneTimeRun()
        self.assertEqual(run_strat.last_run_time, run_strat.TASK_WAS_NOT_RUN_YET)
        self.assertEqual(run_strat._time_created, 0)
        mock_time()
        run_strat.mark_now_as_last_run_time()
        self.assertEqual(run_strat.last_run_time, 20)
        self.assertEqual(run_strat._time_created, 0)


class TestIntervalRun(unittest.TestCase):
    """Interval run task strategy test cases."""
    def setUp(self):
        self.mock_time_gen = mock_time_generator()

    def test_init_interval_less_than_zero(self):
        """Check that exception is raised when interval is set to less than
        0."""
        with self.assertRaises(ValueError) as e:
            IntervalRun(interval=-1)
        self.assertEqual(str(e.exception), "Time interval can not be equal or less than 0.")

    @patch("time.time")
    def test_next_run_time_property(self, mock_time):
        """Success case."""
        # Setup.
        mock_time.return_value = 0
        run_strat = IntervalRun(interval=30)
        self.assertEqual(run_strat._time_created, 0)
        self.assertEqual(run_strat.next_run_time, 30)
        self.assertEqual(run_strat.last_run_time, run_strat.TASK_WAS_NOT_RUN_YET)
        test_cases = [
            {
                "time": 20,
                "expected_last_run_time": run_strat.TASK_WAS_NOT_RUN_YET,
                "expected_next_run_time": 30,
                "should_set_last_run_task_time": False,
                "desc": "Not yet time to run task."
            },
            {
                "time": 30,
                "expected_last_run_time": run_strat.TASK_WAS_NOT_RUN_YET,
                "expected_next_run_time": 30,
                "should_set_last_run_task_time": True,
                "desc": "Time to run task first time."
            },
            {
                "time": 50,
                "expected_last_run_time": 30,
                "expected_next_run_time": 60,
                "should_set_last_run_task_time": False,
                "desc": "Not yet time to run task."
            },
            {
                "time": 60,
                "expected_last_run_time": 30,
                "expected_next_run_time": 60,
                "should_set_last_run_task_time": True,
                "desc": "Time to run task second time."
            },
            {
                "time": 70,
                "expected_last_run_time": 60,
                "expected_next_run_time": 90,
                "should_set_last_run_task_time": False,
                "desc": "Not yet time to run task."
            }
        ]

        for test in test_cases:
            with self.subTest(msg=test["desc"]):
                mock_time.return_value = test["time"]
                self.assertEqual(run_strat.last_run_time, test["expected_last_run_time"])
                self.assertEqual(run_strat.next_run_time, test["expected_next_run_time"])
                if test["should_set_last_run_task_time"]:
                    run_strat.mark_now_as_last_run_time()


class TestRetryRun(unittest.TestCase):
    """Test cases for tasks that should be repeated if failed."""
    def test_has_to_retry(self):
        was_last_run_successful = MagicMock()
        was_last_run_successful.side_effect = [False, True, False, False, False, True]
        run_strat = RetryRun(max_retries=3, retry_interval=10)
        run_strat.was_last_run_successful = was_last_run_successful()
        self.assertEqual(run_strat.has_to_retry(), True)
        self.assertEqual(run_strat._retry_count, 1)
        run_strat.was_last_run_successful = was_last_run_successful()
        self.assertEqual(run_strat.has_to_retry(), False)
        self.assertEqual(run_strat._retry_count, 1)
        run_strat.was_last_run_successful = was_last_run_successful()
        self.assertEqual(run_strat.has_to_retry(), True)
        self.assertEqual(run_strat._retry_count, 2)
        run_strat.was_last_run_successful = was_last_run_successful()
        self.assertEqual(run_strat.has_to_retry(), True)
        self.assertEqual(run_strat._retry_count, 3)
        run_strat.was_last_run_successful = was_last_run_successful()
        self.assertEqual(run_strat.has_to_retry(), False)
        self.assertEqual(run_strat._retry_count, 3)
        run_strat.was_last_run_successful = was_last_run_successful()
        self.assertEqual(run_strat.has_to_retry(), False)
        self.assertEqual(run_strat._retry_count, 3)


class TestTask(unittest.TestCase):
    """Task test cases."""
    def setUp(self):
        self.t1 = Task(
            CommandFactory.make_command(
                "create_vm_in_ovirt", config="some_config"
            ),
            OneTimeRun()
        )
        self.t2 = Task(
            CommandFactory.make_command("get_vms_from_ovirt"),
            IntervalRun(30)
        )

    def test_run(self):
        self.t1.run()
        self.t2.run()


# class TestTaskFactory(unittest.TestCase):
#     """Task factory test cases."""
#     def setUp(self):
#         self.tf = TaskFactory()

#     def test_make_task(self):
#         """Test task factory."""
#         self.assertIsInstance(self.tf.make_task("create_vm_in_ovirt"), CreateVMInOvirt)
#         self.assertIsInstance(self.tf.make_task("get_vms_from_ovirt"), GetVMsFromOvirt)
#         with self.assertRaises(ValueError):
#             self.tf.make_task("unknown_task")
 