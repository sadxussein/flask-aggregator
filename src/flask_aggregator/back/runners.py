"""Module for all get_ functions for external use."""

from flask_aggregator.back.elma_helper import ElmaHelper

def get_elma_vm_access_doc() -> None:
    """Collect VmAccessDoc from elma API.
    
    Table with information about VM documents will be upserted to 
    `elma_vm_access_doc` table.
    """
    elma_helper = ElmaHelper()
    elma_helper.import_vm_access_doc()

