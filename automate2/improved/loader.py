"""
loader.py - Load test cases and navigation matrix from Excel
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import pandas as pd
from config import EXCEL_SOURCE, APP_ALIASES


def load_testcases(permission_types=None, roles=None, limit=None) -> pd.DataFrame:
    """
    Load BOM_Role_TestCases sheet, filter by permission_types and/or roles.
    """
    df = pd.read_excel(EXCEL_SOURCE, sheet_name="BOM_Role_TestCases")

    # Normalise column names - strip whitespace
    df.columns = [c.strip() for c in df.columns]

    if permission_types:
        df = df[df["Permission Type"].isin(permission_types)]
    if roles:
        df = df[df["Role"].isin(roles)]
    if limit:
        df = df.head(int(limit))

    return df.reset_index(drop=True)


def load_nav_matrix() -> dict:
    """
    Load User Matrix | THP Core sheet and build a dict:
    {func_name: {"app": "Point of Sale", ...}}
    Columns 2 (Unnamed: 2) onwards contain the App name per role.
    We use column 2 (Super Admin app) as the canonical app name.
    """
    df = pd.read_excel(EXCEL_SOURCE, sheet_name="User Matrix | THP Core")
    df.columns = [c.strip() for c in df.columns]
    df["Function"] = df["Function"].ffill()

    nav = {}
    for _, row in df.iterrows():
        func  = str(row.get("Function", "")).strip()
        # Column index 2 = "Unnamed: 2" = app name for Super Admin
        app_raw = str(row.iloc[2]).strip()
        # Some cells have multi-line app paths e.g. "Point of Sale\nAccounting/..."
        primary_app = app_raw.split("\n")[0].strip()
        if func and primary_app and primary_app != "nan":
            nav[func] = {"app": primary_app, "full_path": app_raw}
    return nav
