import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from utils import load_expense_data, load_income_data, load_budgets

def show_dashboard():
    st.title("📊 Smart Expense & Income Tracker - Dashboard")

    # Load data
    expense_df = load_expense_data()
    income_df = load_income_data()

    # Process income data
    if not income_df.empty and "Date" in income_df.columns:
        income_df["Date"] = pd.to_datetime(income_df["Date"], dayfirst=True, errors="coerce")
        income_df.dropna(subset=["Date"], inplace=True)
        income_df["Month"] = income_df["Date"].dt.to_period("M").astype(str)

    # Add Month to expense_df if not already present
    if "Month" not in expense_df.columns and "Date" in expense_df.columns:
        expense_df["Month"] = expense_df["Date"].dt.to_period("M").astype(str)

    # Filter out empty dataframes
    if expense_df.empty:
        st.warning("No expense data available.")
        return

    # Month selection
    all_months = sorted(
        list(set(expense_df["Month"].unique().tolist() +
                 income_df.get("Month", pd.Series(dtype=str)).unique().tolist()))
    )
    selected_month = st.selectbox("📅 Select Month", all_months)

    # Category filter
    all_categories = sorted(expense_df["Category"].dropna().unique().tolist())
    excluded_categories = st.multiselect("🚫 Exclude Categories", all_categories, default=["Farmhouse"])
    filtered_exp_df = expense_df[~expense_df["Category"].isin(excluded_categories)]

    # Filtered data
    exp_month_df = filtered_exp_df[filtered_exp_df["Month"] == selected_month]
    inc_month_df = income_df[income_df["Month"] == selected_month] if "Month" in income_df.columns else pd.DataFrame()

    # Tabs for functionality
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Summary", "📂 Category Breakdown", "🧾 All Records", "📊 Monthly Trend"
    ])

    with tab1:
        st.subheader("💡 Monthly Summary")
        exp_total = exp_month_df["Amount"].sum()
        inc_total = inc_month_df["Amount"].sum() if not inc_month_df.empty else 0
        net_savings = inc_total - exp_total

        col1, col2, col3 = st.columns(3)
        col1.metric("💸 Total Expense", f"₹ {exp_total:,.0f}")
        col2.metric("💰 Total Income", f"₹ {inc_total:,.0f}")
        col3.metric("📈 Net Savings", f"₹ {net_savings:,.0f}", delta_color="inverse")

    with tab2:
        st.subheader("📂 Expense by Category (Pie Chart & Budget Highlight)")

        cat_data = exp_month_df.groupby("Category")["Amount"].sum().sort_values(ascending=False)
        budgets_df = load_budgets(selected_month)
        budget_dict = {}
        if not budgets_df.empty:
            budget_dict = dict(zip(budgets_df["Category"], budgets_df["BudgetAmount"]))

        # Pie chart (as before)
        if not cat_data.empty:
            fig1, ax1 = plt.subplots()
            wedges, texts, autotexts = ax1.pie(
                cat_data,
                labels=cat_data.index,
                autopct=lambda pct: f"{pct:.1f}%\n(₹{pct * cat_data.sum() / 100:,.0f})",
                startangle=140
            )
            ax1.axis("equal")
            st.pyplot(fig1)
        else:
            st.info("No data for pie chart.")

        # Budget Table with Highlighting
        st.markdown("### 💡 Budget vs Actual by Category")
        report_rows = []
        for cat, spent in cat_data.items():
            budget = float(budget_dict.get(cat, 0))
            overspent = spent > budget and budget > 0
            report_rows.append({
                "Category": cat,
                "Spent": spent,
                "Budget": budget,
                "Status": "🚨 Over Budget" if overspent else ("✅ Within Budget" if budget else "No Budget"),
                "Delta": spent - budget
            })

        report_df = pd.DataFrame(report_rows)

        def highlight_overspent(row):
            if row["Status"] == "🚨 Over Budget":
                return ["background-color: #ffe5e5; color: red"] * len(row)
            elif row["Status"] == "✅ Within Budget":
                return ["background-color: #e8ffe8"] * len(row)
            else:
                return ["" for _ in row]

        if not report_df.empty:
            st.dataframe(
                report_df.style.apply(highlight_overspent, axis=1),
                use_container_width=True
            )
        else:
            st.info("No expense data for this month.")

    with tab3:
        st.subheader("📋 Expense Records")
        st.dataframe(exp_month_df.reset_index(drop=True), use_container_width=True)

        if not inc_month_df.empty:
            st.subheader("📥 Income Records")
            st.dataframe(inc_month_df.reset_index(drop=True), use_container_width=True)

    with tab4:
        st.subheader("📊 Monthly Trend: Income vs Expense")
        trend_df = expense_df.groupby("Month")["Amount"].sum().reset_index(name="Expense")
        if not income_df.empty and "Month" in income_df.columns:
            income_trend = income_df.groupby("Month")["Amount"].sum().reset_index(name="Income")
            trend_df = pd.merge(trend_df, income_trend, on="Month", how="outer").fillna(0)

        trend_df.sort_values("Month", inplace=True)
        fig3, ax3 = plt.subplots()
        ax3.plot(trend_df["Month"], trend_df["Expense"], marker="o", label="Expense")
        ax3.plot(trend_df["Month"], trend_df["Income"], marker="o", label="Income")
        ax3.set_ylabel("Amount (₹)")
        ax3.set_xlabel("Month")
        ax3.legend()
        st.pyplot(fig3)

    st.success("✅ Dashboard Loaded")
