"""Get VM list from oVirt. Saves resulting VM list as JSON file.

See get_vm_list description.
"""

import json
from back.ovirt_helper import OvirtHelper
from . import config as cfg

if __name__ == "__main__":
    ovirt_helper = OvirtHelper()
    ovirt_helper.connect_to_engines()
    vm_list = ovirt_helper.get_vm_list()
    ovirt_helper.disconnect_from_engines()
    with open(f"{cfg.BACK_FILES_FOLDER}/vm_list.json", 'w', encoding="utf-8") as file:
        json.dump(vm_list, file, indent=4)
