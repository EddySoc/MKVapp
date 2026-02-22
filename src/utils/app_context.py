#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      EddyS
#
# Created:     09/07/2025
# Copyright:   (c) EddyS 2025
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import customtkinter as ct
import queue

class AppContext:
    def __init__(self):
        self.root = ct.CTk()
        self.gui_queue = queue.Queue()
        self.config = None
        self.theme = None
        self.localization = None
        self.session_id = None
        self._debug_console = None  # Lazy-loaded

    @property
    def debug_console(self):
        if self._debug_console is None:
            from widgets.debug_console import DebugConsole  # Lazy import
            self._debug_console = DebugConsole(master=self.root)
        return self._debug_console

ctx = AppContext()