"""Cenral module for virtualizations."""

from concurrent.futures import ThreadPoolExecutor
from itertools import zip_longest

from .virt_protocol import VirtProtocol
from .ovirt_helper import OvirtHelper
from .file_handler import FileHandler
from .logger import Logger
from ..config import Config
from .dbmanager import DBManager
from .models import Vm, Host, Cluster, Storage, DataCenter

class VirtAggregator():
    """Operate different virtualizations automation."""
    def __init__(self, logger=Logger()):
        self.__logger = logger
        self.__virt_helpers = []

    def __connect_to_virtualizations(self) -> None:
        """With all helpers."""
        self.__logger.log_debug(
            f"{self.__class__.__name__} - Connecting to virtualizations."
        )
        for virt_helper in self.__virt_helpers:
            virt_helper.connect_to_virtualization()

    def __disconnect_from_virtualizations(self) -> None:
        """With all helpers."""
        self.__logger.log_debug(
            (
                f"{self.__class__.__name__} - Trying to close all connections "
                "gracefully..."
            )
        )
        for virt_helper in self.__virt_helpers:
            virt_helper.disconnect_from_virtualization()

    def run_data_collection(self) -> None:
        """Gathering data from virtualizations.
        
        Args:
            virt_helpers (list): List of objects with their classes derived
            from VirtProtocol.
            file_handler (FileHandler): file handler.

        Returns:
            None
        """
        futures = []

        # 1. Establish connections with all virtualization endpoints.
        self.__connect_to_virtualizations()

        # 2. Run threads to gather info from virtualizations.
        with ThreadPoolExecutor(
            max_workers=100, thread_name_prefix="collector"
        ) as executor:
            for virt_helper in self.__virt_helpers:
                # Select only getter functions.
                virt_protocol_functions = [
                    f for f in dir(VirtProtocol) if f.startswith("get")
                ]
                for function_name in virt_protocol_functions:
                    futures.append(
                        executor.submit(
                            self.__get_virt_info, virt_helper, function_name
                        )
                    )
            for future in futures:
                future.result()

        # 3. Close connections with virtualizations safely.
        self.__disconnect_from_virtualizations()

    def __get_virt_info(
        self, virt_helper: VirtProtocol, function_name: str
    ) -> None:
        """Get certain info from virtualization based on function name."""
        dpcs = '_'.join(virt_helper.dpc_list)
        # Get table name by removing get_ prefix from function.
        table = function_name.removeprefix("get_")
        self.__logger.log_debug(f"Started thread {dpcs}-{function_name}.")
        dbmanager = DBManager()
        raw_data = getattr(virt_helper, function_name)()
        data = []
        if table == "vms":
            for el in raw_data:
                data.append(Vm(**el))
        elif table == "hosts":
            for el in raw_data:
                data.append(Host(**el))
        elif table == "clusters":
            for el in raw_data:
                data.append(Cluster(**el))
        elif table == "storages":
            for el in raw_data:
                data.append(Storage(**el))
        elif table == "data_centers":
            for el in raw_data:
                data.append(DataCenter(**el))
        dbmanager.add_data(data)
        dbmanager.close()
        self.__logger.log_debug(f"Finished thread {dpcs}-{function_name}.")


    def create_vms(self, file_handler: FileHandler) -> None:
        """Creating VMs with configs stored in JSON files."""
        futures = {}

        # 1. Establish connections with all virtualization endpoints.
        self.__connect_to_virtualizations()

        # 2. Run threads to gather info from virtualizations.
        for dpc in file_handler.dpc_vm_configs:
            futures[dpc] = []
        self.__logger.log_debug(
            f"{self.__class__.__name__} - Starting futures."
        )
        with ThreadPoolExecutor(
            max_workers=10, thread_name_prefix="creator"
        ) as executor:
            for virt_helper in self.__virt_helpers:
                for dpc, vm_configs in file_handler.dpc_vm_configs.items():
                    for vm_config in vm_configs:
                        if dpc in virt_helper.dpc_list:
                            futures[dpc].append(executor.submit(
                                virt_helper.create_vm, vm_config
                            ))
        for futures_tuple in zip_longest(*futures.values()):
            self.__logger.log_debug(futures_tuple)
            for future in futures_tuple:
                if future is not None:
                    future.result()

        # for future_list in futures.values():
        #     for future in future_list:
        #         future.result()

        # 3. Close connections with virtualizations safely.
        self.__disconnect_from_virtualizations()

    def create_vlans(self, file_handler: FileHandler) -> None:
        """Create VLAN's based on input JSON configs."""
        futures = {}

        self.__connect_to_virtualizations()

        for dpc in file_handler.dpc_vm_configs:
            futures[dpc] = []
        self.__logger.log_debug(
            f"{self.__class__.__name__} - Starting futures."
        )
        with ThreadPoolExecutor(
            max_workers=10, thread_name_prefix="creator"
        ) as executor:
            for virt_helper in self.__virt_helpers:
                for dpc, vm_configs in file_handler.dpc_vm_configs.items():
                    for vm_config in vm_configs:
                        if dpc in virt_helper.dpc_list:
                            futures[dpc].append(executor.submit(
                                virt_helper.create_vlan, vm_config
                            ))
        for futures_tuple in zip_longest(*futures.values()):
            self.__logger.log_debug(futures_tuple)
            for future in futures_tuple:
                if future is not None:
                    future.result()

        self.__disconnect_from_virtualizations()

    def create_virt_helpers(
            self, file_handler: dict=None, dpc_list: list=None
    ) -> None:
        """Generate helpers for each unique virtualization endpoint.
        
        Args:
            file_handler (FileHandler): could contain input JSON file. If no
              handler provided system will try to connect to all
                virtualizations set in config.py.

        From FileHandler field `dpc_vm_configs` set of DPC's is taken.
        """
        if file_handler is not None:
            for dpc in file_handler.dpc_vm_configs:
                self.__virt_helpers.append(OvirtHelper(
                    dpc_list=[dpc], logger=self.__logger
                ))
        elif dpc_list is not None:
            for dpc in dpc_list:
                self.__virt_helpers.append(OvirtHelper(
                    dpc_list=[dpc], logger=self.__logger
                ))
        else:
            for dpc in Config.DPC_LIST:
                self.__virt_helpers.append(OvirtHelper(
                    dpc_list=[dpc], logger=self.__logger
                ))
