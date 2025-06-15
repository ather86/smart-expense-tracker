import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Setup Google Sheets access
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# Path to your service account JSON file
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

# Google Sheet ID and Sheet Names
SPREADSHEET_ID = "15kcMP0G1xh84P1k7Yc_0R0g9VC3qkN17MAGnPA6FHmk"
EXPENSE_SHEET = "Transactions"
INCOME_SHEET = "Income"


def clean_amount_column(df):
    # Remove currency symbols and commas
    df["Amount"] = (
        df["Amount"]
        .astype(str)
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

        records = []
        for row in raw_records:
            if any(row.values()):
                clean_row = {k: v for k, v in row.items() if k.strip() != ''}
                records.append(clean_row)

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

        # ✅ Add Month column to avoid KeyError in dashboard
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

        # Use Row 1 as header row for income
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
