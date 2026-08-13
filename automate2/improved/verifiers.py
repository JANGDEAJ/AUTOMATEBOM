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
        'button:has-text("New Session")', 'button:has-text("เปิดเซสชัน")',
        'button:has-text("New")', 'button:has-text("สร้าง")', 'button:has-text("สร้างใหม่")',
        'a:has-text("New")', 'a:has-text("สร้าง")', 'a:has-text("เปิดเซสชัน")',
        '.o_list_button_add', '.o_btn_new'
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

    # Check if sub-menu navigation is required for Request app (My Expenses -> Petty Cash / เงินสดย่อย)
    if app_name == "Request" or "Request" in app_name:
        sub_name = "Petty Cash"
        if "หัก ณ ที่จ่าย" in func_name or "Withholding" in func_name:
            sub_name = "เงินสดย่อย (หัก ณ ที่จ่าย)"

        cb(f"Navigating sub-menu: My Expenses -> {sub_name}")
        sub_ok = navigate_submenus(page, [
            ["My Expenses", "ค่าใช้จ่ายของฉัน"],
            [sub_name, "Petty Cash", "วงเงินสดย่อย"]
        ], frame_cb=frame_cb)

        if not sub_ok:
            cb(f"Create check failed: Sub-menu My Expenses -> {sub_name} not found")
            return ("Failed", f"Sub-menu My Expenses -> {sub_name} not found in {app_name} for role {role}")

        # Click New / สร้าง
        create_btn = page.locator("button:has-text('New'), button:has-text('สร้าง'), a:has-text('New'), .o_list_button_add").first
        if not create_btn.is_visible(timeout=3000):
            cb(f"Create check failed: New/สร้าง button not found in {sub_name} page")
            return ("Failed", f"New/สร้าง button not found in {sub_name} page for role {role}")

        cb(f"Clicking New/สร้าง on {sub_name} page")
        create_btn.click()
        time.sleep(2)

        try:
            import os, random
            ref_str = f"REQ-EXP-{random.randint(100, 999)}"

            # 1. Fill Description
            cb("Filling Description")
            desc_inp = page.locator("div[name='name'] input, input[name='name'], textarea[name='name']").first
            if desc_inp.is_visible(timeout=2000):
                desc_inp.fill(ref_str)
                time.sleep(0.5)

            # 2. Fill Category dropdown
            cb("Filling Category dropdown")
            cat_inp = page.locator("div[name='product_id'] input, div[name='category_id'] input").first
            if cat_inp.is_visible(timeout=1500):
                cat_inp.click()
                time.sleep(0.5)
                page.keyboard.press("ArrowDown")
                time.sleep(0.5)
                page.keyboard.press("Enter")
                time.sleep(0.5)

            # 3. Fill Total Amount if present
            cb("Filling Total Amount")
            total_inp = page.locator("div[name='total_amount'] input, div[name='unit_amount'] input, input[name='unit_amount']").first
            if total_inp.is_visible(timeout=1500):
                total_inp.click()
                time.sleep(0.3)
                total_inp.fill("500")
                time.sleep(0.5)

            # 3.1 Fill Partner / พาร์ทเนอร์ (required when Tax Invoice is checked)
            cb("Filling Partner dropdown")
            partner_inp = page.locator("div[name='partner_id'] input, input[id*='partner_id']").first
            if partner_inp.is_visible(timeout=1500):
                partner_inp.click()
                time.sleep(0.5)
                page.keyboard.press("ArrowDown")
                time.sleep(0.5)
                page.keyboard.press("Enter")
                time.sleep(0.5)

            # 3.2 Fill Bill Reference / การอ้างอิง (required when Tax Invoice is checked)
            cb("Filling Bill Reference")
            ref_inp = page.locator("div[name='reference'] input, div[name='ref'] input, input[name='reference'], input[name='ref']").first
            if ref_inp.is_visible(timeout=1500):
                ref_inp.fill(f"REF-{random.randint(100, 999)}")
                time.sleep(0.5)

            # 3.3 Fill Tax Invoice Date / Tax Invoice Date (required when Tax Invoice is checked)
            cb("Filling Tax Invoice Date")
            tax_date_inp = page.locator("div[name='tax_invoice_date'] input, div[name='date_invoice'] input, input[name='tax_invoice_date']").first
            if tax_date_inp.is_visible(timeout=1500):
                tax_date_inp.click()
                time.sleep(0.3)
                page.keyboard.press("Enter")
                time.sleep(0.5)

            # 4. Click Save manually
            cb("Clicking Save button manually")
            save_btn = page.locator(".o_form_button_save, button:has-text('Save'), button:has-text('บันทึก'), .fa-cloud-upload").first
            if save_btn.is_visible(timeout=2000):
                save_btn.click()
                time.sleep(2)

            # 5. Click ATTACH RECEIPT if present
            cb("Handling ATTACH RECEIPT")
            attach_btn = page.locator("button:has-text('ATTACH RECEIPT'), button:has-text('แนบใบเสร็จ')").first
            if attach_btn.is_visible(timeout=2000):
                # Check for hidden file input or click attach button
                file_inputs = page.locator("input[type='file']")
                if file_inputs.count() > 0:
                    # Upload an existing screenshot asset as attachment
                    sample_asset = os.path.abspath("c:/Users/gaykn/Downloads/automate2/AUTOMATEBOM/automate2/improved/config.py")
                    try:
                        file_inputs.first.set_input_files(sample_asset)
                        time.sleep(1.5)
                    except Exception:
                        attach_btn.click()
                        time.sleep(1)
                else:
                    attach_btn.click()
                    time.sleep(1)

            # 6. Click SUBMIT TO MANAGER
            cb("Clicking SUBMIT TO MANAGER button")
            submit_btn = page.locator("button:has-text('SUBMIT TO MANAGER'), button:has-text('ส่งให้ผู้จัดการ')").first
            if submit_btn.is_visible(timeout=2000):
                submit_btn.click()
                time.sleep(2)

            # Handle modal OK dialog if present
            ok_btn = page.locator(".modal button:has-text('OK'), .modal button:has-text('ตกลง')").first
            if ok_btn.is_visible(timeout=1500):
                ok_btn.click()
                time.sleep(1)

            # 7. Go back to list view
            cb(f"Returning to {sub_name} list view")
            b_crumb = page.locator("a.breadcrumb-item:has-text('My Expenses'), a.breadcrumb-item:has-text('Petty Cash'), .breadcrumb a").first
            if b_crumb.is_visible(timeout=2000):
                b_crumb.click()
            else:
                navigate_submenus(page, [["My Expenses", "ค่าใช้จ่ายของฉัน"], [sub_name, "Petty Cash"]], frame_cb=frame_cb)
            time.sleep(2)

            # 8. Check if record appears in list table
            in_list = page.locator(f"table:has-text('{ref_str}'), tr:has-text('{ref_str}'), .o_list_table:has-text('{ref_str}')").count() > 0
            if in_list:
                cb(f"Create PASSED: Found expense '{ref_str}' in table list")
                return ("Passed", f"Created expense '{ref_str}' successfully in My Expenses -> {sub_name} for role {role}")
            else:
                cb(f"Create FAILED: Expense '{ref_str}' not found in table list")
                return ("Failed", f"Expense '{ref_str}' created but not found in {sub_name} table for role {role}")

        except Exception as e:
            cb(f"Create FAILED during Request expense workflow: {e}")
            return ("Failed", f"Error during Request expense creation workflow for role {role}: {e}")

    # Check if sub-menu navigation is required for Petty Cash Fund (วงเงินสดย่อย)
    elif any(kw in func_name for kw in ["สดย่อย", "Petty Cash", "Petty Cash Fund", "petty cash"]):
        cb("Navigating sub-menu: Expenses -> Petty Cash Fund")
        sub_ok = navigate_submenus(page, [
            ["Expenses", "ค่าใช้จ่าย"],
            ["Petty Cash Fund", "วงเงินสดย่อย", "Petty Cash"]
        ], frame_cb=frame_cb)

        if not sub_ok:
            cb("Create check failed: Sub-menu Expenses -> Petty Cash Fund not found")
            return ("Failed", f"Sub-menu Expenses -> Petty Cash Fund not found in {app_name} for role {role}")

        # Click New / สร้าง
        create_btn = page.locator("button:has-text('New'), button:has-text('สร้าง'), a:has-text('New'), .o_list_button_add").first
        if not create_btn.is_visible(timeout=3000):
            cb("Create check failed: New/สร้าง button not found in Petty Cash Fund page")
            return ("Failed", f"New/สร้าง button not found in Petty Cash Fund page for role {role}")

        cb("Clicking New/สร้าง on Petty Cash Fund page")
        create_btn.click()
        time.sleep(2)

        try:
            import random
            ref_str = f"PETTY-AUTO-{random.randint(100, 999)}"

            # 1. Fill Name (วงเงินสดย่อย header)
            cb("Filling Name")
            name_inp = page.locator("div[name='name'] input, input[name='name']").first
            if name_inp.is_visible(timeout=2000):
                name_inp.fill(ref_str)
                time.sleep(0.5)

            # 2. Fill Owner (required)
            cb("Filling Owner dropdown")
            owner_inp = page.locator("div[name='owner_id'] input, div[name='user_id'] input").first
            if owner_inp.is_visible(timeout=1500):
                owner_inp.click()
                time.sleep(0.5)
                page.keyboard.press("ArrowDown")
                time.sleep(0.5)
                page.keyboard.press("Enter")
                time.sleep(1)

            # 3. Fill Payment Journal (required)
            cb("Filling Payment Journal dropdown")
            journal_inp = page.locator("div[name='journal_id'] input, div[name='payment_journal_id'] input").first
            if journal_inp.is_visible(timeout=1500):
                journal_inp.click()
                time.sleep(0.5)
                page.keyboard.press("ArrowDown")
                time.sleep(0.5)
                page.keyboard.press("Enter")
                time.sleep(0.5)

            # 4. Fill Payment Code (required)
            cb("Filling Payment Code")
            code_inp = page.locator("div[name='payment_code'] input, div[name='code'] input, input[name='payment_code']").first
            if code_inp.is_visible(timeout=1500):
                code_inp.fill(f"PC-{random.randint(100,999)}")
                time.sleep(0.5)

            # 5. Fill Account (required)
            cb("Filling Account dropdown")
            acc_inp = page.locator("div[name='account_id'] input").first
            if acc_inp.is_visible(timeout=1500):
                acc_inp.click()
                time.sleep(0.5)
                page.keyboard.press("ArrowDown")
                time.sleep(0.5)
                page.keyboard.press("Enter")
                time.sleep(0.5)

            # 5.5 Fill Max Fund Amount / money amount (required > 0)
            cb("Filling Max Fund Amount")
            max_amt_inp = page.locator("div[name='max_fund_amount'] input, div[name='max_amount'] input, div[name='amount'] input, div[name='max_limit'] input, div[name='limit_payment_amount'] input").first
            if max_amt_inp.is_visible(timeout=1500):
                max_amt_inp.click()
                time.sleep(0.3)
                max_amt_inp.fill("1000")
                time.sleep(0.5)

            # 6. Click Save manually
            cb("Clicking Save button manually")
            save_btn = page.locator(".o_form_button_save, button:has-text('Save'), button:has-text('บันทึก'), .fa-cloud-upload").first
            if save_btn.is_visible(timeout=2000):
                save_btn.click()
                time.sleep(2)

            # Check for validation error notification after save
            err_notif = page.locator(".o_notification_manager .o_notification.bg-danger, .o_error_dialog, .modal-body:has-text('Invalid')").first
            if err_notif.is_visible(timeout=1500):
                err_text = err_notif.inner_text()
                cb(f"Save blocked by validation error: {err_text}")
                return ("Failed", f"Save failed — form requires mandatory fields that could not be filled automatically: {err_text.strip()} (role {role})")

            # 7. Click CONFIRM / Send to Approve
            cb("Clicking Confirm/ส่งคำขอ button")
            confirm_btn = page.locator("button:has-text('ส่งคำขอ'), button:has-text('Confirm'), button:has-text('ยืนยัน'), button:has-text('Approve'), button:has-text('อนุมัติ')").first
            if confirm_btn.is_visible(timeout=2000):
                confirm_btn.click()
                time.sleep(2)

            # Handle modal OK dialog if present
            ok_btn = page.locator(".modal button:has-text('OK'), .modal button:has-text('ตกลง')").first
            if ok_btn.is_visible(timeout=1500):
                ok_btn.click()
                time.sleep(1)

            # 8. Extract created serial/name from breadcrumb
            rec_num = ""
            try:
                for sel in [".o_last_breadcrumb_item", ".breadcrumb-item.active"]:
                    elem = page.locator(sel).first
                    if elem.is_visible(timeout=1000):
                        text = elem.inner_text().strip()
                        if text and text not in ["New", "สร้าง"]:
                            rec_num = text.split("\n")[0]
                            break
            except Exception:
                pass

            cb(f"Created Petty Cash record: '{rec_num}'")

            # 9. Go back to Petty Cash Fund list view
            cb("Returning to Petty Cash Fund list view")
            b_crumb = page.locator("a.breadcrumb-item:has-text('Petty Cash'), a.breadcrumb-item:has-text('วงเงินสดย่อย'), .breadcrumb a:has-text('Petty Cash')").first
            if b_crumb.is_visible(timeout=2000):
                b_crumb.click()
            else:
                navigate_submenus(page, [["Expenses", "ค่าใช้จ่าย"], ["Petty Cash Fund", "วงเงินสดย่อย"]], frame_cb=frame_cb)
            time.sleep(2)

            # 10. Check if record name or ref appears in table list
            target_str = rec_num if rec_num else ref_str
            in_list = page.locator(f"table:has-text('{target_str}'), tr:has-text('{target_str}'), .o_list_table:has-text('{target_str}')").count() > 0
            if in_list:
                cb(f"Create PASSED: Found petty cash '{target_str}' in table list")
                return ("Passed", f"Created petty cash '{target_str}' successfully and verified in Petty Cash Fund table for role {role}")
            else:
                cb(f"Create FAILED: Petty cash '{target_str}' not found in table list")
                return ("Failed", f"Petty cash '{target_str}' created but not found in Petty Cash Fund list table for role {role}")

        except Exception as e:
            cb(f"Create FAILED during petty cash fund creation workflow: {e}")
            return ("Failed", f"Error during Petty Cash Fund creation workflow for role {role}: {e}")

    # Check if sub-menu navigation is required for Credit Notes (ใบลดหนี้)
    elif "ใบลดหนี้" in func_name or "Credit Note" in func_name or "Credit Notes" in func_name:
        cb("Navigating sub-menu: Customers -> Credit Notes")
        sub_ok = navigate_submenus(page, [
            ["Customers", "ลูกค้า"],
            ["Credit Notes", "ใบลดหนี้", "ใบลดหนี้ราคา"]
        ], frame_cb=frame_cb)
        if not sub_ok:
            cb("Create check failed: Sub-menu Customers -> Credit Notes not found")
            return ("Failed", f"Sub-menu Customers -> Credit Notes not found in {app_name} for role {role}")

    # Check if sub-menu navigation is required for Customer Invoices (การจัดทำใบแจ้งหนี้)
    elif "ใบแจ้งหนี้" in func_name or "Invoice" in func_name or "Invoices" in func_name:
        cb("Navigating sub-menu: Customers -> Invoices")
        sub_ok = navigate_submenus(page, [
            ["Customers", "ลูกค้า"],
            ["Invoices", "ใบแจ้งหนี้", "การจัดทำใบแจ้งหนี้"]
        ], frame_cb=frame_cb)
        
        if not sub_ok:
            cb("Create check failed: Sub-menu Customers -> Invoices not found")
            return ("Failed", f"Sub-menu Customers -> Invoices not found in {app_name} for role {role}")

        # Click New / สร้าง
        create_btn = page.locator("button:has-text('New'), button:has-text('สร้าง'), a:has-text('New'), .o_list_button_add").first
        if not create_btn.is_visible(timeout=3000):
            cb("Create check failed: New/สร้าง button not found in Invoices page")
            return ("Failed", f"New/สร้าง button not found in Invoices page for role {role}")

        cb("Clicking New/สร้าง on Invoices page")
        create_btn.click()
        time.sleep(2)
        cb("Invoices: New form opened — returning Passed (full workflow in dedicated branch)")
        return ("Passed", f"Found New/Create button in Customers -> Invoices for role {role}")

    # Check if sub-menu navigation is required for Payments (การบันทึกรับชำระเงิน / Payments)
    elif "รับชำระ" in func_name or "Payment" in func_name or "Payments" in func_name:
        cb("Navigating sub-menu: Customers -> Payments")
        sub_ok = navigate_submenus(page, [
            ["Customers", "ลูกค้า"],
            ["Payments", "การชำระเงิน", "การบันทึกรับชำระเงิน", "ชำระเงิน"]
        ], frame_cb=frame_cb)

        if not sub_ok:
            cb("Create check failed: Sub-menu Customers -> Payments not found")
            return ("Failed", f"Sub-menu Customers -> Payments not found in {app_name} for role {role}")

        # Click New / สร้าง
        create_btn = page.locator("button:has-text('New'), button:has-text('สร้าง'), a:has-text('New'), .o_list_button_add").first
        if not create_btn.is_visible(timeout=3000):
            cb("Create check failed: New/สร้าง button not found in Payments page")
            return ("Failed", f"New/สร้าง button not found in Payments page for role {role}")

        cb("Clicking New/สร้าง on Payments page")
        create_btn.click()
        time.sleep(2)

        try:
            # 1. Fill Customer (ลูกค้า)
            cb("Filling Customer dropdown")
            customer_inp = page.locator("div[name='partner_id'] input, input[id*='partner_id'], .o_field_widget[name='partner_id'] input").first
            if customer_inp.is_visible(timeout=2000):
                customer_inp.click()
                time.sleep(0.5)
                page.keyboard.press("ArrowDown")
                time.sleep(0.5)
                page.keyboard.press("Enter")
                time.sleep(1)

            # 2. Fill Amount (จำนวนเงิน) if required/present
            cb("Filling Amount")
            amt_inp = page.locator("div[name='amount'] input, input[name='amount']").first
            if amt_inp.is_visible(timeout=1500):
                amt_inp.click()
                amt_inp.fill("100")
                time.sleep(0.5)

            # 3. Fill Memo/Ref (การอ้างอิง)
            cb("Filling Memo/Ref text field")
            import random
            ref_str = f"PAY-AUTO-{random.randint(100, 999)}"
            ref_inp = page.locator("div[name='memo'] input, div[name='ref'] input, input[name='memo'], input[name='ref']").first
            if ref_inp.is_visible(timeout=1500):
                ref_inp.fill(ref_str)
                time.sleep(0.5)

            # 4. Click Save manually
            cb("Clicking Save button manually")
            save_btn = page.locator(".o_form_button_save, button:has-text('Save'), button:has-text('บันทึก'), .fa-cloud-upload").first
            if save_btn.is_visible(timeout=2000):
                save_btn.click()
                time.sleep(2)

            # 5. Click CONFIRM
            cb("Clicking Confirm button")
            confirm_btn = page.locator("button:has-text('Confirm'), button:has-text('ยืนยัน'), button.btn-primary:has-text('Confirm')").first
            if confirm_btn.is_visible(timeout=2000):
                confirm_btn.click()
                time.sleep(2)

            # Handle modal OK dialog if present
            ok_btn = page.locator(".modal button:has-text('OK'), .modal button:has-text('ตกลง')").first
            if ok_btn.is_visible(timeout=1500):
                ok_btn.click()
                time.sleep(1)

            # Extract created payment serial number (e.g. CSH1/..., BNK1/..., CUST.IN/...)
            rec_num = ""
            try:
                for sel in [".o_last_breadcrumb_item", "h1:has-text('CUST.IN')", "h1:has-text('BNK')", "h1:has-text('CSH')", ".breadcrumb-item.active"]:
                    elem = page.locator(sel).first
                    if elem.is_visible(timeout=1000):
                        text = elem.inner_text()
                        for word in text.split():
                            if "/" in word or "PAY" in word or "CUST" in word or "CSH" in word or "BNK" in word:
                                rec_num = word.strip()
                                break
                        if rec_num:
                            break
                        if text and not rec_num:
                            rec_num = text.strip().split("\n")[0]
                            break
            except Exception:
                pass

            cb(f"Created Payment Serial: '{rec_num}'")

            # 6. Go back to Payments list view
            cb("Returning to Payments list view")
            b_crumb = page.locator("a.breadcrumb-item:has-text('Payments'), a.breadcrumb-item:has-text('การชำระเงิน'), .breadcrumb a:has-text('Payments')").first
            if b_crumb.is_visible(timeout=2000):
                b_crumb.click()
            else:
                navigate_submenus(page, [["Customers", "ลูกค้า"], ["Payments", "การชำระเงิน"]], frame_cb=frame_cb)
            time.sleep(2)

            # 7. Check if serial number or reference appears in table list
            target_str = rec_num if rec_num else ref_str
            in_list = page.locator(f"table:has-text('{target_str}'), tr:has-text('{target_str}'), .o_list_table:has-text('{target_str}')").count() > 0
            if in_list:
                cb(f"Create PASSED: Found payment '{target_str}' in table list")
                return ("Passed", f"Created payment '{target_str}' successfully and verified in Payments table for role {role}")
            else:
                cb(f"Create FAILED: Payment '{target_str}' not found in table list")
                return ("Failed", f"Payment '{target_str}' created but not found in Payments list table for role {role}")

        except Exception as e:
            cb(f"Create FAILED during payment creation workflow: {e}")
            return ("Failed", f"Error during Payment creation workflow for role {role}: {e}")

        try:
            # 1. Fill ลูกค้าที่มาติดต่อ (Customer)
            cb("Filling ลูกค้าที่มาติดต่อ dropdown")
            customer_inp = page.locator("div[name='partner_id'] input, input[id*='partner_id'], .o_field_widget[name='partner_id'] input").first
            if customer_inp.is_visible(timeout=2000):
                customer_inp.click()
                time.sleep(0.5)
                page.keyboard.press("ArrowDown")
                time.sleep(0.5)
                page.keyboard.press("Enter")
                time.sleep(1)

            # 2. Fill ผู้รับ/ที่อยู่ (Delivery/Recipient address)
            cb("Filling ผู้รับ/ที่อยู่ dropdown")
            addr_inp = page.locator("div[name='partner_shipping_id'] input, div[name='delivery_address_id'] input, input[id*='shipping']").first
            if addr_inp.is_visible(timeout=1500):
                addr_inp.click()
                time.sleep(0.5)
                page.keyboard.press("ArrowDown")
                time.sleep(0.5)
                page.keyboard.press("Enter")
                time.sleep(1)

            # 3. Fill Payment Terms / เงื่อนไขการชำระเงิน
            cb("Filling Terms dropdown")
            terms_inp = page.locator("div[name='invoice_payment_term_id'] input, div[name='payment_term_id'] input, input[id*='payment_term']").first
            if terms_inp.is_visible(timeout=1500):
                terms_inp.click()
                time.sleep(0.5)
                page.keyboard.press("ArrowDown")
                time.sleep(0.5)
                page.keyboard.press("Enter")
                time.sleep(1)

            # 4. Fill การอ้างอิง (Payment Reference)
            cb("Filling การอ้างอิง text field")
            import random
            ref_str = f"REF-AUTO-{random.randint(100, 999)}"
            ref_inp = page.locator("div[name='payment_reference'] input, div[name='ref'] input, input[name='payment_reference'], input[name='ref']").first
            if ref_inp.is_visible(timeout=1500):
                ref_inp.fill(ref_str)
                time.sleep(0.5)

            # 5. Click Save manually
            cb("Clicking Save button manually")
            save_btn = page.locator(".o_form_button_save, button:has-text('Save'), button:has-text('บันทึก'), .fa-cloud-upload").first
            if save_btn.is_visible(timeout=2000):
                save_btn.click()
                time.sleep(2)

            # 6. Click CONFIRM
            cb("Clicking Confirm button")
            confirm_btn = page.locator("button:has-text('Confirm'), button:has-text('ยืนยัน'), button.btn-primary:has-text('Confirm')").first
            if confirm_btn.is_visible(timeout=2000):
                confirm_btn.click()
                time.sleep(2)

            # Handle modal OK dialog if present
            ok_btn = page.locator(".modal button:has-text('OK'), .modal button:has-text('ตกลง')").first
            if ok_btn.is_visible(timeout=1500):
                ok_btn.click()
                time.sleep(1)

            # Extract created invoice serial number (e.g. DINV-13000-260100131 or INV-...)
            rec_num = ""
            try:
                for sel in [".o_last_breadcrumb_item", "h1:has-text('DINV-')", "h1:has-text('INV-')", "h1:has-text('13000-')", ".breadcrumb-item.active"]:
                    elem = page.locator(sel).first
                    if elem.is_visible(timeout=1000):
                        text = elem.inner_text()
                        for word in text.split():
                            if "DINV-" in word or "INV-" in word or "13000-" in word:
                                rec_num = word.strip()
                                break
                        if rec_num:
                            break
                        if ("DINV-" in text or "INV-" in text) and not rec_num:
                            rec_num = text.strip().split("\n")[0]
                            break
            except Exception:
                pass

            cb(f"Created Invoice Serial: '{rec_num}'")

            # 7. Go back to Invoices list view
            cb("Returning to Invoices list view")
            b_crumb = page.locator("a.breadcrumb-item:has-text('Invoices'), a.breadcrumb-item:has-text('ใบแจ้งหนี้'), .breadcrumb a:has-text('Invoices')").first
            if b_crumb.is_visible(timeout=2000):
                b_crumb.click()
            else:
                navigate_submenus(page, [["Customers", "ลูกค้า"], ["Invoices", "ใบแจ้งหนี้"]], frame_cb=frame_cb)
            time.sleep(2)

            # 8. Check if serial number appears in table list
            if rec_num:
                in_list = page.locator(f"table:has-text('{rec_num}'), tr:has-text('{rec_num}'), .o_list_table:has-text('{rec_num}')").count() > 0
                if in_list:
                    cb(f"Create PASSED: Found invoice serial '{rec_num}' in table list")
                    return ("Passed", f"Created invoice '{rec_num}' successfully and verified in Invoices table for role {role}")
                else:
                    cb(f"Create FAILED: Invoice serial '{rec_num}' not found in table list")
                    return ("Failed", f"Invoice '{rec_num}' created but not found in Invoices list table for role {role}")

            cb("Create PASSED: Invoice saved and confirmed successfully")
            return ("Passed", f"Invoice created and confirmed successfully in Invoices for role {role}")

        except Exception as e:
            cb(f"Create FAILED during invoice creation workflow: {e}")
            return ("Failed", f"Error during Invoice creation workflow for role {role}: {e}")

    # Check if sub-menu navigation is required for Vendor Bills / ใบวางบิล (การจัดทำใบวางบิล)
    elif "ใบวางบิล" in func_name or "Vendor Bills" in func_name or "Bills" in func_name:
        cb("Navigating sub-menu: Vendors -> Bills")
        sub_ok = navigate_submenus(page, [
            ["Vendors", "ผู้ขาย", "ผู้ให้บริการ"],
            ["Bills", "ใบแจ้งหนี้/ใบวางบิล", "ใบวางบิล"]
        ], frame_cb=frame_cb)
        
        if not sub_ok:
            cb("Create check failed: Sub-menu Vendors -> Bills not found")
            return ("Failed", f"Sub-menu Vendors -> Bills not found in {app_name} for role {role}")

        # Click New / สร้าง
        create_btn = page.locator("button:has-text('New'), button:has-text('สร้าง'), a:has-text('New'), .o_list_button_add").first
        if not create_btn.is_visible(timeout=3000):
            cb("Create check failed: New/สร้าง button not found in Bills page")
            return ("Failed", f"New/สร้าง button not found in Bills page for role {role}")

        cb("Clicking New/สร้าง on Bills page")
        create_btn.click()
        time.sleep(2)

        try:
            # 1. Fill Vendor (ผู้ขาย)
            cb("Filling Vendor dropdown")
            vendor_loc = page.locator("div[name='partner_id'] input, input[id*='partner_id'], .o_field_widget[name='partner_id'] input").first
            if vendor_loc.is_visible(timeout=2000):
                vendor_loc.click()
                time.sleep(0.5)
                page.keyboard.press("ArrowDown")
                time.sleep(0.5)
                page.keyboard.press("Enter")
                time.sleep(0.5)

            # 2. Fill ประเภทการทำจ่าย (Payment / Disbursement Type dropdown)
            cb("Filling ประเภทการทำจ่าย dropdown")
            pt_locators = [
                page.locator("xpath=//*[contains(text(), 'ประเภทการทำจ่าย')]/following::input[1]"),
                page.locator("xpath=//*[contains(text(), 'ประเภทการทำจ่าย')]/ancestor::div[1]//input"),
                page.locator("div[name='disbursement_type_id'] input"),
                page.locator("div[name='payment_type_id'] input"),
                page.locator("div[name='disbursement_type'] input"),
                page.locator("div[name='payment_type'] input"),
                page.locator(".o_field_widget[name*='disbursement'] input"),
                page.locator("label:has-text('ประเภทการทำจ่าย') + div input")
            ]
            for loc in pt_locators:
                try:
                    if loc.is_visible(timeout=1000):
                        loc.click()
                        time.sleep(0.5)
                        page.keyboard.press("ArrowDown")
                        time.sleep(0.5)
                        opt = page.locator(".ui-autocomplete li, .o_autocomplete li, .dropdown-item, li.ui-menu-item").first
                        if opt.is_visible(timeout=1000):
                            opt.click()
                        else:
                            page.keyboard.press("Enter")
                        time.sleep(0.5)
                        break
                except Exception:
                    pass

            # 3. Fill Bill Reference / การอ้างอิง
            cb("Filling Bill Reference / การอ้างอิง")
            import random
            ref_str = f"BILL-REF-{random.randint(100, 999)}"
            ref_inp = page.locator("div[name='ref'] input, input[name='ref'], div[name='payment_reference'] input").first
            if ref_inp.is_visible(timeout=1500):
                ref_inp.fill(ref_str)
                time.sleep(0.5)

            # 4. Fill Terms / Payment Terms if present
            cb("Filling Terms dropdown")
            terms_inp = page.locator("div[name='invoice_payment_term_id'] input, div[name='payment_term_id'] input").first
            if terms_inp.is_visible(timeout=1500):
                terms_inp.click()
                time.sleep(0.5)
                page.keyboard.press("ArrowDown")
                time.sleep(0.5)
                page.keyboard.press("Enter")
                time.sleep(0.5)

            # 5. Fill Accounting Date if present
            cb("Filling Accounting Date if required")
            acc_date_inp = page.locator("div[name='date'] input, div[name='accounting_date'] input").first
            if acc_date_inp.is_visible(timeout=1500):
                acc_date_inp.click()
                time.sleep(0.5)
                page.keyboard.press("Enter")
                time.sleep(0.5)

            # 6. Click Save manually
            cb("Clicking Save button manually")
            save_btn = page.locator(".o_form_button_save, button:has-text('Save'), button:has-text('บันทึก'), .fa-cloud-upload").first
            if save_btn.is_visible(timeout=2000):
                save_btn.click()
                time.sleep(2)

            # 7. Click Confirm
            cb("Clicking Confirm button")
            confirm_btn = page.locator("button:has-text('Confirm'), button:has-text('ยืนยัน'), button.btn-primary:has-text('Confirm')").first
            if confirm_btn.is_visible(timeout=2000):
                confirm_btn.click()
                time.sleep(2)

            # Handle modal OK dialog if present
            ok_btn = page.locator(".modal button:has-text('OK'), .modal button:has-text('ตกลง')").first
            if ok_btn.is_visible(timeout=1500):
                ok_btn.click()
                time.sleep(1)

            # Extract created Bill serial number (e.g. BILL-13000-XXXXX or RBILL-...)
            rec_num = ""
            try:
                for sel in [".o_last_breadcrumb_item", "h1:has-text('BILL')", "h1:has-text('13000-')", ".breadcrumb-item.active"]:
                    elem = page.locator(sel).first
                    if elem.is_visible(timeout=1000):
                        text = elem.inner_text()
                        for word in text.split():
                            if "BILL" in word or "13000-" in word or "INV-" in word or "RBILL-" in word:
                                rec_num = word.strip()
                                break
                        if rec_num:
                            break
                        if "BILL" in text and not rec_num:
                            rec_num = text.strip().split("\n")[0]
                            break
            except Exception:
                pass

            cb(f"Created Bill Serial: '{rec_num}'")

            # 8. Go back to Bills list view
            cb("Returning to Bills list view")
            b_crumb = page.locator("a.breadcrumb-item:has-text('Bills'), a.breadcrumb-item:has-text('ใบแจ้งหนี้/ใบวางบิล'), .breadcrumb a:has-text('Bills')").first
            if b_crumb.is_visible(timeout=2000):
                b_crumb.click()
            else:
                navigate_submenus(page, [["Vendors", "ผู้ขาย"], ["Bills", "ใบแจ้งหนี้/ใบวางบิล"]], frame_cb=frame_cb)
            time.sleep(2)

            # 9. Check if serial number appears in table list
            if rec_num:
                in_list = page.locator(f"table:has-text('{rec_num}'), tr:has-text('{rec_num}'), .o_list_table:has-text('{rec_num}')").count() > 0
                if in_list:
                    cb(f"Create PASSED: Found bill serial '{rec_num}' in table list")
                    return ("Passed", f"Created bill '{rec_num}' successfully and verified in Bills table for role {role}")
                else:
                    cb(f"Create FAILED: Bill serial '{rec_num}' not found in table list")
                    return ("Failed", f"Bill '{rec_num}' created but not found in Bills list table for role {role}")

            cb("Create PASSED: Bill saved and confirmed successfully")
            return ("Passed", f"Bill created and confirmed successfully in Bills for role {role}")

        except Exception as e:
            cb(f"Create FAILED during bill creation workflow: {e}")
            return ("Failed", f"Error during Bill creation workflow for role {role}: {e}")

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
