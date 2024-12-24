"""oVirt helper class description."""

__version__ = "0.1"
__author__ = "xussein"

import time
import threading
import json
import re

import ovirtsdk4 as sdk

from flask_aggregator.config import Config
from flask_aggregator.back.virt_protocol import VirtProtocol
from flask_aggregator.back.logger import Logger

class OvirtHelper(VirtProtocol):
    """Class required to perform different actions with oVirt hosted 
    engines."""

    def __init__(self, dpc_list: list=Config.DPC_LIST,
                 urls_list: dict=Config.DPC_URLS,
                 username=Config.USERNAME, password=Config.get_rv_pass(),
                 logger=Logger()
                 ):
        """Construct default class instance."""
        self.__dpc_list = dpc_list
        self.__urls_list = urls_list
        self.__username = username
        self.__password = password
        self.__connections = {}
        self.__logger = logger

    @property
    def pretty_name(self) -> str:
        """Return class' instance pretty name."""
        return "ovirt"

    @property
    def dpc_list(self) -> list:
        """Return class' instance DPC list."""
        return self.__dpc_list

    def connect_to_virtualization(self):
        """Open connections to all engines passed to class instance."""
        for dpc in self.__dpc_list:
            connection = None
            try:
                connection = sdk.Connection(
                    url=self.__urls_list[dpc],
                    username=self.__username,
                    password=self.__password,
                    insecure=True,
                    debug=True
                )
                self.__logger.log_info(
                    f"Connected to {dpc} data processing center.",
                )
                self.__connections[dpc] = connection
            except sdk.ConnectionError as e:
                self.__logger.log_error(
                    (
                        f"Failed to connect to oVirt for DPC {dpc}: {e}. "
                        "Either cannot resolve server name or server is "
                        "unreachable."
                    )
                )
            except sdk.AuthError as e:
                self.__logger.log_error(
                    (
                        f"Failed to authenticate in oVirt Hosted Engine for "
                        f"DPC {dpc}: {e}.",
                    )
                )

    def disconnect_from_virtualization(self):
        """Close connections with all engines.
        
        Closing connections with engines and cleaning up all logger handlers.
        """
        for dpc in self.__dpc_list:
            self.__connections[dpc].close()
            self.__logger.log_info(
                f"Closed connection with {dpc} data processing center.",
            )
        self.__connections = {}

    # TODO: check if necessary. Might be redundant. Could get creation
    # time from vm_service.
    def __get_timestamp(self):
        """Return current time. Primarily used for VMs."""
        return time.strftime("%Y.%d.%m-%H:%M:%S", time.localtime(time.time()))

    def __rename_thread(self):
        """Change name of thread while executing function.
        
        Any function in class is usually run in a thread named creator_N or
        collector_N. We need to add DPC of current class to it to be more
        representable in the log.
        """
        thread_name = threading.current_thread().name.split('_')
        threading.current_thread().name = (
            f"_{'^'.join(self.__dpc_list)}_".join(thread_name)
        )

    def get_data_centers(self):
        """Get data center information from all engines.
        
        Returns:
            data center list (dict): List of following parameters:
            'uuid', 'name', 'engine', 'comment', 'href', 'virtualization'.

        Field 'comment' is quite important for selecting proper template
        for VM. The currenct list of comments is: 'K8S', 'PRC' (processing), 
        'PRC_OLD' (old network processing), 'MON' (monitoring), 'NGX' (front
        nginx), 'ARM' (or VDI), 'SPK_01' and 'SPK_02' (splunk). These values
        define which template to choose, as each corresponding template ends
        with this tag in its name, e.g. 'template_PRC_OLD'.
        """
        self.__rename_thread()
        result = []
        for dpc, connection in self.__connections.items():
            self.__logger.log_info(f"Getting data centers from {dpc}.")
            for data_center in (
                connection.system_service().data_centers_service().list()
            ):
                result.append({
                    "uuid": data_center.id,
                    "name": data_center.name,
                    "engine": dpc,
                    "comment": data_center.comment,
                    "href": (
                        f"{Config.DPC_URLS[dpc][:-3]}webadmin/?locale=en_US#"
                        f"dataCenters-storage;name={data_center.name}"
                    ),
                    "virtualization": self.pretty_name
                })
            self.__logger.log_info(
                f"Finished collecting data centers from {dpc}."
            )
        return result

    def get_storages(self):
        """Get storage domain information from all engines.

        Returns:
            storage domain list (dict): List of following parameters:
            'uuid', 'name', 'engine', 'data_center', 'available', 'used', 
            'committed', 'total', 'percent_left', 'overprovisioning',
            'href', 'virtualization'.
        """
        self.__rename_thread()
        result = []
        for dpc, connection in self.__connections.items():
            self.__logger.log_info(f"Getting storage domains from {dpc}.")
            system_service = connection.system_service()
            data_centers_service = system_service.data_centers_service()
            storage_domains_service = system_service.storage_domains_service()
            for domain in storage_domains_service.list():
                if domain.name not in Config.STORAGE_DOMAIN_EXCEPTIONS:
                    data_centers = set()
                    try:
                        for dc in domain.data_centers:
                            data_center = (
                                data_centers_service
                                .data_center_service(dc.id)
                                .get()
                            )
                            data_centers.add(data_center.name)
                        result.append({
                            "uuid": domain.id,
                            "name": domain.name,
                            "engine": dpc,
                            "data_center": ' '.join(data_centers),
                            "available": domain.available,
                            "used": domain.used,
                            "committed": domain.committed,
                            "total": domain.available + domain.used,
                            "percent_left": 100 - int(((100 * domain.used) 
                                            / (domain.available + domain.used))),
                            "overprovisioning": int((domain.committed * 100)
                                                    / (domain.available
                                                    + domain.used)),
                            "href": (
                                f"{Config.DPC_URLS[dpc][:-3]}"
                                "webadmin/?locale=en_US#"
                                f"storage-general;name={domain.name}"
                            ),
                            "virtualization": self.pretty_name
                        })
                    except TypeError as e:
                        self.__logger.log_error(e)
                        data_centers.add('-')
            self.__logger.log_info(
                f"Finished collecting storage domains from {dpc}."
            )
        return result

    def get_clusters(self):
        """Get cluster ID and name list.
    
        Returns:
            cluster list (dict): List of following parameters:
            'uuid', 'name', 'engine', 'description', 'data_center', 'href',
            'virtualization'.
        """
        self.__rename_thread()
        result = []
        for dpc, connection in self.__connections.items():
            self.__logger.log_info(f"Getting clusters from {dpc}.")
            system_service = connection.system_service()
            data_centers_service = system_service.data_centers_service()
            clusters_service = system_service.clusters_service()
            clusters = clusters_service.list()
            for cluster in clusters:
                try:
                    data_center = data_centers_service.data_center_service(
                        cluster.data_center.id
                    ).get()
                    result.append(
                        {
                            "name": cluster.name, "uuid": cluster.id,
                            "engine": dpc, "description": cluster.description,
                            "data_center": data_center.name,
                            "href": (
                                f"{Config.DPC_URLS[dpc][:-3]}webadmin/"
                                "?locale=en_US#"
                                f"clusters-general;name={cluster.name}"
                            ),
                            "virtualization": self.pretty_name
                        }
                    )
                except sdk.Error as e:
                    self.__logger.debug(
                        f"Exception while working with DPC {dpc}: {e}."
                    )
            self.__logger.log_info(f"Finished collecting clusters from {dpc}.")
        return result

    def get_hosts(self) -> list:
        """Get host ID, name, cluster and IP list.
        
        Returns:
            host list (dict): List of following parameters:
            'uuid', 'name', 'cluster', 'IP', 'engine', 'href'.
        """
        self.__rename_thread()
        result = []
        for dpc, connection in self.__connections.items():
            self.__logger.log_info(f"Getting hosts from {dpc}.")
            system_service = connection.system_service()
            hosts_service = system_service.hosts_service()
            hosts = hosts_service.list()
            clusters_service = system_service.clusters_service()
            data_centers_service = system_service.data_centers_service()
            for host in hosts:
                cluster = clusters_service.cluster_service(
                    host.cluster.id
                ).get()
                data_center = data_centers_service.data_center_service(
                    cluster.data_center.id
                ).get()
                host_service = hosts_service.host_service(host.id)
                nics_service = host_service.nics_service()
                nics = nics_service.list()
                ip = None
                for nic in nics:
                    if nic.name in Config.HOST_MANAGEMENT_BONDS:
                        if nic.ip and nic.ip.address:
                            ip = nic.ip.address
                result.append(
                    {
                        "uuid": host.id,
                        "name": host.name, 
                        "cluster": cluster.name,
                        "status": f"{host.status}",
                        "data_center": data_center.name,
                        "ip": ip,
                        "engine": dpc,
                        "href": (
                            f"{Config.DPC_URLS[dpc][:-3]}"
                            "webadmin/?locale=en_US#"
                            f"hosts-general;name={host.name}"
                        ),
                        "virtualization": self.pretty_name
                    }
                )
            self.__logger.log_info(f"Finished collecting hosts from {dpc}.")
        return result

    def get_vms(self) -> list:
        """Get VM list as dictionary.
        
        Returns:
            VM list (dict): List of following parameters:
            'uuid', 'name', 'hostname', 'state', 'IP', 'engine', 'host',
            'cluster', 'data_center', 'was_migrated', 'total_space',
            'storage_domains', 'href', 'virtualization'.

        Function connects to every oVirt engine passed to class instance file
        and returns data from all VMs as dictionary.
        Field list will be extended in the future.
        """
        self.__rename_thread()
        result = []

        for dpc, connection in self.__connections.items():
            self.__logger.log_info(f"Getting VMs from {dpc}.")
            # Main service
            system_service = connection.system_service()

            # Get VM list and specific data
            vms_service = system_service.vms_service()
            vms = vms_service.list()
            for vm in vms:
                # Getting VM service.
                vm_service = vms_service.vm_service(vm.id)

                vm_data = {}

                # Getting VM fields described in module docstring.
                # ID
                vm_data["uuid"] = vm.id

                # name
                vm_data["name"] = vm.name

                # hostname
                vm_data["hostname"] = vm.fqdn

                # state
                if vm.status == sdk.types.VmStatus.DOWN:
                    vm_data["state"] = "Down"
                elif vm.status == sdk.types.VmStatus.UP:
                    vm_data["state"] = "Up"
                else:
                    vm_data["state"] = "Other"

                # IP
                vm_data["ip"] = ''
                for device in vm_service.reported_devices_service().list():
                    if device.ips:
                        for ip in device.ips:
                            if ip.version == sdk.types.IpVersion.V4:
                                vm_data["ip"] = ip.address

                # engine
                vm_data["engine"] = dpc

                # host
                # Get VM host service to get its name
                hosts_service = system_service.hosts_service()
                # Checking if host is None, because we need only running VMs
                # (ones that are assigned to a host).
                if vm.host is not None:
                    host_service = hosts_service.host_service(vm.host.id)
                    host = host_service.get()
                    vm_data["host"] = host.name
                else:
                    vm_data["host"] = ''

                # cluster
                clusters_service = system_service.clusters_service()
                cluster_service = clusters_service.cluster_service(
                    vm.cluster.id
                )
                cluster = cluster_service.get()
                vm_data["cluster"] = cluster.name

                # datacenter
                data_centers_service = system_service.data_centers_service()
                data_center_service = data_centers_service.data_center_service(
                    cluster.data_center.id
                )
                data_center = data_center_service.get()
                vm_data["data_center"] = data_center.name

                # was_migrated
                if "Migrated by IntelSource" in vm.description:
                    vm_data["was_migrated"] = True
                else:
                    vm_data["was_migrated"] = False

                # Calculating VM total disks usage and storage domains.
                vm_data["total_space"] = 0
                vm_data["storage_domains"] = set()
                disc_attachments = vm_service.disk_attachments_service().list()
                if disc_attachments:
                    for disk_attachment in disc_attachments:
                        disk = system_service.disks_service().disk_service(
                            disk_attachment.disk.id
                        ).get()
                        if disk:    # TODO: check questionable logic below.
                            try:
                                vm_data["total_space"] = (
                                    vm_data["total_space"]
                                    + disk.total_size / 1024 ** 3
                                )
                            except TypeError as e:
                                self.__logger.log_error(f"{disk.id}: {e}.")
                            try:
                                for sd in disk.storage_domains:
                                    storage_domain = (
                                        system_service
                                        .storage_domains_service()
                                        .storage_domain_service(sd.id).get()
                                    )
                                    vm_data["storage_domains"].add(
                                        storage_domain.name
                                    )
                            except FileNotFoundError as e:
                                self.__logger.log_error(e)
                            except TypeError as e:
                                self.__logger.log_error(
                                    f"Error with disk of VM {vm.name}: {e}"
                                )
                vm_data["storage_domains"] = '\n'.join(
                    vm_data["storage_domains"]
                )

                vm_data["href"] = (
                    f"{Config.DPC_URLS[dpc][:-3]}webadmin/?locale=en_US#"
                    f"vms-general;name={vm.name}"
                )

                vm_data["virtualization"] = self.pretty_name

                result.append(vm_data)
            self.__logger.log_info(f"Finished collecting VMs from {dpc}.")
        return result

    def create_vm(self, config):
        """Create VM in target oVirt engine.
        
        Takes dictionary as argument, which must contain vm configuration. 
        Example:
            ```
            [
                {
                    "meta": {
                        "document_num": "6666",
                        "inf_system": "Ред Виртуализация",
                        "owner": "ОИТИ",
                        "environment": "Тест"
                    },
                    "ovirt": {
                        "engine": "e15-test",
                        "data_center": "e15-Datacenter",
                        "cluster": "Default",
                        "storage_domain": "hosted_storage",
                        "host_nic": "bond0"
                    },
                    "vm": {
                        "name": "test_vm_11",
                        "hostname": "test_vm_11",
                        "cores": 2,
                        "memory": 2,
                        "disks": [
                            {
                                "size": 40,
                                "type": 1,
                                "mount_point": "/",
                                "sparse": 0     # where 0 is false, 1 is true
                            }
                        ],
                        "template": "template-packer-redos8-03092024",
                        "os": "RedOS 8",
                        "nic_name": "enp1s0",
                        "gateway": "10.105.249.1",
                        "netmask": "255.255.255.192",
                        "address": "10.105.249.51",
                        "dns_servers": "10.82.254.32 10.82.254.31",
                        "search_domain": "crimea.rncb.ru"
                    },
                    "vlan": {
                        "name": "2921-redvt-eqp-test-e15",
                        "id": 2921,
                        "suffix": ""
                    }
                }
            ]
            ```
        Returns VM data as dict from oVirt if success, -1 otherwise.
        """
        self.__rename_thread()

        # Try find VM with current VM name. If VM exists create corresponding
        # log entry and close function.
        system_service = self.__connections[
            config["ovirt"]["engine"]
        ].system_service()
        vms_service = system_service.vms_service()

        # Creating VM
        vm = sdk.types.Vm(
            name=config["vm"]["name"],
            cluster=sdk.types.Cluster(
                name=config["ovirt"]["cluster"]
            ),
            comment=(
                f"{config['meta']['environment']}, "
                f"{config['meta']['inf_system']}"
            ),
            description=(
                f"Time created: {self.__get_timestamp()},"
                f" Owner: {config['meta']['owner']}, "
                f"ELMA_task_number: {config['meta']['document_num']}"
            ),
            template=sdk.types.Template(
                name=config["vm"]["template"]
            ),
            memory=config["vm"]["memory"] * 2**30,
            memory_policy=sdk.types.MemoryPolicy(
                max=config["vm"]["memory"] * 2**30,
                guaranteed=config["vm"]["memory"] * 2**30
            ),
            cpu=sdk.types.Cpu(
                topology=sdk.types.CpuTopology(
                    # Set CPU topology. If in ELMA document there is > 10
                    # cores, split them between no more than 2 sockets.
                    cores=(
                        int(config["vm"]["cores"])
                        if int(config["vm"]["cores"]) <= 10
                        else int(config["vm"]["cores"] / 2)
                    ),
                    sockets=1 if config["vm"]["cores"] <= 10 else 2
                )
            ),
            initialization=sdk.types.Initialization(
                host_name=config["vm"]["hostname"],
                nic_configurations=[
                    sdk.types.NicConfiguration(
                        name=config["vm"]["nic_name"],
                        boot_protocol=sdk.types.BootProtocol.STATIC,
                        on_boot=True,
                        ip=sdk.types.Ip(
                            version=sdk.types.IpVersion.V4,
                            address=config["vm"]["address"],
                            netmask=config["vm"]["netmask"],
                            gateway=config["vm"]["gateway"],
                        )
                    )
                ],
                dns_servers=(
                    config["vm"]["dns_servers"]
                    if "dns_servers" in config
                    else "10.82.254.32 10.82.254.31"
                ),
                dns_search=(
                    config["vm"]["search_domain"]
                    if "search_domain" in config["vm"]
                    else None
                )
            )
        )
        try:
            vm = vms_service.add(vm, clone=True)
            self.__logger.log_info(f"Creating VM {vm.name}.")

            # After creating VM we have to shut it down to apply new hardware
            # and software options.
            vm_service = vms_service.vm_service(vm.id)
            while vm_service.get().status != sdk.types.VmStatus.DOWN:
                self.__logger.log_debug(
                    "Waiting for VM status set to DOWN "
                    "(ready for next setup)..."
                )
                time.sleep(10)
            self.__logger.log_info(f"Created VM {vm.name}.")

            # Disks operations.
            self.__extend_vm_root_disk(system_service, vm, vm_service, config)
            self.__create_vm_extra_disks(
                system_service, vm, vm_service, config
            )

            # Network operations.
            self.__set_vm_network(system_service, vm_service, config)

            # After applying changes VM will be locked, so wait until lockdown
            # is released.
            while vm_service.get().status != sdk.types.VmStatus.DOWN:
                self.__logger.log_debug(
                    "Waiting system service to release VM's LOCKED status..."
                )
                time.sleep(10)

            # Starting VM via CloudInit.
            vm_service.start()

            # Restrating VM to fix fstab.
            while vm_service.get().status != sdk.types.VmStatus.UP:
                self.__logger.log_debug("Waiting VM to start...")
                time.sleep(10)
            # Waiting 60 second for VM to properly start.
            time.sleep(60)
            self.__logger.log_info(
                "Issued VM reset to fix possible fstab malfunction."
            )
            vm_service.reset()

            # Finalizing VM.
            while vm_service.get().status != sdk.types.VmStatus.UP:
                self.__logger.log_debug("Waiting VM to start...")
                time.sleep(10)
            self.__logger.log_info(
                f"VM {vm.name} in dpc {config['ovirt']['engine']} created "
                "and operational."
            )

            return {
                "id": vm.id, 
                "name": vm.name, 
                "engine": config["ovirt"]["engine"]
            } if vm else -1

        except sdk.Error as e:
            self.__logger.log_error(
                f"Could not create VM {config['vm']['name']}. Reason: {e}."
            )

    def __extend_vm_root_disk(self, system_service, vm, vm_service, config):
        """Extend VM root disk size to one set in config dict."""
        # Extending root disk to a number set in disk list on vm_config.
        disk_attachments_service = vm_service.disk_attachments_service()
        disk_attachments = disk_attachments_service.list()

        # If any disk exist, and there will be only one in the template.
        self.__logger.log_info("Resizing disk from template if it is > 30Gb.")
        if disk_attachments:
            disk_attachment = disk_attachments[0]
            disk_service = system_service.disks_service().disk_service(
                disk_attachment.disk.id
            )

            # Waiting for disk to be created
            while disk_service.get().status == sdk.types.DiskStatus.LOCKED:
                self.__logger.log_debug(
                    "Waiting system service to release disks LOCKED status..."
                )
                time.sleep(10)
            for disk_config in config["vm"]["disks"]:
                if int(disk_config["type"]) == 1 and disk_config['size'] > 30:
                    self.__logger.log_debug(
                        (
                            "Root disk size from vm config is "
                            f"{disk_config['size']} which is larger "
                            "than 30 gb."
                        )
                    )
                    disk_service.update(
                        disk=sdk.types.Disk(
                            # Disk with root partition should always be
                            # first in the list.
                            provisioned_size=disk_config["size"] * 2**30,
                            bootable=True
                        )
                    )

                    # Waiting to apply disk changes.
                    while (
                        disk_service.get().status == sdk.types.DiskStatus.LOCKED
                    ):
                        self.__logger.log_debug(
                            "Waiting system service to release disks LOCKED status..."
                        )
                        time.sleep(10)

                    # Setting disk name and label.
                    disk_service.update(
                        disk=sdk.types.Disk(
                            name=f"{vm.name}-root-disk-1",
                            logical_name="sda"
                        )
                    )

                    # Waiting to apply disk changes.
                    while disk_service.get().status == sdk.types.DiskStatus.LOCKED:
                        self.__logger.log_debug(
                            ("Waiting system service to release disks LOCKED"
                             " status...")
                        )
                        time.sleep(10)
                    self.__logger.log_info(
                        f"Disk with root partition extended for VM {vm.name},"
                        f" with ID {vm.id}."
                    )

    def __create_vm_extra_disks(self, system_service, vm, vm_service, config):
        """Create additional disks for VM, as stated in VM config dict."""
        disk_attachments_service = vm_service.disk_attachments_service()
        # Adding disks, if corresponding disk list on vm_config has more than
        # one element.
        if len(config["vm"]["disks"]) > 1:
            disk_index = 1
            for disk in config["vm"]["disks"]:
                if int(disk["type"]) != 1:

                    # Creating disk. Disk must be under 8gb, otherwise oVirt
                    # throws exception.
                    if disk["size"] > 8192:
                        disk["size"] = 8192
                    self.__logger.log_info(
                        f"Creating additional disks #{disk_index} for VM "
                        f"{vm.name}, with ID {vm.id}. Disk size: "
                        f"{disk['size']}Gb."
                    )
                    disk_index += 1

                    # Attaching disk to VM.
                    disk_attachment = disk_attachments_service.add(
                        sdk.types.DiskAttachment(
                            disk=sdk.types.Disk(
                                name=f"{vm.name}-data-disk-{disk_index}",
                                description=(
                                    f"Additional disk #{disk_index}"
                                    f"for {vm.name}"
                                ),
                                format=(
                                    sdk.types.DiskFormat.COW
                                    if bool(disk["sparse"])
                                    else sdk.types.DiskFormat.RAW
                                ),
                                provisioned_size=disk["size"] * 2**30,
                                storage_domains=[
                                    sdk.types.StorageDomain(
                                        name=config["ovirt"]["storage_domain"]
                                    )
                                ],
                                sparse=bool(disk["sparse"])
                            ),
                            bootable=False,
                            active=True,
                            interface=sdk.types.DiskInterface.VIRTIO_SCSI,
                        )
                    )
                    self.__logger.log_debug(
                        "Created disk_attachment variable "
                        f"(disk #{disk_index})"
                    )
                    disk_service = system_service.disks_service().disk_service(
                        disk_attachment.disk.id
                    )
                    self.__logger.log_debug(
                        f"Found disk_attachment service (disk #{disk_index})"
                    )

                    # Waiting to apply disk changes
                    while disk_service.get().status == sdk.types.DiskStatus.LOCKED:
                        self.__logger.log_debug(
                            "Waiting system service to release disks LOCKED"
                            " status..."
                        )
                        time.sleep(10)

                    if disk_attachment:
                        self.__logger.log_info(
                            f"Created additional disk for VM {vm.name}, with "
                            "ID {vm.id}."
                        )
                    else:
                        self.__logger.log_error(
                            "Failed to create disk with root partition for VM"
                            f" {vm.name}, with ID {vm.id}."
                        )

    def __set_vm_network(self, system_service, vm_service, config):
        """Change VM vNIC (VLAN)."""
        self.__logger.log_info(
            f"Changing VM vNIC to {config['vlan']['name']}. Searching vNIC "
            "profile."            
        )
        vnic_profile_id = self.__get_vnic_profile(system_service, config)
        if vnic_profile_id:
            nics_service = vm_service.nics_service()
            nics = nics_service.list()
            # Applying vNIC profiles for main nic1 on VM
            for nic in nics:
                # All templates will have NIC names 'nic1' as a primary
                # connection.
                if nic.name == 'nic1':
                    nic_service = nics_service.nic_service(nic.id)
                    nic_service.update(
                        sdk.types.Nic(
                            vnic_profile=sdk.types.VnicProfile(
                                id=vnic_profile_id
                            )
                        )
                    )
        else:
            self.__logger.log_error(
                f"No vNIC with VLAN ID {config['vlan']['id']} found!"
            )

    def __get_vnic_profile(self, system_service, config):
        """Return vNIC profile ID if exists, -1 otherwise.
        
        In order to determine if VLAN exists in current data center it is
        necessary to find corresponding network by vNIC profile.
        If VLAN exists - return its ID.
        If VLAN doesn't exist - return -1.
        """
        vnic_profiles_service = system_service.vnic_profiles_service()
        networks_service = system_service.networks_service()
        vnic_profile_id = None
        for profile in vnic_profiles_service.list():
            if profile and profile.network.id:
                network = networks_service.network_service(
                    profile.network.id
                ).get()
                data_center_id = self.__get_data_center(system_service, config)
                if (network
                    and network.vlan.id == config["vlan"]["id"]
                    and data_center_id
                    and network.data_center.id == data_center_id):
                    vnic_profile_id = profile.id
                    break
        return vnic_profile_id

    def __get_data_center(self, system_service, config):
        """Return data center ID if cluster set in config exists.

        `None` otherwise.
        """
        data_center_id = None
        clusters_service = system_service.clusters_service()
        for cluster in clusters_service.list():
            if cluster.name == config["ovirt"]["cluster"]:
                data_centers_service = system_service.data_centers_service()
                data_center = (
                    data_centers_service
                    .data_center_service(cluster.data_center.id)
                    .get()
                )
                data_center_id = data_center.id
        return data_center_id

    def create_vlan(self, config):
        # TODO: change checking if VLAN exists logic
        """Create VLAN.
        
        Example JSON, required by functions should be as following:
            ```
                [
                    {
                        "meta": {
                            "document_num": "6666",
                            "inf_system": "Ред Виртуализация",
                            "owner": "ОИТИ",
                            "environment": "Тест"
                        },
                        "ovirt": {
                            "engine": "e15-test",
                            "cluster": "Default",
                            "storage_domain": "hosted_storage",
                            "host_nic": "bond0"
                        },
                        "vlan": {
                            "name": "2921-redvt-eqp-test-e15",
                            "id": 2921,
                            "suffix": ""
                        }
                    }
                ]
            ```
        """
        self.__rename_thread()

        system_service = self.__connections[
            config['ovirt']['engine']
        ].system_service()

        self.remove_unmanaged_vlan()

        # Getting data center service. Also getting cluster service and full
        # list of clusters.
        dcs_service = system_service.data_centers_service()
        clusters_service = system_service.clusters_service()
        clusters = clusters_service.list()

        # Defining where to put VLAN, based on cluster in prepared/raw VLAN
        # JSON config.
        target_dc = None
        target_cluster = None
        self.__logger.log_info(
            "Checking if there is target cluster and data center."
        )
        for cluster in clusters:
            if cluster.name == config["ovirt"]["cluster"]:
                target_cluster = cluster
                target_dc = dcs_service.data_center_service(
                    cluster.data_center.id
                ).get()
                break

        # Getting target data center's network service. Getting list of all
        # networks in DC to check if vlans already exist.
        self.__logger.log_info(
            f"Checking if VLAN {config['vlan']['name']} with ID "
            f"{config['vlan']['id']} exists in current data center."
        )
        dc_network_service = dcs_service.service(
            target_dc.id
        ).networks_service()
        dc_networks = dc_network_service.list()
        current_vlan_exists = False
        for dc_network in dc_networks:
            if dc_network.vlan and dc_network.vlan.id == config["vlan"]["id"]:
                current_vlan_exists = True
                vlan = dc_network
                self.__logger.log_error(
                    f"Network {config['vlan']['name']} already exists in "
                    f"{target_dc.name} datacenter!"
                )
                break

        # Creating VLAN.
        if not current_vlan_exists:
            vlan = dc_network_service.add(
                sdk.types.Network(
                    name=
                        f"{config['vlan']['id']}{config['vlan']['suffix']}"
                        "-vlan",
                    data_center=sdk.types.DataCenter(
                        id=target_dc.id
                    ),
                    comment=config["vlan"]["name"],
                    description=config["vlan"]["name"],
                    vlan=sdk.types.Vlan(
                        id=config["vlan"]["id"]
                    ),
                    usages=[sdk.types.NetworkUsage.VM],
                    required=False
                )
            )

        # Adding VLAN via cluster, to populate it across all hosts
        cluster_networks_service = clusters_service.cluster_service(
            target_cluster.id
        ).networks_service()
        cluster_networks = cluster_networks_service.list()
        current_vlan_exists = False
        for cluster_network in cluster_networks:
            if cluster_network.vlan.id == config["vlan"]["id"]:
                current_vlan_exists = True
                self.__logger.log_error(
                    f"Network {config['vlan']['name']} already exists in "
                    f"{target_cluster.name} cluster!"
                )

        if not current_vlan_exists:
            cluster_networks_service.add(
                sdk.types.Network(
                    id=vlan.id,
                    required=False
                )
            )

        # Getting list of all hosts to perform check to define if vlan is
        # already attached to host.
        hosts_service = system_service.hosts_service()
        hosts = hosts_service.list()
        for host in hosts:

            # Checking host <-> cluster.
            host_cluster = self.__connections[
                config['ovirt']['engine']
            ].follow_link(host.cluster)
            if host_cluster.name == config["ovirt"]["cluster"]:
                self.__logger.log_info(
                    f"Attaching VLAN to host {host.name}."
                )
                host_service = hosts_service.host_service(host.id)

                # Specific host nics service.
                nics_service = host_service.nics_service()
                nics = nics_service.list()
                current_vlan_exists = False
                for nic in nics:
                    if nic.name == config["ovirt"]["host_nic"]:
                        if not current_vlan_exists:
                            host_service.setup_networks(
                                modified_bonds=[],
                                modified_network_attachments=[
                                    sdk.types.NetworkAttachment(
                                        network=sdk.types.Network(id=vlan.id),
                                        host_nic=sdk.types.HostNic(id=nic.id)
                                    )
                                ]
                            )

        self.__logger.log_info(
            f"Network {config['vlan']['name']} created and attached to all "
            "hosts."
        )

    def remove_unmanaged_vlan(self, vlan_list: list=None) -> dict:
        """Usually after removing VLAN from oVirt, it remains attached to
        hosts and they refuse to attach new ones while 'unmanaged' ones remain
        attached.
        """
        # If no VLANs to remove are specified - remove all unmanaged ones.
        if not vlan_list:
            self.__logger.log_info(
                "No VLAN list specified. Cleaning all unmanaged VLANs."
                )
            for dpc, connection in self.__connections.items():
                hosts_service = connection.system_service().hosts_service()
                for host in hosts_service.list():
                    unmng_netwks_service = hosts_service.host_service(
                        host.id
                    ).unmanaged_networks_service()
                    for network in unmng_netwks_service.list():
                        netw_service = (
                            unmng_netwks_service
                            .unmanaged_network_service(network.id)
                        )
                        try:
                            netw_service.remove()
                        except sdk.NotFoundError as e:
                            self.__logger.log_error(
                                f"Exception while working with VLAN "
                                f"{network.name}: {e}."
                            )
                        else:
                            self.__logger.log_info(
                                f"Removed unmanaged VLAN {network.name} from"
                                f" {dpc} DPC."
                            )

        return {"response": 200, "vlan_list": vlan_list}

    def set_vm_ha(self, vm_filter: dict=None) -> dict:
        """Enable VM high availability parameter.
        
        Args:
            filter (dict): By this filter VMs will be selected for HA
                enabling. Key list in the description below. Example:
                ```
                {
                    "vm_names": [],
                    "vm_ids": [],
                    "vm_env": ''
                }
                ```

        Returns:
            dict: Function reply with success/fail description.

        If at least one of `vm_names`/`vm_ids` arguments (list) are set, only
        particular VMs will be set to HA. If no VMs found error will be
        returned in dict.
        
        If `vm_env` is set, only a certain group of VMs will be set to HA.
        Viable `vm_env` parameters are 'test' and 'prod' (so far).

        If no parameters are set, exception will be thrown and nothing will be
        done.
        """
        result = []
        if "vm_names" in vm_filter and vm_filter["vm_names"] is not None:
            for dpc, connection in self.__connections.items():
                system_service = connection.system_service()
                vms = system_service.vms_service().list()
                vms = (vm for vm in vms if vm.name in vm_filter["vm_names"])
                if vms is None:
                    self.__logger.log_error(
                        f"No VMs with names {vm_filter['vm_name']} have been "
                        f"found in {dpc} engine."
                    )
                    raise ValueError(
                        f"No VMs with names {vm_filter['vm_name']} have been "
                        f"found in {dpc} engine."
                    )
                else:
                    for vm in vms:
                        result.append(
                            self.__set_vm_ha_parameter(system_service, vm)
                        )
        elif "vm_ids" in vm_filter and vm_filter["vm_ids"] is not None:
            for dpc, connection in self.__connections.items():
                system_service = connection.system_service()
                vms = system_service.vms_service().list()
                vms = (vm for vm in vms if vm.id in vm_filter["vm_ids"])
                if vms is None:
                    self.__logger.log_error(
                        f"No VMs with ids {vm_filter['vm_ids']} have been "
                        f"found in {dpc} engine."
                    )
                    raise ValueError(
                        f"No VMs with ids {vm_filter['vm_ids']} have been "
                        f"found in {dpc} engine."
                    )
                else:
                    for vm in vms:
                        result.append(
                            self.__set_vm_ha_parameter(system_service, vm)
                        )
        elif "vm_env" in vm_filter and vm_filter["vm_env"] is not None:
            for dpc, connection in self.__connections.items():
                system_service = connection.system_service()
                vms = system_service.vms_service().list()
                vms = (vm for vm in vms if vm_filter["vm_env"] in vm.comment)
                if vms is None:
                    self.__logger.log_error(
                        f"No VMs with environment {vm_filter['vm_env']} have "
                        f"been found in {dpc} engine."
                    )
                    raise ValueError(
                        f"No VMs with environment {vm_filter['vm_env']} have "
                        f"been found in {dpc} engine."
                    )
                else:
                    for vm in vms:
                        result.append(
                            self.__set_vm_ha_parameter(system_service, vm)
                        )
        else:
            raise KeyError(
                "Bad filter. No valid parameters specified. Valid parameters:"
                " 'vm_name', 'vm_id', 'vm_env'"
            )
        return result

    def __set_vm_ha_parameter(
        self, ss: sdk.services.SystemService, vm: sdk.types.Vm
    ) -> dict:
        """Set HA parameter for concrete VM.
        
        Args:
            ss (ovirtsdk4.services.SystemService): Connection's service.
            vm (ovirtsdk4.types.Vm): VM entity.

        Returns:
            dict: Resulting message. Could be error or success key.
        """
        result = {}
        vm_service = ss.vms_service().vm_service(vm.id)
        disk_att_service = vm_service.disk_attachments_service()
        disk_attachments = disk_att_service.list()
        # Disk storage domain.
        disk_sd = None
        if disk_attachments:
            for disk_attachment in disk_attachments:
                disk = ss.disks_service().disk_service(
                    disk_attachment.disk.id
                ).get()
                if disk_attachment.bootable:
                    disk_sd = disk.storage_domains[0]
        if disk_sd is not None:
            self.__logger.log_info(
                f"Enabling HA for {vm.name}."
            )
            vm_service.update(
                vm=sdk.types.Vm(
                    high_availability=sdk.types.HighAvailability(
                        enabled=True
                    ),
                    lease=(
                        sdk.types.StorageDomainLease(
                            storage_domain=disk_sd
                        )
                    )
                )
            )
            result["success"] = vm.name
        else:
            self.__logger.log_error(
                f"Failed to enable HA for {vm.name}. No storage"
                " domain found."
            )
            result["error"] = vm.name
        return result

    def set_vm_description(self) -> dict:
        """Change VM description to be JSON with correct fields for Elma."""
        # Get VM list.
        for dpc, connection in self.__connections.items():
            system_service = connection.system_service()
            vms_service = system_service.vms_service()
            for vm in vms_service.list():
                vm_service = vms_service.vm_service(vm.id)
                # Get VM current description.
                # Check if current VM description is JSON.
                if self.__is_dict_vm_description(vm.description):
                    self.__logger.log_debug(
                        f"[{self.__class__.__name__}] {vm.name} "
                        f"in {dpc} has a valid json in description."
                    )
                    data = self.__check_update_desc_json(
                        json.loads(vm.description)
                    )
                # If false - parse current description as JSON.
                # If true, skip this step.
                else:
                    self.__logger.log_error(
                        f"[{self.__class__.__name__}] {vm.name} "
                        f"in {dpc} has an invalid json in description."
                    )
                    data = self.__fix_bad_description(vm.description)
                    data = self.__check_update_desc_json(data)
                vm_service.update(
                    sdk.types.Vm(
                        description=json.dumps(data, ensure_ascii=False)
                    )
                )

    def __is_dict_vm_description(self, desc: str) -> bool:
        """Checking if current description can be parsed as dict/json."""
        try:
            json.loads(desc)
        except json.decoder.JSONDecodeError:
            return False
        return True

    def __fix_bad_description(self, data: str) -> dict:
        """Try to create valid JSON based on current description string."""
        result = {}
        # If VM was migrated from VMWare.
        if "Migrated by IntelSource" in data:
            result = {
                "Migrated": "True"
            }
            return result
        # If VM was created in RV and has old description.
        for el in ("Time created", "owner", "ELMA task numer"):
            if el in data:
                match = re.search(rf"{el}: \s*([^,]+)", data)
                result[el] = match.group(1)
        if result:
            return result
        # If nothing else was found put all data under 'Misc' field.
        return {
            "Misc": data
        }

    def __check_update_desc_json(self, data: any) -> str:
        """Checking if current present fields of valid JSON are correct."""
        correct_fields = set([
            "Environment",
            "Migrated",
            "Misc",
            "Time created",
            "owner",
            "ELMA task number"
        ])
        # Checking if data is not empty, which means it is not string
        if any(data) and data != '':
            if correct_fields == set(data.keys()):
                return data
            else:
                missing_keys = correct_fields - set(data.keys())
                for key in missing_keys:
                    data[key] = ''
                return data
        else:
            return {key: '' for key in correct_fields}

    def clean_desc(self):
        for dpc, connection in self.__connections.items():
            system_service = connection.system_service()
            vms_service = system_service.vms_service()
            for vm in vms_service.list():
                vm_service = vms_service.vm_service(vm.id)
                if vm.description == '{"Misc": "", "Time created": "", "ELMA task number": "", "elma_os": "", "owner": "", "Environment": "", "Migrated": ""}':
                    vm_service.update(
                        sdk.types.Vm(
                            description=''
                        )
                    )