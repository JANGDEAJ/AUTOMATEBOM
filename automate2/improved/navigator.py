"""
navigator.py - App Grid navigation helpers with continuous live streaming
"""

import time
from config import SEL_APP_DRAWER, APP_ALIASES, DASHBOARD_URL
from utils import live_wait





def open_app(page, app_name: str, frame_cb=None) -> bool:
    """
    Click the app icon in App Grid (direct or via App Drawer) and wait for app to load.
    Returns True if app icon was found and clicked, False otherwise.
    """
    def cb(label):
        if frame_cb:
            try: frame_cb(page, label)
            except Exception: pass

    try:
        base_url = page.url.split("?")[0].split("#")[0].rstrip("/")
        target_base = DASHBOARD_URL.rstrip("/")
        if base_url != target_base:
            cb("Open browser home page")
            page.goto(DASHBOARD_URL, wait_until="domcontentloaded")
            live_wait(page, cb, 1.0, "Open browser home page")

        aliases = APP_ALIASES.get(app_name, [app_name])

        # 1. Look for app icon directly on current dashboard page
        clicked = False
        for alias in aliases:
            # Try exact match first, then partial match
            for exact in [True, False]:
                loc = page.get_by_text(alias, exact=exact)
                for i in range(loc.count()):
                    elem = loc.nth(i)
                    if elem.is_visible():
                        cb(f"Clicking app icon '{alias}'")
                        elem.click()
                        live_wait(page, cb, 2.5, f"Opening {alias}...")
                        cb(f"Opened {alias}")
                        clicked = True
                        break
                if clicked:
                    break
            if clicked:
                break

        # 2. If not found directly on page, open App Drawer and search again
        if not clicked:
            drawer = page.locator(SEL_APP_DRAWER).first
            if drawer.is_visible(timeout=2000):
                cb("Opened App Drawer")
                drawer.click()
                live_wait(page, cb, 1.0, "Opened App Drawer")

                for alias in aliases:
                    for exact in [True, False]:
                        loc = page.get_by_text(alias, exact=exact)
                        for i in range(loc.count()):
                            elem = loc.nth(i)
                            if elem.is_visible():
                                cb(f"Clicking app icon '{alias}'")
                                elem.click()
                                live_wait(page, cb, 2.5, f"Opening {alias}...")
                                cb(f"Opened {alias}")
                                clicked = True
                                break
                        if clicked:
                            break
                    if clicked:
                        break

        return clicked

    except Exception:
        return False


def is_app_visible(page, app_name: str) -> bool:
    aliases = APP_ALIASES.get(app_name, [app_name])
    for alias in aliases:
        loc = page.get_by_text(alias, exact=True)
        for i in range(loc.count()):
            if loc.nth(i).is_visible():
                return True
    return False


def navigate_submenus(page, menu_path: list[list[str]], frame_cb=None) -> bool:
    """
    Navigate through a sequence of sub-menus (each item in menu_path is a list of text aliases).
    Example: menu_path = [['Customers', 'ลูกค้า'], ['Credit Notes', 'ใบลดหนี้']]
    Returns True if all menus in path were found and clicked, False otherwise.
    """
    def cb(label):
        if frame_cb:
            try: frame_cb(page, label)
            except Exception: pass

    for step_aliases in menu_path:
        clicked = False
        for alias in step_aliases:
            loc = page.get_by_text(alias)
            for i in range(loc.count()):
                elem = loc.nth(i)
                try:
                    if elem.is_visible():
                        cb(f"Clicking menu '{alias}'")
                        elem.click()
                        live_wait(page, cb, 1.5, f"Clicked {alias}")
                        clicked = True
                        break
                except Exception:
                    pass
            if clicked:
                break
        if not clicked:
            cb(f"Menu step failed: None of {step_aliases} found/visible")
            return False
    return True

