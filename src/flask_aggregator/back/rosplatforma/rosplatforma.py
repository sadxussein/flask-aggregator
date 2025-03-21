"""Rosplatforma (RP) paramiko-based API."""

import ast
import ipaddress
import json
import os
import xml.etree.ElementTree as ET

import paramiko


def get_structure_from_string(string: str) -> any:
    """Make dict/list from string."""
    result = string.replace("false", "False").replace("true", "True")
    result = ast.literal_eval(result)
    return result


class Command:
    """List of commands, which get data from RP entity."""

    VMS = "prlctl list --info --json --full"
    BACKUPS = "prlctl backup-list"
    HOSTNAME = "hostname"
    SHAMAN = "shaman stat"
    HOSTS = "mysql -X -D VZAgentDB -e 'select name,ip_address from vHosts;'"


class Connection:
    """SSH-based connection."""

    def __init__(
        self,
        ip: str,
        port: int = None,
        username: str = None,
        password: str = None,
    ):
        self.__client = paramiko.SSHClient()
        self.__client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.__ip = ip
        self.__port = 22 if port is None else port
        self.__username = "root" if username is None else username
        self.__password = (
            os.getenv("RP_PASS") if password is None else password
        )

    def __connect(self):
        """Start SSH connection."""
        self.__client.connect(
            self.__ip, self.__port, self.__username, self.__password
        )

    def exec(self, command: Command) -> str:
        """Execute command on remote host.

        Args:
            command (Command): Bash string command.

        Raises:
            RuntimeError: If remote command execution goes wrong.

        Returns:
            str: String, containing result. Could be empty string, if remote
              command has no output in stdout.
        """
        self.__connect()
        _, stdout, stderr = self.__client.exec_command(command)
        data = stdout.read().decode()
        err = stderr.read().decode()
        self.__disconnect()
        if err:
            raise RuntimeError(
                f"Error while executing command {command}: ", stderr
            )
        return data

    def __disconnect(self):
        """Close SSH connection."""
        self.__client.close()


class ClusterManagementContainer:
    """Management va-mn container of RP."""

    def __init__(self, conn: Connection):
        self.__conn = conn
        self.__hosts = []

    def get_cluster_name(
        self,
    ) -> str:  # TODO: get cluster name from va-mn hostname.
        """Get cluster name from va-mn hostname."""

    def get_hosts_name_and_ip(self) -> list[dict[str, any]]:
        """Access va-mn database and get info about names and ips of hosts."""
        stdout = self.__conn.exec(Command.HOSTS)
        if stdout == "":
            raise ValueError("Empty string from stdout.")
        xml_root = ET.fromstring(stdout)
        rows = xml_root.iter("row")
        if rows is None:
            raise ValueError("Could not find 'row' index in result XML.")
        for row in rows:
            host = {}
            host["name"] = row.find("./field[@name='name']").text
            host["ip_address"] = row.find("./field[@name='ip_address']").text
            self.__hosts.append(host)
        return self.__hosts


class VM:
    """VM entity."""

    def __init__(self, config: dict[str, any]):
        self.__parse_config(config)
        # self.__config = config

    def __str__(self):
        return f"{self.__get_dict()}"

    def __eq__(self, other):
        if isinstance(other, VM):
            return self.get() == other.get()
        return False

    def __parse_config(self, config: dict[str, any]):
        """Get class attributes from dictionary."""
        self.__name = config["Name"]
        self.__ips = self.__get_ips(config["Hardware"])
        self.__cpu_count = config["Hardware"]["cpu"]["cpus"]
        self.__memory = self.__get_memory(config["Hardware"])
        self.__total_disk_size = self.__get_total_disk_size(config["Hardware"])
        self.__state = config["State"]

    def __get_memory(self, hardware: dict[str, any]):
        """Get memory in gigabytes."""
        return int(hardware["memory"]["size"][:-2]) / 1024

    def __get_ips(
        self, hardware: dict[str, any]
    ) -> list[ipaddress.IPv4Address]:
        """Make list of ips from string like
        '10.166.11.143/255.255.255.192 10.0.0.100/255.255.255.0'. There is
        a possibility that no ips are set for VM, so empty list is returned.
        """
        result = []
        for k, v in hardware.items():
            if "net" in k:
                ips = v["ips"].split()
                for ip_with_mask in ips:
                    ip = ip_with_mask.split("/")[0]
                    result.append(ipaddress.ip_address(ip))
        return result

    def __get_total_disk_size(self, hardware: dict[str, any]):
        """Total VM disks size in bytes."""
        result = 0
        for k, v in hardware.items():
            if "hdd" in k:
                size = int(v["size"][:-2]) / 1024
                result = result + size
        if result == 0:
            raise ValueError(
                "Total disk size is not calculated. Perhaps something is"
                " wrong with config JSON file."
            )
        return result

    def __get_dict(self):
        return {"name": self.__name, "ip": self.__ips}

    def get(self) -> dict[str, str]:
        """Return VM dict of strings."""
        return {
            "name": self.__name,
            "ips": self.__ips,
            "cpu": self.__cpu_count,
            "memory": self.__memory,
            "size": self.__total_disk_size,
            "state": self.__state,
        }


class Host:
    """Host entity. Base of RP."""

    def __init__(self, name: str, ip: str):
        self.__name = name
        self.__ip = ip
        # In current infrastructure it is implied that port, username and
        # password are the same for va-mn and hosts.
        self.__conn = Connection(ip)
        self.__vms = []

    def __str__(self):
        result = {"name": self.__name, "ip": self.__ip}
        return f"{result}"

    def get_vms(self) -> list[VM]:
        """VM list, present on current host."""
        json_as_string = self.__conn.exec(Command.VMS)
        # If json_as_string is empty it means there are no VMs on a host.
        if json_as_string == "":
            return []
        vms = get_structure_from_string(json_as_string)
        for vm in vms:
            self.__vms.append(VM(vm))
        return self.__vms

    def get_vlan_list(self):  # TODO: to be done
        pass


class Cluster:
    """Abstract cluster entity, since in RP there is no such.

    Here we call cluster a group of hosts, controlled by va-mn container,
    which is running on one of the hosts.
    """

    def __init__(self, cmc: ClusterManagementContainer):
        self.__hosts = []
        self.__vms = []
        # self.__name =     # TODO: add naming for cluster.
        hosts_name_and_ip = cmc.get_hosts_name_and_ip()
        for host in hosts_name_and_ip:
            self.__hosts.append(Host(name=host["name"], ip=host["ip"]))

    def concat_vms_from_hosts(self) -> list[VM]:
        """List of VM entities from cluster."""
        for host in self.__hosts:
            self.__vms = self.__vms + host.get_vms()
        return self.__vms


class VLAN:
    pass
