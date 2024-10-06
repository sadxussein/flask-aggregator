"""OITI Flask http aggregator.

Used primarily for aggregating oVirt information.
"""

import json

from flask import Flask, render_template

app = Flask(__name__)

def load_json():
    """Return JSON file data."""
    with open("../back/files/vm_list.json", 'r', encoding="utf-8") as file:
        data = json.load(file)
    return data

@app.route("/ovirt_vms")
def index():
    """Show VM list."""
    vms = load_json()
    return render_template("ovirt_vms.html", data=vms)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port="80", debug=True)
