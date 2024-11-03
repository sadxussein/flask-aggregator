"""Collector module.

Gathers information from each virtualization endpoint. Endpoints should be
defined in config.py (`DPC_LIST`) and have corresponding credentials in
`DPC_URLS`, `USERNAME` and `PASSWORD`."""

from .virt_aggregator import VirtAggregator
from .file_handler import FileHandler
from . import config as cfg

if __name__ == "__main__":
    virt_aggregator = VirtAggregator()
    file_handler = FileHandler()
    helper_list = []
    virt_aggregator = VirtAggregator()
    virt_aggregator.create_virt_helpers()
    virt_aggregator.run_data_collection(file_handler)
    file_handler.save_data_to_json_files(cfg.VIRT_DATA_FOLDER)
