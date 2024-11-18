"""OITI Flask http aggregator.

Used primarily for aggregating oVirt information.
"""

import json
import os
from urllib.parse import urlencode

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
            fields = self.DB_MODELS[model_name].get_columns_order()
            filters = { # TODO: make filters unique for each model
                "name": request.args.get("name"),
                "engine": request.args.get("engine")
            }
            data_count, data = dbmanager.get_paginated_data(
                model, page, per_page, filters
            )
            total_pages = (data_count + per_page - 1) // per_page

            def get_pagination_url(page: int) -> str:
                args = request.args.to_dict()
                args["page"] = page
                return f"/view/{model_name}?{urlencode(args)}"

            return render_template(
                "view.html", model_name=model_name, data=data,
                filters=filters, title=model_name, page=page,
                per_page=per_page, total_pages=total_pages,
                get_pagination_url=get_pagination_url, getattr=getattr,
                fields=fields
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
