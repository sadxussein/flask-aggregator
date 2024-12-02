"""Config file for Flask Aggregator."""

import os

from src.flask_aggregator.back.models import *

class Config:
    """Configuration class for Flask Aggregator app."""

    # Core server configuration.
    SECRET_KEY = (
        os.environ.get("SECRET_KEY") or "some-super-secret-super-safe-key"
    )
    SERVER_IP = "10.105.253.11"
    SERVER_PORT = "6299"
    USERNAME = "scriptbot@internal"
    PASSWORD = "CnfhnjdsqGfhjkm@1234"
    DPC_LIST = [
        "e15-test2", "e15", "e15-2", "e15-3", "n32", "n32-sigma", "n32-2",
        "k45"
    ]
    DPC_URLS = {
        "e15-test2": 
            "https://e15-redvirt-engine-test2.rncb.ru/ovirt-engine/api",
        "e15": "https://e15-redvirt-engine1.rncb.ru/ovirt-engine/api",
        "e15-2": "https://e15-redvirt-engine2.rncb.ru/ovirt-engine/api",
        "e15-3": "https://e15-redvirt-engine3.rncb.ru/ovirt-engine/api",
        "n32": "https://n32-redvirt-engine1.rncb.ru/ovirt-engine/api",
        "n32-2": "https://n32-redvirt-engine2.rncb.ru/ovirt-engine/api",
        "n32-sigma": "https://n32-sigma-engine1.rncb.ru/ovirt-engine/api",
        "k45": "https://k45-redvirt-engine1.rncb.ru/ovirt-engine/api"
    }

    # Working directories.
    ROOT_DIR = "/app"
    LOGS_DIR = f"{ROOT_DIR}/logs"

    # Host ovirtmgmt NIC names.
    HOST_MANAGEMENT_BONDS = [
        "bond0.2701", "bond0.1932", "bond0.2721", "bond0.1567", "bond0.397",
        "bond0.30", "bond0.35", "bond0.2921"
    ]

    # List of storage domains to be avoided in data gathering.
    STORAGE_DOMAIN_EXCEPTIONS = ["ovirt-image-repository"]

    DB_MODELS = {
        "vms": Vm,
        "hosts": Host,
        "clusters": Cluster,
        "storages": Storage,
        "data_centers": DataCenter
    }

class DevelopmentConfig(Config):
    """Development flask app configuration."""
    DEBUG = True
    TESTING = True

class ProductionConfig(Config):
    """Production flask app configuration."""
    DEBUG = False
    TESTING = False

# SERVER_IP = "10.105.253.252"
# SERVER_PORT = "6299"
# USERNAME = "scriptbot@internal"
# PASSWORD = "CnfhnjdsqGfhjkm@1234"
# DPC_LIST = [
#     "e15-test", "e15-test2", "e15", "e15-2", "e15-3", "n32", "n32-sigma",
#     "n32-2", "k45"
# ]
# DPC_URLS = {
#     "e15-test": "https://e15-redvirt-engine-test.rncb.ru/ovirt-engine/api",
#     "e15-test2": "https://e15-redvirt-engine-test2.rncb.ru/ovirt-engine/api",
#     "e15": "https://e15-redvirt-engine1.rncb.ru/ovirt-engine/api",
#     "e15-2": "https://e15-redvirt-engine2.rncb.ru/ovirt-engine/api",
#     "e15-3": "https://e15-redvirt-engine3.rncb.ru/ovirt-engine/api",
#     "n32": "https://n32-redvirt-engine1.rncb.ru/ovirt-engine/api",
#     "n32-2": "https://n32-redvirt-engine2.rncb.ru/ovirt-engine/api",
#     "n32-sigma": "https://n32-sigma-engine1.rncb.ru/ovirt-engine/api",
#     "k45": "https://k45-redvirt-engine1.rncb.ru/ovirt-engine/api"
# }

# HOST_MANAGEMENT_BONDS = [
#     "bond0.2701", "bond0.1932", "bond0.2721", "bond0.1567", "bond0.397",
#     "bond0.30", "bond0.35"
# ]

# # List of storage domains to be avoided in data gathering.
# STORAGE_DOMAIN_EXCEPTIONS = ["ovirt-image-repository"]
