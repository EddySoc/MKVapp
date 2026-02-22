#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      EddyS
#
# Created:     06/07/2025
# Copyright:   (c) EddyS 2025
# Licence:     <your licence>
#------------------------------------------------------------------------------

def sync_config_to_state(data, config_mgr, shared=None):
    from shared_data import get_shared
    if config_mgr is None:
        raise ValueError("config_mgr must be provided to avoid recursion")
    s = shared if shared else get_shared()
    mapping = config_mgr.get("sync_cfg", {})

    for cfg_key, var_name in mapping.items():
        value = config_mgr.get("persistent_cfg", cfg_key)
        var = getattr(s, var_name, None)
        if var and value is not None:
            try:
                var.set(value)
                print(f"🔄 Loaded {cfg_key} → {var_name} = {value}")
            except Exception as e:
                print(f"⚠️ Failed to set {var_name}: {e}")

def sync_state_to_config(config_data=None):
    from shared_data import get_shared
    s = get_shared()
    mapping = config_mgr.get("sync_cfg", {})

    for cfg_key, var_name in mapping.items():
        var = getattr(s, var_name, None)
        if var:
            try:
                value = var.get()
                get_config_manager().set("persistent_cfg", cfg_key, value)
                #print(f"💾 Saved {var_name} → {cfg_key} = {value}")
            except Exception as e:
                print(f"⚠️ Failed to save {var_name}: {e}")