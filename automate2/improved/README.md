# BOM UAT Automation Framework & Live Dashboard

This folder (`improved/`) contains the production-grade, token-optimized Playwright test automation suite and live web monitoring dashboard for **BOM UAT (Accounting & Finance)**.

---

## 🏗 System Architecture & Directory Structure

```
automate2/
├── START.bat                        # Unified 1-click launcher (Root level)
├── BOM_Role_TestCases_Accounting_Finance.xlsx  # Master Test Case Excel sheet
└── improved/
    ├── README.md                    # System documentation for AI agents & developers
    ├── config.py                    # Credentials, URL parameters, CSS selectors & app aliases
    ├── loader.py                    # Excel data loader (Test cases & User Matrix mapping)
    ├── login.py                     # 2-stage IDM + Odoo role authentication helper
    ├── navigator.py                 # App Drawer & navigation switcher helpers
    ├── verifiers.py                 # Per-permission verification engines (Read, Create, Validate, Setting)
    ├── reporter.py                  # OpenPyXL report generator (Color-coded Excel + Summary tab)
    ├── run.py                       # CLI test execution runner
    ├── run.bat                      # Windows CLI interactive launcher script
    ├── reports/                     # Generated Excel reports (`test_results.xlsx`)
    ├── screenshots/                 # Captured test evidence screenshots
    └── webapp/
        ├── server.py                # Flask backend with Threading, Instant Interruption & SSE Stream
        ├── start.bat                # Webapp server launcher
        ├── static/
        │   ├── index.html           # Single Page App Dashboard UI
        │   ├── style.css            # Dark glassmorphism UI styles
        │   └── app.js               # EventSource (SSE) client, live monitor controller & table state
        ├── ss_live_monitor.png      # Dashboard preview screenshot
        ├── ss_run.png
        ├── ss_config.png
        └── ss_summary.png
```

---

## 🔑 Key Core Modules

### 1. `config.py`
Central repository for configuration settings:
- **Target URL**: `https://reg1-bom-uat.thpc.cc` (Database: `13000`).
- **IDM Stage 1 Credentials**: `cmp.aa` / `THPCore@2024`.
- **Role Credentials**: Credentials mapped for 6 roles (`Super Admin`, `Admin`, `Supervisor`, `Super User`, `User(Cashier)`, `Outsource`).
- **App Aliases Map**: Aliases mapping English module names (e.g. `Point of Sale`, `Accounting`, `Sales`) to Thai UI labels.

### 2. `login.py`
Executes 2-stage isolated login:
- **Stage 1 (IDM SSO)**: Interacts with `#Ecom_User_ID` iframe inside database `13000`.
- **Stage 2 (Odoo Role Login)**: Fills role-specific `input[name='login']` and `input[name='password']`.
- **Session Isolation**: Spawns fresh browser context (`browser.new_context()`) per role switch to avoid session leak.

### 3. `navigator.py`
Handles menu navigation:
- Trigger button: `a.appDrawerToggle` (4-dots icon).
- Dynamic element detection using `.get_by_text(alias, exact=True)`.

### 4. `verifiers.py`
Logic engines for all 4 permission types:
- **`Read`**: Scans App Drawer for visibility of the target application. PASS if visible when expected, HIDDEN when expected hidden.
- **`Create`**: Navigates to app, checks for presence/absence of creation buttons (e.g. `New`, `Create`, `New Session` for POS).
- **`Validate`**: Navigates to app, scans for approval action buttons (`Approve`, `Validate`, `Confirm`).
- **`Setting`**: Scans application configuration headers (`Settings`, `Configuration`).

### 5. `webapp/server.py`
Flask server providing REST APIs & Server-Sent Events (SSE):
- **Fast Interruption**: Holds an atomic reference to Playwright's `_active_ctx`. When `/api/stop` is hit, it closes `_active_ctx` immediately, halting ongoing Playwright commands instantly without waiting for timeouts.
- **Live Frame Streaming**: Emits `live_frame` base64 snapshots to the Web UI over SSE during test execution.
- **Proof Freeze Delay**: Holds proof screenshots on screen for a user-configurable duration (`proof_delay`) before clearing context.

---

## 🌐 Web Dashboard Features (`http://localhost:5000`)

1. **Live Proof Monitor**: Side panel displaying live screen frames during execution.
2. **Instant Stop**: Immediately halts running tests without browser hang.
3. **Proof Freeze Delay Selector**: Choose hold time (`0s`, `1.5s`, `3s`, `5s`) for visual inspection.
4. **Interactive Filters**: Toggle chips for Permission Types & Roles, set TC limits, or specify comma-separated TC IDs.
5. **Retry Failed Button**: Re-runs only failed test cases from previous execution.
6. **Detailed TC Modal**: Click any TC ID in the table to inspect step-by-step instructions, expected results, and screenshots.
7. **Report Exporting**: Export filtered view as CSV or download full formatted Excel reports.

---

## 🚀 How to Run

### Option A: Web Dashboard (Recommended)
Double-click `START.bat` in the project root directory, or run:
```powershell
cd c:\Users\gaykn\Downloads\automate2\improved\webapp
python server.py
```
Open **[http://localhost:5000](http://localhost:5000)** in browser.

### Option B: CLI Mode
```powershell
cd c:\Users\gaykn\Downloads\automate2\improved

# Run all 672 test cases in headless mode
python run.py --headless

# Run Read tests only
python run.py --headless --type Read

# Run Super Admin Create tests only
python run.py --type Create --role "Super Admin"

# Run specific TC IDs
python run.py --tc TC-265 TC-266 TC-267
```

---

## 💡 Guidance for Future Agents

- **Always maintain UTF-8 encoding**: Explicitly reconfigure `sys.stdout.reconfigure(encoding="utf-8")` when adding print statements.
- **Avoid networkidle**: Use `domcontentloaded` for Odoo pages due to long-polling WebSockets.
- **App Drawer anchor**: `a.appDrawerToggle` is the only reliable toggle for Odoo's top application grid.
- **Role Isolation**: Do not reuse Playwright contexts across different roles. Always close context and create `browser.new_context()`.
