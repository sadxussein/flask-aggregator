"""Script for zabbix agent.

Retrieves information about hosts in oVirt."""

from flask_aggregator.back.virt_aggregator import VirtAggregator

if __name__ == "__main__":
    virt_aggregator = VirtAggregator()
    virt_aggregator.create_virt_helpers()
    virt_aggregator.run_data_collection(
        function_type="default",
        function="get_clusters"
    )
