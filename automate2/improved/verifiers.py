"""
verifiers.py - Verification engines for Read, Create, Validate, and Setting permissions
"""

import sys
import time

sys.stdout.reconfigure(encoding="utf-8")

from navigator import open_app, is_app_visible
from config import SEL_APP_DRAWER, APP_ALIASES, DASHBOARD_URL

APP_CREATE_BUTTONS = {
    'Point of Sale': ['button:has-text("New Session")', 'button:has-text("เปิดเซสชัน")', 'button:has-text("Open")', 'button:has-text("New")', 'button:has-text("สร้าง")', 'a:has-text("New")', '.o_list_button_add'],
    'Sales': ['button:has-text("New")', 'button:has-text("สร้าง")', 'a:has-text("New")', 'a:has-text("สร้าง")', '.o_list_button_add'],
    'Accounting': ['button:has-text("New")', 'button:has-text("สร้าง")', 'a:has-text("New")', '.o_list_button_add'],
    'Purchase': ['button:has-text("New")', 'button:has-text("สร้าง")', 'a:has-text("New")', '.o_list_button_add'],
    'Inventory': ['button:has-text("New")', 'button:has-text("สร้าง")', 'a:has-text("New")', '.o_list_button_add'],
    'Request': ['button:has-text("New")', 'button:has-text("สร้าง")', 'button:has-text("Create")', 'a:has-text("New")'],
    'Fleet': ['button:has-text("New")', 'button:has-text("สร้าง")', 'a:has-text("New")'],
    'MPOS': ['button:has-text("New")', 'button:has-text("สร้าง")', 'a:has-text("New")'],
    'default': ['button:has-text("New")', 'button:has-text("สร้าง")', 'button:has-text("Create")', 'a:has-text("New")', '.o_list_button_add']
}

APP_VALIDATE_BUTTONS = {
    'Point of Sale': ['button:has-text("Validate")', 'button:has-text("ตรวจรับ")', 'button:has-text("Close")', 'button:has-text("ปิด")'],
    'Sales': ['button:has-text("Confirm")', 'button:has-text("ยืนยัน")', 'button:has-text("Validate")'],
    'Accounting': ['button:has-text("Confirm")', 'button:has-text("ยืนยัน")', 'button:has-text("Validate")', 'button:has-text("Approve")', 'button:has-text("อนุมัติ")'],
    'Purchase': ['button:has-text("Confirm")', 'button:has-text("ยืนยัน")', 'button:has-text("Approve")', 'button:has-text("อนุมัติ")'],
    'Inventory': ['button:has-text("Validate")', 'button:has-text("ตรวจรับ")'],
    'Request': ['button:has-text("Approve")', 'button:has-text("อนุมัติ")', 'button:has-text("Validate")', 'button:has-text("Confirm")', 'button:has-text("ยืนยัน")'],
    'default': ['button:has-text("Approve")', 'button:has-text("อนุมัติ")', 'button:has-text("Validate")', 'button:has-text("Confirm")', 'button:has-text("ยืนยัน")', 'button:has-text("Reject")', 'button:has-text("ปฏิเสธ")']
}

APP_SETTING_SELECTORS = {
    'Point of Sale': ['a.main_link:has-text("Configuration")', 'a:has-text("การตั้งค่า")', '.o_menu_sections a:has-text("Configuration")'],
    'Sales': ['a.main_link:has-text("Configuration")', 'a:has-text("การตั้งค่า")', '.o_menu_sections a:has-text("Configuration")'],
    'Accounting': ['a.main_link:has-text("Configuration")', 'a:has-text("การตั้งค่า")', '.o_menu_sections a:has-text("Configuration")'],
    'default': ['a.main_link:has-text("Settings")', 'a.main_link:has-text("Configuration")', 'a:has-text("การตั้งค่า")', '.o_menu_sections a:has-text("Settings")']
}

def _check_any_visible(page, selectors) -> bool:
    for sel in selectors:
        try:
            if page.locator(sel).is_visible():
                return True
        except Exception:
            pass
    return False

def _expect_has(expected: str) -> bool:
    negative_keywords = ['ไม่พบ', 'ไม่แสดง', 'ไม่มีปุ่ม', 'ไม่มีเมนู', 'ไม่มีสิทธิ์']
    for kw in negative_keywords:
        if kw in expected:
            return False
    return True


def _is_error_page(page) -> bool:
    """Check if the current page shows an access error, unauthorized message, or is broken."""
    error_patterns = [
        "text='Access Denied'",
        "text='Access Error'",
        "text='Unauthorized'",
        "text='Forbidden'",
        "text='ไม่มีสิทธิ์'",
        "text='ไม่ได้รับอนุญาต'",
        ".o_error_dialog",
        "text='403'",
        "text='404'",
        "text='500'",
        "text='Internal Server Error'",
        ".o_notification_manager .o_notification.bg-danger",
    ]
    for sel in error_patterns:
        try:
            if page.locator(sel).count() > 0 and page.locator(sel).first.is_visible():
                return True
        except Exception:
            pass
    return False


def _page_has_content(page) -> bool:
    """Check if the page has real readable content — any visible text, tables, forms, or list views."""
    content_indicators = [
        ".o_content",           # Odoo main content area
        ".o_list_view",         # List/table view
        ".o_form_view",         # Form view
        ".o_kanban_view",       # Kanban view
        ".breadcrumb",          # Breadcrumb navigation (means we're inside an app)
        "table",                # Any table
        ".o_control_panel",     # Control panel (search bar area)
        ".o_action_manager",    # Action manager container
    ]
    for sel in content_indicators:
        try:
            loc = page.locator(sel)
            if loc.count() > 0 and loc.first.is_visible():
                return True
        except Exception:
            pass

    # Fallback: check if body has substantial text (more than 50 chars = real content)
    try:
        body_text = page.locator("body").inner_text(timeout=2000)
        if len(body_text.strip()) > 50:
            return True
    except Exception:
        pass

    return False


def verify_read(page, app_name, func_name, expected, role, frame_cb=None):
    def cb(label):
        if frame_cb:
            try: frame_cb(page, label)
            except Exception: pass

    # Always attempt to open the app directly (Point of Sale, etc.)
    should_have = True

    # First check for Access Error on current page
    if _is_error_page(page):
        if should_have:
            cb(f"Read check failed: Access Denied for {role}")
            return ("Failed", f"Access Denied error displayed for role {role}")
        else:
            cb(f"Read check passed: Access Denied as expected for {role}")
            return ("Passed", f"Access Denied displayed as expected for role {role}")

    if should_have:
        # Try opening app
        cb(f"Opening {app_name}")
        opened = open_app(page, app_name, frame_cb=frame_cb)
        time.sleep(1.5)

        # Check for error dialogs or unauthorized message
        if _is_error_page(page):
            cb(f"Read check failed: Access Error in {app_name}")
            return ("Failed", f"Access Error / Unauthorized displayed when opening {app_name}")

        if not opened:
            cb(f"Read check failed: Could not open {app_name}")
            return ("Failed", f"App '{app_name}' icon not found or could not be opened for role {role}")

        # Check if big font app title or readable content is displayed on page
        aliases = APP_ALIASES.get(app_name, [app_name])
        has_title = False
        for alias in aliases:
            try:
                loc = page.get_by_text(alias)
                if loc.count() > 0 and loc.first.is_visible():
                    has_title = True
                    break
            except Exception:
                pass

        if has_title or _page_has_content(page):
            cb(f"Read PASSED: {app_name} page loaded with readable title/content")
            return ("Passed", f"Opened {app_name} — page loaded with readable header/content for {role}")

        cb(f"Read FAILED: {app_name} page is blank or not readable")
        return ("Failed", f"Page for {app_name} is blank or could not be read for {role}")

    else:
        # Negative check: expect hidden
        cb("Checking negative visibility in App Drawer")
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

    open_app(page, app_name, frame_cb=frame_cb)
    time.sleep(1)

    should_have = _expect_has(expected)
    selectors = APP_CREATE_BUTTONS.get(app_name, ['button:has-text("New")', 'button:has-text("Create")', 'a:has-text("New")'])
    found = _check_any_visible(page, selectors)

    if should_have and found:
        return ("Passed", f"Found creation button for {app_name}")
    elif not should_have and not found:
        return ("Passed", f"Creation button hidden as expected for {app_name}")
    elif should_have and not found:
        return ("Failed", f"Missing creation button for {app_name}")
    else:
        return ("Failed", f"Found creation button for {app_name} when not expected")


def verify_validate(page, app_name, func_name, expected, role, frame_cb=None):
    def cb(label):
        if frame_cb:
            try: frame_cb(page, label)
            except Exception: pass

    open_app(page, app_name, frame_cb=frame_cb)
    time.sleep(1)

    should_have = _expect_has(expected)
    selectors = APP_VALIDATE_BUTTONS.get(app_name, APP_VALIDATE_BUTTONS['default'])
    found = _check_any_visible(page, selectors)

    if should_have and found:
        return ("Passed", f"Found validation/approval button for {app_name}")
    elif not should_have and not found:
        return ("Passed", f"Validation button hidden as expected for {app_name}")
    elif should_have and not found:
        return ("Failed", f"Missing validation/approval button for {app_name}")
    else:
        return ("Failed", f"Found validation button for {app_name} when not expected")


def verify_setting(page, app_name, func_name, expected, role, frame_cb=None):
    def cb(label):
        if frame_cb:
            try: frame_cb(page, label)
            except Exception: pass

    open_app(page, app_name, frame_cb=frame_cb)
    time.sleep(1)

    should_have = _expect_has(expected)
    selectors = APP_SETTING_SELECTORS.get(app_name, APP_SETTING_SELECTORS['default'])
    found = _check_any_visible(page, selectors)

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
