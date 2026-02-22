#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      EddyS
#
# Created:     24/08/2025
# Copyright:   (c) EddyS 2025
# Licence:     <your licence>
#-------------------------------------------------------------------------------
# This module replaces legacy config_mgr.data access.
# Use get_config_value() or config_mgr.data instead of direct dictionary access.

from config.smart_config_manager import config_mgr
import logging


def get_config():
    config_mgr = get_config_manager()
    from shared_data import get_shared
    shared = get_shared()
    shared.config_manager = config_mgr
    return config_mgr

def config_mgr_data():
    """Returns the full config dictionary (legacy config_mgr.data replacement)."""
    return get_config_manager().get_all()

def get_config_value(section, key=None, default=None):
    """Access a specific config value."""
    return config_mgr.get(section, key, default)

def get_config_value(section, key=None, default=None):
    value = get_config().get(section, key, default)
    logging.debug(f"Config access: [{section}][{key}] → {value}")
    return value