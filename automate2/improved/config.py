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

# App Grid Name Aliases (Thai UI & English names in User Matrix)
APP_ALIASES = {
    "Point of Sale": ["การขายหน้าร้าน", "Point of Sale", "Sessions", "รายการขาย"],
    "Sales":         ["การขาย", "Sales", "คำสั่งขาย/สั่งจอง"],
    "Accounting":    ["การบัญชี", "Accounting", "การเงิน"],
    "Purchase":      ["การจัดซื้อ", "Purchase"],
    "Inventory":     ["คลังสินค้า", "Inventory"],
    "Request":       ["การเบิกค่าใช้จ่าย", "Request", "Expenses", "My Expenses"],
    "Fleet":         ["การขนส่ง", "Fleet", "ยานพาหนะ", "พรบ."],
    "MPOS":          ["MPOS", "ข้อมูลปณอ."],
    "Contacts":      ["การติดต่อ", "Contacts"],
    "Settings":      ["การตั้งค่า", "Settings"],
    "Interface":     ["Interface"],
    "Contract":      ["การบริหารสัญญา"],
    "Report":        ["รายงานระดับเขต/นครหลวง", "รายงาน"],
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
SEL_APP_DRAWER   = "a.appDrawerToggle, a.o_navbar_apps_menu, a[title='Apps'], .o_main_navbar a.o_nav_entry, header nav a:first-child"
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
AUTOMATEBOM_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
EXCEL_SOURCE   = os.path.join(BASE_DIR, "..", "BOM_Role_TestCases_Accounting_Finance.xlsx")
REPORT_DIR     = os.path.join(AUTOMATEBOM_DIR, "reports")
SCREENSHOT_DIR = os.path.join(AUTOMATEBOM_DIR, "screenshots")
REPORT_FILE    = os.path.join(REPORT_DIR, "test_results.xlsx")

# Browser
VIEWPORT        = {"width": 1280, "height": 800}
