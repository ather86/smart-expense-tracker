import streamlit as st
from datetime import datetime
from utils import save_expense_to_sheet, save_income_to_sheet

def add_entry_prompt():
    st.title("📝 Add Expense / Income Entry")

    entry_type = st.radio("Select Entry Type", ["Expense", "Income"])

    date = st.date_input("Date", value=datetime.today())
    amount = st.number_input("Amount (₹)", min_value=0.0, step=10.0)


import ollama  # Requires Ollama to be running locally

def predict_category_with_ollama(description):
    try:
        system_prompt = """
You are a helpful assistant that classifies expense descriptions into one of the following categories:
["Food", "Transportation", "Utilities", "Health/medical", "Home", "EMI", "Personal", "Gifts", "Pets", "Outside food/party etc.", "Credit card bill", "Parents money", "Raysn's education etc.", "Kauser for monthly exp", "Kauser Business", "Farmhouse", "Other"]

Return only the category name that best matches the description.
"""
        full_prompt = f"{system_prompt}\n\nDescription: {description}\nCategory:"
        response = ollama.chat(model="llama3", messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": full_prompt}
        ])
        category = response['message']['content'].strip()
        return category
    except Exception as e:
        print("❌ Ollama prediction error:", e)
        return ""



    if entry_type == "Expense":
        description = st.text_area("Description (Optional)", key="expense_desc")
        suggested_category = predict_category_with_ollama(description) if description else ""
        category = st.text_input("Expense Category (Auto-suggested below)", value=suggested_category, key="expense_cat")
        if st.button("➕ Add Expense"):
            if amount > 0 and category.strip():
                save_expense_to_sheet(date, amount, description, category)
                st.success("✅ Expense added successfully!")
            else:
                st.error("Please enter a valid amount and category.")

        category = st.text_input("Expense Category (e.g. Food, Rent, EMI)", key="expense_cat")
        description = st.text_area("Description (Optional)", key="expense_desc")
        if st.button("➕ Add Expense"):
            if amount > 0 and category.strip():
                save_expense_to_sheet(date, amount, description, category)
                st.success("✅ Expense added successfully!")
            else:
                st.error("Please enter a valid amount and category.")
    else:  # Income
        source = st.text_input("Income Source (e.g. Salary, Bonus)", key="income_src")
        description = st.text_area("Description (Optional)", key="income_desc")
        if st.button("➕ Add Income"):
            if amount > 0 and source.strip():
                # Match this with your utils.py function definition
                save_income_to_sheet(date, amount, source, description)
                st.success("✅ Income added successfully!")
            else:
                st.error("Please enter a valid amount and source.")
