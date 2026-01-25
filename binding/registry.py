#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      EddyS
#
# Created:     28/07/2025
# Copyright:   (c) EddyS 2025
# Licence:     <your licence>
#-------------------------------------------------------------------------------

# binding/registry.py

class WidgetRegistry:
    def __init__(self):
        self.registered = {}

    def add(self, widget, name, events=None):
        self.registered[widget] = {
            "name": name,
            "events": events or []
        }

    def summary(self):
        print("\n📦 Registry Summary")
        for widget, info in self.registered.items():
            print(f"🔹 {info['name']}: {type(widget).__name__}")
            for evt in info["events"]:
                print(f"   ↪ {evt}")