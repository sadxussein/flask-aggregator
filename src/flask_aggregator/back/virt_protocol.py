"""Interface for different virtualizations."""

from typing import Protocol

class VirtProtocol(Protocol):
    """Protocol for virtualization classes."""
    def connect_to_virtualization(self) -> None:
        """Open connections with virtualization endpoint"""
    def disconnect_from_virtualization(self) -> None:
        """Close connections with virtualization endpoint."""
    def create_vm(self, config: dict) -> None:
        """Create VM."""
    def create_vlan(self, config: dict) -> None:
        """Create VLAN."""
    def get_vms(self) -> list:
        """Get all VMs."""
    def get_hosts(self) -> list:
        """Get all hosts."""
    def get_clusters(self) -> list:
        """Get all clusters."""
    def get_data_centers(self) -> list:
        """Get all 'datacenters' if there are any."""
    def get_storages(self) -> list:
        """Get all storages."""
    # def get_snapshots(self) -> list:
    #     """Get all snapshots."""