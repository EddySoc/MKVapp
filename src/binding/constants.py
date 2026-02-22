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

# binding/constants.py

import customtkinter as ct
from CTkListbox import CTkListbox
from widgets import BaseTBox

INTERACTIVE_WIDGETS = (
    ct.CTkEntry,
    ct.CTkTextbox,
    CTkListbox,
    BaseTBox
)

SKIP_CLASSES = ["Frame", "PanedWindow", "Canvas"]