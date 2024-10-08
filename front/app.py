"""OITI Flask http aggregator.

Used primarily for aggregating oVirt information.
"""

import json

from flask import Flask, render_template, request, jsonify

from back.ovirt_helper import OvirtHelper

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
            return '''
                <h1>Country home, take me home...</h1>
            '''

        @self.app.route("/ovirt_vm_list")
        def get_ovirt_vm_list():
            """Show VM list."""
            vms = self.__load_json()
            return render_template("ovirt_vm_list.html", data=vms)

        @self.app.route("/create_vm", methods=['POST'])
        def create_vm():
            """Create VM endpoint."""
            if "jsonfile" not in request.files:
                return jsonify({"error": "No file part."}), 400

            json_file = request.files["jsonfile"]

            if json_file.name == '':
                return jsonify({"error": "No selected file."}), 400

            if json_file and json_file.filename.endswith(".json"):
                try:
                    ovirt_helper = OvirtHelper()
                    ovirt_helper.connect_to_engines()
                    vm_configs = json.load(json_file)
                    for config in vm_configs:
                        ovirt_helper.create_vm(config)
                    ovirt_helper.disconnect_from_engines()
                    return jsonify({"success": "Created VMs."}), 200
                except json.JSONDecodeError:
                    return jsonify({"error": "Invalid JSON file."}), 400
            else:
                return jsonify({"error": "File is not a valid JSON."}), 400

    def __load_json(self):
        """Return JSON file data."""
        with open("back/files/vm_list.json", 'r', encoding="utf-8") as file:
            data = json.load(file)
        return data

    def start(self):
        """Start Flask aggregator server."""
        self.app.run(host="0.0.0.0", port="6299", debug=True)


if __name__ == "__main__":
    flask_aggregator = FlaskAggregator()
    flask_aggregator.start()
