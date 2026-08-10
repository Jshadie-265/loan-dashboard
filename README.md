# Loan Manager

A web-based loan management system built with Streamlit and SQLite. This application replaces spreadsheet-based loan tracking with a live dashboard, customer management, loan issuance, repayment tracking, and capital ledger — all backed by a SQLite database.

## Quick Start

To run the application:

```bash
pip install -r requirements.txt
streamlit run app.py
```

The app will open automatically in your default browser at `http://localhost:8501`.

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

## Installation

### 1. Clone or download this repository

```bash
cd loan_app
```

### 2. (Optional but recommended) Create a virtual environment

**Windows (PowerShell):**
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

**macOS/Linux:**
```bash
python -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `streamlit` — Web framework
- `pandas` — Data manipulation
- `plotly` — Interactive charts
- `openpyxl` — Excel file reading (for data import)

### 4. Run the application

```bash
streamlit run app.py
```

The app will open automatically in your default browser at `http://localhost:8501`.

If it doesn't open automatically, navigate to that URL manually.

### 5. (Optional) Import existing data

If you're migrating from an Excel workbook named `Loan.xlsx`:

```bash
python import_excel.py Loan.xlsx
```

This creates `loan_app.db` and imports data from the Capital, Loans, and Repayments sheets. It automatically creates customer records for unique borrower names found in the Loans sheet. Safe to re-run — it skips records with IDs that already exist.

## How to Use the App

### Getting Started

When you first launch the app, you'll see the **Dashboard** (home page) showing all business metrics and charts. Initially, all values will be zero since there's no data yet.

### Step-by-Step Workflow

#### 1️⃣ Add Capital (Start Here)

Before issuing loans, you need to have capital in the system:

1. Click **Capital** in the sidebar
2. Click the **"Log Capital Transaction"** button
3. Enter the transaction details:
   - **Date**: When the capital was added
   - **Transaction Type**: Select "Investment" (for adding money)
   - **Amount**: How much capital you're adding (e.g., 1,000,000)
   - **Source/Destination**: Where the money came from (e.g., "Owner Investment", "Bank Transfer")
   - **Notes**: Optional details about the transaction
4. Click **"Log Transaction"**
5. The capital ledger will update and show your running balance

**Example**: Add an initial investment of MWK 2,000,000 from "Owner Capital"

---

#### 2️⃣ Add Customers

Before issuing loans, you need to register borrowers:

1. Click **Customers** in the sidebar
2. Click the **"Add New Customer"** button
3. Fill in customer details:
   - **Full Name**: Borrower's complete name (required)
   - **Phone**: Contact number (optional)
   - **Address**: Physical address (optional)
   - **National ID**: ID number for identification (optional)
4. Click **"Add Customer"**
5. The customer will appear in the customer list below

You can add multiple customers. Use the search box to quickly find existing customers.

---

#### 3️⃣ Issue Loans

Now you can issue loans to registered customers:

1. Click **Loans** in the sidebar
2. Click the **"Issue New Loan"** button
3. Fill in the loan details:
   - **Select Borrower**: Choose from your customer list (dropdown)
   - **Date Taken**: When the loan was issued (defaults to today)
   - **Loan Period**: Choose a preset (2 Weeks, 1 Month, 3 Months) or select "Custom" to pick your own due date
   - **Principal Amount**: The amount being loaned (e.g., 100,000)
   - **Interest Rate (%)**: The interest rate (e.g., 20 for 20%)
   - **Bank**: Which bank the money was sent from (optional)
   - **Account Number**: Borrower's account (optional)
   - **Reference**: Transaction reference number (optional)
   - **Notes**: Any additional information (optional)
4. The app automatically calculates:
   - **Interest**: Principal × Rate (e.g., 100,000 × 20% = 20,000)
   - **Total Due**: Principal + Interest (e.g., 120,000)
5. Click **"Issue Loan"**
6. The loan will appear in the loan register below

**Tip**: The "Loan Register" section shows all loans with their status (Active, Paid, or Overdue). Use the filters to view specific categories or search for a particular borrower.

---

#### 4️⃣ Record Repayments

When borrowers make payments:

1. Click **Repayments** in the sidebar
2. Click the **"Record New Repayment"** button
3. Fill in payment details:
   - **Select Loan**: Choose the loan from the dropdown (shows borrower name, principal, and outstanding balance)
   - **Payment Date**: When the payment was received (defaults to today)
   - **Amount Paid**: How much was paid (e.g., 50,000)
   - **Payment Method**: How they paid (e.g., "Bank Transfer", "Cash", "Mobile Money")
   - **Notes**: Optional details (e.g., "Partial payment", "Full settlement")
4. Click **"Record Repayment"**
5. The loan balance will automatically update
6. If the full amount is paid, the loan status changes to **Paid**

**Important**: The app automatically calculates the remaining balance. If a loan is past its due date and still has a balance, it becomes **Overdue**.

---

#### 5️⃣ Monitor Dashboard

Return to the **Dashboard** (home page) at any time to see:

**Key Performance Indicators (KPIs):**
- 💰 **Total Capital**: All money invested in the business
- 💵 **Money Loaned**: Total principal amount currently out on loan
- 💳 **Available Cash**: Capital minus money loaned
- ⚠️ **Outstanding Balance**: Total amount still owed (principal + interest)
- 📈 **Interest Expected**: Total interest from all active/overdue loans
- ✅ **Profit Earned**: Interest collected from paid loans

**Loan Statistics:**
- Number of Active, Paid, and Overdue loans

**Visual Analytics:**
- **Loan Distribution Pie Chart**: Shows proportion of Active, Paid, and Overdue loans
- **Exposure by Borrower**: Horizontal bar chart showing who owes the most
- **Loan Disbursements Over Time**: Bar chart showing when loans were issued
- **Overdue Loans Table**: Lists all overdue loans with days overdue, helping prioritize collections

---

### Additional Features

#### Capital Management

- **Withdrawals**: Log capital withdrawals when you take money out of the business
  - Go to Capital page → Log Transaction → Select "Withdrawal"
  - The running balance will decrease accordingly

#### Search and Filters

- **Customer Search**: On the Customers page, use the search box to find customers by name
- **Loan Filters**: On the Loans page, filter by status (All/Active/Paid/Overdue) or search by borrower name
- **Repayment History**: On the Repayments page, view all payments with loan and borrower details

#### Understanding Loan Status

- **Active**: Loan has an outstanding balance and hasn't reached the due date yet
- **Paid**: Loan balance is zero (fully repaid)
- **Overdue**: Loan has an outstanding balance and has passed the due date

The app calculates these statuses automatically based on:
- Total due (principal + interest)
- Amount paid (sum of all repayments)
- Due date compared to today's date

---

### Common Workflows

**Scenario 1: First-time setup**
1. Add capital → Add customers → Issue loans → Record repayments → Monitor dashboard

**Scenario 2: Daily operations**
1. Record repayments as they come in
2. Check dashboard for overdue loans
3. Issue new loans as needed

**Scenario 3: End of month review**
1. Check dashboard for profit earned
2. Review overdue loans aging report
3. Analyze exposure by borrower chart
4. Review disbursement trends

## Features

### 💰 Dashboard (Home Page)
- **Real-time KPIs**: Total capital, money loaned, available cash, outstanding balance, interest expected, and profit earned
- **Loan Statistics**: Active, paid, and overdue loan counts
- **Visual Analytics**:
  - Pie chart showing loan distribution by status (Active/Paid/Overdue)
  - Horizontal bar chart of exposure by borrower
  - Time-series bar chart of loan disbursements
  - Overdue loan aging table with days overdue

### 👥 Customers Page
- Add new customers with full name, phone, address, and national ID
- View complete customer list
- Search and filter customers

### 📄 Loans Page
- **Issue new loans** with:
  - Borrower selection from customer list
  - Date taken and due date (with preset periods: 2 Weeks, 1 Month, 3 Months, or Custom)
  - Principal amount and interest rate
  - Automatic interest and total due calculation
  - Bank, account number, reference, and notes
- **Loan register** with filters by status and borrower
- View all loan details: principal, rate, interest, total due, amount paid, balance, and status

### 💵 Repayments Page
- Record payments against loans
- View repayment history
- Automatic balance and status updates

### 💼 Capital Page
- Log capital transactions (investments and withdrawals)
- Running balance calculation
- Complete capital ledger view

## Project Structure

```
loan_app/
├── app.py                      # Dashboard with KPIs and charts
├── db.py                       # SQLite database schema and connection
├── business_logic.py           # Business calculations and queries
├── import_excel.py             # One-time Excel migration script
├── requirements.txt            # Python dependencies
├── loan_app.db                 # SQLite database (created on first run)
├── .streamlit/
│   └── config.toml            # App theme configuration
└── pages/
    ├── 1_Customers.py          # Customer management
    ├── 2_Loans.py              # Loan issuance and register
    ├── 3_Repayments.py         # Payment recording and history
    └── 4_Capital.py            # Capital ledger
```

## Data Model

The application uses four main tables:

- **customers**: Customer/borrower information
- **loans**: Loan records with principal, rate, interest, and due dates
- **repayments**: Payment history linked to loans
- **capital**: Capital transaction ledger

All business metrics are computed live from the database — loan status (Active/Paid/Overdue) and balances are calculated on every page load based on due dates and payment history.

## Important Notes

### Database
- **SQLite** is suitable for single-user or small team use on a local network
- For concurrent multi-user access across different locations, migrate to PostgreSQL (most code changes needed only in `db.py`)
- Database file: `loan_app.db` (created automatically on first run)

### Loan Calculations
- Interest is **fixed at loan issuance** (principal × rate)
- Balance and status are **calculated live** from `total_due` minus sum of repayments
- Status determination:
  - **Paid**: Balance = 0
  - **Overdue**: Balance > 0 and due_date < today
  - **Active**: Balance > 0 and due_date ≥ today

## Troubleshooting

### Port already in use
If port 8501 is busy:
```bash
streamlit run app.py --server.port 8502
```

### Database locked error
Close other connections to `loan_app.db` or restart the app.

### Import errors
Make sure the virtual environment is activated and dependencies are installed:
```bash
pip install -r requirements.txt
```

## Currency

All monetary values are in **Malawian Kwacha (MWK)**, formatted with thousands separators (e.g., MWK 1,500,000.00).

## License

This project is provided as-is for internal business use.
