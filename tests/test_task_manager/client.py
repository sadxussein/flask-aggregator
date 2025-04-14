"""Test client module for monitor server-client model."""

from flask_aggregator.back.task_manager.monitor import Client

if __name__ == "__main__":
    client = Client()
    client.run()
