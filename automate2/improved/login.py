"""
login.py - 2-stage IDM + Odoo role login helpers
"""

import time
from config import (
    SELECTOR_URL, DATABASE_CODE, IDM_USERNAME, IDM_PASSWORD,
    ROLE_CREDENTIALS, SEL_IDM_USER, SEL_IDM_PASS,
    SEL_LOGIN_USER, SEL_LOGIN_PASS, SEL_LOGIN_SUBMIT, VIEWPORT
)


def login(browser, role: str):
    """
    Create a fresh browser context and perform full 2-stage IDM + Odoo login.
    Returns (context, page) ready to use, or raises if login fails.
    """
    context = browser.new_context(viewport=VIEWPORT)
    page    = context.new_page()

    try:
        cred = ROLE_CREDENTIALS.get(role)
        if not cred:
            raise ValueError(f"No credentials configured for role: {role}")

        # ── Navigate to database selector ──────────────────────────────────
        page.goto(SELECTOR_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(2000)

        # ── Click 13000 database ───────────────────────────────────────────
        db = page.get_by_text(DATABASE_CODE, exact=True)
        if db.count() > 0 and db.first.is_visible():
            db.first.click()
            page.wait_for_timeout(2000)

        # ── Click Sign in with IDM ─────────────────────────────────────────
        idm_btn = page.get_by_text("IDM", exact=False)
        if idm_btn.count() > 0 and idm_btn.first.is_visible():
            idm_btn.first.click()
            page.wait_for_timeout(3000)

        # ── Stage 1: fill IDM iframe (cmp.aa) ─────────────────────────────
        filled_idm = False
        for _ in range(12):
            page.wait_for_timeout(1000)
            for frame in list(page.frames):
                try:
                    u = frame.locator(SEL_IDM_USER)
                    if u.is_visible(timeout=500):
                        u.fill(IDM_USERNAME)
                        frame.locator(SEL_IDM_PASS).fill(IDM_PASSWORD)
                        frame.locator(SEL_IDM_PASS).press("Enter")
                        page.wait_for_timeout(4000)
                        filled_idm = True
                        break
                except Exception:
                    pass
            if filled_idm:
                break

        # ── Stage 2: fill Odoo role login ─────────────────────────────────
        login_inp = page.locator(SEL_LOGIN_USER)
        for _ in range(12):
            if login_inp.is_visible(timeout=1000):
                login_inp.fill(cred["username"])
                page.locator(SEL_LOGIN_PASS).fill(cred["password"])
                page.locator(SEL_LOGIN_SUBMIT).click()
                page.wait_for_timeout(6000)
                break
            page.wait_for_timeout(1000)

        return context, page

    except Exception as e:
        try:
            context.close()
        except Exception:
            pass
        raise RuntimeError(f"Login failed for role '{role}': {e}") from e
