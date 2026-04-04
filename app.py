import yaml
import os
import pandas as pd
import streamlit as st
from currency_converter import CurrencyConverter
from typing import NamedTuple
import plotly.express as px

st.set_page_config(page_title="SubscriptionKit", layout="wide")


class Subscription(NamedTuple):
    service: str
    category: str
    currency: str
    amount: float
    payment_method: str
    active: bool = True
    notes: str = ""


CONFIG_FILE = "config.yaml"


def plot_expenses_by_category(df: pd.DataFrame, currency):
    if df.empty:
        return

    df_active = df[df["Active"] == True].copy()
    if df_active.empty:
        return

    df_active["Amount_converted"] = df_active.apply(
        lambda row: float(apply_conversion(row, currency).split()[0]), axis=1
    )

    df_grouped = df_active.groupby("Category")["Amount_converted"].sum().reset_index()

    fig = px.pie(
        df_grouped,
        names="Category",
        values="Amount_converted",
        title=f"Monthly Cost by Category",
        color="Category",
        color_discrete_sequence=px.colors.qualitative.Pastel,
        hole=0.4,
    )

    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hovertemplate="%{label}: %{value:.2f} " + currency,
        marker=dict(line=dict(color="#ffffff", width=2)),
    )

    st.plotly_chart(fig, width="stretch")


def load_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            return yaml.safe_load(f)
    except Exception:
        st.error("Failed to load config.")
        return None


def save_config(config: dict):
    with open(CONFIG_FILE, "w") as f:
        yaml.safe_dump(config, f)


def load_data() -> pd.DataFrame:
    if not os.path.exists(config["DATA_PATH"]):
        df = pd.DataFrame(columns=config["CSV_HEADER"])
        df.to_csv(config["DATA_PATH"], index=False)
    try:
        df = pd.read_csv(config["DATA_PATH"])
        if df.empty:
            return pd.DataFrame(columns=config["CSV_HEADER"])
        return df
    except Exception:
        st.error("Failed to load subscription data.")
        return pd.DataFrame(columns=config["CSV_HEADER"])


@st.cache_resource
def get_currency_converter():
    try:
        return CurrencyConverter(verbose=False)
    except Exception:
        st.error("Failed to initialize Currency Converter.")
        return None


@st.dialog("Budget Settings")
def budget_settings_dialog():
    salary = st.number_input("Salary", min_value=2500, value=config["SALARY"], step=100)
    salary_currency = st.selectbox(
        "Salary Currency",
        config["CURRENCIES"],
        index=config["CURRENCIES"].index(config["SALARY_CURRENCY"]),
    )
    display_currency = st.selectbox(
        "Default Display Currency",
        config["CURRENCIES"],
        index=config["CURRENCIES"].index(config["DISPLAY_CURRENCY"]),
    )

    with st.container(horizontal=True):
        st.space("stretch")
        if st.button("Save Settings"):
            save_config(
                {
                    "SALARY": int(salary),
                    "SALARY_CURRENCY": salary_currency,
                    "DISPLAY_CURRENCY": display_currency,
                    "DATA_PATH": config["DATA_PATH"],
                    "CURRENCIES": config["CURRENCIES"],
                    "CSV_HEADER": config["CSV_HEADER"],
                }
            )
            st.rerun()


@st.dialog("Add Subscription")
def add_subscription_dialog():
    service = st.text_input("Service", placeholder="e.g., Netflix")
    category = st.text_input("Category", placeholder="e.g., Entertainment")
    currency = st.selectbox("Currency", config["CURRENCIES"], index=1)
    amount = st.number_input("Amount", min_value=0.01, format="%.2f", value=9.99)
    payment_method = st.text_input("Payment Method", placeholder="Credit Card, PayPal")
    notes = st.text_area("Notes")

    with st.container(horizontal=True):
        st.space("stretch")
        if st.button("Add"):
            sub = Subscription(
                service=service,
                category=category,
                currency=currency,
                amount=amount,
                payment_method=payment_method,
                notes=notes,
            )

            is_valid, error_message = validate_subscription_input(sub)
            if is_valid:
                if add_subscription(sub):
                    st.rerun()
            else:
                st.error(f"{error_message}")


@st.dialog("Manage Subscriptions")
def manage_subscriptions_dialog(df: pd.DataFrame):
    idx = st.selectbox(
        "Select subscription:",
        options=df.index,
        format_func=lambda x: (
            f"{df.iloc[x]['Service']} ({df.iloc[x]['Category']}) - "
            f"{df.iloc[x]['Amount']:.2f} {df.iloc[x]['Currency']} - "
            f"{'Active' if df.iloc[x]['Active'] else 'Inactive'}"
        ),
    )

    subscription = df.loc[idx]

    active_state = st.checkbox("Active", value=bool(subscription["Active"]))
    with st.container(horizontal=True):
        if st.button("Delete", type="primary"):
            try:
                df_updated = df.drop(idx).reset_index(drop=True)
                df_updated.to_csv(config["DATA_PATH"], index=False)
                st.rerun()
            except Exception as e:
                st.error(f"Failed to delete subscription: {e}")

        st.space("stretch")

        if st.button("Update Status", type="secondary"):
            try:
                df.at[idx, "Active"] = active_state
                df.to_csv(config["DATA_PATH"], index=False)
                st.rerun()
            except Exception as e:
                st.error(f"Failed to update subscription: {e}")


currency_converter = get_currency_converter()
config = load_config()


def convert_currency(amount: float, from_currency: str, to_currency: str) -> float:
    if not currency_converter:
        return amount

    if from_currency == to_currency:
        return amount

    try:
        return currency_converter.convert(amount, from_currency, to_currency)
    except Exception:
        st.warning(
            f"Currency conversion failed for {from_currency} to {to_currency}. Using original amount."
        )
        return amount


def apply_conversion(row: pd.Series, target_currency: str) -> str:
    amount = float(row["Amount"])
    from_currency = row["Currency"]

    converted_amount = convert_currency(amount, from_currency, target_currency)
    return f"{converted_amount:.2f} {target_currency}"


def calculate_remaining_salary(total_expenses: float, expense_currency: str) -> str:
    if expense_currency == config["SALARY_CURRENCY"]:
        remaining = config["SALARY"] - total_expenses
    else:
        salary_in_expense_currency = convert_currency(
            config["SALARY"], config["SALARY_CURRENCY"], expense_currency
        )
        remaining = salary_in_expense_currency - total_expenses

    return f"{remaining:.2f} {expense_currency}"


def add_subscription(sub: Subscription) -> bool:
    try:
        new_record = pd.DataFrame(
            [
                {
                    "Service": sub.service,
                    "Category": sub.category,
                    "Currency": sub.currency,
                    "Amount": sub.amount,
                    "Payment Method": sub.payment_method,
                    "Active": sub.active,
                    "Notes": sub.notes,
                }
            ]
        )
        file_is_empty = (
            not os.path.exists(config["DATA_PATH"])
            or os.path.getsize(config["DATA_PATH"]) == 0
        )
        new_record.to_csv(
            config["DATA_PATH"], mode="a", header=file_is_empty, index=False
        )
        return True
    except Exception:
        st.error("Failed to add subscription. Please try again.")
        return False


def validate_subscription_input(sub: Subscription) -> tuple[bool, str]:
    if not sub.service.strip():
        return False, "Subscription name cannot be empty."

    if not sub.category.strip():
        return False, "Category cannot be empty."

    if not sub.currency.strip():
        return False, "Please select a currency."

    if sub.amount <= 0:
        return False, "Amount must be greater than 0."

    if not sub.payment_method.strip():
        return False, "Payment method cannot be empty."

    return True, ""


def display_metrics(total_expenses: float):
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            label="Monthly Cost",
            value=f'{total_expenses:.2f} {config["DISPLAY_CURRENCY"]}',
        )

    with col2:
        remaining = calculate_remaining_salary(
            total_expenses, config["DISPLAY_CURRENCY"]
        )
        remaining_value = float(remaining.split()[0])
        delta_color = "normal" if remaining_value >= 0 else "inverse"
        st.metric(label="Remaining Budget", value=remaining, delta_color=delta_color)

    with col3:
        if total_expenses > 0:
            percentage = (
                total_expenses
                / convert_currency(
                    config["SALARY"],
                    config["SALARY_CURRENCY"],
                    config["DISPLAY_CURRENCY"],
                )
            ) * 100
            st.metric(label="% of Budget Used", value=f"{percentage:.1f}%")


def main():
    if not currency_converter:
        st.stop()

    df = load_data()
    csv = df.to_csv().encode("utf-8")

    with st.container(horizontal=True):
        if st.button("Add Subscription", icon=":material/add_row_below:"):
            add_subscription_dialog()

        if not df.empty and st.button("Manage Subscriptions", icon=":material/edit:"):
            manage_subscriptions_dialog(df)

        if st.button("Budget Settings", icon=":material/settings:"):
            budget_settings_dialog()

        st.space("stretch")

        st.download_button(
            "Download CSV", data=csv, mime="text/csv", icon=":material/download:"
        )

    if df.empty:
        st.info("No subscriptions.")

    else:
        df_display = df.copy()
        df_display["Amount (Original)"] = df_display.apply(
            lambda row: f"{row['Amount']:.2f} {row['Currency']}", axis=1
        )
        df_display["Amount"] = df_display.apply(
            lambda row: apply_conversion(row, config["DISPLAY_CURRENCY"]), axis=1
        )

        total_amount = sum(
            float(amount_str.split()[0]) for amount_str in df_display["Amount"]
        )

        st.dataframe(
            df_display,
            hide_index=True,
            width="stretch",
            column_config={
                "Amount (Original)": st.column_config.TextColumn("Original Amount"),
                "Amount": st.column_config.TextColumn(
                    f'Amount ({config["DISPLAY_CURRENCY"]})'
                ),
            },
        )

        st.divider()
        display_metrics(total_amount)
        plot_expenses_by_category(df, config["DISPLAY_CURRENCY"])


if __name__ == "__main__":
    main()
