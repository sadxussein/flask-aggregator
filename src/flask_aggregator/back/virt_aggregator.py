"""Cenral module for virtualizations."""

from concurrent.futures import ThreadPoolExecutor
from itertools import zip_longest

from flask_aggregator.config import Config
from flask_aggregator.back.virt_protocol import VirtProtocol
from flask_aggregator.back.ovirt_helper import OvirtHelper
from flask_aggregator.back.file_handler import FileHandler
from flask_aggregator.back.logger import Logger
from flask_aggregator.back.dbmanager import DBManager

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

    def run_data_collection(
        self, function_type: str="default", function: str=None
    ) -> None:
        """Gathering data from virtualizations.
        
        Args:
            virt_helpers (list): List of objects with their classes derived
            from VirtProtocol.
            file_handler (FileHandler): file handler.

        Returns:
            None
        """
        futures = []

        function_prefix = ""
        if function_type == "default":
            function_prefix = "get_"

        # 1. Establish connections with all virtualization endpoints.
        self.__connect_to_virtualizations()

        # 2. Run threads to gather info from virtualizations.
        with ThreadPoolExecutor(
            max_workers=100, thread_name_prefix="collector"
        ) as executor:
            for virt_helper in self.__virt_helpers:
                # Select only getter functions.
                virt_protocol_functions = [
                    f for f in dir(VirtProtocol)
                    if f.startswith(function_prefix)
                ]
                if function is not None:
                    virt_protocol_functions = [
                        f for f in dir(VirtProtocol)
                        if f == function
                    ]
                for function_name in virt_protocol_functions:
                    futures.append(
                        executor.submit(
                            self.__get_virt_info, virt_helper, function_name,
                            function_prefix
                        )
                    )
            for future in futures:
                future.result()

        # 3. Close connections with virtualizations safely.
        self.__disconnect_from_virtualizations()

    def __get_virt_info(
        self, virt_helper: VirtProtocol, function_name: str,
        function_prefix: str
    ) -> None:
        """Get certain info from virtualization based on function name."""
        dpcs = '_'.join(virt_helper.dpc_list)
        # Get table name by removing corresponding prefix from function.
        table = function_name.removeprefix(function_prefix)
        self.__logger.log_debug(f"Started thread {dpcs}-{function_name}.")
        dbmanager = DBManager()
        raw_data = getattr(virt_helper, function_name)()
        # TODO: consider removing next line. Its a hostfix for deduplicating hosts.
        # Some research is required to deduplicate any entity.
        if function_name == "get_hosts":
            dbmanager.upsert_data(
            Config.DB_MODELS[table],
            raw_data,
            ["name"],
            ["id", "name"]
        )
        else:
            dbmanager.upsert_data(
                Config.DB_MODELS[table],
                raw_data,
                ["uuid"],
                ["id", "uuid"]
            )
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
