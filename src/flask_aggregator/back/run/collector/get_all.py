"""Collector module.

Gathers information from each virtualization endpoint. Endpoints should be
defined in config.py (`DPC_LIST`) and have corresponding credentials in
`DPC_URLS`, `USERNAME` and `PASSWORD`."""

from flask_aggregator.back.virt_aggregator import VirtAggregator
from flask_aggregator.back.logger import Logger

def run():
    """External runner."""
    virt_aggregator = VirtAggregator(logger=Logger())
    virt_aggregator.create_virt_helpers()
    virt_aggregator.run_data_collection()

if __name__ == "__main__":
    run()
