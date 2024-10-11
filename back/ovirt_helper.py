"""oVirt helper class description."""

__version__ = "0.1"
__author__ = "xussein"

import logging
import time

import ovirtsdk4 as sdk
from . import config as cfg

class OvirtHelper():
    """Class required to perform different actions with oVirt hosted engines."""

    def __init__(self, dpc_list=cfg.DPC_LIST, urls_list=cfg.DPC_URLS,
                 username=cfg.USERNAME, password=cfg.PASSWORD
                 ):
        """Construct default class instance."""
        # TODO: check input data.
        self.__dpc_list = dpc_list
        self.__urls_list = urls_list
        self.__username = username
        self.__password = password
        self.__connections = {}

        # Setting logging vars, it writes both at log file and stderr.
        self.__logger = logging.getLogger('logger')
        self.__logger.setLevel(logging.DEBUG)
        self.__logger_file_handler = logging.FileHandler('aggregator.log')
        self.__logger_file_handler.setLevel(logging.DEBUG)
        self.__logger_console_handler = logging.StreamHandler()
        self.__logger_console_handler.setLevel(logging.DEBUG)
        self.__logger_formatter = logging.Formatter('%(asctime)s-[%(levelname)s] - %(threadName)s: %(message)s')
        self.__logger_file_handler.setFormatter(self.__logger_formatter)
        self.__logger_console_handler.setFormatter(self.__logger_console_handler)
        self.__logger.addHandler(self.__logger_file_handler)

    def connect_to_engines(self):
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
                self.__logger.info("Connected to '%s' data processing center.",
                                   dpc)
                self.__connections[dpc] = connection
            except sdk.ConnectionError as e:
                self.__logger.error("Failed to connect to oVirt for DPC '%s': '%s'. Either cannot resolve server name or server is unreachable.",
                                    dpc,
                                    e)
            except sdk.AuthError as e:
                self.__logger.error("Failed to authenticate in oVirt Hosted Engine for DPC '%s': '%s'.",
                                    dpc,
                                    e)

    def disconnect_from_engines(self):
        """Close connections with all engines.
        
        Closing connections with engines and cleaning up all logger handlers.
        """
        for dpc in self.__dpc_list:
            self.__logger.info("Closed connection with '%s' data processing center.",
                               dpc)
            self.__connections[dpc].close()
        for handler in self.__logger.handlers[:]:
            self.__logger.removeHandler(handler)
            handler.close()
        self.__connections = {}

    def __get_timestamp(self):
        """Return current time. Primarily used for VMs."""
        return time.strftime("%Y.%d.%m-%H:%M:%S", time.localtime(time.time()))

    def get_data_center_list(self):
        """Get data center information from all engines.
        
        Returns:
            data center list (dict): List of following parameters:
            'ID', 'name', 'engine'.
        """
        result = []
        for dpc, connection in self.__connections.items():
            for data_center in connection.system_service().data_centers_service().list():
                result.append({
                    "ID": data_center.id,
                    "name": data_center.name,
                    "engine": dpc
                })
        return result

    def get_storage_domain_list(self):
        """Get storage domain information from all engines.

        Returns:
            storage domain list (dict): List of following parameters:
            'ID', 'name', 'engine', 'space_available', 'space_used', 
            'space_committed', 'space_total' 'space_overprovisioning'.
        """
        result = []
        for dpc, connection in self.__connections.items():
            system_service = connection.system_service()
            storage_domains_service = system_service.storage_domains_service()
            for domain in storage_domains_service.list():
                if domain.name not in cfg.STORAGE_DOMAIN_EXCEPTIONS:
                    result.append({
                        "ID": domain.id,
                        "name": domain.name,
                        "engine": dpc,
                        "space_available": domain.available / (1024 ** 3),
                        "space_used": domain.used / (1024 ** 3),
                        "space_committed": domain.committed / (1024 ** 3),
                        "space_total": domain.available / (1024 ** 3) + domain.used / (1024 ** 3),
                        "space_overprovisioning": int((domain.committed * 100)
                                                / (domain.available + domain.used))
                    })
        return result

    def get_cluster_list(self):
        """Get cluster ID and name list.
    
        Returns:
            cluster list (dict): List of following parameters:
            'ID', 'name', 'engine'.
        """
        result = []
        for dpc, connection in self.__connections.items():
            system_service = connection.system_service()
            clusters_service = system_service.clusters_service()
            clusters = clusters_service.list()
            for cluster in clusters:
                result.append({"name": cluster.name, "ID": cluster.id, "engine": dpc})
        return result

    def get_host_list(self):
        """Get host ID, name, cluster and IP list.
        
        Returns:
            host list (dict): List of following parameters:
            'ID', 'name', 'cluster', 'IP', 'engine'.
        """
        result = []
        for dpc, connection in self.__connections.items():
            system_service = connection.system_service()
            hosts_service = system_service.hosts_service()
            hosts = hosts_service.list()
            clusters_service = system_service.clusters_service()
            data_centers_service = system_service.data_centers_service()
            for host in hosts:
                cluster = clusters_service.cluster_service(host.cluster.id).get()
                data_center = data_centers_service.data_center_service(cluster.data_center.id).get()
                host_service = hosts_service.host_service(host.id)
                nics_service = host_service.nics_service()
                nics = nics_service.list()
                ip = None
                for nic in nics:
                    if nic.name in cfg.HOST_MANAGEMENT_BONDS:
                        if nic.ip and nic.ip.address:
                            ip = nic.ip.address
                result.append({"ID": host.id,
                               "name": host.name, 
                               "cluster": cluster.name, 
                               "data_center": data_center.name,
                               "IP": ip,
                               "engine": dpc})
        return result

    def get_vm_list(self):
        """Get VM list as dictionary.
        
        Returns:
            dict: List of all VMs from oVirt as dictionary.

        Function connects to every oVirt engine passed to class instance file 
        and returns data from all VMs as dictionary.

        Current field list:

            ID
            name
            hostname
            state
            IP
            engine
            host
            cluster
            data_center
            was_migrated

        Field list will be extended in the future.
        """
        result = []

        # self.__connect_to_engines()

        for dpc, connection in self.__connections.items():
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
                vm_data["ID"] = vm.id

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
                reported_devices_service = vm_service.reported_devices_service()
                reported_devices = reported_devices_service.list()
                for device in reported_devices:
                    if device.ips:
                        for ip in device.ips:
                            if ip.version == sdk.types.IpVersion.V4:
                                vm_data["IP"] = ip.address
                    else:
                        vm_data["IP"] = ''

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
                cluster_service = clusters_service.cluster_service(vm.cluster.id)
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
                    vm_data["was_migrated"] = "True"
                else:
                    vm_data["was_migrated"] = ""

                print(list(vm_data.values()))
                result.append(vm_data)

        # self.__disconnect_from_engines()

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
                        "dns_servers": "10.82.254.32 10.82.254.31"
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
        # Try find VM with current VM name. If VM exists create corresponding
        # log entry and close function.
        system_service = self.__connections[config["ovirt"]["engine"]].system_service()
        vms_service = system_service.vms_service()

        # Creating VM
        vm = sdk.types.Vm(
            name=config["vm"]["name"],
            cluster=sdk.types.Cluster(
                name=config["ovirt"]["cluster"]
            ),
            comment=f"{config['meta']['environment']}, {config['meta']['inf_system']}",
            description=f"Time created: {self.__get_timestamp()}, owner: {config['meta']['owner']}, ELMA task number: {config['meta']['document_num']}",
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
                    cores=config["vm"]["cores"] if config["vm"]["cores"] <= 10 else config["vm"]["cores"] / 2,
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
                dns_servers=config["vm"]["dns_servers"] if "dns_servers" in config else "10.82.254.32 10.82.254.31",
                dns_search=config["vm"]["search_domain"] if "search_domain" in config else "crimea.rncb.ru"
            )
        )
        try:
            vm = vms_service.add(vm, clone=True)
            self.__logger.info("Creating VM '%s'.", vm.name)

            # After creating VM we have to shut it down to apply new hardware and
            # software options.
            vm_service = vms_service.vm_service(vm.id)
            while vm_service.get().status != sdk.types.VmStatus.DOWN:
                self.__logger.debug("Waiting for VM status set to DOWN (ready for next setup)...")
                time.sleep(10)
            self.__logger.info("Created VM %s.", vm.name)

            # Disks operations.
            self.__extend_vm_root_disk(system_service, vm, vm_service, config)
            self.__create_vm_extra_disks(system_service, vm, vm_service, config)

            # Network operations.
            self.__set_vm_network(system_service, vm_service, config)

            # After applying changes VM will be locked, so wait until lockdown is released.
            while vm_service.get().status != sdk.types.VmStatus.DOWN:
                self.__logger.debug("Waiting system service to release VM's LOCKED status...")
                time.sleep(10)

            # Starting VM via CloudInit.
            vm_service.start()

            # Restrating VM to fix fstab.
            while vm_service.get().status != sdk.types.VmStatus.UP:
                self.__logger.debug("Waiting VM to start...")
                time.sleep(10)
            # Waiting 60 second for VM to properly start.
            time.sleep(60)
            self.__logger.info("Issued VM reset to fix possible fstab malfunction.")
            vm_service.reset()

            # Finalizing VM.
            while vm_service.get().status != sdk.types.VmStatus.UP:
                self.__logger.debug("Waiting VM to start...")
                time.sleep(10)
            self.__logger.info("VM '%s' in dpc '%s' created and operational.",
                        vm.name,
                        config["ovirt"]["engine"])

            return {"id": vm.id, "name": vm.name, "engine": config["ovirt"]["engine"]} if vm else -1

        except sdk.Error as e:
            self.__logger.error("Could not create VM '%s'. Reason: '%s'.",
                                config["vm"]["name"],
                                e)

    def __extend_vm_root_disk(self, system_service, vm, vm_service, config):
        """Extend VM root disk size to one set in config dict."""
        # Extending root disk to a number set in disk list on vm_config.
        disk_attachments_service = vm_service.disk_attachments_service()
        disk_attachments = disk_attachments_service.list()

        # If any disk exist, and there will be only one in the template.
        self.__logger.info("Resizing disk from template if it is > 30Gb.")
        if disk_attachments:
            disk_attachment = disk_attachments[0]
            disk_service = system_service.disks_service().disk_service(disk_attachment.disk.id)

            # Waiting for disk to be created
            while disk_service.get().status == sdk.types.DiskStatus.LOCKED:
                self.__logger.debug("Waiting system service to release disks LOCKED status...")
                time.sleep(10)
            for disk_config in config["vm"]["disks"]:
                if int(disk_config["type"]) == 1:
                    self.__logger.debug("Root disk detected.")
                    if disk_config['size'] > 30:
                        self.__logger.debug("Root disk size from vm config is '%s' which is larger than 30 gb.",
                                            disk_config['size'])
                        disk_service.update(
                            disk=sdk.types.Disk(
                                # Disk with root partition should always be
                                # first in the list.
                                provisioned_size=disk_config["size"] * 2**30,
                                bootable=True
                            )
                        )

                    # Waiting to apply disk changes.
                    while disk_service.get().status == sdk.types.DiskStatus.LOCKED:
                        self.__logger.debug("Waiting system service to release disks LOCKED status...")
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
                        self.__logger.debug("Waiting system service to release disks LOCKED status...")
                        time.sleep(10)
                    self.__logger.info("Disk with root partition extended for VM '%s', with ID '%s'.",
                                       vm.name,
                                       vm.id)

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
                    self.__logger.info("Creating additional disks #%i for VM '%s', with ID '%s'. Disk size: %sGb.",
                                       disk_index,
                                       vm.name,
                                       vm.id,
                                       disk['size'])
                    disk_index += 1

                    # Attaching disk to VM.
                    disk_attachment = disk_attachments_service.add(
                        sdk.types.DiskAttachment(
                            disk=sdk.types.Disk(
                                name=f"{vm.name}-data-disk-{disk_index}",
                                description=f"Additional disk #{disk_index} for {vm.name}",
                                format=sdk.types.DiskFormat.COW if bool(disk["sparse"]) else sdk.types.DiskFormat.RAW,
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
                    self.__logger.debug("Created disk_attachment variable (disk #%s)", disk_index)
                    disk_service = system_service.disks_service().disk_service(disk_attachment.disk.id)
                    self.__logger.debug("Found disk_attachment service (disk #%s)", disk_index)

                    # Waiting to apply disk changes
                    while disk_service.get().status == sdk.types.DiskStatus.LOCKED:
                        self.__logger.debug("Waiting system service to release disks LOCKED status...")
                        time.sleep(10)

                    if disk_attachment:
                        self.__logger.info("Created additional disk for VM '%s', with ID '%s'.",
                                           vm.name,
                                           vm.id)
                    else:
                        self.__logger.error("Failed to create disk with root partition for VM '%s', with ID '%s'.",
                                            vm.name,
                                            vm.id)

    def __set_vm_network(self, system_service, vm_service, config):
        """Change VM vNIC (VLAN)."""
        self.__logger.info("Changing VM vNIC to %s. Searching vNIC profile.",
                           config['vlan']['name'])
        vnic_profile_id = self.__get_vnic_profile(system_service, config)
        if vnic_profile_id:
            nics_service = vm_service.nics_service()
            nics = nics_service.list()
            # Applying vNIC profiles for main nic1 on VM
            for nic in nics:
                # All templates will have NIC names 'nic1' as a primary connection
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
            self.__logger.error("No vNIC with VLAN ID '%s' found!", config['vlan']['id'])

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
                network = networks_service.network_service(profile.network.id).get()
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
                data_center = data_centers_service.data_center_service(cluster.data_center.id).get()
                data_center_id = data_center.id
        return data_center_id

    def create_vlan(self, config):  # TODO: change checking if VLAN exists logic
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
        system_service = self.__connections[config['ovirt']['engine']].system_service()

        # Getting data center service. Also getting cluster service and full list of clusters.
        dcs_service = system_service.data_centers_service()
        clusters_service = system_service.clusters_service()
        clusters = clusters_service.list()

        # Defining where to put VLAN, based on cluster in prepared/raw VLAN JSON config.
        target_dc = None
        target_cluster = None
        for cluster in clusters:
            if cluster.name == config["ovirt"]["cluster"]:
                target_cluster = cluster
                target_dc = dcs_service.data_center_service(cluster.data_center.id).get()
                break

        # Getting target data center's network service. Getting list of all networks
        # in DC to check if vlans already exist.
        dc_network_service = dcs_service.service(target_dc.id).networks_service()
        dc_networks = dc_network_service.list()
        current_vlan_exists = False
        for dc_network in dc_networks:
            if dc_network.vlan and dc_network.vlan.id == config["vlan"]["id"]:
                current_vlan_exists = True
                vlan = dc_network
                self.__logger.error("Network '%s' already exists in '%s' datacenter!",
                                    config['vlan']['name'],
                                    target_dc.name)
                break

        # Creating VLAN.
        if not current_vlan_exists:
            vlan = dc_network_service.add(
                sdk.types.Network(
                    name=f"{config['vlan']['id']}{config['vlan']['suffix']}-vlan",
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
        cluster_networks_service = clusters_service.cluster_service(target_cluster.id).networks_service()
        cluster_networks = cluster_networks_service.list()
        current_vlan_exists = False
        for cluster_network in cluster_networks:
            if cluster_network.vlan.id == config["vlan"]["id"]:
                current_vlan_exists = True
                self.__logger.error("Network '%s' already exists in '%s' cluster!",
                                    config['vlan']['name'],
                                    target_cluster.name)

        if not current_vlan_exists:
            cluster_networks_service.add(
                sdk.types.Network(
                    id=vlan.id,
                    required=False
                )
            )

        # Getting list of all hosts to perform check to define if vlan is already attached to host.
        hosts_service = system_service.hosts_service()
        hosts = hosts_service.list()
        for host in hosts:

            # Checking host <-> cluster.
            host_cluster = self.__connections[config['ovirt']['engine']].follow_link(host.cluster)
            if host_cluster.name == config["ovirt"]["cluster"]:
                self.__logger.info("Attaching VLAN to host '%s'.", host.name)
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

        self.__logger.info("Network '%s' created and attached to all hosts.",
                           config['vlan']['name'])

