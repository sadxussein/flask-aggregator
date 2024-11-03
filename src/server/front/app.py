"""OITI Flask http aggregator.

Used primarily for aggregating oVirt information.
"""

import json

from flask import Flask, render_template, request, jsonify

from ..back.virt_aggregator import VirtAggregator
from ..back.file_handler import FileHandler
from ..back.sqlite_handler import SQLiteHandler

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

        @self.app.route("/vms")
        def ovirt_vms():
            """Show VM list from database."""
            sqlite_handler = SQLiteHandler()
            filters = {
                "uuid": request.args.get("uuid"),
                "name": request.args.get("name")
            }
            data = sqlite_handler.get_data("vms", filters)
            return render_template(
                "vms.html", data=data, filters=filters
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

        @self.app.route("/ovirt/cluster_list/raw_json")
        def ovirt_cluster_raw_json():
            """Show cluster list (raw JSON)."""
            file_handler = FileHandler()
            file_handler.get_group_data("clusters")
            return jsonify(
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

    def start(self):        # TODO: pass parameters for Flask server
        """Start Flask aggregator server."""
        self.app.run(host="0.0.0.0", port="6299", debug=True)

if __name__ == "__main__":
    flask_aggregator = FlaskAggregator()
    flask_aggregator.start()
