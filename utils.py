import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st
import datetime

# Setup Google Sheets access
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

# Google Sheet ID and Sheet Names
SPREADSHEET_ID = "15kcMP0G1xh84P1k7Yc_0R0g9VC3qkN17MAGnPA6FHmk"
EXPENSE_SHEET = "Transactions"
INCOME_SHEET = "Income"
BUDGET_SHEET = "Budgets"

# ========= Budget Functions =========

@st.cache_data(ttl=60)  # cache for 1 minute to avoid API rate limit
def load_budgets(month=None):
    """
    Load budgets for all categories (or a specific month) from Google Sheet.
    Returns a DataFrame: columns = ['Month', 'Category', 'BudgetAmount']
    """
    try:
        sheet = client.open_by_key(SPREADSHEET_ID).worksheet(BUDGET_SHEET)
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        if month:
            df = df[df["Month"] == month]
        return df
    except Exception as e:
        print("❌ Error loading budgets:", e)
        return pd.DataFrame(columns=["Month", "Category", "BudgetAmount"])

def save_budget(month, category, budget_amount):
    """
    Save or update the budget for a given category and month.
    If already present, it updates. If not, it appends.
    """
    try:
        df = load_budgets()  # cached version is OK
        mask = (df["Month"] == month) & (df["Category"] == category)
        sheet = client.open_by_key(SPREADSHEET_ID).worksheet(BUDGET_SHEET)

        if mask.any():
            idx = df[mask].index[0] + 2  # header is row 1
            sheet.update_cell(idx, 3, budget_amount)  # Column 3 = BudgetAmount
            print(f"Updated budget for {category} in {month}")
        else:
            sheet.append_row([month, category, budget_amount])
            print(f"Added new budget for {category} in {month}")
    except Exception as e:
        print("❌ Error saving budget:", e)

# ========= Expense/Income Functions =========

def clean_amount_column(df):
    df["Amount"] = (
        df["Amount"].astype(str)
        .str.replace("₹", "", regex=False)
        .str.replace("£", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.strip()
        .astype(float)
    )
    return df

def load_expense_data():
    try:
        print("🔁 Connecting to Google Sheet...")
        sheet = client.open_by_key(SPREADSHEET_ID).worksheet(EXPENSE_SHEET)

        raw_records = sheet.get_all_records(
            head=4,
            expected_headers=["Date", "Amount", "Description", "Category"]
        )
        print(f"🔢 Raw records fetched: {len(raw_records)}")
        print("📋 First raw row:", raw_records[0] if raw_records else "EMPTY")

        records = [
            {k: v for k, v in row.items() if k.strip() != ''}
            for row in raw_records if any(row.values())
        ]

        print(f"✅ Cleaned records count: {len(records)}")
        if records:
            print("🔍 First cleaned record:", records[0])

        df = pd.DataFrame(records)
        print(f"📊 DataFrame shape before parsing: {df.shape}")

        df['Amount'] = (
            df['Amount'].astype(str)
            .str.replace('£', '', regex=False)
            .str.replace('₹', '', regex=False)
            .str.replace(',', '', regex=False)
            .str.strip()
        )
        df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')

        df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
        df = df.dropna(subset=['Date', 'Amount'])

        df['Month'] = df['Date'].dt.to_period('M').astype(str)

        print(f"📉 DataFrame shape after dropna: {df.shape}")
        print("📅 Unique Months:", df['Month'].unique())
        print("🏷️ Unique Categories:", df['Category'].dropna().unique())

        return df

    except Exception as e:
        print("❌ Error loading data from Google Sheet:", e)
        return pd.DataFrame()

def load_income_data():
    try:
        sheet = client.open_by_key(SPREADSHEET_ID).worksheet(INCOME_SHEET)

        income_records = sheet.get_all_records(
            head=1,
            expected_headers=["Date", "Amount", "Description", "Source"]
        )
        print("📋 Income sheet raw headers:", income_records[0].keys() if income_records else "No data")

        income_records = [
            {k: v for k, v in row.items() if k.strip() != ''} 
            for row in income_records if any(row.values())
        ]
        df = pd.DataFrame(income_records)

        if df.empty:
            return df

        df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
        df.dropna(subset=['Date'], inplace=True)
        df['Month'] = df['Date'].dt.to_period('M').astype(str)

        df['Amount'] = (
            df['Amount'].astype(str)
            .str.replace("₹", "", regex=False)
            .str.replace("£", "", regex=False)
            .str.replace(",", "", regex=False)
            .str.strip()
        )
        df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')

        return df

    except Exception as e:
        print("❌ Error loading income data:", e)
        return pd.DataFrame()

def save_expense_to_sheet(date, amount, description, category):
    try:
        sheet = client.open_by_key(SPREADSHEET_ID).worksheet(EXPENSE_SHEET)
        new_row = [date.strftime("%d/%m/%Y"), amount, description, category]
        sheet.append_row(new_row)
        print("✅ Expense saved to sheet:", new_row)
    except Exception as e:
        print("❌ Failed to save expense:", e)

def save_income_to_sheet(date, amount, source, description):  # Correct order
    try:
        sheet = client.open_by_key(SPREADSHEET_ID).worksheet(INCOME_SHEET)
        new_row = [date.strftime("%d/%m/%Y"), amount, description, source]
        sheet.append_row(new_row)
        print("✅ Income saved to sheet:", new_row)
    except Exception as e:
        print("❌ Failed to save income:", e)
