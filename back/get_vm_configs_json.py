"""Generate JSON VM configs."""

import os

from .ovirt_helper import OvirtHelper
from . import config as cfg

if __name__ == "__main__":
    ovirt_helper = OvirtHelper()
    ovirt_helper.connect_to_engines()
    for root, dirs, files in os.walk(f"{cfg.FRONT_FILES_FOLDER}/excel"):
        for file in files:
            print(file)
            ovirt_helper.save_vm_configs_json(os.path.join(root, file))
    ovirt_helper.disconnect_from_engines()
    