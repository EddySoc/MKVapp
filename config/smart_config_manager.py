#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      EddyS
#
# Created:     23/08/2025
# Copyright:   (c) EddyS 2025
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import json, threading, time
from pathlib import Path
from logger_singleton import logger
from utils.settings_helpers import WatchedDict
from config.schema_utils import assert_valid_schema

class SmartConfigManager:
    def __init__(self, config_dir="Settings", schema_map=None, debug=False,shared=None):
        self.config_dir = Path(__file__).resolve().parent.parent / config_dir
        self.config_dir.mkdir(exist_ok=True)
        self.schema_map = schema_map or {}
        self.debug = debug
        self.data = {}
        self.bound_vars = {}
        self._loading = False
        self.shared = shared
        self.load_count = 0  # 👈 Counter
        self._already_loaded = False
        self._load_all(shared=shared)


    def bind_var(self, var, key, section="persistent_cfg"):
        """whatever var changes,it is updates and saved"""
        if not hasattr(var, "trace_add"):
            raise TypeError(f"Expected a Tkinter variable, got {type(var)}")
        def on_change(*_):
            section_data = self.data.setdefault(section, {})
            section_data[key] = var.get()
            self.save(section)
        var.trace_add("write", on_change)

    def _load_all(self, shared=None):
        if getattr(self, "_already_loaded", False):
            #print("⏭️ _load_all skipped (already loaded)")
            return
        self._already_loaded = True
        self.load_count += 1
        #print(f"🔁 _load_all called {self.load_count} time(s)")

        try:
            from config.sync_utils import sync_config_to_state
            for file in self.config_dir.glob("*.json"):
                section = file.stem
                try:
                    with open(file, "r", encoding="utf-8") as f:
                        raw = json.load(f)
                    if section in self.schema_map:
                        assert_valid_schema({section: raw}, {section: self.schema_map[section]})
                    self.data[section] = WatchedDict(
                        raw,
                        on_change=lambda k, v, s=section: self._on_change(s, k, v)
                    )
                    if self.debug:
                        #print(f"✅ Loaded {section}")
                        pass

                except Exception as e:
                    logger.error(f"❌ Failed to load {file.name}: {e}")

        finally:
            self._loading = False

    def load_config(self):
        self._load_all()

    def _on_change(self, section, key, value):
        self.save(section)
        self.reload(msg=f"🔄 {section}[{key}] → {value}")

    def reload(self, msg=None):
        try:
            self._load_all(shared=self.shared)
            if msg:
                from utils import log_settings
                log_settings(msg)
                log_settings(f"✅ Config reload successful: {len(self.data)} sections loaded.")
        except Exception as e:
            from utils import log_settings
            log_settings(f"❌ Config reload failed: {e}", tag="rood")

    def save(self, section):
        path = self.config_dir / f"{section}.json"
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.data[section], f, indent=2)
            #logger.info(f"💾 Saved {section} to {path}")
        except Exception as e:
            logger.error(f"❌ Failed to save {section}: {e}")

    def get(self, section_or_key, key=None, default=None):
        if isinstance(key, dict) and default is None:
            # Assume the user meant to pass default, not key
            default = key
            key = None

        result = None

        if key is None:
            if section_or_key in self.bound_vars:
                result = self.bound_vars[section_or_key].get()
            else:
                result = self.data.get("persistent_cfg", {}).get(section_or_key, default)
        else:
            section_data = self.data.get(section_or_key)
            if section_data is None:
                logger.warning(f"⚠️ Missing section: {section_or_key}")
                return default
            result = section_data.get(key, default)

        # Ensure result is not None if default is a dict
        if result is None and isinstance(default, dict):
            return default

        return result

    def get_all(self):
        """Return a copy of all configuration data."""
        return {section: dict(data) for section, data in self.data.items()}

    def set(self, section, key, value):
        if section not in self.data:
            self.data[section] = WatchedDict({}, on_change=lambda k, v: self._on_change(section, k, v))
        self.data[section][key] = value

    def enable_auto_reload(self, interval=10):
        def watch():
            while True:
                self._load_all()
                time.sleep(interval)
        threading.Thread(target=watch, daemon=True).start()

    # Static schema definition
    schema_map = {
        "persistent_cfg": {
            "Font_family": str,
            "Font_size": int,
            "Theme": str
        },
        "API_cfg": {
            "opensubtitles": {
                "api_key": str
            }
        }
    }

    def get_schema(self):
        return self.schema_map

# Internal singleton reference
_config_instance = None

def get_config_manager(schema_map=None, debug=False, shared=None):
    """
    Returns a singleton instance of SmartConfigManager.
    Ensures consistent config access across the app.
    """
    global _config_instance
    if _config_instance is None:
        schema = schema_map or SmartConfigManager.schema_map
        _config_instance = SmartConfigManager(schema_map=schema, debug=debug, shared=shared)
    return _config_instance

# ✅ Public popup_key for direct access
config_mgr = get_config_manager(debug=True)

def get_config_mgr():
    global _config_mgr
    if _config_mgr is None:
        _config_mgr = get_config_manager()
    return _config_mgr

def get_config_data():
    return config_mgr.data
