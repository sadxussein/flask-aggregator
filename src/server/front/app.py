"""OITI Flask http aggregator.

Used primarily for aggregating oVirt information.
"""

import json
import os

from flask import (
    Flask, request, render_template, jsonify, flash, redirect, url_for, abort
)

from ..back.virt_aggregator import VirtAggregator
from ..back.file_handler import FileHandler
from ..back.dbmanager import DBManager
from ..back.models import Vm, Host, Cluster, Storage, DataCenter
from ..config import DevelopmentConfig, ProductionConfig
from .forms import LoginForm

class FlaskAggregator():
    """Flask-based aggregator class. Used primarily for oVirt interactions."""
    DB_MODELS = {
        "vms": Vm,
        "hosts": Host,
        "clusters": Cluster,
        "storages": Storage,
        "data_centers": DataCenter
    }

    def __init__(self):
        self.__app = Flask(__name__)
        self.__configure_routes()

    def __configure_routes(self):
        """Configure each url for server."""
        @self.__app.route('/')
        def index():
            """Show index page."""
            return render_template("index.html")

        @self.__app.route("/login", methods=["GET", "POST"])
        def login():
            form = LoginForm()
            if form.validate_on_submit():
                flash(
                    f"Login requested for user {form.username.data}"
                    f", remember_me={form.remember_me.data}"
                )
                return redirect(url_for('vms'))
            return render_template("login.html", form=form)

        @self.__app.route("/ovirt")
        def ovirt_index():
            """oVirt index page."""
            return '''
                <h1>oVirt index page.</h1>
            '''

        @self.__app.route("/view/<model_name>")
        def view(model_name):
            """Show model list from database.
            
            Model list is defined in DM_MODELS dictionary of this class.
            """
            model = self.DB_MODELS.get(model_name)
            if model is None:
                abort(404, description=f"Table {model_name} not found.")
            page = request.args.get("page", 1, type=int)
            per_page = request.args.get("per_page", 10, type=int)
            dbmanager = DBManager()
            filters = {
                "uuid": request.args.get("uuid"),
                "name": request.args.get("name"),
                "ip": request.args.get("ip")
            }
            data = dbmanager.get_paginated_data(model, page, per_page)
            data_count = dbmanager.get_data_count(model)
            total_pages = (data_count + per_page - 1) // per_page
            return render_template(
                f"{model_name}.html", model_name=model_name, data=data, 
                filters=filters,title="VMs", page=page, per_page=per_page,
                total_pages=total_pages
            )

        @self.__app.route("/ovirt/host_list")
        def ovirt_host_list():
            """Show host list."""
            file_handler = FileHandler()
            file_handler.get_group_data("hosts")
            return render_template(
                "ovirt_host_list.html",
                data=file_handler.file_data["hosts"]
            )

        @self.__app.route("/ovirt/cluster_list")
        def ovirt_cluster_list():
            """Show cluster list."""
            file_handler = FileHandler()
            file_handler.get_group_data("clusters")
            return render_template(
                "ovirt_cluster_list.html",
                data=file_handler.file_data["clusters"]
            )

        @self.__app.route("/ovirt/cluster_list/raw_json")
        def ovirt_cluster_raw_json():
            """Show cluster list (raw JSON)."""
            file_handler = FileHandler()
            file_handler.get_group_data("clusters")
            return jsonify(
                data=file_handler.file_data["clusters"]
            )

        @self.__app.route("/ovirt/storage_domain_list")
        def ovirt_storage_domain_list():
            """Show storage domain list."""
            file_handler = FileHandler()
            file_handler.get_group_data("storages")
            return render_template(
                "ovirt_storage_domain_list.html",
                data=file_handler.file_data["storages"]
            )

        @self.__app.route("/ovirt/data_center_list")
        def ovirt_data_center_list():
            """Show storage domain list."""
            file_handler = FileHandler()
            file_handler.get_group_data("data_centers")
            return render_template(
                "ovirt_data_center_list.html",
                data=file_handler.file_data["data_centers"]
            )

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
                    virt_aggregator = VirtAggregator()
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
                    virt_aggregator = VirtAggregator()
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

flask_aggregator = FlaskAggregator()
app = flask_aggregator.get_app()
