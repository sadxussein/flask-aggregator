"""Monitor client and server, unix-socket based."""

import os
import json
import time
import socket
from typing import Any

from flask_aggregator.back.logger import Logger

# TODO: add logging.
class Server:
    """Interface for watching at tasks interactivly and in real-time."""
    def __init__(
        self,
        socket_path: str="/tmp/fa-mon",
        polling_interval: float=1
    ):
        self.socket_path = socket_path
        self._running = True
        self._polling_interval = polling_interval
        self._task_data = []
        self._logger = Logger()

    def observer_callback(self, data: list[Any]):
        """Callback for filling monitoring server with data from task
        registry.
        """
        self._task_data = data

    def run(self):
        """Main entry for monitor."""
        if os.path.exists(self.socket_path):
            os.remove(self.socket_path)

        try:
            server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            server.bind(self.socket_path)
            server.listen(1)

            conn, _ = server.accept()
            while self._running:
                serialized = json.dumps(self._task_data).encode()
                conn.sendall(serialized)
                time.sleep(self._polling_interval)
        except Exception as e:
            self._logger.log_error(e)
        finally:
            self._logger.log_info("Stopping monitor server.")
            server.close()

    def stop(self):
        """Stop monitor."""
        self._running = False
        if os.path.exists(self.socket_path):
            os.remove(self.socket_path)


class Client:
    """Unix socket based client."""
    def __init__(
        self,
        socket_path: str="/tmp/fa-mon",
        polling_interval: float=1
    ):
        self._running = True
        self.socket_path = socket_path
        self._polling_interval = polling_interval

    def run(self):
        """Start monitoring client."""
        try:
            client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            client.connect(self.socket_path)

            while self._running:
                recieved_raw_data = client.recv(1024)

                if not recieved_raw_data:
                    self.stop()

                self.__render_task_monitor(recieved_raw_data)

                time.sleep(self._polling_interval)

        except Exception as e:
            print("Exception:", e)
        finally:
            client.close()

    def __render_task_monitor(self, data: any):
        data = json.loads(data.decode())
        os.system("clear")
        for row in data:
            print(row["name"], row["result"], row["error"], row["state"])

    def stop(self):
        """Stop monitoring client."""
        self._running = False
