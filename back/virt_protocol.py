"""Interface for different virtualizations."""

from typing import Protocol

class VirtProtocol(Protocol):
    """Protocol for virtualization classes."""
    def create_vm(self, config: dict) -> None:
        """Create VM."""
    def create_vlan(self, config: dict) -> None:
        """Create VLAN."""
    def get_vms(self) -> dict:
        """Get all VMs."""
    def get_hosts(self) -> dict:
        """Get all hosts."""
    def get_clusters(self) -> dict:
        """Get all clusters."""
    def get_data_centers(self) -> dict:
        """Get all 'datacenters' if there are any."""
    def get_storages(self) -> dict:
        """Get all storages."""
