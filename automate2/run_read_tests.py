import os
import sys
import time
import argparse
import pandas as pd
from datetime import datetime
from playwright.sync_api import sync_playwright

# Set stdout encoding for Windows console Thai characters
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

EXCEL_PATH = os.path.join(os.path.dirname(__file__), 'BOM_Role_TestCases_Accounting_Finance.xlsx')
RESULTS_PATH = os.path.join(os.path.dirname(__file__), 'test_results_read.xlsx')
SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), 'screenshots')

BLUE_SITE_URL = "https://reg1-bom-uat.thpc.cc/web/database/selector"

def load_credentials():
    df_user = pd.read_excel(EXCEL_PATH, sheet_name='User')
    creds = {}
    for _, row in df_user.iterrows():
        role = str(row['Role']).strip() if pd.notna(row['Role']) else ''
        login = str(row['login']).strip() if pd.notna(row['login']) else ''
        pwd = str(row['password']).strip() if pd.notna(row['password']) else ''
        if role and login and pwd and login.startswith('uat.'):
            creds[role] = {'username': login, 'password': pwd}
    # Map common excel role names to cred keys
    role_map = {
        'Super Admin': 'Super Admin (ฝ่าย/หนปณ.)',
        'Admin': 'Admin (ฝช.)',
        'Supervisor': 'Supervisor',
        'Super User': 'Super User',
        'User(Cashier)': 'User (Cashier)',
        'User (Cashier)': 'User (Cashier)',
        'Outsource': 'Outsource',
        'IDM': 'IDM'
    }
    return creds, role_map

def load_read_testcases():
    df_tc = pd.read_excel(EXCEL_PATH, sheet_name='BOM_Role_TestCases')
    read_tc = df_tc[df_tc['Permission Type'] == 'Read'].copy()
    return read_tc

def load_navigation_matrix():
    df_matrix = pd.read_excel(EXCEL_PATH, sheet_name='User Matrix | THP Core')
    nav_map = {}
    for _, row in df_matrix.iterrows():
        fn = row.get('Function')
        path = row.get('Unnamed: 2')
        if pd.notna(fn) and pd.notna(path):
            fn_str = str(fn).strip()
            path_str = str(path).strip()
            # Extract top-level App name (e.g. "Point of Sale", "Accounting", "Sales", etc.)
            app_name = path_str.split('/')[0].split('\n')[0].strip()
            nav_map[fn_str] = {'path': path_str, 'app': app_name}
    return nav_map

def run_tests(headed=True, target_role=None, limit=None):
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    creds, role_map = load_credentials()
    read_tc = load_read_testcases()
    nav_matrix = load_navigation_matrix()

    if target_role:
        read_tc = read_tc[read_tc['Role'].str.contains(target_role, case=False, na=False)]
    if limit:
        read_tc = read_tc.head(int(limit))

    print(f"Loaded {len(read_tc)} Read test cases to execute.")
    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not headed)
        context = None
        page = None

        current_logged_role = None

        for idx, row in read_tc.iterrows():
            tc_id = row['TC ID']
            role = row['Role']
            func_name = row['Function']
            step_desc = row['ขั้นตอนทดสอบ']

            mapped_role_key = role_map.get(role, role)
            user_cred = creds.get(mapped_role_key)

            print(f"\n[{tc_id}] Role: {role} | Function: {func_name}")
            
            if not user_cred:
                print(f"  [SKIP] No credentials found for role: {role}")
                results.append({**row.to_dict(), 'Status': 'Skipped', 'Comments': 'No credentials in User sheet'})
                continue

            # Handle Login if role changed
            if current_logged_role != role:
                print(f"  --> Logging in as {role} ({user_cred['username']})...")
                try:
                    if context:
                        try:
                            context.close()
                        except Exception:
                            pass
                    context = browser.new_context(viewport={'width': 1280, 'height': 800})
                    page = context.new_page()

                    page.goto(BLUE_SITE_URL, wait_until='domcontentloaded')
                    page.wait_for_timeout(2000)
                    
                    # If database selector is present, click 13000
                    db_link = page.get_by_text("13000", exact=True)
                    if db_link.count() > 0 and db_link.first.is_visible():
                        db_link.first.click()
                        page.wait_for_timeout(2000)

                    # Click "Sign in with IDM" if present
                    idm_btn = page.get_by_text("IDM", exact=False)
                    if idm_btn.count() > 0 and idm_btn.first.is_visible():
                        idm_btn.first.click()
                        page.wait_for_timeout(3000)

                    # Stage 1: Check for IDM iframe with #Ecom_User_ID and fill IDM creds (cmp.aa)
                    idm_cred = creds.get('IDM', {'username': 'cmp.aa', 'password': 'THPCore@2024'})
                    for _ in range(10):
                        page.wait_for_timeout(1000)
                        filled_idm = False
                        for f in list(page.frames):
                            try:
                                if f.locator('#Ecom_User_ID').is_visible(timeout=500):
                                    f.fill('#Ecom_User_ID', idm_cred['username'])
                                    f.fill('#Ecom_Password', idm_cred['password'])
                                    f.locator('#Ecom_Password').press('Enter')
                                    page.wait_for_timeout(4000)
                                    filled_idm = True
                                    break
                            except Exception:
                                pass
                        if filled_idm:
                            break

                    # Stage 2: Wait for Odoo login form to appear after IDM redirect and fill role credentials
                    login_inp = page.locator("input[name='login']")
                    logged_in_stage2 = False
                    for _ in range(10):
                        if login_inp.is_visible(timeout=1000):
                            login_inp.fill(user_cred['username'])
                            page.locator("input[name='password']").fill(user_cred['password'])
                            page.locator("button[type='submit']").click()
                            page.wait_for_timeout(6000)
                            logged_in_stage2 = True
                            break
                        page.wait_for_timeout(1000)

                    print(f"  [LOGIN DEBUG] Current URL after Stage 2: {page.url}")
                    current_logged_role = role
                except Exception as e:
                    print(f"  [ERROR] Login failed: {e}")
                    results.append({**row.to_dict(), 'Status': 'Failed', 'Comments': f'Login error: {str(e)[:100]}'})
                    continue

            # Perform Read Navigation / Verification
            expected_result = str(row.get('ผลที่คาดหวัง', '')).strip()
            should_be_hidden = 'ไม่พบ' in expected_result or 'ไม่แสดง' in expected_result

            nav_info = nav_matrix.get(func_name, {})
            target_app = nav_info.get('app', func_name)

            status = 'Failed'
            comment = ''
            screenshot_path = os.path.join(SCREENSHOT_DIR, f"{tc_id}_{role}.png")

            try:
                # Step 1: Open 4 dots app switcher icon (exact selector: a.appDrawerToggle)
                app_switcher = page.locator("a.appDrawerToggle, .o_navbar_apps_menu, a[accesskey='A']").first
                if app_switcher.is_visible(timeout=5000):
                    app_switcher.click()
                    page.wait_for_timeout(2000)

                # Map English App names to target App grid names
                app_aliases = {
                    'Point of Sale': ['Point of Sale', 'รายการขาย', 'Sessions'],
                    'Sales': ['Sales', 'คำสั่งขาย/สั่งจอง'],
                    'Accounting': ['Accounting', 'การเงิน', 'การบัญชี'],
                    'Request': ['Request', 'Expenses', 'My Expenses'],
                    'Fleet': ['Fleet', 'ยานพาหนะ', 'พรบ.'],
                    'MPOS': ['MPOS', 'ข้อมูลปณอ.']
                }

                target_aliases = app_aliases.get(target_app, [target_app, func_name])

                # Step 2: Look for target App icon in App grid
                is_visible = False
                found_alias = ''
                for alias in target_aliases:
                    loc = page.get_by_text(alias, exact=True)
                    if loc.count() == 0:
                        loc = page.locator(".o_app, .o_caption, a.dropdown-item, a.main_link").filter(has_text=alias)
                    
                    for i in range(loc.count()):
                        target_elem = loc.nth(i)
                        if target_elem.is_visible():
                            is_visible = True
                            found_alias = alias
                            try:
                                target_elem.click()
                                page.wait_for_timeout(1000)
                            except Exception:
                                pass
                            break
                    if is_visible:
                        break

                if should_be_hidden:
                    if not is_visible:
                        status = 'Passed'
                        comment = f"PASS: App/Menu '{target_app}' ({func_name}) is correctly HIDDEN as expected"
                    else:
                        status = 'Failed'
                        comment = f"FAIL: App/Menu '{target_app}' (found '{found_alias}') IS VISIBLE but should be HIDDEN for role {role}"
                else:
                    if is_visible:
                        status = 'Passed'
                        comment = f"PASS: App/Menu '{target_app}' (found '{found_alias}') is VISIBLE and accessible"
                    else:
                        status = 'Failed'
                        comment = f"FAIL: App/Menu '{target_app}' ({func_name}) NOT FOUND in App grid"
                
                page.screenshot(path=screenshot_path)
                # Navigate back to main web dashboard for next test case
                try:
                    page.goto("https://reg1-bom-uat.thpc.cc/web", wait_until='domcontentloaded')
                    page.wait_for_timeout(1000)
                except Exception:
                    pass
            except Exception as e:
                status = 'Failed'
                comment = f"Verification error: {str(e)[:150]}"
                page.screenshot(path=screenshot_path)
                try:
                    page.goto("https://reg1-bom-uat.thpc.cc/web", wait_until='domcontentloaded')
                    page.wait_for_timeout(1000)
                except Exception:
                    pass

            print(f"  Result: {status} | Comment: {comment}")
            results.append({
                **row.to_dict(),
                'Status': status,
                'Comments': comment,
                'Screenshot': screenshot_path
            })

        browser.close()

    # Save results to Excel
    res_df = pd.DataFrame(results)
    res_df.to_excel(RESULTS_PATH, index=False)
    print(f"\nExecution finished! Report saved to {RESULTS_PATH}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run Accounting & Finance Read Permission Test Cases")
    parser.add_argument('--headless', action='store_true', help="Run browser in headless mode")
    parser.add_argument('--role', type=str, help="Filter by specific role")
    parser.add_argument('--limit', type=int, help="Limit number of test cases")
    args = parser.parse_args()

    run_tests(headed=not args.headless, target_role=args.role, limit=args.limit)
