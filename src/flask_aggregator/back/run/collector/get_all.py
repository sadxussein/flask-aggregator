"""Collector module.

Gathers information from each virtualization endpoint. Endpoints should be
defined in config.py (`DPC_LIST`) and have corresponding credentials in
`DPC_URLS`, `USERNAME` and `PASSWORD`."""

from src.flask_aggregator.back.virt_aggregator import VirtAggregator
from src.flask_aggregator.back.logger import Logger

if __name__ == "__main__":
    virt_aggregator = VirtAggregator(logger=Logger())
    virt_aggregator.create_virt_helpers()
    virt_aggregator.run_data_collection()
