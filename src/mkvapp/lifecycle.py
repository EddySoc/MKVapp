#-------------------------------------------------------------------------------
# Name:        lifecycle.py
# Purpose:      This module wires up shared services, menus,
#               bindings, and app shutdowns into neat, reusable functions
#
# Author:      EddyS
#
# Created:     28/06/2025
# Copyright:   (c) EddyS 2025
# Licence:     <your licence>
#-------------------------------------------------------------------------------

# mkvapp/lifecycle.py
import os
from shared_data import get_shared
from menus import popup
from binding import BindingManager
from utils.scan_helpers import fast_scandir


def setup_utils():
    shared_data.utils = utils  # Optional reference to shared utilities

def setup_pop_menu(app):
    shared_data.pop_menu = Popup(app)

def setup_binding_manager(app):
    shared_data.manager = BindingManager(app, shared_data.pop_menu)

def init_after_ui(app):
    update_on_start(app)

def update_on_start(app):
    s = get_shared()

    # Grab source path
    src_var = s.entry_data.get("source", {}).get("var")
    if not src_var:
        print("⚠️ No source variable found")
        return

    source_path = src_var.get()
    if not source_path or not os.path.exists(source_path):
        print(f"⚠️ Invalid source path: {source_path}")
        return

    fast_scandir(app,source_path)

