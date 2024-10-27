"""OITI Flask http aggregator.

Used primarily for aggregating oVirt information.
"""

import json
import threading

from flask import Flask, render_template, request, jsonify

from back.virt_aggregator import VirtAggregator
from back.config import BACK_FILES_FOLDER
from back.file_handler import FileHandler

class FlaskAggregator():
    """Flask-based aggregator class. Used primarily for oVirt interactions."""
    def __init__(self):
        self.app = Flask(__name__)
        self.__configure_routes()

    def __configure_routes(self):
        """Configure each url for server."""
        @self.app.route('/')
        def index():
            """Show index page."""
            return render_template("index.html")

        @self.app.route("/ovirt")
        def ovirt_index():
            """oVirt index page."""
            return '''
                <h1>oVirt index page.</h1>
            '''

        @self.app.route("/ovirt/vm_list")
        def ovirt_vm_list():
            """Show VM list."""
            file_handler = FileHandler()
            file_handler.get_group_data("vms")
            return render_template(
                "ovirt_vm_list.html",
                data=file_handler.file_data["vms"]
            )

        @self.app.route("/ovirt/host_list")
        def ovirt_host_list():
            """Show host list."""
            file_handler = FileHandler()
            file_handler.get_group_data("hosts")
            return render_template(
                "ovirt_host_list.html",
                data=file_handler.file_data["hosts"]
            )

        @self.app.route("/ovirt/cluster_list")
        def ovirt_cluster_list():
            """Show cluster list."""
            file_handler = FileHandler()
            file_handler.get_group_data("clusters")
            return render_template(
                "ovirt_cluster_list.html",
                data=file_handler.file_data["clusters"]
            )

        @self.app.route("/ovirt/storage_domain_list")
        def ovirt_storage_domain_list():
            """Show storage domain list."""
            file_handler = FileHandler()
            file_handler.get_group_data("storages")
            return render_template(
                "ovirt_storage_domain_list.html",
                data=file_handler.file_data["storages"]
            )

        @self.app.route("/ovirt/data_center_list")
        def ovirt_data_center_list():
            """Show storage domain list."""
            file_handler = FileHandler()
            file_handler.get_group_data("data_centers")
            return render_template(
                "ovirt_data_center_list.html",
                data=file_handler.file_data["data_centers"]
            )

        @self.app.route("/ovirt/create_vm", methods=["POST"])
        def ovirt_create_vm():
            """Create VM endpoint."""
            if "jsonfile" not in request.files:
                return jsonify({"error": "No file part."}), 400

            json_file = request.files["jsonfile"]

            if json_file.name == '':
                return jsonify({"error": "No selected file."}), 400

            if json_file and json_file.filename.endswith(".json"):
                try:
                    file_handler = FileHandler()
                    file_handler.input_json = json.load(json_file)
                    # Formatting to get separate list for each unique DPC.
                    file_handler.reformat_input_json()
                    virt_aggregator = VirtAggregator()
                    virt_aggregator.create_virt_helpers(file_handler)
                    virt_aggregator.create_vms(file_handler)
                    return jsonify({"success": "Created VMs."}), 200
                except json.JSONDecodeError:
                    return jsonify({"error": "Invalid JSON file."}), 400
            else:
                return jsonify({"error": "File is not a valid JSON."}), 400

        @self.app.route("/ovirt/create_vlan", methods=["POST"])
        def ovirt_create_vlan():
            """Create VLAN endpoint."""
            if "jsonfile" not in request.files:
                return jsonify({"error": "No file part."}), 400

            json_file = request.files["jsonfile"]

            if json_file.name == '':
                return jsonify({"error": "No selected file."}), 400

            if json_file and json_file.filename.endswith(".json"):
                try:
                    file_handler = FileHandler()
                    file_handler.input_json = json.load(json_file)
                    # Formatting to get separate list for each unique DPC.
                    file_handler.reformat_input_json()
                    # Creating list of unique VLANs per DPC.
                    file_handler.make_unique_vlan_configs()
                    virt_aggregator = VirtAggregator()
                    virt_aggregator.create_virt_helpers(file_handler)
                    virt_aggregator.create_vlans(file_handler)
                    return jsonify({"success": "Created VMs."}), 200
                except json.JSONDecodeError:
                    return jsonify({"error": "Invalid JSON file."}), 400
            else:
                return jsonify({"error": "File is not a valid JSON."}), 400

    def __load_json(self, file_name):
        """Return JSON file data."""
        with open(f"{BACK_FILES_FOLDER}/{file_name}", 'r', encoding="utf-8") as file:
            data = json.load(file)
        return data

    def __get_dpc_list(self, configs):
        """Return list of all DPCs to work with.
        
        Args:
            configs (dict): VM/VLAN config dict.

        Returns:
            dpc_set (list): List of unique DPCs to work with.
        """
        dpc_set = set()
        for config in configs:
            dpc_set.add(config["ovirt"]["engine"])
        return list(dpc_set)

    def __get_elma_document_number(self, configs):
        """Return ELMA document number(s) to identify it in ELMA DB.
        
        Args:
            configs (dict): VM/VLAN config dict.

        Returns:
            number_set (str): Either single number or numbers concatenated
            by space.
        """
        number_set = set()
        for config in configs:
            number_set.add(config["meta"]["document_num"])
        return ' '.join(list(number_set)) if len(number_set) > 1 else list(number_set)[0]

    def __reformat_input_config(self, configs):
        """Reformat input JSON file.

        Args:  
            configs (dict): VM/VLAN config dict.

        Returns:
            configs (dict): same information as input, but different hierarchy.

        Reformatting input JSON file hierarchy from `list -> vm configs as dicts` to
        `dpc dict key -> list -> vm configs as dicts`. With such hierarchy it
        is easier to split threads for each DPC.
        """
        result = {}
        dpc_list = self.__get_dpc_list(configs)
        for dpc in dpc_list:
            result[dpc] = []
        for config in configs:
            result[config["ovirt"]["engine"]].append(config)
        return result

    def __ovirt_create_vms(self, helper, dpc_configs):
        print(f"Started thread {threading.current_thread().name}.")
        result = []
        for config in dpc_configs:
            result.append(helper.create_vm(config))
        return result

    def __ovirt_create_vlans(self, helper, dpc_configs):
        print(f"Started thread {threading.current_thread().name}.")
        result = []
        for config in dpc_configs:
            result.append(helper.create_vlan(config))
        return result

    def start(self):        # TODO: pass parameters for Flask server
        """Start Flask aggregator server."""
        self.app.run(host="0.0.0.0", port="6299", debug=True)

if __name__ == "__main__":
    flask_aggregator = FlaskAggregator()
    flask_aggregator.start()
