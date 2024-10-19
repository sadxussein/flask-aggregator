"""Cenral module for virtualizations."""

from concurrent.futures import ThreadPoolExecutor

from .virt_protocol import VirtProtocol
from .file_handler import FileHandler
from .logger import Logger

class VirtAggregator():
    """Operate different virtualizations automation."""
    def __init__(self, logger=Logger()):
        self.__logger = logger

    def run_data_collection(self,
                     virt_helpers: list,
                     file_handler: FileHandler
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

        # 1. Establish connections with all virtualization endpoints.
        for virt_helper in virt_helpers:
            virt_helper.connect_to_virtualization()

        # 2. Run threads to gather info from virtualizations.
        with ThreadPoolExecutor(max_workers=25, thread_name_prefix="collector") as executor:
            for virt_helper in virt_helpers:
                virt_protocol_functions = [f for f in dir(VirtProtocol) if f.startswith("get")]
                for function_name in virt_protocol_functions:
                    futures.append(
                        executor.submit(self.__get_virt_info, virt_helper,
                                        function_name, file_handler
                        )
                    )
            for future in futures:
                future.result()

        # 3. Close connections with virtualizations safely.
        for virt_helper in virt_helpers:
            virt_helper.disconnect_from_virtualization()

    def __get_virt_info(self,
                     virt_helper: VirtProtocol,
                     function_name: str,
                     file_handler: FileHandler
                     ) -> None:
        """Get certain info from virtualization based on function name."""
        self.__logger.log_info(f"Started thread {virt_helper.dpc_list}-{function_name}.")
        file_handler.collect_data(
            getattr(virt_helper, function_name)(),
            f"{virt_helper.pretty_name}_{function_name}"
        )
        self.__logger.log_info(f"Finished thread {virt_helper.dpc_list}-{function_name}.")

    def create_vms(self,
                     virt_helpers: VirtProtocol,
                     file_handler: FileHandler
                     ) -> None:
        """Creating VMs with configs stored in JSON files."""  
