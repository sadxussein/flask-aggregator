"""Get storage domain information."""

import json
from back.ovirt_helper import OvirtHelper
from . import config as cfg

if __name__ == "__main__":
    ovirt_helper = OvirtHelper()
    ovirt_helper.connect_to_engines()
    cluster_names = ovirt_helper.get_storage_domain_list()
    ovirt_helper.disconnect_from_engines()
    with open(f"{cfg.BACK_FILES_FOLDER}/storage_domain_list.json", 'w', encoding="utf-8") as file:
        json.dump(cluster_names, file, indent=4)
