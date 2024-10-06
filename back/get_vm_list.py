"""Get VM list from oVirt. Saves resulting VM list as JSON file.

Current field list:
    ID
    name
    hostname
    state    
    IP
    engine
    host
    cluster
    datacenter
    was_migrated

Field list will be extended in the future.
"""

import json
from ovirt_helper import OvirtHelper
import config as cfg

if __name__ == "__main__":
    ovirt_helper = OvirtHelper(cfg.DPC_LIST, cfg.DPC_URLS, cfg.USERNAME, cfg.PASSWORD)
    vm_list = ovirt_helper.get_json_vm_list()
    with open(f"{cfg.BACK_FILES_FOLDER}/vm_list.json", 'w', encoding="utf-8") as file:
        json.dump(vm_list, file, indent=4)
