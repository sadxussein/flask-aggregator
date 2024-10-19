"""Save and parse data from and to files."""

import re
import json
import ipaddress

import pandas as pd

from . import config as cfg

class FileHandler():
    """Handle files."""
    def __init__(self):
        self.__data = {}

    def collect_data(self, data: list, file_name: str) -> None:
        """Collect data from all virtualization sources."""
        if file_name in self.__data:
            self.__data[file_name] = self.__data[file_name] + data
        else:
            self.__data[file_name] = data

    def save_data_to_json_files(self) -> None:
        """Save info from function to JSON file."""
        for file_name, data in self.__data.items():
            with open(
                f"{cfg.VIRT_DATA_FOLDER}/{file_name}.json",
                'w',
                encoding="utf-8"
            ) as file:
                json.dump(data, file, ensure_ascii=False, indent=4)

    # def save_to_json_file(self, data: list, file_name: str) -> None:
    #     """Save info from function to JSON file."""
    #     with open(
    #         f"{cfg.VIRT_DATA_FOLDER}/{file_name}.json",
    #         'w',
    #         encoding="utf-8"
    #     ) as file:
    #         json.dump(data, file, ensure_ascii=False, indent=4)

    # def parse_vm_configs_from_excel(self, excel_file):
    #     """Parse ELMA excel file and return valid JSON VM config file."""
    #     result = []

    #     # Get VM info from excel file. Skip first two rows, which contain
    #     # meta information about VM.
    #     df_vm_meta = pd.read_excel(excel_file, nrows=2, header=None)

    #     # Skipping first 4 rows, containing VM meta, only loading main info
    #     # about VM. Transforming it to become vertical and dropping header
    #     # at first line.
    #     df_vm_config = pd.read_excel(excel_file, skiprows=4)
    #     df_vm_config = df_vm_config.T
    #     df_vm_config = df_vm_config.drop(df_vm_config.index[0])

    #     # Loop through all lines in data frame.
    #     for row in df_vm_config.itertuples():
    #         config = {"meta": {}, "ovirt": {}, "vm": {}, "vlan": {}}

    #         # Setting up file ID number (elma ID "3185" from "Заявка ВМ-3185
    #         # в BPMSoft Маркетинг.xlsx").
    #         document_num = re.match(r'^\D*(\d+)', excel_file)
    #         if document_num:
    #             config["meta"]["document_num"] = document_num.group(1)
    #         if not pd.isnull(row[1]):
    #             config["meta"]["inf_system"] = df_vm_meta.iat[0, 1]
    #             config["meta"]["owner"] = df_vm_meta.iat[1, 1]

    #             # From here and on we keep working with rows of data from
    #             # data frame. Rows are placed in following order in data
    #             # frame: (1) vm name, (2) vm hostname, (3) cpu number, (4)
    #             # memory size, (5) disks and mount points, (6) environment,
    #             # (7) OS, (8) backup flag (not used), (9) SRM protect flag
    #             # (not used), (10) crimea domain flag (not used), (11) admins
    #             # (not used), (12) DPC, (13) VLAN name, (14) VLAN id, (15)
    #             # subnet, (16) IP, (17) expiration date (not used), (18)
    #             # FreeIPA flag (not used), (19) comment (not used). So, rows
    #             # used are 0-6, 11-15. And as in Pandas itertuples rows are
    #             # counted from 1 we add +1 to their number.
    #             config["meta"]["environment"] = row[6]

    #             if "15" in row[12]:
    #                 # Checking environment. If VM should be productive it goes
    #                 # to e15-2, otherwise e15.
    #                 if (row[6] == "Продуктив"
    #                     and not "dbo-" in row[1]
    #                     and row[14] not in cfg.OLD_PROCESSING_VLANS
    #                     and "prc" not in row[13]):
    #                     config["ovirt"]["engine"] = "e15-2"
    #                 else:
    #                     config["ovirt"]["engine"] = "e15"
    #             elif "32" in row[12]:
    #                 # Here we have to check VLAN. If VLAN is in old network
    #                 # (N32_NEW_CIRCUIT_VLAN_SET), send VM to n32-2, n32
    #                 # otherwise.
    #                 if int(row[14]) in cfg.N32_NEW_CIRCUIT_VLAN_SET:
    #                     config["ovirt"]["engine"] = "n32"
    #                 else:
    #                     config["ovirt"]["engine"] = "n32-2"
    #             elif "45" in row[12]:
    #                 config["ovirt"]["engine"] = "k45"
    #             else:
    #                 # Set to none so that parser would throw an exception.
    #                 config["ovirt"]["engine"] = None

    #             config["vm"]["name"] = row[1]
    #             config["vm"]["hostname"] = row[2]
    #             config["vm"]["cores"] = row[3]
    #             config["vm"]["memory"] = row[4]

    #             # Searching for disks is a bit complicated. We are looking
    #             # for a string looking like 'Root|/|70\nOther|swap|16' or
    #             # 'Root|/|50\nOther|swap|16\nOther|/app|280'. So regex is
    #             # quite a choice for parsing each disk.
    #             disks_pattern = re.compile(r"(\w+)\|([\/]?.*)\|(\d+)")
    #             disks = disks_pattern.finditer(row[5])
    #             config["vm"]["disks"] = []
    #             if disks:
    #                 for disk in disks:
    #                     if str(disk.group(1)) == "Root":
    #                         disk_type = 1
    #                     else:
    #                         disk_type = 2
    #                     # Making sparse disks by default.
    #                     config["vm"]["disks"].append({"size": int(disk.group(3)),
    #                                               "type": disk_type,
    #                                               "mount_point": disk.group(2),
    #                                               "sparse": 1})
    #             config["vm"]["os"] = row[7]
    #             if config["vm"]["os"] == "RedOS 8":
    #                 config["vm"]["nic_name"] = "enp1s0"
    #             elif config["vm"]["os"] == "RedOS7.3":
    #                 config["vm"]["nic_name"] = "ens3"
    #             elif config["vm"]["os"] == "Астра Линукс 1.7 Воронеж":
    #                 config["vm"]["nic_name"] = "eth0"
    #             network = ipaddress.IPv4Network(row[15], strict=False)
    #             network_address = network.network_address
    #             config["vm"]["gateway"] = f"{network_address + 1}"
    #             config["vm"]["netmask"] = f"{network.netmask}"
    #             config["vm"]["address"] = row[16]

    #             # These two are set to some default values, but certain logic
    #             # could be applied also.
    #             config["vm"]["dns_servers"] = "10.82.254.32 10.82.254.31"
    #             config["vm"]["search_domain"] = "crimea.rncb.ru"

    #             config["vlan"]["name"] = row[13]
    #             config["vlan"]["id"] = row[14]
    #             if "prc" in row[13].lower():
    #                 config["vlan"]["suffix"] = "-prc"
    #             elif config["vlan"]["id"] in cfg.DBO_VLANS:
    #                 config["vlan"]["suffix"] = "-dbo"
    #             else:
    #                 config["vlan"]["suffix"] = ''

    #             # Now to setup values which depend on other values.
    #             # Defining cluster. So far we have logic for DBO, processing
    #             # and old processing clusters.
    #             if "dbo-" in config["vm"]["name"]:
    #                 config["ovirt"]["cluster"], config["ovirt"]["data_center"] = self.__get_vm_cluster_and_data_center("dbo", config, clusters)
    #             elif "prc" in config["vlan"]["name"].lower() and config["vlan"]["id"] not in cfg.OLD_PROCESSING_VLANS:
    #                 config["ovirt"]["cluster"], config["ovirt"]["data_center"] = self.__get_vm_cluster_and_data_center("Processing", config, clusters)
    #             elif config["vlan"]["id"] in cfg.OLD_PROCESSING_VLANS:
    #                 config["ovirt"]["cluster"], config["ovirt"]["data_center"] = self.__get_vm_cluster_and_data_center("Processing-OLD", config, clusters)
    #             # If no logic is viable for any cluster we set default one
    #             # (always with "The default server cluster" in its
    #             # description).
    #             else:
    #                 config["ovirt"]["cluster"] = next((cluster["name"] for cluster in clusters if "The default server cluster" in cluster["description"] and config["ovirt"]["engine"] == cluster["engine"]), None)
    #                 config["ovirt"]["data_center"] = next((cluster["data_center"] for cluster in clusters if "The default server cluster" in cluster["description"] and config["ovirt"]["engine"] == cluster["engine"]), None)

    #             # Setting up host (hypervisor) NIC.
    #             if config["vlan"]["id"] in cfg.DBO_VLANS:
    #                 if config["ovirt"]["engine"] == "e15":
    #                     if config["vlan"]["id"] % 2 == 0:
    #                         config["ovirt"]["host_nic"] = "ens51"
    #                     else:
    #                         config["ovirt"]["host_nic"] = "ens52"
    #                 elif config["ovirt"]["engine"] == "n32-2":
    #                     if config["vlan"]["id"] % 2 == 1:
    #                         config["ovirt"]["host_nic"] = "ens51"
    #                     else:
    #                         config["ovirt"]["host_nic"] = "ens52"
    #             elif (config["vlan"]["id"] in cfg.OLD_PROCESSING_VLANS and
    #                   (config["ovirt"]["engine"] in ["e15", "k45"])):
    #                 config["ovirt"]["host_nic"] = "bond1"
    #             else:
    #                 config["ovirt"]["host_nic"] = "bond0"

    #             config["ovirt"]["storage_domain"] = self.__get_vm_storage_domain(config)

    #             template_prefix = ''
    #             for dc in data_centers:
    #                 if dc["name"] == config["ovirt"]["data_center"] and dc["comment"] is not None:
    #                     template_prefix = f"_{dc['comment']}"

    #             if config["vm"]["os"] == "RedOS 8":
    #                 config["vm"]["template"] = "template-packer-redos8-03092024" + template_prefix
    #             elif config["vm"]["os"] == "RedOS7.3":
    #                 config["vm"]["template"] = "template-redos7-29072024" + template_prefix
    #             elif config["vm"]["os"] == "Астра Линукс 1.7 Воронеж":
    #                 config["vm"]["template"] = "template-packer-astra-04092024" + template_prefix

    #             result.append(config)
    #     return result

    def delete_file(self, file):
        """Delete file."""
