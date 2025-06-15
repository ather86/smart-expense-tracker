import streamlit as st
from utils import load_budgets, save_budget
import datetime

def show_budget_manager():
    st.title("💰 Set Monthly Budgets by Category")
    # Pick month (format: YYYY-MM)
    today = datetime.date.today()
    month = st.selectbox(
        "Select Month",
        options=[
            f"{today.year}-{str(m).zfill(2)}"
            for m in range(1, 13)
        ],
        index=today.month - 1,
    )

    # Load existing budgets for this month
    budgets_df = load_budgets(month)
    if budgets_df.empty:
        st.info("No budgets set for this month yet.")

    # List all known categories (add more as needed)
    categories = sorted(set(budgets_df["Category"].tolist() + [
        "Home", "Health/medical", "Utilities", "Transportation", "Food",
        "Parents money", "Kauser for monthly exp", "EMI", "Personal",
        "Outside food/party etc.", "Raysn's education etc.", "Credit card bill",
        "Gifts", "Farmhouse", "Kauser Business", "Pets", "Other"
    ]))

    # Allow setting/editing budgets per category
    new_budgets = []
    st.subheader(f"Budgets for {month}")
    for category in categories:
        current_budget = 0.0
        if not budgets_df.empty and category in budgets_df["Category"].values:
            try:
                current_budget = float(
                    budgets_df[budgets_df["Category"] == category]["BudgetAmount"].values[0]
                )
            except Exception:
                current_budget = 0.0
        new_value = st.number_input(
            f"{category} Budget", min_value=0.0, step=100.0, value=float(current_budget), key=f"{month}-{category}"
        )
        new_budgets.append((category, new_value))

    if st.button("💾 Save Budgets"):
        for category, budget_amount in new_budgets:
            if budget_amount > 0:
                save_budget(month, category, budget_amount)
        st.success("✅ Budgets saved for this month!")

    st.markdown("---")
    st.write("### Current Budgets Table")
    st.dataframe(load_budgets(month).reset_index(drop=True), use_container_width=True)
