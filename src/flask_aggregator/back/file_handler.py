"""Save and parse data from and to files."""

import json

class FileHandler():
    """Handle files."""
    def __init__(self):
        self.__file_data = {}
        self.__input_json = {}
        self.__dpc_vm_configs = {}
        self.__dpc_list = []

    @property
    def file_data(self):
        """Return files stored in data.
        
        Returns:
            data (dict): Key: file name, value: file data.
        """
        return self.__file_data

    @property
    def dpc_vm_configs(self):
        """Return DPC specifics VM configs."""
        return self.__dpc_vm_configs

    @property
    def dpc_list(self):
        """Return list of unique DPCs."""
        return self.__dpc_list

    @property
    def input_json(self):
        """Return JSON stored in handler.
        
        Returns:
            json (dict): VM config.
        """
        return self.__input_json

    @input_json.setter
    def input_json(self, input_json):
        self.__input_json = input_json

    def collect_data(self, data: list, file_name: str) -> None:
        """Collect data from all virtualization sources.
        
        Args:
            data (list): Returned from VirtProtocol classes getter functions,
                such as ovirt_helper.get_vms(). Always should be a list of
                dicts.
            file_name (str): What name will be used for file, which stores
                `data` values.

        What this function does is simply collects dictionary with keys as 
        file names and values as lists of dicts.
        """
        if file_name in self.__file_data:
            self.__file_data[file_name] = self.__file_data[file_name] + data
        else:
            self.__file_data[file_name] = data

    def save_data_to_json_files(self, target_folder: str) -> None:
        """Save info from function to JSON file."""
        for file_name, data in self.__file_data.items():
            with open(
                f"{target_folder}/{file_name}.json",
                'w',
                encoding="utf-8"
            ) as file:
                json.dump(data, file, ensure_ascii=False, indent=4)

    def make_unique_vlan_configs(self) -> None:
        """In order to create VLANs it is better to get a set of unique
        VLANs and create only them."""
        result = {}
        seen = {}
        for dpc in self.__dpc_list:
            result[dpc] = []
            seen[dpc] = set()
        for dpc, configs in self.__dpc_vm_configs.items():
            for config in configs:
                if config["vlan"]["name"] not in seen[dpc]:
                    result[dpc].append(config)
                    seen[dpc].add(config["vlan"]["name"])
        self.__dpc_vm_configs = result

    def reformat_input_json(self):
        """Reformat input JSON file.

        Reformatting input JSON file hierarchy from `list -> vm configs as 
        dicts` to `dpc dict key -> list -> vm configs as dicts`. With such
        hierarchy it is easier to split threads for each DPC.
        """
        self.__get_dpc_list()
        for dpc in self.__dpc_list:
            self.__dpc_vm_configs[dpc] = []
        for config in self.__input_json:
            self.__dpc_vm_configs[config["ovirt"]["engine"]].append(config)

    def __get_dpc_list(self):
        """Extract from JSON file DPC set."""
        dpc_set = set()
        for config in self.__input_json:
            dpc_set.add(config["ovirt"]["engine"])
        self.__dpc_list = list(dpc_set)

    def delete_file(self, file):
        """Delete file."""
