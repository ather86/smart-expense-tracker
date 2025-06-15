import streamlit as st
from utils import save_expense_to_sheet, save_income_to_sheet
from datetime import datetime
import ollama
import requests

# Health check for Ollama
def is_ollama_running():
    try:
        r = requests.get("http://localhost:11434/")
        return r.status_code == 200
    except Exception:
        return False

def get_category_suggestion(description):
    if not is_ollama_running() or not description.strip():
        return ""
    try:
        response = ollama.chat(
            model="llama3",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expense tracker assistant. Given a transaction description, "
                        "return the most likely category like Food, Transport, Health, EMI, etc. Only return the category name."
                    ),
                },
                {"role": "user", "content": f"Suggest category for: {description}"},
            ]
        )
        return response["message"]["content"].strip()
    except Exception as e:
        print("❌ Ollama error:", e)
        return ""

def add_entry_prompt():
    st.title("➕ Add Income or Expense Entry")
    entry_type = st.radio("Select Entry Type", ["Expense", "Income"], horizontal=True)
    date = st.date_input("Date", value=datetime.today())
    amount = st.number_input("Amount (₹)", min_value=0.0, step=0.01)
    description = st.text_input("Description", key="desc_input", help="Type what the transaction was for.")

    # Autofill suggestion logic:
    suggested_category = ""
    if description:
        if "last_description" not in st.session_state or st.session_state["last_description"] != description:
            st.session_state["last_description"] = description
            suggested_category = get_category_suggestion(description)
            st.session_state["suggested_category"] = suggested_category
        else:
            suggested_category = st.session_state.get("suggested_category", "")
    else:
        suggested_category = ""

    # Show autofilled category (user can override)
    category = st.text_input("Category", value=suggested_category, key="cat_input", help="Edit or accept the suggestion.")

    # Optional: show a tip if suggestion came from AI
    if suggested_category and suggested_category == category:
        st.caption("🤖 Category suggested by AI. You can edit it.")

    if st.button("Save Expense" if entry_type == "Expense" else "Save Income"):
        if entry_type == "Expense":
            save_expense_to_sheet(date, amount, description, category)
            st.success(f"✅ Expense entry saved: {description} ({category})")
        else:
            # For income, let's use "category" as source for now
            save_income_to_sheet(date, amount, category, description)
            st.success(f"✅ Income entry saved: {description} ({category})")
