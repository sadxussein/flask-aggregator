"""Task manager unittest."""

import unittest
from unittest.mock import MagicMock, patch

from flask_aggregator.back.task_manager.task_manager import (
    CommandFactory, CreateVMInOvirt, GetVMsFromOvirt, Task, TaskManager,
    OneTimeRun, IntervalRun
)


def mock_time_generator():
    """Simple +10 mock time generator."""
    counter = 100
    while True:
        yield counter
        counter += 10


mock_time_gen = mock_time_generator()


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
        t1 = Task(command=c1)
        t2 = Task(command=c2, interval=10)
        tm.add_task(t1)
        tm.add_task(t2)

        self.assertEqual(tm._task_queue.qsize(), 2)

        tm.run(max_iterations=20)

        self.assertEqual(len(tm._tasks), 2)


class TestOneTimeRun(unittest.TestCase):
    """One-time run task strategy test cases."""
    @patch("time.time")
    def test_init(self, mock_time):
        """Success case."""
        mock_time.return_value = 100
        run_strat = OneTimeRun()
        self.assertEqual(run_strat.last_run_time, 100)

    def test_has_to_retry(self):
        was_last_run_successful = MagicMock()
        was_last_run_successful.side_effect = [False, True, False, False, False, True]
        run_strat = OneTimeRun(max_retries=3, retry_interval=10)
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
        

class TestIntervalRun(unittest.TestCase):
    """Interval run task strategy test cases."""
    @patch("time.time")
    def test_init(self, mock_time):
        """Success case."""
        mock_time.return_value = 100
        i = IntervalRun(interval=30)
        self.assertEqual(i.last_run_time, 100)
        self.nex

class TestTask(unittest.TestCase):
    """Task test cases."""

    def setUp(self):
        self.t1 = Task(
            CommandFactory.make_command(
                "create_vm_in_ovirt", config="some_config"
            ),
            3,
            120,
            30,
        )
        self.t2 = Task(CommandFactory.make_command("get_vms_from_ovirt"))

    def test_init(self):
        """Test default init."""
        self.assertEqual(self.t1._retries, 3)
        self.assertEqual(self.t1._retry_timeout, 120)
        self.assertEqual(self.t1._interval, 30)
        self.assertEqual(self.t1._was_last_run_successful, False)
        self.assertEqual(self.t1._last_run_time, None)
        self.assertEqual(self.t1.__was_run_once, False)
        self.assertEqual(self.t1.__was_run_once, False)

    def test_init_default(self):
        """Test default init."""
        self.assertEqual(self.t2._retries, 1)
        self.assertEqual(self.t2._retry_timeout, 60)
        self.assertEqual(self.t2._interval, None)
        self.assertEqual(self.t2._was_last_run_successful, False)
        self.assertEqual(self.t2._last_run_time, None)

    @patch("time.time")
    def test_next_run_time(self, mock_time):
        """Test last run time setting."""
        mock_time.return_value = 100
        self.t1.set_last_run_time()
        self.assertEqual(self.t1.next_run_time, 130)
        self.assertEqual(self.t2.next_run_time, 100)

    def test_interval(self):
        """Test interval property."""
        self.assertEqual(self.t1.interval, 30)
        self.assertEqual(self.t2.interval, None)

    def test_was_last_run_successful(self):
        """Test was_last_run_successful property."""
        self.assertEqual(self.t1.was_last_run_successful, False)
        self.assertEqual(self.t2.was_last_run_successful, False)


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
 