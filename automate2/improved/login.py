"""
login.py - 2-stage IDM + Odoo role login helpers with continuous live streaming
"""

import time
from config import (
    SELECTOR_URL, DATABASE_CODE, IDM_USERNAME, IDM_PASSWORD,
    ROLE_CREDENTIALS, SEL_IDM_USER, SEL_IDM_PASS,
    SEL_LOGIN_USER, SEL_LOGIN_PASS, SEL_LOGIN_SUBMIT, VIEWPORT
)


def _live_wait(page, cb, seconds: float, label: str):
    """
    Sleep for `seconds` while continuously streaming live frames every 250ms.
    """
    t_end = time.time() + seconds
    while time.time() < t_end:
        cb(label)
        time.sleep(0.25)


def login(browser, role: str, frame_cb=None):
    """
    Create a fresh browser context and perform full 2-stage IDM + Odoo login.
    Streams continuous live frames throughout navigation.
    Returns (context, page) ready to use.
    """
    context = browser.new_context(viewport=VIEWPORT)
    page    = context.new_page()

    def cb(label):
        if frame_cb:
            try: frame_cb(page, label)
            except Exception: pass

    try:
        cred = ROLE_CREDENTIALS.get(role)
        if not cred:
            raise ValueError(f"No credentials configured for role: {role}")

        # ── Navigate to site ──────────────────────────────────────────────
        cb("Open browser home page")
        page.goto(SELECTOR_URL, wait_until="domcontentloaded")
        _live_wait(page, cb, 1.5, "Open browser home page")

        # ── Click 13000 database ───────────────────────────────────────────
        db = page.get_by_text(DATABASE_CODE, exact=True)
        if db.count() > 0 and db.first.is_visible():
            db.first.click()
            _live_wait(page, cb, 1.5, f"Selected DB {DATABASE_CODE}")

        # ── Click Sign in with IDM ─────────────────────────────────────────
        idm_btn = page.get_by_text("IDM", exact=False)
        if idm_btn.count() > 0 and idm_btn.first.is_visible():
            idm_btn.first.click()
            _live_wait(page, cb, 2.0, "Clicked IDM Sign-In")

        # ── Stage 1: fill IDM iframe (cmp.aa) ─────────────────────────────
        filled_idm = False
        for _ in range(12):
            _live_wait(page, cb, 0.8, "Scanning for IDM login iframe")
            for frame in list(page.frames):
                try:
                    u = frame.locator(SEL_IDM_USER)
                    if u.is_visible(timeout=500):
                        cb("Log to IDM")
                        u.fill(IDM_USERNAME)
                        cb("Log to IDM (Entered Username)")
                        frame.locator(SEL_IDM_PASS).fill(IDM_PASSWORD)
                        cb("Log to IDM (Entered Password)")
                        frame.locator(SEL_IDM_PASS).press("Enter")
                        _live_wait(page, cb, 3.5, "IDM Authenticating...")
                        filled_idm = True
                        cb("IDM Authenticated")
                        break
                except Exception:
                    pass
            if filled_idm:
                break

        # ── Stage 2: fill Odoo role login ─────────────────────────────────
        login_inp = page.locator(SEL_LOGIN_USER)
        for _ in range(12):
            if login_inp.is_visible(timeout=1000):
                cb(f"Log to Odoo ({role})")
                login_inp.fill(cred["username"])
                cb(f"Log to Odoo (Filled User {role})")
                page.locator(SEL_LOGIN_PASS).fill(cred["password"])
                cb(f"Log to Odoo (Filled Pass {role})")
                page.locator(SEL_LOGIN_SUBMIT).click()
                _live_wait(page, cb, 5.0, f"Logging in as {role}...")
                cb(f"Logged in as {role}")
                break
            _live_wait(page, cb, 0.8, f"Waiting for Odoo login form ({role})")

        return context, page

    except Exception as e:
        try:
            context.close()
        except Exception:
            pass
        raise RuntimeError(f"Login failed for role '{role}': {e}") from e
