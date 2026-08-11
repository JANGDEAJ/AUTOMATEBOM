# BOM UAT Automation Framework & Live Dashboard

This folder (`improved/`) contains the production-grade Playwright test automation suite and live web monitoring dashboard for **BOM UAT (Accounting & Finance)**.

---

## 🏗 System Architecture & Directory Structure

```
automate2/
├── START.bat
├── BOM_Role_TestCases_Accounting_Finance.xlsx
└── improved/
    ├── README.md
    ├── config.py          # Credentials, URLs, CSS selectors, app aliases
    ├── loader.py          # Excel loader & HQ/Branch role split logic
    ├── login.py           # 2-stage IDM + Odoo login
    ├── navigator.py       # App Drawer navigation helpers
    ├── verifiers.py       # Read/Create/Validate/Setting verification engines
    ├── reporter.py        # Color-coded Excel report generator
    ├── run.py             # CLI runner
    ├── reports/           # test_results.xlsx
    ├── screenshots/       # Proof screenshots
    └── webapp/
        ├── server.py      # Flask backend, SSE, persistent state
        └── static/
            ├── index.html
            ├── style.css
            └── app.js     # Dashboard JS, filter engine, SSE client
```

---

## 🔑 Key Core Modules

### 1. config.py
- **URL**: https://reg1-bom-uat.thpc.cc (DB: 13000)
- **IDM**: cmp.aa / THPCore@2024
- **Roles**: Super Admin (HQ), Super Admin (สาขา), Admin (HQ), Admin (สาขา), Supervisor, Super User, User(Cashier), Outsource

### 2. loader.py — HQ vs Branch Split
- `Super Admin` and `Admin` rows are auto-labeled `(HQ)` or `(สาขา)` based on the Function name.
- **Branch Functions** (20 functions e.g. การขายสินค้าและบริการเงินสด): labeled `(สาขา)`
- **Everything else**: labeled `(HQ)`
- No row duplication — each function belongs to exactly one category.

### 3. navigator.py — Standard Navigation
Default sequence for every test (unless told otherwise):
1. From Odoo home, open **App Drawer** (4-dots icon, top-left)
2. Click the **App icon** in the grid (e.g. Point of Sale)
3. Verify based on permission type

### 4. verifiers.py
- **Read**: Always opens app via App Drawer → App icon click. All roles use same path.
- **Create**: Checks for New/Create/สร้าง button.
- **Validate**: Checks for Approve/Validate/Confirm button.
- **Setting**: Checks for Configuration/Settings menu.

> **Rule**: All tests follow the same menu navigation path. The bot does NOT change the click sequence between roles unless explicitly instructed.

### 5. server.py — Persistent State
- **On boot**: Restores all previous results from `test_results.xlsx` into memory.
- **New runs**: Upsert into existing results — old results are never wiped.
- **Save & Sync**: Writes to Excel without touching or re-expanding the table.
- **Reset**: Clears one row to Pending in-place, no table re-expansion.
- **Cell edits**: Saved to disk immediately on change.
- **STRICT DATA SAFETY**: NEVER bulk-overwrite or reset existing `test_results.xlsx` statuses to Skipped. Existing saved results are strictly read-only and preserved.

---

## 📋 Testing Process

### Standard Navigation Sequence
1. Login (IDM → Odoo) with role credentials.
2. Open **App Drawer** (4-dots, top-left).
3. Click the **App icon**.
4. Verify result based on permission type.
5. Screenshot proof.
6. Return to Odoo home. Repeat.


- **Multi-language (Thai + English) Button Matching**: Verification engines automatically scan for both Thai (สร้าง, เปิดเซสชัน, สร้างใหม่, ยืนยัน, การตั้งค่า) and English (New, New Session, Create, Confirm, Settings) UI text variants.

## 📌 Test Batch Path Rules

Each test batch (defined by a TC range + permission type) has its own **fixed navigation path**.

**Rules:**
- Once a path is set for a range (e.g. Read TC-265 to TC-381), it stays permanently for that range.
- Working on a new range (e.g. Read TC-382 to TC-xxx) does NOT affect any previous range.
- Going back to a previous range always uses its original path — never the new one.
- Paths are NEVER changed unless the user explicitly says so.
- The user defines paths step-by-step. The bot waits for instructions before each new batch.

**Example:**
| Batch | Range | Path |
|-------|-------|------|
| Read | TC-265 to TC-381 | App Drawer → Point of Sale icon |
| Read | TC-382 to TC-xxx | (to be defined by user) |

Future batches will be added here as they are defined.

### Current Test Progress
| Range | App | Type | Notes |
|-------|-----|------|-------|
| TC-265 to TC-381 | Point of Sale | Read | In progress — all roles use same click path |

---

## 🌐 Dashboard Features (http://localhost:5000)

- Role chips: HQ and สาขา variants for Super Admin and Admin
- Save & Sync: saves to Excel, table unchanged
- Reset: clears one row to Pending in-place
- Live proof monitor + screenshot gallery
- Queue badges for sequential test execution

---

## 🚀 How to Run

```powershell
cd c:\Users\gaykn\Downloads\automate2\AUTOMATEBOM\automate2\improved\webapp
python server.py
```
Open http://localhost:5000
