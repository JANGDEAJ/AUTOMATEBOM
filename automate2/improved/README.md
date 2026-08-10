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
    ├── loader.py                    # In-memory Excel data loader & nav matrix cache
    ├── login.py                     # 2-stage IDM + Odoo role authentication helper
    ├── navigator.py                 # App Drawer & navigation switcher helpers
    ├── verifiers.py                 # Per-permission verification engines (Read, Create, Validate, Setting)
    ├── reporter.py                  # OpenPyXL report generator (Color-coded Excel + Summary tab)
    ├── run.py                       # CLI test execution runner
    ├── run.bat                      # Windows CLI interactive launcher script
    ├── reports/                     # Generated Excel reports (`test_results.xlsx`)
    ├── screenshots/                 # Captured test evidence screenshots
    └── webapp/
        ├── server.py                # Flask backend with Threading, SSE Stream & /api/update_row
        ├── start.bat                # Webapp server launcher
        └── static/
            ├── index.html           # Single Page App Dashboard UI
            ├── style.css            # Dark glassmorphism UI styles
            └── app.js               # In-memory filter engine, SSE client & Live Excel table
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
- Trigger button: `SEL_APP_DRAWER` (supports `a.appDrawerToggle`, `a.o_navbar_apps_menu`, `a[title='Apps']`).
- Dynamic element detection using `.get_by_text(alias, exact=True)`.

### 4. `verifiers.py`
Logic engines for all 4 permission types:
- **`Read`**: Checks if the target application page opens and presents readable content without Access Denied errors.
- **`Create`**: Navigates to app, checks for presence/absence of creation buttons (e.g. `New`, `Create`, `New Session` for POS).
- **`Validate`**: Navigates to app, scans for approval action buttons (`Approve`, `Validate`, `Confirm`).
- **`Setting`**: Scans application configuration headers (`Settings`, `Configuration`).

### 5. `webapp/server.py` & `loader.py`
Flask server providing REST APIs, SSE Streams, and in-memory Excel dataset caching:
- **In-Memory Cache**: Pre-warms Excel workbooks on server start for 0ms response latency on `/api/testcases`.
- **Fast Interruption**: Holds an atomic reference to Playwright's `_active_ctx`. When `/api/stop` is hit, it closes `_active_ctx` immediately.
- **Live Frame Streaming**: Emits `live_frame` base64 snapshots to the Web UI over SSE during test execution.
- **In-Place Excel Row Sync**: `/api/update_row` saves cell edits directly into `test_results.xlsx`.

---

## 🌐 Web Dashboard Features (`http://localhost:5000`)

1. **Live Synced Excel Table**: In-place cell editing for Function, Status, and Comments synced 2-way with `test_results.xlsx`.
2. **Two Separate Excel Options**:
   - **`Save & Sync Current`**: Persists in-memory edits directly to `test_results.xlsx` on the server in place without browser file download.
   - **`Download Excel File`**: Downloads the `.xlsx` report file to local storage.
3. **Sequential Auto-Next Execution**: Setting `Limit = 1` and clicking **Run Selected** automatically targets the next pending/untested test case (`TC-265`, then `TC-269`, etc.).
4. **Live Breakdown Status Graph**: Dynamic bar widget showing real-time distribution of Passed, Failed, Queued Target, and Matched cases.
5. **Continuous Live Proof Monitor**: Real-time browser frame streaming with Fullscreen 1200px popout modal.
6. **Latest-First Proof Feed**: Prepends freshly captured proof screenshots to the top of the Recent Proofs feed.
7. **Preset Shortcuts**: Quick presets (`Run All`, `Test Read`, `Test Create`, `Test Validate`, `Test Setting`) with instant matched case count context.

---

## 🚀 How to Run

### Option A: Web Dashboard (Recommended)
Double-click `START.bat` in the project root directory, or run:
```powershell
cd c:\Users\gaykn\Downloads\autobom\AUTOMATEBOM\automate2\improved\webapp
python server.py
```
Open **[http://localhost:5000](http://localhost:5000)** in browser.

### Option B: CLI Mode
```powershell
cd c:\Users\gaykn\Downloads\autobom\AUTOMATEBOM\automate2\improved

# Run all test cases in headless mode
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
- **App Drawer anchor**: Use fallback selector list in `SEL_APP_DRAWER` for Odoo top navbar compatibility.
- **Role Isolation**: Do not reuse Playwright contexts across different roles. Always close context and create `browser.new_context()`.
