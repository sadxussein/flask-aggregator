"""Dedicated testing module for Rosplatforma basic API."""

import unittest
from unittest.mock import MagicMock, patch
import ipaddress

from flask_aggregator.back.rosplatforma.rosplatforma import (
    ClusterManagementContainer, Connection, Host, VM, Cluster)

VM_LIST_AS_JSON_FILE_PATH = "/home/krasnoschekovvd/flask-aggregator/src/flask_aggregator/tests/test-vms.json"
RAW_STRING_VM_CONFIGS = """[
        {
                "ID": "56850624-9fd8-441a-b24f-00131f7f79ca",
                "EnvID": "1451558436",
                "Name": "ts-app-stg-nih-01",
                "Description": "Шаблон РЕД ОС без cloud-init и установленным агентом vz-tools.",
                "Type": "VM",
                "State": "running",
                "OS": "debian",
                "Template": "no",
                "Uptime": "0",
                "Home": "/mnt/vstorage/vols/datastores/Datastore/56850624-9fd8-441a-b24f-00131f7f79ca/",
                "Owner": "root",
                "GuestTools": {
                        "state": "installed",
                        "version": "7.12-9.rv7.1"
                },
                "GuestTools autoupdate": "on",
                "Autostart": "on",
                "Autostop": "stop",
                "Autocompact": "off",
                "Boot order": "cdrom0 hdd0 net0 hdd1 ",
                "EFI boot": "off",
                "Allow select boot device": "off",
                "External boot device": "",
                "On guest crash": "restart",
                "Remote display": {
                        "mode": "auto",
                        "port": 6737,
                        "websocket": 5715,
                        "address": "0.0.0.0"
                },
                "Remote display state": "running",
                "Hardware": {
                        "cpu": {
                                "sockets": 1,
                                "cpus": 8,
                                "cores": 8,
                                "VT-x": true,
                                "hotplug": false,
                                "accl": "high",
                                "mode": "64",
                                "ioprio": 4,
                                "iolimit": "0"
                        },
                        "memory": {
                                "size": "16384Mb",
                                "hotplug": false
                        },
                        "video": {
                                "size": "32Mb",
                                "3d acceleration": "off",
                                "vertical sync": "yes"
                        },
                        "memory_guarantee": {
                                "auto": true
                        },
                        "hdd0": {
                                "enabled": true,
                                "port": "scsi:1",
                                "image": "/mnt/vstorage/vols/datastores/Datastore/56850624-9fd8-441a-b24f-00131f7f79ca/template.qcow2",
                                "type": "expanded",
                                "size": "102400Mb",
                                "subtype": "virtio-scsi",
                                "serial": "2bfc1bd2af7d45769e61"
                        },
                        "hdd1": {
                                "enabled": true,
                                "port": "scsi:0",
                                "image": "/mnt/vstorage/vols/datastores/Datastore/56850624-9fd8-441a-b24f-00131f7f79ca/harddisk1.hdd",
                                "type": "expanded",
                                "size": "204800Mb",
                                "subtype": "virtio-scsi",
                                "serial": "411b907483d6444d9564"
                        },
                        "cdrom0": {
                                "enabled": true,
                                "port": "ide:0",
                                "image": "/mnt/vstorage/vols/datastores/Datastore/import/cloud-init-config.iso"
                        },
                        "usb": {
                                "enabled": true
                        },
                        "net0": {
                                "enabled": true,
                                "dev": "vme001c42e1a819",
                                "network": "1211-vlan",
                                "mac": "001C42E1A819",
                                "card": "virtio",
                                "preventpromisc": "on",
                                "mac_filter": "on",
                                "ip_filter": "on",
                                "nameservers": "10.82.254.32 10.82.254.31",
                                "searchdomains": "crimea.rncb.ru",
                                "ips": "10.166.11.143/255.255.255.192 10.0.0.100/255.255.255.0 ",
                                "gw": "10.166.11.129"
                        }
                },
                "SmartMount": {
                        "enabled": false
                },
                "Disabled Windows logo": "on",
                "Nested virtualization": "off",
                "Offline management": {
                        "enabled": false
                },
                "Hostname": "ts-app-stg-nih-01",
                "High Availability": {
                        "enabled": "yes",
                        "prio": 0
                }
        }
]
"""
ETALON_JSON_VM_CONFIGS = [
    {
        "ID": "56850624-9fd8-441a-b24f-00131f7f79ca",
        "EnvID": "1451558436",
        "Name": "ts-app-stg-nih-01",
        "Description": "Шаблон РЕД ОС без cloud-init и установленным агентом vz-tools.",
        "Type": "VM",
        "State": "running",
        "OS": "debian",
        "Template": "no",
        "Uptime": "0",
        "Home": "/mnt/vstorage/vols/datastores/Datastore/56850624-9fd8-441a-b24f-00131f7f79ca/",
        "Owner": "root",
        "GuestTools": {
            "state": "installed",
            "version": "7.12-9.rv7.1"
        },
        "GuestTools autoupdate": "on",
        "Autostart": "on",
        "Autostop": "stop",
        "Autocompact": "off",
        "Boot order": "cdrom0 hdd0 net0 hdd1 ",
        "EFI boot": "off",
        "Allow select boot device": "off",
        "External boot device": "",
        "On guest crash": "restart",
        "Remote display": {
            "mode": "auto",
            "port": 6737,
            "websocket": 5715,
            "address": "0.0.0.0"
        },
        "Remote display state": "running",
        "Hardware": {
            "cpu": {
                "sockets": 1,
                "cpus": 8,
                "cores": 8,
                "VT-x": True,
                "hotplug": False,
                "accl": "high",
                "mode": "64",
                "ioprio": 4,
                "iolimit": "0"
            },
            "memory": {
                "size": "16384Mb",
                "hotplug": False
            },
            "video": {
                "size": "32Mb",
                "3d acceleration": "off",
                "vertical sync": "yes"
            },
            "memory_guarantee": {
                "auto": True
            },
            "hdd0": {
                "enabled": True,
                "port": "scsi:1",
                "image": "/mnt/vstorage/vols/datastores/Datastore/56850624-9fd8-441a-b24f-00131f7f79ca/template.qcow2",
                "type": "expanded",
                "size": "102400Mb",
                "subtype": "virtio-scsi",
                "serial": "2bfc1bd2af7d45769e61"
            },
            "hdd1": {
                "enabled": True,
                "port": "scsi:0",
                "image": "/mnt/vstorage/vols/datastores/Datastore/56850624-9fd8-441a-b24f-00131f7f79ca/harddisk1.hdd",
                "type": "expanded",
                "size": "204800Mb",
                "subtype": "virtio-scsi",
                "serial": "411b907483d6444d9564"
            },
            "cdrom0": {
                "enabled": True,
                "port": "ide:0",
                "image": "/mnt/vstorage/vols/datastores/Datastore/import/cloud-init-config.iso"
            },
            "usb": {
                "enabled": True
            },
            "net0": {
                "enabled": True,
                "dev": "vme001c42e1a819",
                "network": "1211-vlan",
                "mac": "001C42E1A819",
                "card": "virtio",
                "preventpromisc": "on",
                "mac_filter": "on",
                "ip_filter": "on",
                "nameservers": "10.82.254.32 10.82.254.31",
                "searchdomains": "crimea.rncb.ru",
                "ips": "10.166.11.143/255.255.255.192 10.0.0.100/255.255.255.0 ",
                "gw": "10.166.11.129"
            }
        },
        "SmartMount": {
                "enabled": False
        },
        "Disabled Windows logo": "on",
        "Nested virtualization": "off",
        "Offline management": {
                "enabled": False
        },
        "Hostname": "ts-app-stg-nih-01",
        "High Availability": {
                "enabled": "yes",
                "prio": 0
        }
    }
]
ETALON_VM_CONFIGS = [
    {
        "name": "ts-app-stg-nih-01",
        "ips": [ipaddress.ip_address("10.166.11.143"), ipaddress.ip_address("10.0.0.100")],
        "cpu": 8,
        "memory": 16,
        "size": 300,
        "state": "running",
    }
]

class TestConnection(unittest.TestCase):
    """Connection test case."""

    @patch("paramiko.SSHClient")
    def setUp(self, mock_ssh_client):
        """Mocking paramiko client and making connection."""
        self.mock_ssh_client = mock_ssh_client.return_value
        self.connection = Connection("192.168.1.1", 22, "user", "pass")

    def test_exec_success(self):
        """Testing exec function successful variant."""        

        self.mock_ssh_client.exec_command.return_value = (
            None,
            MagicMock(),
            MagicMock(),
        )
        self.mock_ssh_client.exec_command.return_value[1].read.return_value = (
            b"Success\n"
        )
        self.mock_ssh_client.exec_command.return_value[2].read.return_value = (
            b""
        )

        result = self.connection.exec("ls -la")
        self.assertEqual(result, "Success\n")
        self.mock_ssh_client.connect.assert_called_once()
        self.mock_ssh_client.exec_command.assert_called_once_with("ls -la")
        self.mock_ssh_client.close.assert_called_once()

    def test_exec_failed(self):
        """Testing exec function failed variant."""
        self.mock_ssh_client.exec_command.return_value = (
            None,
            MagicMock(),
            MagicMock(),
        )

        self.mock_ssh_client.exec_command.return_value[1].read.return_value = (
            b""
        )
        self.mock_ssh_client.exec_command.return_value[2].read.return_value = (
            b"Error\n"
        )

        with self.assertRaises(RuntimeError) as context:
            self.connection.exec("cat /var/log/messages")
        self.assertIn("Error while executing command", str(context.exception))
        self.mock_ssh_client.connect.assert_called_once()
        self.mock_ssh_client.close.assert_called_once()


class TestClusterManagementContainer(unittest.TestCase):
    """va-mn management container test case."""
    @patch("flask_aggregator.back.rosplatforma.rosplatforma.Connection")
    def setUp(self, mock_connection):
        """Make mocked Connection class and real CMC class."""
        self.mock_connection = mock_connection.return_value
        self.cmc_client = ClusterManagementContainer(self.mock_connection)

    def test_set_hosts_name_and_ip_correct_xml(self):
        """Success test case."""
        self.mock_connection.exec.return_value = """<?xml version="1.0"?>

<resultset statement="select name,ip_address from vHosts" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<row>
        <field name="name">k45-sigma-04</field>
        <field name="ip_address">10.166.255.124</field>
</row>

<row>
        <field name="name">k45-sigma-06</field>
        <field name="ip_address">10.166.255.126</field>
</row>
</resultset>"""
        result_dict = self.cmc_client.get_hosts_name_and_ip()
        test_dict = [
            {
                "name": "k45-sigma-04",
                "ip_address": "10.166.255.124"
            },
            {
                "name": "k45-sigma-06",
                "ip_address": "10.166.255.126"
            },
        ]
        self.assertEqual(result_dict, test_dict)
        self.mock_connection.exec.assert_called_once()

    def test_set_hosts_name_and_ip_no_row_in_xml(self):
        """Case if no 'row' key is present in result XML."""
        self.mock_connection.exec.return_value = """<?xml version="1.0"?>

<resultset statement="select name,ip_address from vHosts" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<bad_row_key>
        <field name="name">k45-sigma-04</field>
        <field name="ip_address">10.166.255.124</field>
</bad_row_key>

<bad_row_key>
        <field name="name">k45-sigma-06</field>
        <field name="ip_address">10.166.255.126</field>
</bad_row_key>
</resultset>"""
        result_dict = self.cmc_client.get_hosts_name_and_ip()
        test_dict = []
        self.assertEqual(result_dict, test_dict)
        self.mock_connection.exec.assert_called_once()

    def test_set_hosts_name_and_ip_empty_xml(self):
        """Case when XML is empty (empty string from exec)."""
        self.mock_connection.exec.return_value = ""
        with self.assertRaises(ValueError) as context:
            self.cmc_client.get_hosts_name_and_ip()
        self.assertIn("Empty string from stdout.", str(context.exception))
        self.mock_connection.exec.assert_called_once()

class TestCluster(unittest.TestCase):
    """Cluster abstract entity test cases."""
    def setUp(self):
        self.mock_cmc = MagicMock()
        self.mock_cmc.get_hosts_name_and_ip.return_value = [
            {"name": "host_1", "ip": "192.168.1.2"},
            {"name": "host_2", "ip": "192.168.1.3"}
        ]   

    @patch("flask_aggregator.back.rosplatforma.rosplatforma.Host")
    def test_get_vms(self, MockHost):
        """Make sure that list is concatenated properly."""
        mock_host_1 = MagicMock()
        mock_host_2 = MagicMock()
        mock_host_1.get_vms.return_value = [VM(ETALON_JSON_VM_CONFIGS[0]), VM(ETALON_JSON_VM_CONFIGS[0])]
        mock_host_2.get_vms.return_value = [VM(ETALON_JSON_VM_CONFIGS[0])]

        MockHost.side_effect = [mock_host_1, mock_host_2]

        cluster = Cluster(self.mock_cmc)
        expected_result = [VM(ETALON_JSON_VM_CONFIGS[0]), VM(ETALON_JSON_VM_CONFIGS[0]), VM(ETALON_JSON_VM_CONFIGS[0])]
        self.assertEqual(cluster.concat_vms_from_hosts(), expected_result)

class TestHost(unittest.TestCase):
    """Host test cases."""
    @patch("flask_aggregator.back.rosplatforma.rosplatforma.Connection")
    def setUp(self, mock_connection):
        self.mock_connection = mock_connection.return_value
        self.host = Host("rp-host", "192.168.1.1")

    def test_get_vms_success(self):
        """config property and get_vm_list function success variant."""
        self.mock_connection.exec.return_value = RAW_STRING_VM_CONFIGS
        vms = self.host.get_vms()
        self.assertIsInstance(vms, list)
        self.assertTrue(all(isinstance(vm, VM) for vm in vms))
        etalon_configs = ETALON_VM_CONFIGS
        result = [vm.get() for vm in vms]
        self.assertEqual(result, etalon_configs)
        self.mock_connection.exec.assert_called_once()

    def test_get_vms_empty_exec(self):
        """Case if connection exec function returns empty string."""
        self.mock_connection.exec.return_value = ""
        vms = self.host.get_vms()
        self.assertIsInstance(vms, list)
        self.assertEqual(len(vms), 0)
        self.mock_connection.exec.assert_called_once()

    def test_get_vms_bad_exec_return_value(self):
        """Case if exec returns bad JSON from host."""
        self.mock_connection.exec.return_value = """
            [Some text info without parsable logic bracketed as a list.]
        """
        with self.assertRaises(Exception):
            self.host.get_vms()
        self.mock_connection.exec.assert_called_once()

class TestVM(unittest.TestCase):
    """VM class test cases."""
    def setUp(self):
        self.vm = VM(ETALON_JSON_VM_CONFIGS[0])

    def test_parse_config_success(self):
        pass

# class TestCluster(unittest.TestCase):
#     @patch("flask_aggregator.back.rosplatforma.rosplatforma.Host")
#     def setUp(self, mock_host):
#         self.mock_host = mock_host

#     def test_

# if __name__ == "__main__":
#     conn = Connection("10.166.255.10", 22, "root", os.getenv("RP_PASS"))
#     cmc = ClusterManagementContainer(conn)
#     result = cmc.get_hosts_name_and_ip()
#     print(result)
