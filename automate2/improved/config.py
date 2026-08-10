"""
config.py - Centralized configuration for BOM UAT Automation
"""

import os

# Site & Database
SITE_URL        = "https://reg1-bom-uat.thpc.cc"
SELECTOR_URL    = f"{SITE_URL}/web/database/selector"
DASHBOARD_URL   = f"{SITE_URL}/web"
DATABASE_CODE   = "13000"

# IDM (Stage 1 SSO)
IDM_USERNAME = "cmp.aa"
IDM_PASSWORD = "THPCore@2024"

# Role Credentials (Stage 2 Odoo login)
ROLE_CREDENTIALS = {
    "Super Admin":    {"username": "uat.super_admin",  "password": "Uat@super_admin#2026"},
    "Admin":          {"username": "uat.admin",         "password": "Uat@admin#2026"},
    "Supervisor":     {"username": "uat.supervisor",    "password": "Uat@supervisor#2026"},
    "Super User":     {"username": "uat.super_user",    "password": "Uat@super_user#2026"},
    "User(Cashier)":  {"username": "uat.user",          "password": "Uat@user#2026"},
    "Outsource":      {"username": "uat.outsource",     "password": "Uat@outsource#2026"},
}

# App Grid Name Aliases (Thai UI may differ from English name in User Matrix)
APP_ALIASES = {
    "Point of Sale": ["Point of Sale", "Sessions"],
    "Sales":         ["Sales"],
    "Accounting":    ["Accounting"],
    "Purchase":      ["Purchase"],
    "Inventory":     ["Inventory"],
    "Request":       ["Request", "Expenses", "My Expenses"],
    "Fleet":         ["Fleet"],
    "MPOS":          ["MPOS"],
    "Contacts":      ["Contacts"],
    "Settings":      ["Settings"],
}

# Expected-Result Keywords per permission type
EXPECT = {
    "Read": {
        "pass_kw": ["เห็นเมนูและสามารถดูข้อมูลได้ปกติ"],
        "fail_kw": ["ไม่พบ", "ไม่แสดง"],
    },
    "Create": {
        "pass_kw": ["ระบบบันทึกข้อมูลสำเร็จ"],
        "fail_kw": ["ไม่มีปุ่มสร้างรายการ", "ไม่มีสิทธิ์"],
    },
    "Validate (approve/reject)": {
        "pass_kw": ["ระบบอนุมัติ/ปฏิเสธรายการสำเร็จ"],
        "fail_kw": ["ไม่มีปุ่ม Approve/Reject", "ไม่มีสิทธิ์"],
    },
    "Setting (set approver/master)": {
        "pass_kw": ["เข้าถึงหน้า Setting และบันทึกการตั้งค่าได้สำเร็จ"],
        "fail_kw": ["ไม่มีเมนู/ปุ่ม Setting", "ไม่มีสิทธิ์"],
    },
}

# CSS Selectors
SEL_APP_DRAWER   = "a.appDrawerToggle"
SEL_LOGIN_USER   = "input[name='login']"
SEL_LOGIN_PASS   = "input[name='password']"
SEL_LOGIN_SUBMIT = "button[type='submit']"
SEL_IDM_USER     = "#Ecom_User_ID"
SEL_IDM_PASS     = "#Ecom_Password"

# Create/Validate/Setting button signatures to check for
CREATE_BUTTON_SELECTORS    = ["button.o_form_button_save", "button:has-text('New')", "button:has-text('Create')", "a:has-text('New')"]
VALIDATE_BUTTON_SELECTORS  = ["button:has-text('Approve')", "button:has-text('Validate')", "button:has-text('Confirm')"]
SETTING_BUTTON_SELECTORS   = ["a.main_link:has-text('Settings')", "a:has-text('Configuration')", "a:has-text('General Settings')"]

# Paths
BASE_DIR       = os.path.dirname(os.path.abspath(__file__))
EXCEL_SOURCE   = os.path.join(BASE_DIR, "..", "BOM_Role_TestCases_Accounting_Finance.xlsx")
REPORT_DIR     = os.path.join(BASE_DIR, "reports")
SCREENSHOT_DIR = os.path.join(BASE_DIR, "screenshots")
REPORT_FILE    = os.path.join(REPORT_DIR, "test_results.xlsx")

# Browser
VIEWPORT        = {"width": 1280, "height": 800}
