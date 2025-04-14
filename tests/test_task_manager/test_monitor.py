"""Test cases for monitor module."""

import time
import json
import unittest
from unittest.mock import patch, MagicMock
from concurrent.futures import ThreadPoolExecutor

import flask_aggregator.back.task_manager.monitor as mon


class TestServer(unittest.TestCase):
    """Test cases for monitor server, which only sends messages to client."""
    def setUp(self):
        self.server = mon.Server()
        self.timeout = 3

    @patch("socket.socket")
    def test_run(self, mock_socket_class):
        """Simple run test. Make sure that monitor server is sending data to
        client via unix socket.
        """
        # Making test data for observer external callback.
        # Also mocking 'sendall' to check what it has when called.
        data = [
            {
                "name": "some_name",
                "result": "some_result",
                "error": None
            },
            {
                "name": "some_other_name",
                "result": None,
                "error": "some_error"
            }
        ]
        self.server.observer_callback(data)
        mock_socket = MagicMock()
        mock_conn = MagicMock()
        mock_socket_class.return_value = mock_socket
        mock_socket.accept.return_value = (mock_conn, None)

        # Test run for 'timeout' seconds.
        with ThreadPoolExecutor() as e:
            future = e.submit(self.server.run)

            start_time = time.time()
            now = start_time
            while now - start_time < self.timeout:
                now = time.time()
                time.sleep(1)

            self.server.stop()

            future.result()

        # Checking that mocked sendall called and that data is correct.
        mock_conn.sendall.assert_called()
        args, _ = mock_conn.sendall.call_args
        sent_data = args[0].decode()
        self.assertEqual(json.loads(sent_data), data)


class TestClient(unittest.TestCase):
    """Test cases for monitor client. It only shows what server sends him."""
    def setUp(self):
        self.client = mon.Client()
        self.timeout = 3

    @patch("socket.socket")
    def test_run(self, mock_socket_class):
        """Simple run test. Make sure that monitor client is showing the
        result in stdout.
        """
        mock_socket = MagicMock()
        mock_socket.recv.return_value = b"""[
            {
                "name": "some_name",
                "result": "some_result",
                "error": null
            },
            {
                "name": "some_other_name",
                "result": null,
                "error": "some_error"
            }
        ]"""
        mock_socket_class.return_value = mock_socket

        with ThreadPoolExecutor() as e:
            future = e.submit(self.client.run)

            start_time = time.time()
            now = start_time
            while now - start_time < self.timeout:
                now = time.time()
                time.sleep(1)

            self.client.stop()

            future.result()


class TestServerClient(unittest.TestCase):
    """Test cases for both monitor client and server."""
    def setUp(self):
        self.server = mon.Server()
        self.client = mon.Client()
        self.timeout = 3

    def test_send_message_from_server_to_client(self):
        """Test case for sending message from server to client."""
        self.server.observer_callback([
            {
                "name": "some_name",
                "result": "some_result",
                "error": None
            },
            {
                "name": "some_other_name",
                "result": None,
                "error": "some_error"
            }
        ])

        with ThreadPoolExecutor() as e:
            server_future = e.submit(self.server.run)
            time.sleep(1)
            client_future = e.submit(self.client.run)

            start_time = time.time()
            now = start_time
            while now - start_time < self.timeout:
                now = time.time()
                time.sleep(1)

            self.client.stop()  # TODO: some warning here. Don't know what to
                                # do with it yet.
            self.server.stop()

            server_future.result()
            client_future.result()

    # TODO: test big message.
    # TODO: test None message.

    def tearDown(self):
        self.client.stop()
        self.server.stop()


def start_test():
    """For debugger runs and usage in __main__."""
    test = TestServerClient(methodName="test_send_message_from_server_to_client")
    test.setUp()
    test.test_send_message_from_server_to_client()
    test.tearDown()


if __name__ == "__main__":
    start_test()
