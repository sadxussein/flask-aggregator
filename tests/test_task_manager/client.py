"""Runner module for task manager monitor client."""

from concurrent.futures import ThreadPoolExecutor

from flask_aggregator.back.task_manager.monitor import Client


class MonitorClient:
    """Real test example of task manager monitor client."""
    def __init__(self):
        self._client = Client()
        self._running = True

    def stop(self):
        """Stop monitor client."""
        self._running = False
        self._client.stop()

    def __interact(self):
        """Simple user IO interaction."""
        user_input = input("press 'e' to finish")
        if user_input == "e":
            self.stop()

    def run(self):
        """Runner with user interaction."""
        with ThreadPoolExecutor() as e:
            future = e.submit(self._client.run)
            while self._running:
                self.__interact()
            future.result()


if __name__ == "__main__":
    client = MonitorClient()
    client.run()
