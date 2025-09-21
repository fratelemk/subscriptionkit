import yaml
import os
import pandas as pd
import streamlit as st
from currency_converter import CurrencyConverter
from typing import NamedTuple


class Subscription(NamedTuple):
    subscription: str
    category: str
    currency: str
    amount: float
    payment_method: str
    billing_cycle: str = "Monthly"
    active: bool = True
    notes: str = ""


st.set_page_config(page_title="SubscriptionKit", layout="wide")

FILEPATH = "data.csv"
CURRENCIES = ("USD", "GBP", "EUR", "RON")
HEADER = [
    "Subscription",
    "Category",
    "Currency",
    "Amount",
    "Payment Method",
    "Billing Cycle",
    "Active",
    "Notes",
]
CONFIG_FILE = "config.yaml"


def load_config():
    """Initialize and cache the currency converter."""
    try:
        with open(CONFIG_FILE, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        return None


@st.dialog("Budget Settings")
def budget_settings_dialog():
    budget = st.number_input(
        "Budget",
        min_value=0,
        value=5000,
    )
    target_currency = st.selectbox("Target Currency", CURRENCIES)
    default_currency = st.selectbox("Default Display Currency", CURRENCIES)

    if st.button("Save Settings"):
        new_config = {
            "BUDGET": int(budget),
            "BUDGET_CURRENCY": target_currency,
            "DEFAULT_CURRENCY": default_currency,
        }
        save_config(new_config)
        st.success("✅ Budget and currency settings saved!")
        st.rerun()


def save_config(config: dict):
    """Save budget and currency settings to YAML."""
    with open(CONFIG_FILE, "w") as f:
        yaml.safe_dump(config, f)


@st.dialog("Add Subscription")
def add_subscription_dialog():
    subscription_name = st.text_input("Subscription Name", placeholder="e.g., Netflix")
    category = st.text_input("Category", placeholder="e.g., Entertainment")
    currency = st.selectbox("Currency", CURRENCIES, index=1)
    amount = st.number_input("Amount", min_value=0.01, format="%.2f", value=9.99)
    billing_cycle = st.selectbox(
        "Billing Cycle", ["Monthly", "Yearly", "Weekly"], index=0
    )
    payment_method = st.text_input("Payment Method", placeholder="Credit Card, PayPal")
    active = st.checkbox("Active", value=True)
    notes = st.text_area("Notes (optional)")

    if st.button("Add Subscription"):
        sub = Subscription(
            subscription=subscription_name.strip(),
            category=category.strip(),
            currency=currency,
            amount=amount,
            billing_cycle=billing_cycle,
            payment_method=payment_method.strip(),
            active=active,
            notes=notes.strip(),
        )

        is_valid, error_message = validate_subscription_input(sub)
        if is_valid:
            if add_subscription(sub):
                st.success(
                    f"✅ Added: {sub.subscription} - {sub.amount:.2f} {sub.currency}"
                )
                st.rerun()
        else:
            st.error(f"❌ {error_message}")


@st.dialog("Delete Subscription")
def delete_subscription_dialog(df: pd.DataFrame):
    if df.empty:
        st.info("No subscriptions to delete.")
        return

    subscription_to_delete = st.selectbox(
        "Select subscription to delete:",
        options=df.index,
        format_func=lambda x: (
            f"{df.iloc[x]['Subscription']} "
            f"({df.iloc[x]['Category']}) - "
            f"{df.iloc[x]['Amount']:.2f} {df.iloc[x]['Currency']}"
        ),
    )

    if st.button("Delete Selected Subscription", type="secondary"):
        try:
            df_updated = df.drop(subscription_to_delete).reset_index(drop=True)
            df_updated.to_csv(FILEPATH, index=False)
            st.success("Subscription deleted successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"Failed to delete subscription: {e}")


@st.cache_resource
def get_currency_converter():
    """Initialize and cache the currency converter."""
    try:
        return CurrencyConverter(verbose=False)
    except Exception as e:
        print(f"Failed to initialize currency converter: {e}")
        st.error("Currency converter initialization failed. Please refresh the page.")
        return None


currency_converter = get_currency_converter()
config = load_config()


def load_data():
    """Load subscription data with error handling."""

    if not os.path.exists(FILEPATH):
        df = pd.DataFrame(columns=HEADER)
        df.to_csv(FILEPATH, index=False)
        print(f"Created new data file: {FILEPATH}")
    try:
        df = pd.read_csv(FILEPATH)
        if df.empty:
            return pd.DataFrame(columns=HEADER)
        return df
    except Exception as e:
        print(f"Error loading data: {e}")
        st.error("Failed to load subscription data.")
        return pd.DataFrame(columns=HEADER)


def convert_currency(amount: float, from_currency: str, to_currency: str) -> float:
    """Convert currency with error handling."""
    if not currency_converter:
        return amount

    if from_currency == to_currency:
        return amount

    try:
        return currency_converter.convert(amount, from_currency, to_currency)
    except Exception as e:
        print(
            f"Currency conversion failed: {from_currency} to {to_currency}, amount: {amount}, error: {e}"
        )
        st.warning(
            f"Currency conversion failed for {from_currency} to {to_currency}. Using original amount."
        )
        return amount


def apply_conversion(row: pd.Series, target_currency: str) -> str:
    """Apply currency conversion to a row and format the result."""
    amount = float(row["Amount"])
    from_currency = row["Currency"]

    converted_amount = convert_currency(amount, from_currency, target_currency)
    return f"{converted_amount:.2f} {target_currency}"


def calculate_remaining_salary(total_expenses: float, expense_currency: str) -> str:
    """Calculate remaining salary after expenses."""
    if expense_currency == config["BUDGET_CURRENCY"]:
        remaining = config["BUDGET"] - total_expenses
    else:
        salary_in_expense_currency = convert_currency(
            config["BUDGET"], config["BUDGET_CURRENCY"], expense_currency
        )
        remaining = salary_in_expense_currency - total_expenses

    return f"{remaining:.2f} {expense_currency}"


def add_subscription(sub: Subscription) -> bool:
    """Add a new subscription to the CSV file using a Subscription object."""
    try:
        new_record = pd.DataFrame(
            [sub._asdict()]
        )  # convert NamedTuple to dict for DataFrame
        file_is_empty = not os.path.exists(FILEPATH) or os.path.getsize(FILEPATH) == 0
        new_record.to_csv(FILEPATH, mode="a", header=file_is_empty, index=False)
        return True
    except Exception as e:
        print(f"Failed to add subscription: {e}")
        st.error("Failed to add subscription. Please try again.")
        return False


def validate_subscription_input(sub: Subscription) -> tuple[bool, str]:
    """Validate a Subscription object before adding it."""

    if not sub.subscription.strip():
        return False, "Subscription name cannot be empty."

    if not sub.category.strip():
        return False, "Category cannot be empty."

    if not sub.currency.strip():
        return False, "Please select a currency."

    if sub.amount <= 0:
        return False, "Amount must be greater than 0."

    if not sub.billing_cycle.strip():
        return False, "Billing cycle cannot be empty."

    if not sub.payment_method.strip():
        return False, "Payment method cannot be empty."

    return True, ""


def main():
    st.title("💳 SubscriptionKit")

    if not currency_converter:
        st.stop()

    df = load_data()

    # 1️⃣ Display info if no subscriptions exist
    if df.empty:
        st.info(
            "No subscriptions found. Add your first subscription using the 'Add Subscription' button below!"
        )

    else:
        # 2️⃣ Prepare dataframe for display
        df_display = df.copy()
        df_display["Amount (Original)"] = df_display.apply(
            lambda row: f"{row['Amount']:.2f} {row['Currency']}", axis=1
        )
        df_display["Amount"] = df_display.apply(
            lambda row: apply_conversion(row, config["DEFAULT_CURRENCY"]), axis=1
        )

        total_amount = sum(
            float(amount_str.split()[0]) for amount_str in df_display["Amount"]
        )

        # 3️⃣ Display dataframe
        _left, _right = st.columns(2)
        _left.dataframe(
            df_display,
            hide_index=True,
            width="stretch",
            column_config={
                "Subscription": st.column_config.TextColumn("Service"),
                "Amount (Original)": st.column_config.TextColumn("Original Amount"),
                "Amount": st.column_config.TextColumn(
                    f'Amount ({config["DEFAULT_CURRENCY"]})'
                ),
            },
        )

        st.divider()

        # 4️⃣ Metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                label="Expenses",
                value=f'{total_amount:.2f} {config["DEFAULT_CURRENCY"]}',
            )

        with col2:
            remaining = calculate_remaining_salary(
                total_amount, config["DEFAULT_CURRENCY"]
            )
            remaining_value = float(remaining.split()[0])
            delta_color = "normal" if remaining_value >= 0 else "inverse"
            st.metric(
                label="Remaining Budget", value=remaining, delta_color=delta_color
            )

        with col3:
            if total_amount > 0:
                percentage = (
                    total_amount
                    / convert_currency(
                        config["BUDGET"],
                        config["BUDGET_CURRENCY"],
                        config["DEFAULT_CURRENCY"],
                    )
                ) * 100
                st.metric(label="% of Budget Used", value=f"{percentage:.1f}%")

        st.divider()

    col_add, col_delete, col_budget = st.columns([1, 1, 1])

    with col_add:
        if st.button("➕ Add Subscription"):
            add_subscription_dialog()

    with col_delete:
        if not df.empty and st.button("🗑️ Manage Subscriptions"):
            delete_subscription_dialog(df)

    with col_budget:
        if st.button("⚙️ Budget Settings"):
            budget_settings_dialog()


if __name__ == "__main__":
    main()
