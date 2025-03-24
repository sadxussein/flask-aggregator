"""Task manager unittest."""

import unittest
from unittest.mock import MagicMock, patch

from flask_aggregator.back.task_manager.task_manager import TaskManager, TaskFactory, CreateVMInOvirt, GetVMsFromOvirt

def mock_time_generator():
    """Simple +10 mock time generator."""
    counter = 100
    while True:
        yield counter
        counter += 10

mock_time_gen = mock_time_generator()

class TestTaskManager(unittest.TestCase):
    """Task manager test cases."""
    @patch("concurrent.futures.ThreadPoolExecutor.submit")
    # @patch("time.time")
    def test_run_single_task_single_iteration(self, mock_submit):
        """Test add task to queue."""
        # mock_time.side_effect = lambda: next(mock_time_gen)

        tm = TaskManager()
        task = GetVMsFromOvirt(interval=1)
        tm.add_task(task)

        self.assertEqual(tm._task_queue.qsize(), 1)

        tm.run(max_iterations=10)

        self.assertEqual(len(tm._tasks), 1)

        # task.assert_called_once(task.set_last_run_time)
        mock_submit.assert_called_once_with(task)

class TestTask(unittest.TestCase):
    """Task test cases."""
    def setUp(self):
        self.t1 = CreateVMInOvirt(3, 120, interval=30)
        self.t2 = GetVMsFromOvirt()

    def test_init(self):
        """Test default init."""
        self.assertEqual(self.t1._retries, 3)
        self.assertEqual(self.t1._retry_timeout, 120)
        self.assertEqual(self.t1._interval, 30)
        self.assertEqual(self.t1._was_last_run_successful, False)
        self.assertEqual(self.t1._last_run_time, None)

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

class TestTaskFactory(unittest.TestCase):
    """Task factory test cases."""
    def setUp(self):
        self.tf = TaskFactory()

    def test_make_task(self):
        """Test task factory."""
        self.assertIsInstance(self.tf.make_task("create_vm_in_ovirt"), CreateVMInOvirt)
        self.assertIsInstance(self.tf.make_task("get_vms_from_ovirt"), GetVMsFromOvirt)
        with self.assertRaises(ValueError):
            self.tf.make_task("unknown_task")
