# 🚀 BOM UAT Automation & Live Proof Dashboard

Production-grade Playwright UAT test automation engine and live web monitoring dashboard for **BOM (Accounting & Finance)**.

---

## ⚡ Quick Start & Installation Guide

Follow these simple steps to install and run the project on any computer:

### 1. Prerequisites
- **Python 3.10+**: Ensure Python is installed ([python.org](https://www.python.org/downloads/)).
- **Git**: Ensure Git is installed ([git-scm.com](https://git-scm.com/)).

### 2. Clone the Repository
```bash
git clone https://github.com/JANGDEAJ/AUTOMATEBOM.git
cd AUTOMATEBOM
```

### 3. Install Dependencies
Install required Python libraries and Playwright browser drivers:
```bash
pip install -r requirements.txt
playwright install chromium
```

---

## 🌐 How to Launch the Web Dashboard

### Option A: 1-Click Launcher (Windows)
Double-click `START.bat` in the project root directory.

### Option B: Command Line Launcher
```bash
cd automate2/improved/webapp
python server.py
```
Open **[http://localhost:5000](http://localhost:5000)** in your browser.

---

## 🔥 Key Features & Workflow

1. **Sequential Queue Auto-Advancement**:
   - When running with limits (`Limit = 1` or `N`), the queue badges (`#1`, `#2`...) automatically skip completed test cases (`Passed`, `Failed`, `Skipped`) and target the **next pending test cases** in the queue.

2. **Robust Page Read Verification**:
   - `verify_read` verifies whether application pages display readable content. Any loaded page without `Access Denied` or `Access Error` dialogs evaluates as **Passed**.

3. **Fail-Proof Live Screen Monitor**:
   - Features a dual SSE stream and direct 300ms HTTP poller (`/api/live_frame`) ensuring continuous, real-time live browser screen updates during execution.

4. **Multi-Location Excel Synchronization**:
   - Editing table cells (**Function**, **Status**, **Comments**) or clicking **Save & Sync to Current Excel** updates `test_results.xlsx` across all project directories simultaneously:
     - `automate2/test_results.xlsx`
     - `automate2/improved/reports/test_results.xlsx`
     - `AUTOMATEBOM/test_results.xlsx`

5. **Untouched Original Master Plan**:
   - Master test case template (`BOM_Role_TestCases_Accounting_Finance.xlsx`) remains 100% read-only and untouched.

---

## 🔧 How to Customize & Tweak Settings

### 1. Credentials & Target URLs (`config.py`)
File path: `automate2/improved/config.py`
- Change `SITE_URL` or `DATABASE_CODE` (`13000`).
- Update IDM Stage 1 credentials (`cmp.aa`) or role credentials (`Super Admin`, `Admin`, `Supervisor`, `Super User`, `User(Cashier)`, `Outsource`).

### 2. Master Test Cases
File path: `automate2/BOM_Role_TestCases_Accounting_Finance.xlsx`
- Edit test functions, expected results, or permission types directly in the master Excel sheet.

---

## 💻 CLI Mode (Headless Execution)

To run automated tests directly from terminal:
```bash
cd automate2/improved

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

## 📁 Output Reports & Evidence

- 📊 **Excel Reports**: `automate2/test_results.xlsx` & `automate2/improved/reports/test_results.xlsx`
- 📸 **Proof Screenshots**: `automate2/improved/screenshots/`
