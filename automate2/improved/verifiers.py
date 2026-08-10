import sys
import time

sys.stdout.reconfigure(encoding="utf-8")

from navigator import open_app
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

def verify_read(page, app_name, func_name, expected, role):
    if page.url != DASHBOARD_URL:
        page.goto(DASHBOARD_URL)
    
    page.click(SEL_APP_DRAWER)
    time.sleep(2)
    
    aliases = APP_ALIASES.get(app_name, [app_name])
    found = False
    
    for alias in aliases:
        loc = page.locator(f'a.o_app:has-text("{alias}")')
        count = loc.count()
        for i in range(count):
            if loc.nth(i).is_visible():
                found = True
                break
        if found:
            break
            
    should_have = _expect_has(expected)
    if should_have and found:
        return ("PASS", f"Found {app_name} as expected")
    elif not should_have and not found:
        return ("PASS", f"Did not find {app_name} as expected")
    elif should_have and not found:
        return ("FAIL", f"Expected to find {app_name} but it was missing")
    else:
        return ("FAIL", f"Expected not to find {app_name} but it was present")

def verify_create(page, app_name, func_name, expected, role):
    open_app(page, app_name)
    time.sleep(2)
    
    selectors = APP_CREATE_BUTTONS.get(app_name, ['button:has-text("New")', 'a:has-text("New")'])
    found = _check_any_visible(page, selectors)
    
    should_have = _expect_has(expected)
    if should_have and found:
        return ("PASS", f"Found create button for {app_name}")
    elif not should_have and not found:
        return ("PASS", f"Did not find create button for {app_name}")
    elif should_have and not found:
        return ("FAIL", f"Missing create button for {app_name}")
    else:
        return ("FAIL", f"Found create button for {app_name} when not expected")

def verify_validate(page, app_name, func_name, expected, role):
    open_app(page, app_name)
    time.sleep(2)
    
    selectors = APP_VALIDATE_BUTTONS.get(app_name, APP_VALIDATE_BUTTONS['default'])
    found = _check_any_visible(page, selectors)
    
    should_have = _expect_has(expected)
    if should_have and found:
        return ("PASS", f"Found validate/confirm button for {app_name}")
    elif not should_have and not found:
        return ("PASS", f"Did not find validate/confirm button for {app_name}")
    elif should_have and not found:
        return ("FAIL", f"Missing validate/confirm button for {app_name}")
    else:
        return ("FAIL", f"Found validate/confirm button for {app_name} when not expected")

def verify_setting(page, app_name, func_name, expected, role):
    open_app(page, app_name)
    time.sleep(1.5)
    
    selectors = APP_SETTING_SELECTORS.get(app_name, APP_SETTING_SELECTORS['default'])
    found = _check_any_visible(page, selectors)
    
    should_have = _expect_has(expected)
    if should_have and found:
        return ("PASS", f"Found setting/configuration menu for {app_name}")
    elif not should_have and not found:
        return ("PASS", f"Did not find setting/configuration menu for {app_name}")
    elif should_have and not found:
        return ("FAIL", f"Missing setting/configuration menu for {app_name}")
    else:
        return ("FAIL", f"Found setting/configuration menu for {app_name} when not expected")

VERIFIER_MAP = {
    'read': verify_read,
    'create': verify_create,
    'validate': verify_validate,
    'setting': verify_setting
}

def run_verification(page, app_name, func_name, expected, role):
    action = None
    for key in VERIFIER_MAP:
        if key in func_name.lower():
            action = key
            break
            
    if not action:
        return ("SKIP", f"No verifier for {func_name}")
        
    verifier = VERIFIER_MAP[action]
    return verifier(page, app_name, func_name, expected, role)
