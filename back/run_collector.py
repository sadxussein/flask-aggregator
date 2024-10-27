"""Collector module.

Gathers information from each virtualization endpoint. Endpoints should be
defined in config.py (`DPC_LIST`) and have corresponding credentials in
`DPC_URLS`, `USERNAME` and `PASSWORD`.
"""

from .ovirt_helper import OvirtHelper
from .virt_aggregator import VirtAggregator
from .file_handler import FileHandler
from .logger import Logger
from . import config as cfg

if __name__ == "__main__":
    logger = Logger()
    virt_aggregator = VirtAggregator(logger=logger)
    file_handler = FileHandler()
    helper_list = []
    for dpc in cfg.DPC_LIST:
        helper_list.append(OvirtHelper(dpc_list=[dpc]))
    virt_aggregator.run_data_collection(helper_list,
                                        file_handler)
    file_handler.save_data_to_json_files(cfg.VIRT_DATA_FOLDER)
