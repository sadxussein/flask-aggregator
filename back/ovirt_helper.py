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
                print(self.__connections)
            except sdk.ConnectionError as e:
                self.__logger.error("Failed to connect to oVirt for DPC '%s': '%s'. Either cannot resolve server name or server is unreachable.",
                                    dpc,
                                    e)
            except sdk.AuthError as e:
                self.__logger.error("Failed to authenticate in oVirt Hosted Engine for DPC '%s': '%s'.",
                                    dpc,
                                    e)

    def disconnect_from_engines(self):
        """Close connections with all engines."""
        for dpc in self.__dpc_list:
            self.__logger.info("Closed connection with '%s' data processing center.",
                               dpc)
            self.__connections[dpc].close()
        self.__connections = {}

    def __get_timestamp(self):
        """Return current time. Primarily used for VMs."""
        return time.strftime("%Y.%d.%m-%H:%M:%S", time.localtime(time.time()))

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
                                "mount_point": "/"
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
                        "id": 2921
                    }
                }
            ]
            ```
        Returns VM UUID from oVirt if success, -1 otherwise.
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
            description=f"Time created: {self.__get_timestamp()}, owner: {config['meta']['owner']}, ELMA task number: {config['meta']['document_num']}",      # TODO: parse owner, it passes full list now
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
                    cores=config["vm"]["cores"],
                    sockets=1
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
        except sdk.Error as e:
            self.__logger.error("Could not create VM '%s'. Reason: '%s'.",
                                config["vm"]["name"],
                                e)



#         logger.info(f"VM {vm.name} created with ID: {vm.id} in {config['ovirt']['cluster']} cluster.")
#         logger.info("Now rebooting VM to apply cloud-init and new resource allocation.")

#         vm_service = vms_service.vm_service(vm.id)
        
#         # After creating VM we have to shut it down to apply new hardware and software options
#         while vm_service.get().status != sdk.types.VmStatus.DOWN:
#             logger.debug("Waiting for VM status set to DOWN (ready for next setup)...")
#             time.sleep(10)
# # ------------------------------------------------------------- DISKS ---------------------------------------------------------------------------------------------------------
#         # Extending root disk to a number set in disk list on vm_config
#         disk_attachments_service = vm_service.disk_attachments_service()
#         disk_attachments = disk_attachments_service.list()
#         # If any disk exist, and there will be only one in the template
#         logger.info("Resizing disk from template if it is > 30Gb.")
#         if disk_attachments:
#             disk_attachment = disk_attachments[0]
#             disk_service = system_service.disks_service().disk_service(disk_attachment.disk.id)
#             # Waiting for disk to be created
#             while disk_service.get().status == sdk.types.DiskStatus.LOCKED:
#                 logger.debug("Waiting system service to release disks LOCKED status...")
#                 time.sleep(10)
#             for disk_config in config["vm"]["disks"]:
#                 if int(disk_config["type"]) == 1:
#                     logger.debug("Root disk detected.")
#                     if disk_config['size'] > 30:
#                         logger.debug(f"Root disk size from vm config is {disk_config['size']} which is larger than 30 gb.")
#                         disk_service.update(
#                             disk=sdk.types.Disk(
#                                 # Disk with root partition should always be first in the list
#                                 provisioned_size=disk_config["size"] * 2**30,
#                                 bootable=True                                
#                             )
#                         )                    

#                     # Waiting to apply disk changes.
#                     while disk_service.get().status == sdk.types.DiskStatus.LOCKED:
#                         logger.debug("Waiting system service to release disks LOCKED status...")
#                         time.sleep(10)

#                     # Setting disk name and label.
#                     disk_service.update(
#                         disk=sdk.types.Disk(
#                             name=f"{vm.name}-root-disk-1",
#                             logical_name="sda"
#                         )
#                     )

#                     # Waiting to apply disk changes
#                     while disk_service.get().status == sdk.types.DiskStatus.LOCKED:
#                         logger.debug("Waiting system service to release disks LOCKED status...")
#                         time.sleep(10)
#                     logger.info(f"Disk with root partition extended for VM '{vm.name}', with ID '{vm.id}'.")

#         # Adding disks, if corresponding disk list on vm_config has more than one element                        
#         if len(config["vm"]["disks"]) > 1:
#             disk_index = 1
#             for disk in config["vm"]["disks"]:
#                 if int(disk["type"]) != 1:
#                     # Creating disk. Disk must be under 8gb, otherwise oVirt throws exception.
#                     if disk["size"] > 8192:
#                         disk["size"] = 8192
#                     logger.info(f"Creating additional disks #{disk_index} for VM '{vm.name}', with ID '{vm.id}'. Disk size: {disk['size']}Gb.")
#                     disk_index += 1

#                     # Attaching disk to VM.
#                     disk_attachment = disk_attachments_service.add(
#                         sdk.types.DiskAttachment(
#                             disk=sdk.types.Disk(
#                                 name=f"{vm.name}-data-disk-{disk_index}",
#                                 description=f"Additional disk #{disk_index} for {vm.name}",
#                                 format=sdk.types.DiskFormat.COW,
#                                 provisioned_size=disk["size"] * 2**30,
#                                 storage_domains=[
#                                     sdk.types.StorageDomain(
#                                         name=config["ovirt"]["storage_domain"]
#                                     )
#                                 ]
#                             ),
#                             bootable=False,
#                             active=True,
#                             interface=sdk.types.DiskInterface.VIRTIO_SCSI
#                         )                
#                     )
#                     disk_service = system_service.disks_service().disk_service(disk_attachment.disk.id)

#                     # Waiting to apply disk changes
#                     while disk_service.get().status == sdk.types.DiskStatus.LOCKED:
#                         logger.debug("Waiting system service to release disks LOCKED status...")
#                         time.sleep(10)

#                     if disk_attachment:                                    
#                         logger.info(f"Created additional disk for VM '{vm.name}', with ID '{vm.id}'.")
#                     else:
#                         logger.error(f"Failed to create disk with root partition for VM '{vm.name}', with ID '{vm.id}'.")
#                         raise Exception(f"[ERR] Failed to create disk with root partition for VM '{vm.name}', with ID '{vm.id}'.")     
# # ------------------------------------------------------------- NETWORKING ----------------------------------------------------------------------------------------------------
#         logger.info(f"Changing vNIC to {config['vlan']['name']}.")
#         # Finding vNIC profile
#         vnic_profiles_service = system_service.vnic_profiles_service()
#         vnic_profiles = vnic_profiles_service.list()
#         networks_service = system_service.networks_service()        
#         vlan_network = None

#         # Defining to which datacenter VM currently belongs. It is needed to
#         # determine whick vNIC profile is needed, since there may be vNIC's
#         # with same VLAN tag in different datacenters.
#         vm_cluster = system_service.clusters_service().cluster_service(vm.cluster.id).get()
#         vm_datacenter = system_service.data_centers_service().datacenter_service(vm_cluster.datacenter.id).get()
#         networks = networks_service.list()
#         target_network = None
#         for network in networks:
#             if network.datacenter and network.datacenter.id == vm_datacenter.id:
#                 if network.vlan and network.vlan.id == int(config["vlan"]["id"]):
#                     logger.info(f"Detected network with VLAN id {network.vlan.id} (ID: {network.id}) that fits one of VM.")
#                     target_network = network
#                     break

#         # for vnic_profile in vnic_profiles:
#         #     network = networks_service.network_service(vnic_profile.network.id).get()
#         #     if network.vlan.id == int(config["vlan"]["id"]):
#         #     # if vnic_profile.name == vm_config['vlan_name'] or f"{vm_config['vlan_id']}" in vnic_profile.name:
#         #         logger.debug(f"Detected VLAN {vnic_profile.name}, VLAN tag {network.vlan.id} with id {vnic_profile.id} present.")
#         #         vlan_network = vnic_profile
#         #         break

#         # Checking if VLAN exists. If not - create one
#         if target_network is None:
#         # if vlan_network == None:

#             # If no "cluster" field is defined in incoming JSON script will try and guess
#             # where to put VLAN. Strongly advised to use this field in JSON, since VLAN
#             # placement logic can change. Also selecting correct NIC, which also (in a better way)
#             # should be defined in incoming JSON.
#             vlan_config = prepare_vlan_config(config, connection)
            
#             # Creating VLAN based on JSON config.
#             create_vlan(vlan_config, connection)
           
#             logger.info(f"Network {config['vlan']['name']} with VLAN tag {config['vlan']['id']} (ID: {network.id}) created and attached to all hosts.")
                   
#         # For some reason vlan network can have 2 ids, which can lead to inability to add it to VM
#         # This requires further research TODO
#         for network in networks:
#             if network.datacenter and network.datacenter.id == vm_datacenter.id:
#                 if network.vlan and network.vlan.id == int(config["vlan"]["id"]):
#                     logger.info(f"Detected network with VLAN id {network.vlan.id} that fits one of VM.")
#                     target_network = network
#                     break
#         # Finding vNIC profile      
#         vlan_network = None
#         for vnic_profile in vnic_profiles:
#             # network = networks_service.network_service(vnic_profile.network.id).get()
#             if target_network.vlan.id == int(config["vlan"]["id"]):
#                 vlan_network = vnic_profile
#                 break
#         # Getting all NICs on VM
#         nics_service = vm_service.nics_service()
#         nics = nics_service.list()
#         # Applying vNIC profiles for main nic1 on VM
#         for nic in nics:
#             # All templates will have NIC names 'nic1' as a primary connection
#             if nic.name == 'nic1':
#                 nic_service = nics_service.nic_service(nic.id)
#                 nic_service.update(
#                     sdk.types.Nic(
#                         vnic_profile=sdk.types.VnicProfile(
#                             id=vlan_network.id
#                         )
#                     )
#                 )

#         # After applying changes VM will be locked, so wait until lockdown is released
#         while vm_service.get().status != sdk.types.VmStatus.DOWN:
#                 logger.debug("Waiting system service to release VM's LOCKED status...")
#                 time.sleep(10)      
# # ------------------------------------------------------------- STARTING VM ---------------------------------------------------------------------------------------------------                        
#         # Starting VM via CloudInit
#         vm_service.start()
# # ------------------------------------------------------------- RESTARTING VM TO RESET FSTAB ----------------------------------------------------------------------------------
#         while vm_service.get().status != sdk.types.VmStatus.UP:
#             logger.debug("Waiting VM to start...")                
#             time.sleep(10)
#         # Waiting 60 second for VM to properly start.
#         time.sleep(60)
#         logger.debug("Issued VM reset to fix possible fstab malfunction.")
#         vm_service.reset()