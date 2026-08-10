"""
run.py - Main entry point for BOM UAT Automation (all permission types)

Usage:
    python run.py                              # All tests, headed
    python run.py --headless                   # Headless mode
    python run.py --type Read                  # Only Read tests
    python run.py --type Read Create           # Read + Create tests
    python run.py --role "Super Admin"         # Only Super Admin
    python run.py --limit 10                   # First 10 rows only
    python run.py --tc TC-265 TC-266           # Specific TC IDs
"""

import sys, os, argparse, traceback
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from playwright.sync_api import sync_playwright
from config import SCREENSHOT_DIR, REPORT_DIR
from loader import load_testcases, load_nav_matrix
from login import login
from verifiers import run_verification
from reporter import save_report

ALL_PERMISSION_TYPES = [
    "Read",
    "Create",
    "Validate (approve/reject)",
    "Setting (set approver/master)",
]


def parse_args():
    p = argparse.ArgumentParser(description="BOM UAT Automation Runner")
    p.add_argument("--headless", action="store_true",  help="Run browser headless")
    p.add_argument("--type",  nargs="+", default=None, metavar="PERM",
                   help="Permission type(s) to run (default: all)")
    p.add_argument("--role",  nargs="+", default=None, metavar="ROLE",
                   help="Roles to filter (default: all)")
    p.add_argument("--limit", type=int,  default=None, help="Max test cases to run")
    p.add_argument("--tc",    nargs="+", default=None, metavar="TC_ID",
                   help="Specific TC IDs to run")
    return p.parse_args()


def main():
    args = parse_args()
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    os.makedirs(REPORT_DIR,     exist_ok=True)

    perm_types = args.type or ALL_PERMISSION_TYPES

    # Load data
    df  = load_testcases(permission_types=perm_types, roles=args.role, limit=args.limit)
    nav = load_nav_matrix()

    if args.tc:
        df = df[df["TC ID"].isin(args.tc)]

    total = len(df)
    print(f"\n BOM UAT Automation - {total} test cases | Types: {perm_types}")
    print("=" * 70)

    results  = []
    cur_role = None
    ctx      = None
    page_obj = None

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=args.headless)

        for idx, row in df.iterrows():
            tc_id   = row["TC ID"]
            role    = row["Role"]
            func    = row["Function"]
            ptype   = row["Permission Type"]
            expected= str(row.get("ผลที่คาดหวัง", "")).strip()

            nav_info = nav.get(func, {})
            app_name = nav_info.get("app", func)
            # Match primary app name to known aliases key
            for key in ["Point of Sale","Sales","Accounting","Purchase",
                        "Inventory","Request","Fleet","MPOS","Contacts","Settings"]:
                if key.lower() in app_name.lower():
                    app_name = key
                    break

            print(f"\n[{tc_id}] {ptype} | {role} | {func}")

            # Login if role changed
            if role != cur_role:
                if ctx:
                    try:
                        ctx.close()
                    except Exception:
                        pass
                try:
                    ctx, page_obj = login(browser, role)
                    cur_role = role
                    print(f"  Logged in as {role} -> {page_obj.url[:60]}")
                except Exception as e:
                    print(f"  [LOGIN FAILED] {e}")
                    results.append({**row.to_dict(), "Status": "Failed",
                                    "Comments": f"Login error: {str(e)[:100]}", "Screenshot": ""})
                    continue

            # Screenshot path
            ss_name = f"{tc_id}_{role.replace(' ','_')}_{ptype.replace(' ','_')[:10]}.png"
            ss_path = os.path.join(SCREENSHOT_DIR, ss_name)

            # Run verification
            status = comment = ""
            try:
                status, comment = run_verification(
                    page_obj, ptype, app_name, func, expected, role
                )
            except Exception as e:
                status  = "Failed"
                comment = f"Unexpected error: {traceback.format_exc()[:200]}"

            # Screenshot
            try:
                page_obj.screenshot(path=ss_path)
            except Exception:
                ss_path = ""

            # Navigate back to dashboard for next test
            try:
                from config import DASHBOARD_URL
                page_obj.goto(DASHBOARD_URL, wait_until="domcontentloaded")
                page_obj.wait_for_timeout(800)
            except Exception:
                pass

            icon = "OK" if status == "Passed" else ("!!!" if status == "Failed" else "---")
            print(f"  [{icon}] {status} | {comment}")

            results.append({**row.to_dict(), "Status": status,
                            "Comments": comment, "Screenshot": ss_path})

        if ctx:
            try:
                ctx.close()
            except Exception:
                pass
        browser.close()

    save_report(results)


if __name__ == "__main__":
    main()
