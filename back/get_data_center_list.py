"""Get data center information.

Current field list:
name
id
engine

Field list will be extended in the future.
"""

import json
from back.ovirt_helper import OvirtHelper
from . import config as cfg

if __name__ == "__main__":
    ovirt_helper = OvirtHelper()
    ovirt_helper.connect_to_engines()
    data_center_list = ovirt_helper.get_data_center_list()
    ovirt_helper.disconnect_from_engines()
    with open(f"{cfg.BACK_FILES_FOLDER}/data_center_list.json", 'w', encoding="utf-8") as file:
        json.dump(data_center_list, file, indent=4)
