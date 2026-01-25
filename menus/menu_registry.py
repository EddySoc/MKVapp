#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      EddyS
#
# Created:     01/09/2025
# Copyright:   (c) EddyS 2025
# Licence:     <your licence>
#-------------------------------------------------------------------------------

# project_root/actions/menu_registry.py
class MenuRegistry:
    """
    Central registry for menu actions.

    Supports:
    - Registering functions with tags, symbols, groups
    - Grouped and hierarchical summaries
    - Tree-based visualization of nested menu structure

    Eddy, this is now flexible enough to auto-generate GUI menus or CLI trees.
    """

    _instance = None  # Singleton instance

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_internal()
        return cls._instance

    def _init_internal(self):
        self._registry = {}         # label → entry
        self._tag_groups = {}       # group → [labels]
        self._func_labels = set()   # (id(func), tag) to prevent duplicates
        self._action_cache = {}

    def register(self, func, tag, symbol="", group="default", label=None, icon=None):
        """
        Registers a function with metadata.
        - tag: internal identifier (e.g. module path or category)
        - label: display name (e.g. '🧹 Purge Files')
        - symbol: semantic grouping (e.g. 'subtitles', 'videos')
        """

        # Auto-generate label if not provided
        label = label or f"{symbol} {tag}".strip()

        # Use (func ID, tag, group) as deduplication key to allow same func in multiple groups
        key = (id(func), tag, group)
        if key in self._func_labels:
            # Already registered in this specific group
            return

        self._func_labels.add(key)

        # Build registry entry
        entry = {
            "func": func,
            "tag": tag,           # Internal identifier
            "symbol": symbol,     # Semantic category
            "group": group,       # UI grouping
            "icon": icon          # optional icon
        }

        # Store entry under display label (only once globally)
        if label not in self._registry:
            self._registry[label] = entry

        # Group labels under tag group - allow same label in multiple groups
        if label not in self._tag_groups.setdefault(group, []):
            self._tag_groups[group].append(label)

    def get(self, label):
        return self._registry.get(label)

    def all(self):
        return self._registry

    def get_group(self, name):
        return self._registry.get(name, [])

    def grouped(self):
        return self._tag_groups

    def get_menu_items(self, menu_name):
        return self._tag_groups.get(menu_name, [])

    def build_menu_tree(self):
        tree = {}
        for label, entry in self._registry.items():
            path = entry["group"].split("/")
            current = tree
            for part in path:
                current = current.setdefault(part, {})
            current[label] = entry  # Store full entry instead of just func name
        return tree

    def print_tree(self, tree=None, indent=0):
        """
        Recursively prints the menu tree.
        """
        if tree is None:
            tree = self.build_menu_tree()
        for key, value in tree.items():
            if isinstance(value, dict):
                print(" " * indent + f"{key}/")
                self.print_tree(value, indent + 4)
            else:
                print(" " * indent + f"• {key} → {value}")

    def summary(self, view="tree"):
        """
        Prints a summary of the registry.
        Use view='flat' for grouped list, or 'tree' for nested structure.
        """
        print("📋 Menu Registry Summary:")
        if view == "flat":
            for group, labels in self._tag_groups.items():
                print(f" - {group}:")
                for label in labels:
                    func = self._registry[label]["func"]
                    print(f"    • {label} → {func.__name__}")
        else:
            tree = self.build_menu_tree()
            self.print_tree(tree)

    def get_keys(self):
        return list(self._registry.keys())

    def get_entries_by_group(self, group_name):
        return [
            self._registry[label]
            for label in self._tag_groups.get(group_name, [])
            if label in self._registry
        ]

    def build_action_registry(self, menu_name):
        if menu_name in self._action_cache:
            return self._action_cache[menu_name]
        actions = {
            entry["func"].__name__: entry["func"]
            for entry in self.get_entries_by_group(menu_name)
        }
        self._action_cache[menu_name] = actions
        return actions

    def get_func_by_label(self, label):
        entry = self._registry.get(label)
        return entry["func"] if entry else None

    def summary_dict(self):
        return {
            group: [
                {
                    "label": label,
                    "func": self._registry[label]["func"].__name__,
                    "icon": self._registry[label].get("icon")
                }
                for label in labels
            ]
            for group, labels in self._tag_groups.items()
        }

    def discover_shared_groups(self, keywords=("shared", "common", "global", "utils")):
        """
        Auto-discovers menu groups that likely contain shared or reusable actions.
        Filters by group name or label patterns.
        """
        discovered = set()

        for group, labels in self._tag_groups.items():
            # Match group name directly
            if any(kw in group.lower() for kw in keywords):
                discovered.add(group)
                continue

            # Match label patterns (e.g. clear_textbox, reset_form)
            for label in labels:
                if label.lower().startswith(("clear", "reset", "sanitize", "normalize")):
                    discovered.add(group)
                    break

        return list(discovered)

# Global access point
global_menu_registry = MenuRegistry()