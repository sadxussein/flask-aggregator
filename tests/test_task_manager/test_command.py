"""Command test cases module."""

import unittest

import tests.test_task_manager.debug_tools as dc
import flask_aggregator.back.task_manager.command as cmd


class TestCommand(unittest.TestCase):
    """Testing for abstract class and its subclasses."""
    def setUp(self):
        pass

    def test_execute_success(self):
        """`execute` command finishes with success state."""
        c = dc.AdditionCommand(1, 3)
        c.execute()
        self.assertEqual(c.state, cmd.State.SUCCESS)
        self.assertEqual(c.result, 4)
        self.assertEqual(c.error, None)

    def test_execute_failed(self):
        """`execute` command finishes with raised exception."""
        c = dc.AdditionCommand(1, "bad_arg")
        c.execute()
        self.assertEqual(c.error, "Bad agruments. Exiting.")
        self.assertEqual(c.result, None)
        self.assertEqual(c.state, cmd.State.FAILED)


if __name__ == "__main__":
    unittest.main()
