"""Test module."""

import os

from .parser import Parser
from . import config as cfg

if __name__ == "__main__":
    parser = Parser()
    for root, dirs, files in os.walk(cfg.EXCEL_FILES_FOLDER):
        excel_files = [f for f in files if f.endswith(".xlsx")]
        for file in excel_files:
            parser.prepare_vm_environment(
                f"{cfg.EXCEL_FILES_FOLDER}/{file}"
            )
