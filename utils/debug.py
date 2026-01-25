#-------------------------------------------------------------------------------
# Name:        debug.py
# Purpose:
#
# Author:      EddyS
#
# Created:     08/07/2025
# Copyright:   (c) EddyS 2025
# Licence:     <your licence>
#-------------------------------------------------------------------------------

from utils.debug_helpers import track_event as track
from widgets.debug_console import debug_print as show

__all__ = ["track", "show"]