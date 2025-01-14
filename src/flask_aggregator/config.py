"""Config file for Flask Aggregator."""

import os

from flask_aggregator.back.models import (
    Vm, Host, Cluster, DataCenter, Storage, Backups, ElmaVM, BackupsView,
    VmsToBeBackedUpView
)

class Config:
    """Configuration class for Flask Aggregator app."""
    @staticmethod
    def get_env_var(name: str) -> str:
        """Return value of ENV variable.
        
        Args:
            name (str): Name of ENV variable.

        Returns:
            str: ENV variable value.

        Raises:
            EnvironmentError: If ENV variable is not found.
        """
        value = os.getenv(name)
        if value is None:
            raise EnvironmentError(f"ENV variable {name} not found.")
        return value

    @staticmethod
    def get_rv_pass() -> str:
        """RedVirt `scriptbot` user password."""
        return Config.get_env_var("RV_PASS")

    @staticmethod
    def get_db_pass() -> str:
        """Main database password."""
        return Config.get_env_var("DB_PASS")

    @staticmethod
    def get_elma_pass() -> str:
        """Elma API password."""
        return Config.get_env_var("ELMA_PASS")

    @staticmethod
    def get_elma_token() -> str:
        """Elma API token."""
        return Config.get_env_var("ELMA_TOKEN")

    @staticmethod
    def get_cb_db_pass_n32_k45() -> str:
        """Cyberbackup K45 and N32 DB password."""
        return Config.get_env_var("CB_DB_PASS_N32_K45")

    @staticmethod
    def get_cb_db_pass_e15() -> str:
        """Cyberbackup E15 DB password."""
        return Config.get_env_var("CB_DB_PASS_E15")

    @staticmethod
    def validate_env_vars(required_vars: list[str]) -> None:
        """Checking if all ENV variables are present."""
        missing_vars = [v for v in required_vars if os.getenv(v) is None]
        if missing_vars:
            raise EnvironmentError(f"Missing ENV vars: {missing_vars}")

    # Core server configuration.
    # TODO: change to what is above.
    SECRET_KEY = (
        os.environ.get("SECRET_KEY") or "some-super-secret-super-safe-key"
    )
    SERVER_IP = "10.105.253.11"
    SERVER_PORT = "6299"
    USERNAME = "scriptbot@internal"

    ELMA_USER = "RedVirt"

    DPC_LIST = [
        "e15-test2", "e15", "e15-2", "e15-3", "n32",
        "n32-sigma", "n32-2", "k45"
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
    LOGS_DIR = f"{ROOT_DIR}/log"

    # Host ovirtmgmt NIC names.
    HOST_MANAGEMENT_BONDS = [
        "bond0.2701", "bond0.1932", "bond0.2721", "bond0.1567", "bond0.397",
        "bond0.30", "bond0.35", "bond0.2921", "bond0.1197"
    ]

    # List of storage domains to be avoided in data gathering.
    STORAGE_DOMAIN_EXCEPTIONS = ["ovirt-image-repository"]

    DB_MODELS = {
        "vms": Vm,
        "hosts": Host,
        "clusters": Cluster,
        "storages": Storage,
        "data_centers": DataCenter,
        "backups": Backups,
        "elma_vms": ElmaVM,
        "backups_view": BackupsView,
        "vms_to_be_backed_up_view": VmsToBeBackedUpView
    }

    # CB database connection.
    CYBERBACKUP_DPC_LIST = ["e15", "n32", "k45"]
    CYBERBACKUP_DB_ADDRESSES = {
        "e15": "10.105.252.10",
        "n32": "10.105.245.10",
        "k45": "10.105.238.10"
    }
    CYBERBACKUP_DB_PORT = "5432"
    CYBERBACKUP_DB_NAME = "cyberprotect_vault_manager"
    CYBERBACKUP_DB_USER = "cyberbackup"

class DevelopmentConfig(Config):
    """Development flask app configuration."""
    DEBUG = True
    TESTING = True

    DB_USERNAME = "aggregator"
    DB_PASSWORD = Config.get_db_pass()
    DB_NAME = "aggregator_test"
    DB_ADDRESS = "10.105.253.252"
    DB_PORT = "6298"
    DB_URL = (
        f"postgresql+psycopg2://{DB_USERNAME}:{DB_PASSWORD}@{DB_ADDRESS}"
        f":{DB_PORT}/{DB_NAME}"
    )

class ProductionConfig(Config):
    """Production flask app configuration."""
    DEBUG = False
    TESTING = False

    DB_USERNAME = "aggregator"
    DB_PASSWORD = Config.get_db_pass()
    DB_NAME = "aggregator_db"
    DB_ADDRESS = "localhost"
    DB_PORT = "5432"
    DB_URL = (
        f"postgresql+psycopg2://{DB_USERNAME}:{DB_PASSWORD}@{DB_ADDRESS}"
        f":{DB_PORT}/{DB_NAME}"
    )
