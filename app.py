import pandas as pd
import streamlit as st
from currency_converter import CurrencyConverter
import plotly.express as px
from datetime import date
from report import Report
from utils import (
    Subscription,
    load_config,
    save_config,
    convert_currency,
    apply_conversion,
    format_amount,
    load_subscriptions,
    append_subscription,
    build_display_df,
    total_converted,
    persist_edits,
)

st.set_page_config(page_title="SubscriptionKit", layout="wide")


@st.cache_resource
def get_currency_converter():
    try:
        return CurrencyConverter(verbose=False)
    except Exception:
        st.error("Failed to initialize currency converter.")
        return None


@st.dialog("Budget Settings")
def budget_settings_dialog():
    salary = st.number_input(
        "Salary", min_value=2500, value=config["SALARY"], step=100
    )
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
                    **config,
                    "SALARY": int(salary),
                    "SALARY_CURRENCY": salary_currency,
                    "DISPLAY_CURRENCY": display_currency,
                }
            )
            st.rerun()


@st.dialog("Add Subscription")
def add_subscription_dialog():
    service = st.text_input("Service", placeholder="e.g., Netflix")
    category = st.selectbox("Category", config["CATEGORIES"])
    amount = st.number_input(
        "Amount", min_value=0.01, format="%.2f", value=9.99
    )
    currency = st.selectbox("Currency", config["CURRENCIES"], index=1)
    payment_method = st.text_input(
        "Payment Method", placeholder="Credit Card, PayPal"
    )
    notes = st.text_area("Notes")

    def _validate_input(sub: Subscription) -> tuple[bool, str]:
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

    with st.container(horizontal=True):
        st.space("stretch")
        if st.button("Add"):
            sub = Subscription(
                service=service,
                category=category,
                amount=amount,
                currency=currency,
                payment_method=payment_method,
                notes=notes,
            )

            is_valid, error_message = _validate_input(sub)
            if is_valid:
                append_subscription(
                    config,
                    {
                        "Service": sub.service,
                        "Category": sub.category,
                        "Amount": sub.amount,
                        "Currency": sub.currency,
                        "Payment Method": sub.payment_method,
                        "Active": sub.active,
                        "Notes": sub.notes,
                    },
                )
                st.rerun()
            else:
                st.error(error_message)


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

def _metrics(
    total_expenses: float, salary_in_display: float, display_currency: str
):
    monthly_cost = format_amount(total_expenses, display_currency)
    remaining_salary = format_amount(
        salary_in_display - total_expenses, display_currency
    )
    percentage = (
        round((total_expenses / salary_in_display) * 100, 1)
        if salary_in_display
        else 0
    )

    with st.container(horizontal=False, gap="xsmall"):
        st.metric("Total Monthly Cost", monthly_cost)
        st.metric("Remaining Salary", remaining_salary)
        st.metric("% of Salary Used", percentage)


def _plot(converter: CurrencyConverter, df: pd.DataFrame, currency: str):
    _df = df[df["Active"] == True].copy()
    if _df.empty:
        return

    _df["Amount_converted"] = _df.apply(
        lambda r: apply_conversion(converter, r, currency), axis=1
    )

    fig = px.pie(
        _df.groupby("Category")["Amount_converted"].sum().reset_index(),
        names="Category",
        values="Amount_converted",
        title="Monthly Cost by Category",
        color="Category",
        color_discrete_sequence=px.colors.qualitative.Pastel,
        hole=0.4,
    )

    fig.update_layout(showlegend=False)

    fig.update_traces(
        textinfo="percent+label",
        hovertemplate="%{label}: %{value:.2f} " + currency,
        marker=dict(line=dict(color="#ffffff", width=2)),
    )

    st.plotly_chart(fig, width="stretch")


def main():
    if not currency_converter:
        st.stop()
    assert currency_converter is not None

    try:
        df = load_subscriptions(config)
    except Exception:
        st.error("Failed to load subscription data.")
        df = pd.DataFrame(columns=config["CSV_HEADER"])

    df_active = df[df["Active"] == True]
    pdf_bytes = b""
    if not df_active.empty:
        pdf = Report()
        pdf.build(df_active)
        pdf_bytes = bytes(pdf.output())

    with st.container(horizontal=True):
        if st.button("Add Subscription", icon=":material/add_row_below:"):
            add_subscription_dialog()

        if not df.empty and st.button(
            "Manage Subscriptions", icon=":material/edit:"
        ):
            manage_subscriptions_dialog(df)

        if st.button("Budget Settings", icon=":material/settings:"):
            budget_settings_dialog()

        st.space("stretch")

        if pdf_bytes:
            st.download_button(
                "Download Report",
                data=pdf_bytes,
                file_name=f"subscriptions_{date.today().strftime('%m_%d_%Y')}_RON.pdf",
                mime="application/pdf",
                icon=":material/picture_as_pdf:",
            )

    if df.empty:
        st.info("No subscriptions.")
        return

    display_currency = config["DISPLAY_CURRENCY"]
    df_display = build_display_df(currency_converter, df, display_currency)
    salary_in_display = convert_currency(
        currency_converter,
        config["SALARY"],
        config["SALARY_CURRENCY"],
        display_currency,
    )
    total_amount = total_converted(
        currency_converter, df_active, display_currency
    )

    edited = st.data_editor(
        df_display,
        hide_index=True,
        width="stretch",
        column_order=config["DISPLAY_COLUMNS"],
        column_config={
            "Service": st.column_config.TextColumn("Service", required=True),
            "Category": st.column_config.SelectboxColumn(
                "Category", options=config["CATEGORIES"], required=True
            ),
            "Amount": st.column_config.NumberColumn(
                "Amount",
                format="%.2f",
                min_value=0.01,
                required=True,
            ),
            "Currency": st.column_config.SelectboxColumn(
                "Currency", options=config["CURRENCIES"], required=True
            ),
            "Payment Method": st.column_config.TextColumn(
                "Payment Method", required=True
            ),
            "Notes": st.column_config.TextColumn("Notes"),
            "Status": st.column_config.TextColumn("Status"),
        },
        disabled=["Converted Amount", "Status"],
        key="subs_editor",
    )

    if not edited.equals(df_display):
        persist_edits(edited, config)
        st.rerun()

    st.divider()

    with st.container(horizontal=True, vertical_alignment="top"):
        _metrics(total_amount, salary_in_display, display_currency)
        _plot(currency_converter, df, display_currency)


if __name__ == "__main__":
    main()
