"""
navigator.py - App Grid navigation helpers with simple audit logging
"""

from config import SEL_APP_DRAWER, APP_ALIASES, DASHBOARD_URL


def open_app(page, app_name: str, frame_cb=None) -> bool:
    """
    Click the top-left 4-dots icon and look for app_name in App Grid.
    """
    def cb(label):
        if frame_cb:
            try: frame_cb(page, label)
            except Exception: pass

    try:
        if DASHBOARD_URL not in page.url:
            cb("Open browser home page")
            page.goto(DASHBOARD_URL, wait_until="domcontentloaded")
            page.wait_for_timeout(1000)

        drawer = page.locator(SEL_APP_DRAWER).first
        if not drawer.is_visible(timeout=5000):
            return False
        cb("Opened App Drawer")
        drawer.click()
        page.wait_for_timeout(1500)

        aliases = APP_ALIASES.get(app_name, [app_name])
        for alias in aliases:
            loc = page.get_by_text(alias, exact=True)
            for i in range(loc.count()):
                elem = loc.nth(i)
                if elem.is_visible():
                    try:
                        cb(f"Clicked {alias}")
                        elem.click()
                        page.wait_for_timeout(1500)
                        cb(f"Opened {alias}")
                    except Exception:
                        pass
                    return True
        return False

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
