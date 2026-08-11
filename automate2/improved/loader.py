"""
loader.py - Load test cases and navigation matrix from Excel with in-memory caching
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import pandas as pd
from config import EXCEL_SOURCE, APP_ALIASES

_tc_cache = None
_nav_cache = None


def load_testcases(permission_types=None, roles=None, limit=None, force_reload=False) -> pd.DataFrame:
    """
    Load BOM_Role_TestCases sheet from memory cache (or Excel if uncached), filter by permission_types/roles.
    """
    global _tc_cache
    if _tc_cache is None or force_reload:
        df = pd.read_excel(EXCEL_SOURCE, sheet_name="BOM_Role_TestCases")
        df.columns = [c.strip() for c in df.columns]
        
        # Inject App column mapping using the nav matrix
        nav = load_nav_matrix(force_reload)
        def resolve_app(func):
            app_raw = nav.get(str(func).strip(), {}).get("app", "")
            app_name = str(app_raw).strip()
            # Normalize to short keys if possible
            for key in ["Point of Sale","Sales","Accounting","Purchase",
                        "Inventory","Request","Fleet","MPOS","Contacts","Settings"]:
                if key.lower() in app_name.lower():
                    return key
            return app_name if app_name and app_name != "nan" else func
            
        df["App"] = df["Function"].apply(resolve_app)
        
        # Branch Functions (สาขา)
        branch_functions = [
            "การขายสินค้าและบริการเงินสด (ขายสด)",
            "การขายสินค้าและบริการ (ขายเชื่อ)",
            "การปรับปรุงรายการรับชำระค่าบริการ/สินค้า",
            "การจัดทำใบลดหนี้ราคา กรณีขายสินค้า/บริการ",
            "การจัดทำใบเพิ่มหนี้",
            "การจัดทำใบเสนอราคา",
            "การจัดทำใบแจ้งหนี้",
            "การจัดทำใบวางบิล",
            "การคำนวณค่า Commission",
            "การจัดทำเงินรับล่วงหน้า (ธุรกิจตอบรับ)",
            "การตั้งหรือเพิ่มวงเงินสดย่อย",
            "การขอเบิกเงินสดย่อย",
            "การขอเบิกชดเชยเงินสดย่อย",
            "การขอเบิกค่าใช้จ่ายต่าง ๆ (Expense)",
            "การบริหารภาษีหัก ณ ที่จ่าย",
            "การเงินยืมระหว่างสาขา/ที่ทำการ",
            "การคืนเงินยืมระหว่างสาขา/ที่ทำการ",
            "การกระทบยอด เรียกเก็บค่าอากรพัสดุต่างประเทศ กรมศุลกากร",
            "การจัดทำวางเงินประกันสัญญา",
            "การจัดทำวางเงินประกันไปเช่าพื้นที่/อาคาร"
        ]
        
        def assign_hq_branch(row):
            role = str(row.get("Role", ""))
            func = str(row.get("Function", "")).strip()
            if role in ["Super Admin", "Admin"]:
                suffix = " (สาขา)" if func in branch_functions else " (HQ)"
                return role + suffix
            return role
            
        df["Role"] = df.apply(assign_hq_branch, axis=1)
        
        _tc_cache = df

    df = _tc_cache.copy()

    if permission_types:
        df = df[df["Permission Type"].isin(permission_types)]
    if roles:
        df = df[df["Role"].isin(roles)]
    if limit:
        df = df.head(int(limit))

    return df.reset_index(drop=True)


def load_nav_matrix(force_reload=False) -> dict:
    """
    Load User Matrix | THP Core sheet from memory cache (or Excel if uncached).
    """
    global _nav_cache
    if _nav_cache is not None and not force_reload:
        return _nav_cache

    df = pd.read_excel(EXCEL_SOURCE, sheet_name="User Matrix | THP Core")
    df.columns = [c.strip() for c in df.columns]
    
    # Forward-fill Function and App columns
    df["Function"] = df["Function"].ffill()
    app_col = "Unnamed: 2" if "Unnamed: 2" in df.columns else df.columns[2]
    df[app_col] = df[app_col].ffill()

    nav = {}
    for _, row in df.iterrows():
        func  = str(row.get("Function", "")).strip()
        app_raw = str(row.get(app_col, "")).strip()
        primary_app = app_raw.split("\n")[0].strip()
        if func and primary_app and primary_app != "nan":
            nav[func] = {"app": primary_app, "full_path": app_raw}

    _nav_cache = nav
    return nav
