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

## 🔧 How to Customize & Tweak Settings

All system parameters can be customized without writing code:

### 1. Tweaking Credentials & Target URLs (`config.py`)
File path: `automate2/improved/config.py`
- **Target Site URL**: Change `SITE_URL` or `DATABASE_CODE` (`13000`).
- **IDM Stage 1 Credentials**: Change `IDM_USERNAME` and `IDM_PASSWORD`.
- **Role Credentials**: Update usernames/passwords for `Super Admin`, `Admin`, `Supervisor`, `Super User`, `User(Cashier)`, `Outsource`.

### 2. Customizing Test Cases & Functions
File path: `automate2/BOM_Role_TestCases_Accounting_Finance.xlsx`
- Edit test functions, expected results, or permission types directly in the master Excel sheet.
- Changes are automatically read on server start.

### 3. Editing Results & Syncing to Excel
- Edit table cells (**Function**, **Status**, **Comments**) directly inside the live web table.
- Click **Save & Sync to Current Excel** to persist edits directly to:
  - `automate2/test_results.xlsx`
  - `automate2/improved/reports/test_results.xlsx`

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
