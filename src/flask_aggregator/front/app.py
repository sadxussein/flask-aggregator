"""OITI Flask http aggregator.

Used primarily for aggregating oVirt information.
"""

import json
import os
from urllib.parse import urlencode
import io

import pandas as pd
from flask import (
    Flask, request, render_template, jsonify, send_file
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
from flask_aggregator.back.models import Storage
# from flask_aggregator.back.controllers import DBController
from flask_aggregator.back.db import (
    DBRepositoryFactory, DBRepository, DBConnection
)
from flask_aggregator.back.view_object import ViewObjectFactory, ViewObject
from flask_aggregator.front.view import (
    TextField,
    DropDownField,
    UIContainer,
    SubmitButton,
    CheckBox,
    Table,
    TableRow,
    TableCell,
    LinkButton,
    LinkWrapper
)

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
            return render_template("header.html")

        @self.__app.route("/view/<model_name>")
        def view(model_name):
            # Set up connection and correct repository for database
            # interactions.
            db_con = DBConnection(DevelopmentConfig.DB_URL)
            repo_factory = DBRepositoryFactory()
            repo_factory.set_connection(db_con)
            repo = repo_factory.make_repo(model_name)
            # Get filters from frontend.
            filters = {}
            for fltr in repo.filter_fields:
                filters[fltr["name"]] = request.args.get(fltr["name"])
            # Pass filters to database backend.
            repo.add_filter(
                filters=filters,
                sort_by=request.args.get("sort_by", "name"),
                sort_order=request.args.get("order", "asc"),
                page=request.args.get("page", 1, type=int),
                per_page=request.args.get("per_page", 10, type=int)
            )
            # Make data from repository.
            raw_data, item_count = repo.build()
            raw_view_objects = [
                ViewObjectFactory.create_obj(obj, repo.col_order)
                for obj in raw_data
            ]
            data = [obj.to_dict() for obj in raw_view_objects]
            # Make pagination function, which is being passed to frontend.
            def get_pagination_url(page: int) -> str:
                args = request.args.to_dict()
                args["page"] = page
                return f"/view/{model_name}?{urlencode(args)}"
            # Make arguments from template frontend. They will be both passed
            # to database backend and circled back to frontend.
            page = request.args.get("page", 1, type=int)
            per_page = request.args.get("per_page", 10, type=int)
            show_dbs = request.args.get("show_dbs")
            show_absent_in_ov = request.args.get("show_absent_in_ov")
            kwargs = {
                "model_name": model_name,
                "filters": filters,
                "fields": repo.col_order,
                "page": page,
                "per_page": per_page,
                "sort_by": request.args.get("sort_by", "name"),
                "order": request.args.get("order", "asc"),
                "total_pages": (item_count + per_page - 1) // per_page,
                "total_items": item_count,
                "show_dbs": False if show_dbs is None else True,
                "show_absent_in_ov": (
                    False if show_absent_in_ov is None else True
                ),
                "get_pagination_url": get_pagination_url
            }

            # UI attempt.
            # Filter.
            filter_container = UIContainer(
                id_="filter-container",
                name="filter-container",
                tag="form"
            )
            for fltr in repo.filter_fields:
                if fltr["type"] == "text":
                    cur_val = request.args.get(fltr["name"])
                    filter_container.add_component(TextField(
                        id_=fltr["name"],
                        name=fltr["name"],
                        label=fltr["name"],
                        value=cur_val if cur_val else fltr["default_value"]
                    ))
                elif fltr["type"] == "option":
                    cur_option = request.args.get(fltr["name"])
                    print(cur_option)
                    filter_container.add_component(DropDownField(
                        id_=fltr["name"],
                        name=fltr["name"],
                        label=fltr["name"],
                        items=fltr["options"],
                        cur_option=cur_option if cur_option else ''
                    ))
                if fltr["type"] == "check":
                    cur_state = request.args.get(fltr["name"])
                    filter_container.add_component(CheckBox(
                        id_=fltr["name"],
                        name=fltr["name"],
                        label=fltr["name"],
                        checked=True if cur_state else False
                    ))
            filter_container.add_component(SubmitButton(name="Search"))
            # Table.
            table_container = UIContainer(
                id_="table-container",
                name="table-container"
            )
            table = Table(
                id_="table-view",
                name="table-view"
            )
            table_header_container = UIContainer(tag="thead")
            table_body_container = UIContainer(tag="tbody")
            table_container.add_component(table)
            table.add_component(table_header_container)
            table.add_component(table_body_container)
            table_header = TableRow()
            for k in repo.col_order:
                table_header.add_component(TableCell(
                    k,
                    is_header=True,
                    id_=k,
                    class_="table-clickable-header"
                ))
            table_header_container.add_component(table_header)
            for row in data:
                table_row = TableRow()
                for k, v in row.items():
                    if k == "href":
                        table_row.add_component(TableCell(
                            "ovirt engine link",
                            link=v
                        ))
                    else:
                        table_row.add_component(TableCell(v))
                table_body_container.add_component(table_row)
            layout = UIContainer(
                id_="view",
                name="view"
            )
            view_footer_container = UIContainer(class_="view-footer-container")
            download_btn = LinkButton(
                label="Download as CSV",
                href=f"/download/{model_name}"
            )
            view_footer_container.add_component(download_btn)
            layout.add_component(filter_container)
            layout.add_component(table_container)
            layout.add_component(view_footer_container)

            return render_template(
                "test.html",
                layout=layout,
                **kwargs
            )

        @self.__app.route("/download/<model_name>")
        def view_csv(model_name):
            """Get file from frontend."""
            db_con = DBConnection(DevelopmentConfig.DB_URL)
            repo_factory = DBRepositoryFactory()
            repo_factory.set_connection(db_con)
            repo = repo_factory.make_repo(model_name)
            # Make data from repository.
            raw_data, _ = repo.build()
            raw_view_objects = [
                ViewObjectFactory.create_obj(obj, repo.col_order)
                for obj in raw_data
            ]
            data = [obj.to_dict() for obj in raw_view_objects]
            # Saving as .csv file.
            df = pd.DataFrame(data)
            memory_output = io.BytesIO()
            df.to_csv(memory_output, index=False, encoding="utf-8-sig")
            memory_output.seek(0)
            return send_file(
                memory_output,
                mimetype="text/csv",
                as_attachment=True,
                download_name=f"{model_name}.csv"
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
