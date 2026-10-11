
import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(
    page_title="SpendSmart",
    page_icon="💰",
    layout="wide"
)

DATA_FILE = Path(__file__).parent / "expenses.csv"



def load_expenses():
    if DATA_FILE.exists():
        try:
            df = pd.read_csv(DATA_FILE)

            if df.empty:
                return []

            return df.to_dict("records")

        except (
            pd.errors.EmptyDataError,
            pd.errors.ParserError,
            UnicodeDecodeError
        ):
            return []

    return []



if "expenses" not in st.session_state:
    st.session_state.expenses = load_expenses()


st.title("💰 SpendSmart")
st.write("Your Personal Expense Tracker")


# Monthly budget
st.header("🎯 Monthly Budget")

monthly_budget = st.number_input(
    "Set your monthly budget (₹)",
    min_value=100.0,
    value=5000.0,
    step=500.0,
    key="monthly_budget"
)

current_month = pd.Timestamp.now().strftime("%Y-%m")

if st.session_state.expenses:
    budget_df = pd.DataFrame(st.session_state.expenses)

    if "Date" in budget_df.columns:
        budget_df["Date"] = pd.to_datetime(
            budget_df["Date"], errors="coerce"
        )

        budget_df["Amount (₹)"] = pd.to_numeric(
            budget_df["Amount (₹)"], errors="coerce"
        ).fillna(0)

        current_month_df = budget_df[
            budget_df["Date"].dt.strftime("%Y-%m")
            == current_month
        ]

        current_month_spending = current_month_df[
            "Amount (₹)"
        ].sum()

        remaining = monthly_budget - current_month_spending

        st.metric(
            "Spent This Month",
            f"₹{current_month_spending:,.2f}"
        )

        st.progress(
            min(current_month_spending / monthly_budget, 1.0)
        )

        if remaining >= 0:
            st.success(
                f"₹{remaining:,.2f} remaining in your monthly budget."
            )
        else:
            st.warning(
                f"You exceeded your budget by ₹{abs(remaining):,.2f}!"
            )


# Add an expense
st.header("Add a new expense")

with st.form("expense_form"):
    amount = st.number_input(
        "Amount (₹)",
        min_value=0.01,
        value=100.0,
        step=10.0
    )

    category = st.selectbox(
        "Category",
        [
            "Food",
            "Transport",
            "Shopping",
            "Education",
            "Bills",
            "Other"
        ]
    )

    description = st.text_input("Description")
    expense_date = st.date_input("Expense date")

    submitted = st.form_submit_button("Add Expense")


if submitted:
    new_expense = {
        "Date": str(expense_date),
        "Description": description.strip() or "No description",
        "Category": category,
        "Amount (₹)": round(amount, 2)
    }

    st.session_state.expenses.append(new_expense)

    pd.DataFrame(
        st.session_state.expenses
    ).to_csv(DATA_FILE, index=False)

    st.success("Expense saved successfully!")


# Prepare expense data
st.header("Your spending summary")

if st.session_state.expenses:
    df = pd.DataFrame(st.session_state.expenses)

    # Handle older records without dates
    if "Date" not in df.columns:
        df["Date"] = pd.NA

    df["Date"] = pd.to_datetime(
        df["Date"], errors="coerce"
    )

    # Filter expenses by month
    valid_dates = df["Date"].dropna()

    if not valid_dates.empty:
        months = sorted(
            valid_dates.dt.strftime("%Y-%m").unique(),
            reverse=True
        )

        selected_month = st.selectbox(
            "Choose a month",
            ["All months"] + months
        )

        if selected_month != "All months":
            df = df[
                df["Date"].dt.strftime("%Y-%m")
                == selected_month
            ]

    # Display metrics, history and chart
    if not df.empty:
        total = pd.to_numeric(
            df["Amount (₹)"], errors="coerce"
        ).sum()

        expense_count = len(df)
        average_expense = total / expense_count

        category_totals = (
            df.groupby("Category")["Amount (₹)"]
            .sum()
            .sort_values(ascending=False)
        )

        highest_category = (
            category_totals.index[0]
            if not category_totals.empty
            else "N/A"
        )

        # Four dashboard metrics
        col1, col2, col3, col4 = st.columns(4)

        col1.metric("💰 Total Spending", f"₹{total:,.2f}")
        col2.metric("🧾 Total Expenses", expense_count)
        col3.metric("📊 Top Category", highest_category)
        col4.metric("💸 Average Expense", f"₹{average_expense:,.2f}")

        # Expense history
        st.subheader("Expense History")

        display_df = df.copy()
        display_df["Date"] = display_df["Date"].dt.strftime(
            "%Y-%m-%d"
        ).fillna("Date unavailable")

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
        
        # Download expense records
        csv_data = df.copy()
        csv_data["Date"] = csv_data["Date"].dt.strftime(
            "%Y-%m-%d"
        )

        st.download_button(
            label="📥 Download Expenses as CSV",
            data=csv_data.to_csv(index=False).encode("utf-8"),
            file_name="spendsmart_expenses.csv",
            mime="text/csv"
        )
        
        # Delete an expense
        st.subheader("🗑️ Manage Expenses")

        expense_indices = df.index.tolist()

        selected_expense = st.selectbox(
            "Select an expense to delete",
            options=expense_indices,
            format_func=lambda i: (
                f"{df.loc[i, 'Date'].strftime('%Y-%m-%d') if pd.notna(df.loc[i, 'Date']) else 'No date'}"
                f" | {df.loc[i, 'Category']}"
                f" | ₹{float(df.loc[i, 'Amount (₹)']):,.2f}"
                f" | {df.loc[i, 'Description']}"
            ),
            key="expense_to_delete"
        )

        if st.button("🗑️ Delete Selected Expense"):
            st.session_state.expenses.pop(int(selected_expense))

            pd.DataFrame(
                st.session_state.expenses
            ).to_csv(DATA_FILE, index=False)

            st.success("Expense deleted successfully!")
            st.rerun()



        # Spending chart
        st.subheader("Spending by Category")
        st.bar_chart(category_totals)

    else:
        st.info("No expenses found for this month.")

else:
    st.info("No expenses yet. Add your first expense above!")

