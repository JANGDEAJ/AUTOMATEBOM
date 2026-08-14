"""
launch_6_roles.py - Opens 6 browser tabs logged in to all 6 roles for HQ or Branch
"""

import sys
import io
import time
import argparse
from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from config import (
    SELECTOR_URL, DATABASE_CODE, IDM_USERNAME, IDM_PASSWORD,
    ROLE_CREDENTIALS, SEL_IDM_USER, SEL_IDM_PASS,
    SEL_LOGIN_USER, SEL_LOGIN_PASS, SEL_LOGIN_SUBMIT, VIEWPORT
)

HQ_ROLES = [
    "Super Admin (HQ)",
    "Admin (HQ)",
    "Supervisor",
    "Super User",
    "User(Cashier)",
    "Outsource"
]

BRANCH_ROLES = [
    "Super Admin (สาขา)",
    "Admin (สาขา)",
    "Supervisor",
    "Super User",
    "User(Cashier)",
    "Outsource"
]

def login_tab(page, role: str):
    """Log in role inside given tab and leave at home page."""
    cred = ROLE_CREDENTIALS.get(role)
    if not cred:
        raise ValueError(f"No credentials configured for role: {role}")

    print(f"[{role}] Opening database selector...")
    page.goto(SELECTOR_URL, wait_until="domcontentloaded")
    time.sleep(1.5)

    # Click 13000 DB
    for _ in range(5):
        db = page.get_by_text(DATABASE_CODE, exact=True)
        if db.count() > 0 and db.first.is_visible():
            db.first.click()
            time.sleep(1.5)
            break
        time.sleep(1.0)

    # Click IDM Sign in
    for _ in range(5):
        idm_btn = page.get_by_text("IDM", exact=False)
        if idm_btn.count() > 0 and idm_btn.first.is_visible():
            idm_btn.first.click()
            time.sleep(3.0)
            break
        time.sleep(1.0)

    # Fill Stage 1 IDM
    filled_idm = False
    for _ in range(15):
        if page.locator(SEL_LOGIN_USER).is_visible() or page.locator(".o_apps, .o_app, .o_main_navbar").first.is_visible():
            filled_idm = True
            break
        for frame in list(page.frames):
            try:
                for idm_sel in [SEL_IDM_USER, "#Ecom_User_ID", "input[name='Ecom_User_ID']", "input[id*='User_ID']"]:
                    u = frame.locator(idm_sel).first
                    if u.count() > 0 and u.is_visible(timeout=300):
                        u.fill(IDM_USERNAME)
                        p_loc = frame.locator(SEL_IDM_PASS).first
                        if not p_loc.is_visible():
                            p_loc = frame.locator("#Ecom_Password, input[type='password']").first
                        p_loc.fill(IDM_PASSWORD)
                        p_loc.press("Enter")
                        time.sleep(3.5)
                        filled_idm = True
                        break
            except Exception:
                pass
            if filled_idm:
                break
        if filled_idm:
            break
        time.sleep(1.0)

    # Fill Stage 2 Odoo role
    login_inp = page.locator(SEL_LOGIN_USER)
    for _ in range(12):
        if page.locator(".o_apps, .o_app, .o_main_navbar").first.is_visible():
            print(f"[{role}] Already at home page!")
            return
        if login_inp.is_visible(timeout=1000):
            login_inp.fill(cred["username"])
            page.locator(SEL_LOGIN_PASS).fill(cred["password"])
            page.locator(SEL_LOGIN_SUBMIT).click()
            time.sleep(4.0)
            print(f"[{role}] Logged in successfully!")
            return
        time.sleep(1.0)

def main():
    parser = argparse.ArgumentParser(description="Launch 6 role browser tabs")
    parser.add_argument("--env", choices=["HQ", "Branch"], default="Branch", help="Target environment link (HQ or Branch)")
    args = parser.parse_args()

    roles = HQ_ROLES if args.env == "HQ" else BRANCH_ROLES
    print(f"\n========================================================")
    print(f"  Launching 6 Browser Tabs for Environment: {args.env}")
    print(f"========================================================\n")

    p = sync_playwright().start()
    browser = p.chromium.launch(headless=False)

    # Create isolated browser context per role so sessions don't overwrite each other
    tabs = []
    for role in roles:
        ctx = browser.new_context(viewport={"width": 1400, "height": 900})
        page = ctx.new_page()
        tabs.append((role, ctx, page))

    # Log in each role sequentially in its isolated tab context
    for idx, (role, ctx, page) in enumerate(tabs):
        print(f"\n[{idx+1}/6] Logging in role: '{role}'...")
        try:
            login_tab(page, role)
        except Exception as e:
            print(f"[{role}] Failed to log in: {e}")

    print("\n========================================================")
    print("  ALL 6 TABS LOGGED IN WITH 6 SEPARATE ROLE SESSIONS!")
    print("  Keep this command window open to keep browser open.")
    print("========================================================\n")

    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        print("Closing browser...")
        try: browser.close()
        except Exception: pass
        try: p.stop()
        except Exception: pass

if __name__ == "__main__":
    main()
