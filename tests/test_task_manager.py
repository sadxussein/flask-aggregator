"""Task manager unittest."""

import unittest
from unittest.mock import MagicMock, patch

from flask_aggregator.back.task_manager.task_manager import (
    CommandFactory, CreateVMInOvirt, GetVMsFromOvirt, Task, TaskManager,
    OneTimeRun, IntervalRun, RetryRun
)


def mock_time_generator():
    """Simple +10 mock time generator."""
    counter = 0
    while True:
        yield counter
        counter += 10



# class TestTaskManager(unittest.TestCase):
#     """Task manager test cases."""

#     # @patch("concurrent.futures.ThreadPoolExecutor.submit")
#     # @patch("time.time")
#     def test_run_single_task_single_iteration(self):
#         """Test add task to queue."""
#         # mock_time.side_effect = lambda: next(mock_time_gen)

#         tm = TaskManager()
#         c1 = CommandFactory.make_command(
#             "create_vm_in_ovirt", config="some_config"
#         )
#         c2 = CommandFactory.make_command("get_vms_from_ovirt")
#         t1 = Task(command=c1, strategy=OneTimeRun())
#         t2 = Task(command=c2, strategy=IntervalRun(10))
#         tm.add_task(t1)
#         tm.add_task(t2)

#         self.assertEqual(tm._task_queue.qsize(), 2)

#         tm.run(max_iterations=3)

#         self.assertEqual(len(tm._tasks), 2)


# class TestOneTimeRun(unittest.TestCase):
#     """One-time run task strategy test cases."""
#     def setUp(self):
#         self.mock_time_gen = mock_time_generator()

#     @patch("time.time")
#     def test_init(self, mock_time):
#         """Success case."""
#         mock_time.side_effect = lambda: next(self.mock_time_gen)

#         run_strat = OneTimeRun()
#         self.assertEqual(run_strat._time_created, 0)
#         self.assertEqual(run_strat.last_run_time, run_strat.TASK_WAS_NOT_RUN_YET)
#         self.assertEqual(run_strat.task_has_to_run, True)
#         self.assertEqual(run_strat.was_run_once, False)
#         mock_time() # Skipping time (+10)
#         self.assertEqual(run_strat.last_run_time, run_strat.TASK_WAS_NOT_RUN_YET)
#         self.assertEqual(run_strat.task_has_to_run, True)
#         self.assertEqual(run_strat.was_run_once, False)
#         run_strat.mark_now_as_last_run_time()
#         self.assertEqual(run_strat.last_run_time, 20)   # Time is called twice (+10 each call)
#         self.assertEqual(run_strat.task_has_to_run, False)
#         self.assertEqual(run_strat.was_run_once, True)


# class TestIntervalRun(unittest.TestCase):
#     """Interval run task strategy test cases."""
#     def setUp(self):
#         self.mock_time_gen = mock_time_generator()

#     def test_init_interval_less_than_zero(self):
#         """Check that exception is raised when interval is set to less than
#         0."""
#         with self.assertRaises(ValueError) as e:
#             IntervalRun(interval=-1)
#         self.assertEqual(str(e.exception), "Time interval can not be equal or less than 0.")

#     @patch("time.time")
#     def test_next_run_time_property(self, mock_time):
#         """Success case."""
#         # Setup.
#         mock_time.return_value = 0
#         run_strat = IntervalRun(interval=30)
#         self.assertEqual(run_strat._time_created, 0)
#         self.assertEqual(run_strat._next_run_time, 30)
#         self.assertEqual(run_strat.last_run_time, run_strat.TASK_WAS_NOT_RUN_YET)
#         self.assertEqual(run_strat.task_has_to_run, False)
#         test_cases = [
#             {
#                 "time": 20,
#                 "expected_last_run_time": run_strat.TASK_WAS_NOT_RUN_YET,
#                 "expected_next_run_time": 30,
#                 "expected_has_to_run": False,
#                 "should_set_last_run_task_time": False,
#                 "desc": "Not yet time to run task."
#             },
#             {
#                 "time": 30,
#                 "expected_last_run_time": run_strat.TASK_WAS_NOT_RUN_YET,
#                 "expected_next_run_time": 30,
#                 "expected_has_to_run": True,
#                 "should_set_last_run_task_time": True,
#                 "desc": "Time to run task first time."
#             },
#             {
#                 "time": 50,
#                 "expected_last_run_time": 30,
#                 "expected_next_run_time": 60,
#                 "expected_has_to_run": False,
#                 "should_set_last_run_task_time": False,
#                 "desc": "Not yet time to run task. After 1st."
#             },
#             {
#                 "time": 60,
#                 "expected_last_run_time": 30,
#                 "expected_next_run_time": 60,
#                 "expected_has_to_run": True,
#                 "should_set_last_run_task_time": True,
#                 "desc": "Time to run task second time."
#             },
#             {
#                 "time": 70,
#                 "expected_last_run_time": 60,
#                 "expected_next_run_time": 90,
#                 "expected_has_to_run": False,
#                 "should_set_last_run_task_time": False,
#                 "desc": "Not yet time to run task. After 2nd."
#             }
#         ]

#         for test in test_cases:
#             with self.subTest(msg=test["desc"]):
#                 mock_time.return_value = test["time"]
#                 run = run_strat.task_has_to_run
#                 self.assertEqual(run, test["expected_has_to_run"])
#                 self.assertEqual(run_strat.last_run_time, test["expected_last_run_time"])
#                 self.assertEqual(run_strat._next_run_time, test["expected_next_run_time"])
#                 if test["should_set_last_run_task_time"]:
#                     run_strat.mark_now_as_last_run_time()


# class TestRetryRun(unittest.TestCase):
#     """Test cases for tasks that should be repeated if failed."""
#     def test_has_to_retry(self):
#         was_last_run_successful = MagicMock()
#         was_last_run_successful.side_effect = [False, True, False, False, False, True]
#         run_strat = RetryRun(max_retries=3, retry_interval=10)
#         run_strat.was_last_run_successful = was_last_run_successful()
#         self.assertEqual(run_strat.has_to_retry(), True)
#         self.assertEqual(run_strat._retry_count, 1)
#         run_strat.was_last_run_successful = was_last_run_successful()
#         self.assertEqual(run_strat.has_to_retry(), False)
#         self.assertEqual(run_strat._retry_count, 1)
#         run_strat.was_last_run_successful = was_last_run_successful()
#         self.assertEqual(run_strat.has_to_retry(), True)
#         self.assertEqual(run_strat._retry_count, 2)
#         run_strat.was_last_run_successful = was_last_run_successful()
#         self.assertEqual(run_strat.has_to_retry(), True)
#         self.assertEqual(run_strat._retry_count, 3)
#         run_strat.was_last_run_successful = was_last_run_successful()
#         self.assertEqual(run_strat.has_to_retry(), False)
#         self.assertEqual(run_strat._retry_count, 3)
#         run_strat.was_last_run_successful = was_last_run_successful()
#         self.assertEqual(run_strat.has_to_retry(), False)
#         self.assertEqual(run_strat._retry_count, 3)


class TestTask(unittest.TestCase):
    """Task test cases."""
    @patch("time.time")
    def test_has_to_run(self, mock_time):
        mock_time.return_value = 0
        t1 = Task(
            CommandFactory.make_command(
                "create_vm_in_ovirt", config="some_config"
            ),
            OneTimeRun()
        )
        t2 = Task(
            CommandFactory.make_command("get_vms_from_ovirt"),
            IntervalRun(30)
        )
        self.assertEqual(t1._strategy.task_has_to_run, True)
        self.assertEqual(t1._strategy._last_run_time, -1)
        self.assertEqual(t2._strategy.task_has_to_run, False)
        self.assertEqual(t2._strategy._last_run_time, -1)
        if t1.has_to_run:
            t1.run()
        if t2.has_to_run:
            t2.run()
        self.assertEqual(t2._strategy._next_run_time, 30)

        mock_time.return_value = 20
        self.assertEqual(t1._strategy.task_has_to_run, False)
        self.assertEqual(t1._strategy._last_run_time, 0)
        self.assertEqual(t2._strategy.task_has_to_run, False)
        self.assertEqual(t2._strategy._last_run_time, -1)
        if t1.has_to_run:
            t1.run()
        if t2.has_to_run:
            t2.run()
        self.assertEqual(t2._strategy._next_run_time, 30)

        mock_time.return_value = 40
        self.assertEqual(t1._strategy.task_has_to_run, False)
        self.assertEqual(t1._strategy._last_run_time, 0)
        self.assertEqual(t2._strategy.task_has_to_run, True)
        self.assertEqual(t2._strategy._last_run_time, -1)
        if t1.has_to_run:
            t1.run()
        if t2.has_to_run:
            t2.run()
        self.assertEqual(t1._strategy.task_has_to_run, False)
        self.assertEqual(t1._strategy._last_run_time, 0)
        self.assertEqual(t2._strategy.task_has_to_run, False)
        self.assertEqual(t2._strategy._next_run_time, 70)

        mock_time.return_value = 100
        self.assertEqual(t1._strategy.task_has_to_run, False)
        self.assertEqual(t1._strategy._last_run_time, 0)
        self.assertEqual(t2._strategy.task_has_to_run, True)
        self.assertEqual(t2._strategy._next_run_time, 70)
        if t1.has_to_run:
            t1.run()
        if t2.has_to_run:
            t2.run()
        self.assertEqual(t1._strategy.task_has_to_run, False)
        self.assertEqual(t1._strategy._last_run_time, 0)
        self.assertEqual(t2._strategy.task_has_to_run, False)
        self.assertEqual(t2._strategy._next_run_time, 130)

if __name__ == "__main__":
    unittest.main()
