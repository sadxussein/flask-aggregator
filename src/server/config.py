"""Config file for OITI Flask aggregator."""

import os

class Config:
    """Configuration class for flask app."""
    SECRET_KEY = (
        os.environ.get("SECRET_KEY") or "some-super-secret-super-safe-key"
    )

class DevelopmentConfig(Config):
    """Development flask app configuration."""
    DEBUG = True
    TESTING = True

class ProductionConfig(Config):
    """Production flask app configuration."""
    DEBUG = False
    TESTING = False

SERVER_IP = "10.105.253.252"
SERVER_PORT = "6299"
USERNAME = "scriptbot@internal"
PASSWORD = "CnfhnjdsqGfhjkm@1234"
DPC_LIST = [
    "e15-test", "e15-test2", "e15", "e15-2", "e15-3", "n32", "n32-sigma",
    "n32-2", "k45"
]
DPC_URLS = {
    "e15-test": "https://e15-redvirt-engine-test.rncb.ru/ovirt-engine/api",
    "e15-test2": "https://e15-redvirt-engine-test2.rncb.ru/ovirt-engine/api",
    "e15": "https://e15-redvirt-engine1.rncb.ru/ovirt-engine/api",
    "e15-2": "https://e15-redvirt-engine2.rncb.ru/ovirt-engine/api",
    "e15-3": "https://e15-redvirt-engine3.rncb.ru/ovirt-engine/api",
    "n32": "https://n32-redvirt-engine1.rncb.ru/ovirt-engine/api",
    "n32-2": "https://n32-redvirt-engine2.rncb.ru/ovirt-engine/api",
    "n32-sigma": "https://n32-sigma-engine1.rncb.ru/ovirt-engine/api",
    "k45": "https://k45-redvirt-engine1.rncb.ru/ovirt-engine/api"
}
BACK_FILES_FOLDER = "server/back/files"
SQLITE_FOLDER = f"{BACK_FILES_FOLDER}/sqlite"
LOGS_FOLDER = f"{BACK_FILES_FOLDER}/logs"
VIRT_DATA_FOLDER = f"{BACK_FILES_FOLDER}/virt_data"
JSON_FILES_FOLDER = f"{BACK_FILES_FOLDER}/json"
HOST_MANAGEMENT_BONDS = [
    "bond0.2701", "bond0.1932", "bond0.2721", "bond0.1567", "bond0.397",
    "bond0.30", "bond0.35"
]

# List of storage domains to be avoided in data gathering.
STORAGE_DOMAIN_EXCEPTIONS = ["ovirt-image-repository"]

# VLANs exceptions.
# DBO exceptions.
DBO_VLANS = set([
    918, 919, 922, 923, 924, 925, 926, 927, 928, 929, 930, 931,
    932, 933, 934, 935, 936, 940, 942, 944, 945, 946, 947, 948, 949
])

# Main network n32 exceptions.
N32_VLAN_EXCEPTIONS = set([1505, 1506, 1507, 1508, 1509, 1510])
N32_VLAN_RANGE = set(range(1500, 1699))
N32_NEW_CIRCUIT_VLAN_SET = N32_VLAN_RANGE - N32_VLAN_EXCEPTIONS

OLD_PROCESSING_VLANS = set([60, 65])
