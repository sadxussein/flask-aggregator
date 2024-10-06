"""oVirt helper class description."""

__version__ = "0.1"
__author__ = "xussein"

import ovirtsdk4 as sdk

class OvirtHelper():
    """Class required to perform different actions with oVirt hosted engines."""
    def __init__(self, dpc_list, urls_list, username, password):
        # TODO: check input data.
        self.__dpc_list = dpc_list
        self.__urls_list = urls_list
        self.__username = username
        self.__password = password

    def get_json_vm_list(self):
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
            datacenter
            was_migrated

        Field list will be extended in the future.
        """
        result = []

        for dpc in self.__dpc_list:
            try:
                # Connect to ovirt.
                connection = sdk.Connection(
                    url=self.__urls_list[dpc],
                    username=self.__username,
                    password=self.__password,
                    insecure=True,
                    debug=True
                )

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

            except sdk.ConnectionError as e:
                print(f"Failed to connect to oVirt for DPC {dpc}: {e}")
            finally:
                # Safely closing connection
                connection.close()

        return result
