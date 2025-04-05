"""Strategy tests module."""

import unittest
from unittest.mock import patch
import flask_aggregator.back.task_manager.strategy as strat
import tests.test_task_manager.debug_tools as dt


# pylint: disable=protected-access

class TestOneTimeRun(unittest.TestCase):
    """One time run strategy test cases."""
    @patch("time.time")
    def test_update_times(self, mock_time):
        """Test creation of class instance."""
        time_gen = dt.mock_time_generator()

        mock_time.return_value = next(time_gen) # time.time() = 0
        strategy = strat.OneTimeRun()
        self.assertEqual(strategy.task_has_to_run, True)
        self.assertEqual(strategy.last_run_time, strat.IntervalRun.TASK_WAS_NOT_RUN_YET)

        mock_time.return_value = next(time_gen) # time.time() = 10
        strategy.mark_run_time()
        self.assertEqual(strategy.last_run_time, 10)


class TestIntervalRun(unittest.TestCase):
    """Interval run strategy test cases."""
    @patch("time.time")
    def test_update_times(self, mock_time):
        """Test creation of class instance."""
        time_gen = dt.mock_time_generator()

        mock_time.return_value = next(time_gen) # time.time() = 0
        strategy = strat.IntervalRun(20)
        self.assertEqual(strategy.task_has_to_run, True)
        self.assertEqual(strategy.last_run_time, strat.IntervalRun.TASK_WAS_NOT_RUN_YET)
        self.assertEqual(strategy._next_run_time, 0)
        self.assertEqual(strategy._interval, 20)

        strategy.mark_run_time()

        mock_time.return_value = next(time_gen) # time.time() = 10
        self.assertEqual(strategy.task_has_to_run, False)
        self.assertEqual(strategy.last_run_time, 0)
        self.assertEqual(strategy._next_run_time, 20)
        self.assertEqual(strategy._interval, 20)

        strategy.mark_run_time()

        mock_time.return_value = next(time_gen) # time.time() = 20
        self.assertEqual(strategy.task_has_to_run, False)
        self.assertEqual(strategy.last_run_time, 10)
        self.assertEqual(strategy._next_run_time, 30)
        self.assertEqual(strategy._interval, 20)
