"""Save and parse data from and to files."""

import os
import re
import json
import ipaddress
import requests

import yaml
import pandas as pd

from . import config as cfg

class Parser():
    """Handle files."""
    def __init__(self):
        self.__file_data = {}
        self.__input_json = {}
        self.__dpc_vm_configs = {}
        self.__dpc_list = []
        self.__create_folders()

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

    def save_data_to_json_files(self, target_folder: str) -> None:
        """Save info from function to JSON file."""
        for file_name, data in self.__file_data.items():
            with open(
                f"{target_folder}/{file_name}.json",
                'w',
                encoding="utf-8"
            ) as file:
                json.dump(data, file, ensure_ascii=False, indent=4)

    def __create_folders(self) -> None:
        """Prepare necessary folder infrastructure for files operations."""
        os.makedirs(cfg.LOGS_FOLDER, exist_ok=True)
        os.makedirs(cfg.FILES_FOLDER, exist_ok=True)
        os.makedirs(cfg.EXCEL_FILES_FOLDER, exist_ok=True)
        os.makedirs(cfg.ANSIBLE_DEFAULT_INVENTORIES_FOLDER, exist_ok=True)
        os.makedirs(cfg.ANSIBLE_IPA_INVENTORIES_FOLDER, exist_ok=True)
        os.makedirs(
            f"{cfg.ANSIBLE_IPA_INVENTORIES_FOLDER}/internal", exist_ok=True
        )
        os.makedirs(
            f"{cfg.ANSIBLE_IPA_INVENTORIES_FOLDER}/dmz", exist_ok=True
        )
        os.makedirs(cfg.VM_CONFIGS_FOLDER, exist_ok=True)
        os.makedirs(cfg.IPA_INTEGRATION_LOG_FOLDER, exist_ok=True)
        os.makedirs(cfg.IPA_NETWORK_CHECK_LOG_FOLDER, exist_ok=True)

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

    def __parse_vm_configs_from_excel(self, excel_file: str) -> list:
        """Parse ELMA excel file and return valid JSON VM config file.
        
        Any discussion considering ELMA document should be with Bruslenko A.M.
        or Stepanishin A.Y.
        """
        result = []
        document_nums = set()

        response = requests.get(
            f"http://{cfg.SERVER_IP}:{cfg.SERVER_PORT}"
            "/ovirt/cluster_list/raw_json", timeout=30
        )
        clusters = response.json()["data"]
        response = requests.get(
            f"http://{cfg.SERVER_IP}:{cfg.SERVER_PORT}"
            "/ovirt/data_center_list/raw_json", timeout=30
        )
        data_centers = response.json()["data"]

        # Get VM info from excel file. Skip first two rows, which contain
        # meta information about VM.
        df_vm_meta = pd.read_excel(excel_file, nrows=2, header=None)

        # Skipping first 4 rows, containing VM meta, only loading main info
        # about VM. Transforming it to become vertical and dropping header
        # at first line.
        df_vm_config = pd.read_excel(excel_file, skiprows=4)
        df_vm_config = df_vm_config.T
        df_vm_config = df_vm_config.drop(df_vm_config.index[0])

        # Loop through all lines in data frame.
        for row in df_vm_config.itertuples():
            config = {"meta": {}, "ovirt": {}, "vm": {}, "vlan": {}}

            # Setting up file ID number (elma ID "3185" from "Заявка ВМ-3185
            # в BPMSoft Маркетинг.xlsx").
            document_num = re.match(r'^\D*(\d+)', excel_file)
            if document_num:
                config["meta"]["document_num"] = document_num.group(1)
                document_nums.add(config["meta"]["document_num"])
            if not pd.isnull(row[1]):
                config["meta"]["inf_system"] = df_vm_meta.iat[0, 1]
                config["meta"]["owner"] = df_vm_meta.iat[1, 1]

                # From here and on we keep working with rows of data from
                # data frame. Rows are placed in following order in data
                # frame: (1) vm name, (2) vm hostname, (3) cpu number, (4)
                # memory size, (5) disks and mount points, (6) environment,
                # (7) OS, (8) backup flag (not used), (9) SRM protect flag
                # (not used), (10) crimea domain flag (not used), (11) admins
                # (not used), (12) DPC, (13) VLAN name, (14) VLAN id, (15)
                # subnet, (16) IP, (17) expiration date (not used), (18)
                # FreeIPA flag (not used), (19) comment (not used). So, rows
                # used are 0-6, 11-15. And as in Pandas itertuples rows are
                # counted from 1 we add +1 to their number.
                config["meta"]["environment"] = row[6]

                if "15" in row[12]:
                    # Checking environment. If VM should be productive it goes
                    # to e15-2, otherwise e15.
                    if (row[6] == "Продуктив"
                        and not "dbo-" in row[1]
                        and row[14] not in cfg.OLD_PROCESSING_VLANS
                        and "prc" not in row[13]):
                        config["ovirt"]["engine"] = "e15-2"
                    else:
                        config["ovirt"]["engine"] = "e15"
                elif "32" in row[12]:
                    # Here we have to check VLAN. If VLAN is in old network
                    # (N32_NEW_CIRCUIT_VLAN_SET), send VM to n32-2, n32
                    # otherwise.
                    if int(row[14]) in cfg.N32_NEW_CIRCUIT_VLAN_SET:
                        config["ovirt"]["engine"] = "n32-2"
                    else:
                        config["ovirt"]["engine"] = "n32"
                elif "45" in row[12]:
                    config["ovirt"]["engine"] = "k45"
                else:
                    # Set to none so that parser would throw an exception.
                    config["ovirt"]["engine"] = None

                config["vm"]["name"] = row[1]
                config["vm"]["hostname"] = row[2]
                config["vm"]["cores"] = row[3]
                config["vm"]["memory"] = row[4]

                # Searching for disks is a bit complicated. We are looking
                # for a string looking like 'Root|/|70\nOther|swap|16' or
                # 'Root|/|50\nOther|swap|16\nOther|/app|280'. So regex is
                # quite a choice for parsing each disk.
                disks_pattern = re.compile(r"(\w+)\|([\/]?.*)\|(\d+)")
                disks = disks_pattern.finditer(row[5])
                config["vm"]["disks"] = []
                if disks:
                    for disk in disks:
                        if str(disk.group(1)) == "Root":
                            disk_type = 1
                        else:
                            disk_type = 2
                        # Making sparse disks by default.
                        config["vm"]["disks"].append(
                            {
                                "size": int(disk.group(3)),
                                "type": disk_type,
                                "mount_point": disk.group(2),
                                "sparse": 1
                            }
                        )
                config["vm"]["os"] = row[7]
                if config["vm"]["os"] == "RedOS 8":
                    config["vm"]["nic_name"] = "enp1s0"
                elif config["vm"]["os"] == "RedOS7.3":
                    config["vm"]["nic_name"] = "ens3"
                elif config["vm"]["os"] == "Астра Линукс 1.7 Воронеж":
                    config["vm"]["nic_name"] = "eth0"
                network = ipaddress.IPv4Network(row[15], strict=False)
                network_address = network.network_address
                config["vm"]["gateway"] = f"{network_address + 1}"
                config["vm"]["netmask"] = f"{network.netmask}"
                config["vm"]["address"] = row[16]

                # These two are set to some default values, but certain logic
                # could be applied also.
                config["vm"]["dns_servers"] = "10.82.254.32 10.82.254.31"
                config["vm"]["search_domain"] = "crimea.rncb.ru"

                config["vlan"]["name"] = row[13]
                config["vlan"]["id"] = row[14]
                if "prc" in row[13].lower():
                    config["vlan"]["suffix"] = "-prc"
                elif config["vlan"]["id"] in cfg.DBO_VLANS:
                    config["vlan"]["suffix"] = "-dbo"
                else:
                    config["vlan"]["suffix"] = ''

                # Defining cluster. So far we have logic for DBO, processing
                # and old processing clusters.
                if "dbo-" in config["vm"]["name"]:
                    config["ovirt"]["cluster"], config["ovirt"]["data_center"] = self.__get_vm_cluster_and_data_center("dbo", config, clusters)
                elif "prc" in config["vlan"]["name"].lower() and config["vlan"]["id"] not in cfg.OLD_PROCESSING_VLANS:
                    config["ovirt"]["cluster"], config["ovirt"]["data_center"] = self.__get_vm_cluster_and_data_center("Processing", config, clusters)
                elif config["vlan"]["id"] in cfg.OLD_PROCESSING_VLANS:
                    config["ovirt"]["cluster"], config["ovirt"]["data_center"] = self.__get_vm_cluster_and_data_center("Processing-OLD", config, clusters)
                # If no logic is viable for any cluster we set default one
                # (always with "The default server cluster" in its
                # description).
                else:
                    config["ovirt"]["cluster"] = next(
                        (
                            cluster["name"] for cluster in clusters["data"]
                            if "The default server cluster"
                            in cluster["description"]
                            and config["ovirt"]["engine"] == cluster["engine"]
                        ),
                        None
                    )
                    config["ovirt"]["data_center"] = next(
                        (
                            cluster["data_center"] for cluster
                            in clusters["data"] 
                            if "The default server cluster"
                            in cluster["description"]
                            and config["ovirt"]["engine"] == cluster["engine"]
                        ),
                        None
                    )
                # Setting up host (hypervisor) NIC.
                if config["vlan"]["id"] in cfg.DBO_VLANS:
                    if config["ovirt"]["engine"] == "e15":
                        if config["vlan"]["id"] % 2 == 0:
                            config["ovirt"]["host_nic"] = "ens51"
                        else:
                            config["ovirt"]["host_nic"] = "ens52"
                    elif config["ovirt"]["engine"] == "n32-2":
                        if config["vlan"]["id"] % 2 == 1:
                            config["ovirt"]["host_nic"] = "ens51"
                        else:
                            config["ovirt"]["host_nic"] = "ens52"
                elif (config["vlan"]["id"] in cfg.OLD_PROCESSING_VLANS and
                      (config["ovirt"]["engine"] in ["e15", "k45"])):
                    config["ovirt"]["host_nic"] = "bond1"
                else:
                    config["ovirt"]["host_nic"] = "bond0"

                config["ovirt"]["storage_domain"] = self.__get_vm_storage_domain(config)

                template_prefix = ''
                for dc in data_centers:
                    if dc["name"] == config["ovirt"]["data_center"] and dc["comment"] is not None:
                        template_prefix = f"_{dc['comment']}"

                if config["vm"]["os"] == "RedOS 8":
                    config["vm"]["template"] = "template-packer-redos8-02112024" + template_prefix
                elif config["vm"]["os"] == "RedOS7.3":
                    config["vm"]["template"] = "template-redos7-06112024" + template_prefix
                elif config["vm"]["os"] == "Астра Линукс 1.7 Воронеж":
                    config["vm"]["template"] = "template-packer-astra-174-05112024" + template_prefix

                result.append(config)
        return result

    def __get_vm_cluster_and_data_center(self, target, config, clusters):
        """Get VM both cluster and data center.
        
        'target' here is a definitive part of cluster name, e.g. 'dbo' in
        'e15-DBO-cluster'.
        """
        result = (None, None)
        for cluster in clusters:
            if target.lower() in cluster["name"].lower() and config["ovirt"]["engine"] == cluster["engine"]:
                result = (cluster["name"], cluster["data_center"])
        return result

    def __get_vm_storage_domain(self, config):
        """Define on which storage VM should be put.
        
        Hard-coded logic, since defining which storage is preferable at any
        given moment is complicated even for living people.
        """
        result = None
        if config["ovirt"]["engine"] == "e15":
            if config["ovirt"]["cluster"] == "e15-Processing":
                result = "E15-DEPO4-REDPRC1"
            elif config["ovirt"]["cluster"] == "e15-Processing-OLD":
                result = "E15-AF250S3-4-PRC-OLD1"
            else:
                result =  "E15-DEPO4-REDDS2"
        if config["ovirt"]["engine"] == "e15-2":
            result = "E15-DEPO4-RED2-DS1"
        elif config["ovirt"]["engine"] == "n32":
            if config["ovirt"]["cluster"] == "n32-Processing":
                result = "N32-AF250S1-REDPRC1"
            else:
                result = "N32-AF250S3-REDDS2"
        elif config["ovirt"]["engine"] == "n32-2":
            result = "N32-TATLIN-REDDS2"
        elif config["ovirt"]["engine"] == "k45":
            if config["ovirt"]["cluster"] == "k45-Processing":
                result = "K45-AF250S3-REDPRC2"
            elif config["ovirt"]["cluster"] == "k45-Processing-OLD":
                result = "K45-AF250S3-PRC-OLD1"
            else:
                result = "K45-AF250S3-REDDS2"
        return result

    def prepare_vm_environment(self, excel_file: str) -> None:
        """Prepare all necessary files for VM creation and setup.
        
        Args:
            excel_file (str): Excel file path.

        Generate three folder of files (e.g. 'vm1234.yml'):
        1. inventories for VM preparation playbook/role, with info about VM
        disks.
        2. inventories for IPA Internal.
        3. inventories for IPA DMZ.
        """
        self.__create_folders()
        vm_configs = self.__parse_vm_configs_from_excel(excel_file)
        document_num = vm_configs[0]["meta"]["document_num"]
        self.__file_data[f"vm{document_num}"] = vm_configs
        self.__generate_ansible_environment(vm_configs, document_num)
        self.__create_bash_vm_commands(document_num)
        self.save_data_to_json_files(cfg.VM_CONFIGS_FOLDER)
        bash_commands = self.__create_bash_vm_commands(document_num)
        with open(
            f"{cfg.FILES_FOLDER}/bash_commands.sh", 'a',
            encoding="utf-8"
        ) as file:
            for line in bash_commands:
                print(line, file=file)

    def __generate_ansible_environment(self, configs, document_num):  # TODO: fix long lines
        """Generate ansible playbooks and inventories for VM tuning and
        FreeIPA accessing."""
        default_inventory = {"all": {"hosts": {}}}
        ipa_inventory_internal = {
            "all": {
                "vars": {
                    "free_ipa": "yes",
                    "ipa_client_state": "present",
                    "ipa_host": "yes"
                },
                "hosts": {}
            }
        }
        ipa_inventory_dmz = {
            "ipa_dmz": {
                "vars": {
                    "free_ipa": "yes",
                    "ipa_client_state": "present",
                    "ipa_host": "yes"
                },
                "hosts": {}
            }
        }
        for config in configs:
            default_inventory["all"]["hosts"][config["vm"]["name"]] = {}
            default_inventory["all"]["hosts"][config["vm"]["name"]]["ansible_host"] = config["vm"]["address"]
            ipa_inventory_internal["all"]["hosts"][config["vm"]["name"]] = {}
            ipa_inventory_internal["all"]["hosts"][config["vm"]["name"]]["ansible_host"] = config["vm"]["address"]
            ipa_inventory_dmz["ipa_dmz"]["hosts"][config["vm"]["name"]] = {}
            ipa_inventory_dmz["ipa_dmz"]["hosts"][config["vm"]["name"]]["ansible_host"] = config["vm"]["address"]
            if len(config["vm"]["disks"]) > 1:
                default_inventory["all"]["hosts"][config["vm"]["name"]]["disks"] = []
                for disk in config["vm"]["disks"]:
                    if disk["type"] == 2:
                        disk_dict = {}
                        disk_dict["mount_point"] = disk["mount_point"]
                        disk_dict["size"] = disk["size"]
                        default_inventory["all"]["hosts"][config["vm"]["name"]]["disks"].append(disk_dict)

        # Saving results.
        with open(f"{cfg.ANSIBLE_DEFAULT_INVENTORIES_FOLDER}/vm{document_num}.yml", 'w', encoding="utf-8") as file:
            yaml.dump(default_inventory, file, default_flow_style=False)
        with open(f"{cfg.ANSIBLE_IPA_INVENTORIES_FOLDER}/internal/vm{document_num}.yml", 'w', encoding="utf-8") as file:
            yaml.dump(ipa_inventory_internal, file, default_flow_style=False)
        with open(f"{cfg.ANSIBLE_IPA_INVENTORIES_FOLDER}/dmz/vm{document_num}.yml", 'w', encoding="utf-8") as file:
            yaml.dump(ipa_inventory_dmz, file, default_flow_style=False)

    def __create_bash_vm_commands(self, document_num):
        """Create bash commands for VM creation.
        
        Returns:
            list (string): Following command lines will be generated:
            1. `curl` POST with VM creation options;
            2. `ansible-playbook` for VM setup (disks, users, fixes, etc.);
            3. `ansible-playbook` for VM IPA insertion.
        """
        result = []

        vm_configs = os.path.abspath(cfg.VM_CONFIGS_FOLDER)
        server_path = f"http://{cfg.SERVER_IP}:{cfg.SERVER_PORT}/ovirt/create_vm"
        default_playbooks = os.path.abspath(cfg.ANSIBLE_DEFAULT_INVENTORIES_FOLDER)
        net_check_log = os.path.abspath(cfg.IPA_NETWORK_CHECK_LOG_FOLDER)
        interg_log = os.path.abspath(cfg.IPA_INTEGRATION_LOG_FOLDER)
        int_playbs = os.path.abspath(cfg.ANSIBLE_IPA_INTERNAL_FOLDER)
        dmz_playbs = os.path.abspath(cfg.ANSIBLE_IPA_DMZ_FOLDER)

        result.append(f"# vm{document_num}")
        result.append("# CURL POST VM")
        result.append(
            (
                f"curl -X POST -F 'jsonfile=@{vm_configs}/vm{document_num}."
                f"json' {server_path}"
            )
        )
        result.append("# PREPARE VM")
        result.append(
            (
                f"ansible-playbook -i {default_playbooks}/vm{document_num}"
                ".yml default-playbook.yml"
            )
        )
        result.append("# IPA INTERNAL")
        result.append(
            (
                f"rm -f {net_check_log}/vm{document_num}.log &&"
                f" ANSIBLE_LOG_PATH={net_check_log}/vm{document_num}.log "
                f"ansible-playbook -i {int_playbs}/vm{document_num}.yml "
                " network_check.yml -u svc_ansibleoiti"
            )
        )
        result.append(
            (
                f"ANSIBLE_LOG_PATH={interg_log}/vm{document_num}_"
                "$(date +%Y-%m-%d_%H-%M-%S).log ansible-playbook -i "
                f"{int_playbs}/vm{document_num}.yml host_prepare.yml -u "
                "svc_ansibleoiti --tags all,ipa_client_repair,"
                "splunk_reinstall --skip-tags pause"
            )
        )
        result.append("# IPA DMZ")
        result.append(
            (
                f"rm -f {net_check_log}/vm{document_num}.log &&"
                f" ANSIBLE_LOG_PATH={net_check_log}/vm{document_num}.log "
                f"ansible-playbook -i {dmz_playbs}/vm{document_num}.yml "
                " network_check.yml -u svc_ansibleoiti"
            )
        )
        result.append(
            (
                f"ANSIBLE_LOG_PATH={interg_log}/vm{document_num}_"
                "$(date +%Y-%m-%d_%H-%M-%S).log ansible-playbook -i "
                f"{dmz_playbs}/vm{document_num}.yml host_prepare.yml -u "
                "svc_ansibleoiti --tags all,ipa_client_repair,"
                "splunk_reinstall --skip-tags pause"
            )
        )
        result.append('')

        return result
