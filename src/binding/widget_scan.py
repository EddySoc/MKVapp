#-------------------------------------------------------------------------------
# Name:        widget_scan.py
# Purpose:
#
# Author:      EddyS
#
# Created:     28/06/2025
# Copyright:   (c) EddyS 2025
# Licence:     <your licence>
#-------------------------------------------------------------------------------

# binding/widget_scan.py

def get_all_children(widget):
    """
    Recursively retrieve all child widgets from a given widget.
    """
    children = widget.winfo_children()
    all_children = []

    for child in children:
        all_children.append(child)
        # Dive deeper recursively
        all_children.extend(get_all_children(child))

    return all_children