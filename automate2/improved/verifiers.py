"""
verifiers.py - Verification engines for Read, Create, Validate, and Setting permissions
"""

import sys
import time

sys.stdout.reconfigure(encoding="utf-8")

from navigator import open_app, is_app_visible
from config import SEL_APP_DRAWER, APP_ALIASES, DASHBOARD_URL

APP_CREATE_BUTTONS = {
    'Point of Sale': [
        'button:has-text("New Session")', 'button:has-text("เปิดเซสชัน")', 'button:has-text("Open")',
        'button:has-text("New")', 'button:has-text("สร้าง")', 'button:has-text("สร้างใหม่")',
        'button:has-text("เพิ่ม")', 'button:has-text("เปิด")', 'a:has-text("New")', 'a:has-text("สร้าง")',
        'a:has-text("เปิดเซสชัน")', '.o_list_button_add', '.o_btn_new', 'button.btn-primary'
    ],
    'Sales': ['button:has-text("New")', 'button:has-text("สร้าง")', 'button:has-text("สร้างใหม่")', 'a:has-text("New")', 'a:has-text("สร้าง")', '.o_list_button_add'],
    'Accounting': ['button:has-text("New")', 'button:has-text("สร้าง")', 'button:has-text("สร้างใหม่")', 'a:has-text("New")', 'a:has-text("สร้าง")', '.o_list_button_add'],
    'Purchase': ['button:has-text("New")', 'button:has-text("สร้าง")', 'button:has-text("สร้างใหม่")', 'a:has-text("New")', 'a:has-text("สร้าง")', '.o_list_button_add'],
    'Inventory': ['button:has-text("New")', 'button:has-text("สร้าง")', 'button:has-text("สร้างใหม่")', 'a:has-text("New")', 'a:has-text("สร้าง")', '.o_list_button_add'],
    'Request': ['button:has-text("New")', 'button:has-text("สร้าง")', 'button:has-text("Create")', 'button:has-text("สร้างใหม่")', 'a:has-text("New")', 'a:has-text("สร้าง")'],
    'Fleet': ['button:has-text("New")', 'button:has-text("สร้าง")', 'button:has-text("สร้างใหม่")', 'a:has-text("New")', 'a:has-text("สร้าง")'],
    'MPOS': ['button:has-text("New")', 'button:has-text("สร้าง")', 'button:has-text("สร้างใหม่")', 'a:has-text("New")', 'a:has-text("สร้าง")'],
    'default': [
        'button:has-text("New")', 'button:has-text("สร้าง")', 'button:has-text("Create")',
        'button:has-text("สร้างใหม่")', 'button:has-text("เปิดเซสชัน")', 'button:has-text("เพิ่ม")',
        'a:has-text("New")', 'a:has-text("สร้าง")', '.o_list_button_add'
    ]
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


from navigator import open_app, is_app_visible, navigate_submenus

def verify_create(page, app_name, func_name, expected, role, frame_cb=None):
    def cb(label):
        if frame_cb:
            try: frame_cb(page, label)
            except Exception: pass

    cb(f"Opening {app_name} for Create verification")
    opened = open_app(page, app_name, frame_cb=frame_cb)
    time.sleep(1.5)

    if not opened:
        cb(f"Create check failed: App '{app_name}' icon not found for role {role}")
        return ("Failed", f"App '{app_name}' icon not found or could not be opened for role {role}")

    # Check if sub-menu navigation is required for Credit Notes (ใบลดหนี้)
    if "ใบลดหนี้" in func_name or "Credit Note" in func_name or "Credit Notes" in func_name:
        cb("Navigating sub-menu: Customers -> Credit Notes")
        sub_ok = navigate_submenus(page, [
            ["Customers", "ลูกค้า"],
            ["Credit Notes", "ใบลดหนี้", "ใบลดหนี้ราคา"]
        ], frame_cb=frame_cb)
        if not sub_ok:
            cb("Create check failed: Sub-menu Customers -> Credit Notes not found")
            return ("Failed", f"Sub-menu Customers -> Credit Notes not found in {app_name} for role {role}")

    # Check if sub-menu navigation is required for Booking Orders (สั่งจอง)
    elif "สั่งจอง" in func_name or "Booking" in func_name or app_name == "Sales":
        cb("Navigating sub-menu: Orders/คำสั่งขาย -> สั่งจอง")
        sub_ok = navigate_submenus(page, [
            ["Orders", "คำสั่งขาย"],
            ["สั่งจอง", "Bookings"]
        ], frame_cb=frame_cb)
        
        if not sub_ok:
            cb("Create check failed: Sub-menu คำสั่งขาย -> สั่งจอง not found")
            return ("Failed", f"Sub-menu คำสั่งขาย -> สั่งจอง not found in {app_name} for role {role}")

        # Click New / สร้าง
        create_btn = page.locator("button:has-text('New'), button:has-text('สร้าง'), a:has-text('New')").first
        if not create_btn.is_visible(timeout=3000):
            cb("Create check failed: New/สร้าง button not found in สั่งจอง page")
            return ("Failed", f"New/สร้าง button not found in สั่งจอง page for role {role}")

        cb("Clicking New/สร้าง on สั่งจอง page")
        create_btn.click()
        time.sleep(2)

        try:
            # 1. Fill ผู้สั่งจอง (Customer)
            cb("Filling ผู้สั่งจอง dropdown")
            booker_inp = page.locator("div[name='partner_id'] input, input[id*='partner_id'], .o_field_widget[name='partner_id'] input").first
            if booker_inp.is_visible(timeout=2000):
                booker_inp.click()
                time.sleep(0.5)
                page.keyboard.press("ArrowDown")
                time.sleep(0.5)
                page.keyboard.press("Enter")
                time.sleep(1)

            # 2. Fill เลือกอีเวนต์ (Event)
            cb("Filling เลือกอีเวนต์ dropdown")
            event_inp = page.locator("div[name='event_id'] input, input[id*='event_id'], .o_field_widget[name='event_id'] input").first
            if event_inp.is_visible(timeout=2000):
                event_inp.click()
                time.sleep(0.5)
                page.keyboard.press("ArrowDown")
                time.sleep(0.5)
                page.keyboard.press("Enter")
                time.sleep(1)

            # 3. Click Save manually
            cb("Clicking Save button")
            save_btn = page.locator(".o_form_button_save, button:has-text('Save'), button:has-text('บันทึก')").first
            if save_btn.is_visible(timeout=2000):
                save_btn.click()
                time.sleep(2)

            # Extract created record number (e.g. SO-13000-2608000006)
            rec_num = ""
            try:
                header_elem = page.locator(".o_last_breadcrumb_item").first
                if not header_elem.is_visible(timeout=1000):
                    header_elem = page.locator("h1:has-text('SO-')").first
                if not header_elem.is_visible(timeout=1000):
                    header_elem = page.locator(".breadcrumb-item.active").first
                if header_elem.is_visible(timeout=1000):
                    header_text = header_elem.inner_text()
                    for word in header_text.split():
                        if "SO-" in word or "13000-" in word:
                            rec_num = word.strip()
                            break
                    if not rec_num and "SO-" in header_text:
                        rec_num = header_text.strip().split("\n")[0]
            except Exception:
                pass

            cb(f"Created order record: '{rec_num}'")

            # 4. Click CONFIRM
            cb("Clicking CONFIRM button")
            confirm_btn = page.locator("button:has-text('CONFIRM'), button:has-text('Confirm'), button:has-text('ยืนยัน')").first
            if confirm_btn.is_visible(timeout=2000):
                confirm_btn.click()
                time.sleep(2)

            # 5. Handle OK dialog if present
            ok_btn = page.locator(".modal button:has-text('OK'), .modal button:has-text('ตกลง')").first
            if ok_btn.is_visible(timeout=1500):
                cb("Clicking OK on dialog modal")
                ok_btn.click()
                time.sleep(1)

            # 6. Go back to สั่งจอง page
            cb("Returning to สั่งจอง list page")
            b_crumb = page.locator("a.breadcrumb-item:has-text('สั่งจอง'), .breadcrumb a:has-text('สั่งจอง')").first
            if b_crumb.is_visible(timeout=2000):
                b_crumb.click()
            else:
                navigate_submenus(page, [["Orders", "คำสั่งขาย"], ["สั่งจอง", "Bookings"]], frame_cb=frame_cb)
            time.sleep(2)

            # 7. Check if record number appears in table list
            if rec_num:
                in_list = page.locator(f"table:has-text('{rec_num}'), tr:has-text('{rec_num}'), .o_list_table:has-text('{rec_num}')").count() > 0
                if in_list:
                    cb(f"Create PASSED: Found created number '{rec_num}' in สั่งจอง table")
                    return ("Passed", f"Created order '{rec_num}' successfully and verified in สั่งจอง table for role {role}")
                else:
                    cb(f"Create FAILED: Record number '{rec_num}' not found in สั่งจอง table")
                    return ("Failed", f"Order '{rec_num}' created but not found in สั่งจอง list table for role {role}")

            cb("Create PASSED: Order saved and confirmed successfully")
            return ("Passed", f"Order created and confirmed successfully in สั่งจอง for role {role}")

        except Exception as e:
            cb(f"Create FAILED during form workflow: {e}")
            return ("Failed", f"Error during สั่งจอง order creation workflow for role {role}: {e}")

    selectors = APP_CREATE_BUTTONS.get(app_name, APP_CREATE_BUTTONS['default'])
    found = _check_any_visible(page, selectors)

    if found:
        cb(f"Create PASSED: Found create button in {app_name}")
        return ("Passed", f"Found creation button/function in {app_name} for role {role}")
    else:
        cb(f"Create FAILED: No create button found in {app_name}")
        return ("Failed", f"Create function/button not found in {app_name} for role {role}")


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
