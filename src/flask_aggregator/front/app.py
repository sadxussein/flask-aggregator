"""OITI Flask http aggregator.

Used primarily for aggregating oVirt information.
"""

import json
import os
from urllib.parse import urlencode

from flask import (
    Flask, request, render_template, jsonify, abort
)

from flask_aggregator.config import (
    Config, DevelopmentConfig, ProductionConfig
)
from flask_aggregator.back.models import DataCenter, Cluster
from flask_aggregator.back.logger import Logger
from flask_aggregator.back.virt_aggregator import VirtAggregator
from flask_aggregator.back.ovirt_helper import OvirtHelper
from flask_aggregator.back.file_handler import FileHandler
from flask_aggregator.back.dbmanager import DBManager

class FlaskAggregator():
    """Flask-based aggregator class. Used primarily for oVirt interactions."""    

    def __init__(self):
        self.__app = Flask(__name__)
        self.__configure_routes()

    def __configure_routes(self):
        """Configure each url for server."""
        @self.__app.route('/')
        def index():
            """Show index page."""
            return render_template("index.html")

        @self.__app.route("/view/<model_name>")
        def view(model_name):
            """Show model list from database.
            
            Model list is defined in DM_MODELS dictionary of this class.
            """
            model = Config.DB_MODELS.get(model_name)
            if model is None:
                abort(404, description=f"Table {model_name} not found.")

            kwargs = {}

            # Arguments that come from flask frontend.
            page = request.args.get("page", 1, type=int)
            per_page = request.args.get("per_page", 10, type=int)
            sort_by = request.args.get("sort_by", "name")
            order = request.args.get("order", "asc")
            old_backups = request.args.get("old_backups", "all")
            elma_backups = request.args.get("elma_backups", "all")
            # show_dbs = request.args.get("show_dbs", "all")

            dbmanager = DBManager()
            fields = Config.DB_MODELS[model_name].get_columns_order()
            filters = {}
            for f in model.get_filters():
                filters[f] = request.args.get(f)
            data_count, data = None, None
            if (
                model_name == "backups"
                and old_backups != "all_cb_entries"
            ):
                data_count, data = dbmanager.get_old_backups(
                    model, page, per_page, filters, sort_by, order, fields,
                    old_backups
                )
            elif model_name == "backups_view":
                data_count, data = dbmanager.get_data_from_view(
                    model, page, per_page, fields, filters, sort_by, order
                )
            elif (
                model_name == "vms_to_be_backed_up_view"
            ):
                show_dbs = request.args.get("show_dbs")
                show_absent_in_ov = request.args.get("show_absent_in_ov")
                kwargs["show_dbs"] = False if show_dbs is None else True
                kwargs["show_absent_in_ov"] = (
                    False if show_absent_in_ov is None else True
                )
                data_count, data = dbmanager.get_data_from_view(
                    model, page, per_page, fields, filters, sort_by, order,
                    show_dbs=kwargs["show_dbs"],
                    show_absent_in_ov=kwargs["show_absent_in_ov"]
                )
            else:
                data_count, data = dbmanager.get_paginated_data(
                    model, page, per_page, filters, sort_by, order, fields
                )

            total_pages = (data_count + per_page - 1) // per_page

            def get_pagination_url(page: int) -> str:
                args = request.args.to_dict()
                args["page"] = page
                return f"/view/{model_name}?{urlencode(args)}"

            dbmanager.close()

            return render_template(
                "view.html", model_name=model_name, data=data,
                filters=filters, title=model_name, page=page,
                per_page=per_page, total_pages=total_pages,
                get_pagination_url=get_pagination_url, getattr=getattr,
                fields=fields, sort_by=sort_by, order=order,
                total_items=data_count, old_backups=old_backups,
                elma_backups=elma_backups, **kwargs
            )

        @self.__app.route("/ovirt/cluster_list/raw_json")
        def ovirt_cluster_raw_json():
            """Show cluster list (raw JSON)."""
            dbmanager = DBManager()
            data = dbmanager.get_all_data_as_dict(Cluster)
            return jsonify(
                data=data
            )

        @self.__app.route("/ovirt/data_center_list/raw_json")
        def ovirt_data_center_raw_json():
            """Show data center list (raw JSON)."""
            dbmanager = DBManager()
            data = dbmanager.get_all_data_as_dict(DataCenter)
            return jsonify(
                data=data
            )

        @self.__app.route("/ovirt/set_vm_ha", methods=["POST"])
        def ovirt_set_vm_ha():
            """Set VM high availability parameter."""
            if "jsonfile" not in request.files:
                return jsonify({"error": "No file part."}), 400

            json_file = request.files["jsonfile"]

            if json_file.name == '':
                return jsonify({"error": "No selected file."}), 400

            if json_file and json_file.filename.endswith(".json"):
                try:
                    ovirt_helper = OvirtHelper(dpc_list=["e15-test2"])
                    ovirt_helper.connect_to_virtualization()
                    result = ovirt_helper.set_vm_ha(json.load(json_file))
                    ovirt_helper.disconnect_from_virtualization()
                    return jsonify(result)
                except json.JSONDecodeError as e:
                    return (
                        jsonify(
                            {"JSONDecodeError": f"Invalid JSON file. {str(e)}"}
                        ),
                        400
                    )
                except KeyError as e:
                    return jsonify({"KeyError": str(e)}), 400
            else:
                return jsonify({"error": "File is not a valid JSON."}), 400

        @self.__app.route("/ovirt/create_vm", methods=["POST"])
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
                    virt_aggregator = VirtAggregator(logger=Logger())
                    virt_aggregator.create_virt_helpers(file_handler)
                    virt_aggregator.create_vms(file_handler)
                    return jsonify({"success": "Created VMs."}), 200
                except json.JSONDecodeError:
                    return jsonify({"error": "Invalid JSON file."}), 400
            else:
                return jsonify({"error": "File is not a valid JSON."}), 400

        @self.__app.route("/ovirt/create_vlan", methods=["POST"])
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
                    virt_aggregator = VirtAggregator(logger=Logger())
                    virt_aggregator.create_virt_helpers(file_handler)
                    virt_aggregator.create_vlans(file_handler)
                    return jsonify({"success": "Created VMs."}), 200
                except json.JSONDecodeError:
                    return jsonify({"error": "Invalid JSON file."}), 400
            else:
                return jsonify({"error": "File is not a valid JSON."}), 400

    def get_app(self) -> Flask:
        """Return Flask aggregator server."""
        env = os.getenv("FLASK_ENV", "development")
        if env == "production":
            self.__app.config.from_object(ProductionConfig)
        else:
            self.__app.config.from_object(DevelopmentConfig)
        return self.__app

# If run from flask run.
flask_aggregator = FlaskAggregator()
app = flask_aggregator.get_app()

# If run from venv directly.
def main():
    app.run()
