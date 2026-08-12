"""
utils.py - Shared utility functions for BOM UAT Automation
"""

import time


def live_wait(page, cb, seconds: float, label: str):
    """
    Sleep for `seconds` while continuously streaming live frames every 250ms.
    """
    t_end = time.time() + seconds
    while time.time() < t_end:
        cb(label)
        time.sleep(0.25)
