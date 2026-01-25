#-------------------------------------------------------------------------------
# Name:        logger_sigleton.py
# Purpose:
#
# Author:      EddyS
#
# Created:     28/06/2025
# Copyright:   (c) EddyS 2025
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import logging
import sys

# Optional: control this with an ENV or config if needed
LOG_LEVEL = logging.INFO  # Can be DEBUG, WARNING, ERROR

logger = logging.getLogger("mkvapp")

if not logger.hasHandlers():
    logger.setLevel(LOG_LEVEL)
    handler = logging.StreamHandler(sys.stdout)

    formatter = logging.Formatter(
        fmt="🌀 [%(asctime)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S"
    )

    handler.setFormatter(formatter)
    logger.addHandler(handler)