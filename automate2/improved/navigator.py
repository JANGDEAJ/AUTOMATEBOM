"""
navigator.py - App Grid navigation helpers
"""

from config import SEL_APP_DRAWER, APP_ALIASES, DASHBOARD_URL


def open_app(page, app_name: str) -> bool:
    """
    Click the top-left 4-dots icon and look for app_name (or its aliases) in
    the App Grid. Returns True if found + visible, False otherwise.
    Also navigates to the app if found.
    """
    try:
        # Back to dashboard first to ensure App Drawer icon is present
        if DASHBOARD_URL not in page.url:
            page.goto(DASHBOARD_URL, wait_until="domcontentloaded")
            page.wait_for_timeout(1500)

        # Click 4-dots app drawer
        drawer = page.locator(SEL_APP_DRAWER).first
        if not drawer.is_visible(timeout=5000):
            return False
        drawer.click()
        page.wait_for_timeout(2000)

        # Search aliases (most specific first)
        aliases = APP_ALIASES.get(app_name, [app_name])
        for alias in aliases:
            loc = page.get_by_text(alias, exact=True)
            for i in range(loc.count()):
                elem = loc.nth(i)
                if elem.is_visible():
                    try:
                        elem.click()
                        page.wait_for_timeout(1500)
                    except Exception:
                        pass
                    return True
        return False

    except Exception:
        return False


def is_app_visible(page, app_name: str) -> bool:
    """
    Check if app_name (or aliases) exists and is visible in current page state.
    Does NOT click anything. Used for negative (hidden) checks.
    """
    aliases = APP_ALIASES.get(app_name, [app_name])
    for alias in aliases:
        loc = page.get_by_text(alias, exact=True)
        for i in range(loc.count()):
            if loc.nth(i).is_visible():
                return True
    return False
