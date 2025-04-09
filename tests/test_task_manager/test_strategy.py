"""Strategy tests module."""

import unittest
from unittest.mock import patch
import flask_aggregator.back.task_manager.strategy as strat
import tests.test_task_manager.debug_tools as dt


# pylint: disable=protected-access

class TestOneTimeRun(unittest.TestCase):
    """One time run strategy test cases."""
    @patch("time.time")
    def test_init(self, mock_time):
        """Test case for initial parameters of one time run instance."""
        time_gen = dt.mock_time_generator()

        mock_time.return_value = next(time_gen) # time.time() = 0
        strategy = strat.OneTimeRun()
        self.assertEqual(strategy.time_created, 0)
        self.assertEqual(strategy.start_run_time, strat.IntervalRun.TASK_WAS_NOT_RUN_YET)
        self.assertEqual(strategy.stop_run_time, strat.IntervalRun.TASK_WAS_NOT_RUN_YET)
        self.assertEqual(strategy.last_run_time, strat.IntervalRun.TASK_WAS_NOT_RUN_YET)
        self.assertEqual(strategy.task_has_to_run, True)

    @patch("time.time")
    def test_update_times(self, mock_time):
        """Test creation of class instance."""
        time_gen = dt.mock_time_generator()

        mock_time.return_value = next(time_gen) # time.time() = 0
        strategy = strat.OneTimeRun()
        self.assertEqual(strategy.time_created, 0)
        self.assertEqual(strategy.start_run_time, strat.IntervalRun.TASK_WAS_NOT_RUN_YET)
        self.assertEqual(strategy.stop_run_time, strat.IntervalRun.TASK_WAS_NOT_RUN_YET)
        self.assertEqual(strategy.last_run_time, strat.IntervalRun.TASK_WAS_NOT_RUN_YET)
        self.assertEqual(strategy.task_has_to_run, True)

        mock_time.return_value = next(time_gen) # time.time() = 10
        strategy.mark_start_time()
        self.assertEqual(strategy.time_created, 0)
        self.assertEqual(strategy.start_run_time, 10)
        self.assertEqual(strategy.stop_run_time, -1)
        self.assertEqual(strategy.last_run_time, 10)
        self.assertEqual(strategy.task_has_to_run, False)

        mock_time.return_value = next(time_gen) # time.time() = 20
        strategy.mark_stop_time()
        self.assertEqual(strategy.time_created, 0)
        self.assertEqual(strategy.start_run_time, 10)
        self.assertEqual(strategy.stop_run_time, 20)
        self.assertEqual(strategy.last_run_time, 10)
        self.assertEqual(strategy.task_has_to_run, False)


class TestIntervalRun(unittest.TestCase):
    """Interval run strategy test cases."""
    @patch("time.time")
    def test_init(self, mock_time):
        """Test case for initial parameters of interval run instance."""
        time_gen = dt.mock_time_generator()

        mock_time.return_value = next(time_gen) # time.time() = 0
        strategy = strat.IntervalRun(20)
        self.assertEqual(strategy.time_created, 0)
        self.assertEqual(strategy.start_run_time, strat.IntervalRun.TASK_WAS_NOT_RUN_YET)
        self.assertEqual(strategy.stop_run_time, strat.IntervalRun.TASK_WAS_NOT_RUN_YET)
        self.assertEqual(strategy.last_run_time, strat.IntervalRun.TASK_WAS_NOT_RUN_YET)
        self.assertEqual(strategy.next_run_time, 0)
        self.assertEqual(strategy.interval, 20)
        self.assertEqual(strategy.task_has_to_run, True)

    def test_bad_interval(self):
        """In case if interval is < 0 exception should be raised."""
        with self.assertRaises(ValueError) as e:
            strategy = strat.IntervalRun(-1)
        self.assertEqual(str(e.exception), "Time interval can not be equal or less than 0.")

    @patch("time.time")
    def test_update_times(self, mock_time):
        """Test creation of class instance."""
        time_gen = dt.mock_time_generator()

        mock_time.return_value = next(time_gen) # time.time() = 0
        
        strategy = strat.IntervalRun(20)

        self.assertEqual(strategy.time_created, 0)
        self.assertEqual(strategy.start_run_time, strat.IntervalRun.TASK_WAS_NOT_RUN_YET)
        self.assertEqual(strategy.stop_run_time, strat.IntervalRun.TASK_WAS_NOT_RUN_YET)
        self.assertEqual(strategy.last_run_time, strat.IntervalRun.TASK_WAS_NOT_RUN_YET)
        self.assertEqual(strategy.next_run_time, 0)
        self.assertEqual(strategy.interval, 20)
        self.assertEqual(strategy.task_has_to_run, True)

        strategy.mark_start_time()

        mock_time.return_value = next(time_gen) # time.time() = 10

        self.assertEqual(strategy.time_created, 0)
        self.assertEqual(strategy.start_run_time, 0)
        self.assertEqual(strategy.stop_run_time, strat.IntervalRun.TASK_WAS_NOT_RUN_YET)
        self.assertEqual(strategy.last_run_time, 0)
        self.assertEqual(strategy.next_run_time, 20)
        self.assertEqual(strategy.interval, 20)
        self.assertEqual(strategy.task_has_to_run, False)
        
        mock_time.return_value = next(time_gen) # time.time() = 20

        strategy.mark_stop_time()
        strategy.mark_start_time()

        self.assertEqual(strategy.time_created, 0)
        self.assertEqual(strategy.start_run_time, 20)
        self.assertEqual(strategy.stop_run_time, 20)
        self.assertEqual(strategy.last_run_time, 20)
        self.assertEqual(strategy.next_run_time, 40)
        self.assertEqual(strategy.interval, 20)
        self.assertEqual(strategy.task_has_to_run, False)

        mock_time.return_value = next(time_gen) # time.time() = 30
        mock_time.return_value = next(time_gen) # time.time() = 40

        strategy.mark_stop_time()

        self.assertEqual(strategy.time_created, 0)
        self.assertEqual(strategy.start_run_time, 20)
        self.assertEqual(strategy.stop_run_time, 40)
        self.assertEqual(strategy.last_run_time, 20)
        self.assertEqual(strategy.next_run_time, 40)
        self.assertEqual(strategy.interval, 20)
        self.assertEqual(strategy.task_has_to_run, True)
