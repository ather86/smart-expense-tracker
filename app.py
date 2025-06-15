import streamlit as st
from dashboard import show_dashboard
from income_expense_entry import add_entry_prompt
from insights_engine import show_insights

# ✅ This is the right place to set page config
st.set_page_config(page_title="Smart Expense Tracker", layout="wide")

st.sidebar.title("📅 Monthly Expense Tracker")
page = st.sidebar.radio("Go to", ["Dashboard", "Add Entry", "AI Insights"])

if page == "Dashboard":
    show_dashboard()
elif page == "Add Entry":
    add_entry_prompt()
elif page == "AI Insights":
    show_insights()
