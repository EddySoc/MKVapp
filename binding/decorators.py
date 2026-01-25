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

# binding/decorators.py

registered_bindables = []

def bindable(name=None, events=None):
    """
    Decorator to register a widget class with a custom name and event bindings.
    """
    def wrapper(cls):
        registered_bindables.append((cls, name, events or []))
        return cls
    return wrapper