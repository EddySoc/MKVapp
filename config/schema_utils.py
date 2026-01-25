#-------------------------------------------------------------------------------
# Name:        schema_utils.py
# Purpose:
#
# Author:      EddyS
#
# Created:     28/06/2025
# Copyright:   (c) EddyS 2025
# Licence:     <your licence>
#-------------------------------------------------------------------------------

# schema_utils.py

def validate_config_section(config, required_keys):
    """
    Validates a config dictionary section contains all required keys.
    Args:
        config (dict): The section of the config to validate.
        required_keys (list or set): Keys that must exist in config.
    Returns:
        bool: True if all keys are present, False otherwise.
        list: Missing keys (if any)
    """
    missing = [k for k in required_keys if k not in config]
    return not missing, missing

def get_nested_section(config, path):
    """Safely traverse nested config using dot-paths like 'API_cfg.opensubtitles'"""
    keys = path.split(".")
    section = config
    for key in keys:
        if isinstance(section, dict) and key in section:
            section = section[key]
        else:
            return None
    return section

def assert_valid_schema(config_data, schema_map):
    all_valid = True
    for section_path, expected_keys in schema_map.items():
        section_data = get_nested_section(config_data, section_path)
        if section_data is None:
            print(f"❌ Section '{section_path}' is missing entirely.")
            all_valid = False
            continue

        valid, missing = validate_config_section(section_data, expected_keys)
        if not valid:
            print(f"❌ Missing in '{section_path}': {missing}")
            all_valid = False

        return all_valid