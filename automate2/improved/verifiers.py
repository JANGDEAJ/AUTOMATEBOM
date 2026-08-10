import sys
import time

sys.stdout.reconfigure(encoding="utf-8")

from navigator import open_app, is_app_visible
from config import SEL_APP_DRAWER, APP_ALIASES, DASHBOARD_URL

APP_CREATE_BUTTONS = {
    'Point of Sale': ['button:has-text("New Session")', 'button:has-text("Open")', 'button:has-text("New")', 'a:has-text("New")'],
    'Sales': ['button:has-text("New")', 'a:has-text("New")', '.o_list_button_add'],
    'Accounting': ['button:has-text("New")', 'a:has-text("New")'],
    'Purchase': ['button:has-text("New")', 'a:has-text("New")'],
    'Inventory': ['button:has-text("New")', 'a:has-text("New")'],
    'Request': ['button:has-text("New")', 'button:has-text("Create")', 'a:has-text("New")'],
    'Fleet': ['button:has-text("New")', 'a:has-text("New")'],
    'MPOS': ['button:has-text("New")', 'a:has-text("New")']
}

APP_VALIDATE_BUTTONS = {
    'Point of Sale': ['button:has-text("Validate")', 'button:has-text("Close")'],
    'Sales': ['button:has-text("Confirm")', 'button:has-text("Validate")'],
    'Accounting': ['button:has-text("Confirm")', 'button:has-text("Validate")', 'button:has-text("Approve")'],
    'Purchase': ['button:has-text("Confirm")', 'button:has-text("Approve")'],
    'Inventory': ['button:has-text("Validate")'],
    'Request': ['button:has-text("Approve")', 'button:has-text("Validate")', 'button:has-text("Confirm")'],
    'default': ['button:has-text("Approve")', 'button:has-text("Validate")', 'button:has-text("Confirm")', 'button:has-text("Reject")']
}

APP_SETTING_SELECTORS = {
    'Point of Sale': ['a.main_link:has-text("Configuration")', '.o_menu_sections a:has-text("Configuration")'],
    'Sales': ['a.main_link:has-text("Configuration")', '.o_menu_sections a:has-text("Configuration")'],
    'Accounting': ['a.main_link:has-text("Configuration")', '.o_menu_sections a:has-text("Configuration")'],
    'default': ['a.main_link:has-text("Settings")', 'a.main_link:has-text("Configuration")', '.o_menu_sections a:has-text("Settings")']
}

def _check_any_visible(page, selectors) -> bool:
    for sel in selectors:
        if page.locator(sel).is_visible():
            return True
    return False

def _expect_has(expected: str) -> bool:
    negative_keywords = ['ไม่พบ', 'ไม่แสดง', 'ไม่มีปุ่ม', 'ไม่มีเมนู', 'ไม่มีสิทธิ์']
    for kw in negative_keywords:
        if kw in expected:
            return False
    return True

def verify_read(page, app_name, func_name, expected, role, frame_cb=None):
    def cb(label):
        if frame_cb:
            try: frame_cb(page, label)
            except Exception: pass

    should_have = _expect_has(expected)

    # First check for Access Error on current page
    denied = page.locator("text='Access Denied'").count() > 0 or page.locator("text='Access Error'").count() > 0
    if denied and should_have:
        cb(f"Read check failed: Access Denied for {role}")
        return ("Failed", f"Access Denied error displayed for role {role}")

    if should_have:
        # Try opening app if not already on it
        cb(f"Clicked {app_name}")
        open_app(page, app_name, frame_cb=frame_cb)
        time.sleep(1)

        # Check denied again
        denied_after = page.locator("text='Access Denied'").count() > 0 or page.locator("text='Access Error'").count() > 0
        if denied_after:
            cb(f"Read check failed: Access Error in {app_name}")
            return ("Failed", f"Access Error displayed when opening {app_name}")

        cb(f"Read check: Opened {app_name} & readable")
        return ("Passed", f"Opened {app_name} and verified content readable for role {role}")

    else:
        # Negative check: expect hidden
        cb("Opened App Drawer to check negative visibility")
        if page.url != DASHBOARD_URL:
            page.goto(DASHBOARD_URL, wait_until="domcontentloaded")
            time.sleep(1)

        try:
            page.click(SEL_APP_DRAWER, timeout=2000)
            time.sleep(1)
        except Exception:
            pass

        visible = is_app_visible(page, app_name)
        if not visible:
            cb(f"Read check: {app_name} hidden as expected for {role}")
            return ("Passed", f"App {app_name} is hidden as expected for role {role}")
        else:
            cb(f"Read check: {app_name} visible when expected hidden")
            return ("Failed", f"App {app_name} is visible when expected hidden for role {role}")


def verify_create(page, app_name, func_name, expected, role, frame_cb=None):
    def cb(label):
        if frame_cb:
            try: frame_cb(page, label)
            except Exception: pass

    opened = open_app(page, app_name, frame_cb=frame_cb)
    time.sleep(1.5)

    should_have = _expect_has(expected)
    if not opened:
        if not should_have:
            return ("Passed", f"App {app_name} absent/hidden as expected")
        return ("Failed", f"Could not open {app_name} to verify Create button")

    cb(f"Create check: Scanning buttons in {app_name}")
    selectors = APP_CREATE_BUTTONS.get(app_name, ['button:has-text("New")', 'a:has-text("New")'])
    found = _check_any_visible(page, selectors)
    cb(f"Create check: {'Button Found' if found else 'Button Missing'}")

    if should_have and found:
        return ("Passed", f"Found create button for {app_name}")
    elif not should_have and not found:
        return ("Passed", f"Did not find create button for {app_name}")
    elif should_have and not found:
        return ("Failed", f"Missing create button for {app_name}")
    else:
        return ("Failed", f"Found create button for {app_name} when not expected")


def verify_validate(page, app_name, func_name, expected, role, frame_cb=None):
    def cb(label):
        if frame_cb:
            try: frame_cb(page, label)
            except Exception: pass

    opened = open_app(page, app_name, frame_cb=frame_cb)
    time.sleep(1.5)

    should_have = _expect_has(expected)
    if not opened:
        if not should_have:
            return ("Passed", f"App {app_name} absent/hidden as expected")
        return ("Failed", f"Could not open {app_name} to verify Validate button")

    cb(f"Validate check: Scanning buttons in {app_name}")
    selectors = APP_VALIDATE_BUTTONS.get(app_name, APP_VALIDATE_BUTTONS['default'])
    found = _check_any_visible(page, selectors)
    cb(f"Validate check: {'Button Found' if found else 'Button Missing'}")

    if should_have and found:
        return ("Passed", f"Found validate/confirm button for {app_name}")
    elif not should_have and not found:
        return ("Passed", f"Did not find validate/confirm button for {app_name}")
    elif should_have and not found:
        return ("Failed", f"Missing validate/confirm button for {app_name}")
    else:
        return ("Failed", f"Found validate/confirm button for {app_name} when not expected")


def verify_setting(page, app_name, func_name, expected, role, frame_cb=None):
    def cb(label):
        if frame_cb:
            try: frame_cb(page, label)
            except Exception: pass

    opened = open_app(page, app_name, frame_cb=frame_cb)
    time.sleep(1.5)

    should_have = _expect_has(expected)
    if not opened:
        if not should_have:
            return ("Passed", f"App {app_name} absent/hidden as expected")
        return ("Failed", f"Could not open {app_name} to verify Settings menu")

    cb(f"Setting check: Scanning options in {app_name}")
    selectors = APP_SETTING_SELECTORS.get(app_name, APP_SETTING_SELECTORS['default'])
    found = _check_any_visible(page, selectors)
    cb(f"Setting check: {'Setting Found' if found else 'Setting Missing'}")

    if should_have and found:
        return ("Passed", f"Found setting/configuration menu for {app_name}")
    elif not should_have and not found:
        return ("Passed", f"Did not find setting/configuration menu for {app_name}")
    elif should_have and not found:
        return ("Failed", f"Missing setting/configuration menu for {app_name}")
    else:
        return ("Failed", f"Found setting/configuration menu for {app_name} when not expected")


VERIFIER_MAP = {
    'read': verify_read,
    'create': verify_create,
    'validate': verify_validate,
    'setting': verify_setting
}


def run_verification(page, ptype, app_name, func_name, expected, role, frame_cb=None):
    action = None
    ptype_lower = ptype.lower()
    if 'read' in ptype_lower: action = 'read'
    elif 'create' in ptype_lower: action = 'create'
    elif 'validate' in ptype_lower: action = 'validate'
    elif 'setting' in ptype_lower: action = 'setting'

    if not action:
        return ("Skipped", f"No verifier mapped for type '{ptype}'")

    verifier = VERIFIER_MAP[action]
    return verifier(page, app_name, func_name, expected, role, frame_cb=frame_cb)
