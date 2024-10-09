"""Config file for OITI Flask aggregator."""

USERNAME = "scriptbot@internal"
PASSWORD = "CnfhnjdsqGfhjkm@1234"
DPC_LIST = ["e15-test", "e15-test2", "e15", "e15-2", "n32", "n32-2", "k45"]
DPC_URLS = {
    "e15-test": "https://e15-redvirt-engine-test.rncb.ru/ovirt-engine/api",
    "e15-test2": "https://e15-redvirt-engine-test2.rncb.ru/ovirt-engine/api",
    "e15": "https://e15-redvirt-engine1.rncb.ru/ovirt-engine/api",
    "e15-2": "https://e15-redvirt-engine2.rncb.ru/ovirt-engine/api",
    "n32": "https://n32-redvirt-engine1.rncb.ru/ovirt-engine/api",
    "n32-2": "https://n32-redvirt-engine2.rncb.ru/ovirt-engine/api",
    "k45": "https://k45-redvirt-engine1.rncb.ru/ovirt-engine/api"
}
BACK_FILES_FOLDER = "files"
