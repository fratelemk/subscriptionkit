import os
import pandas as pd
import streamlit as st
from currency_converter import CurrencyConverter

st.set_page_config(page_title="SubscriptionKit", layout="wide")

FILEPATH = "data.csv"

SALARY = os.getenv("SALARY")
SALARY_CURRENCY = os.getenv("SALARY_CURRENCY")
DEFAULT_CURRENCY = os.getenv("DEFAULT_CURRENCY")

CURRENCIES = ("USD", "GBP", "EUR", "RON")


def apply_conversion(row: pd.Series, new_currency: str) -> str:
    amount, currency = row["Amount"], row["Currency"]

    if new_currency == currency:
        return f"{amount} {currency}"

    converted_rate = round(
        currency_converter.convert(amount, currency, new_currency), 2
    )

    return f"{converted_rate} {new_currency}"


def calculate_remaining(amount: float, currency: str) -> str:
    if currency == SALARY_CURRENCY:
        return f"{(SALARY - amount):.2f} {currency}"

    converted_salary = currency_converter.convert(SALARY, SALARY_CURRENCY, currency)

    return f"{(converted_salary - amount):.2f} {currency}"


form = st.form("_subscription", border=False)

subscription = form.text_input("Subscription", "iCloud+")
currency = form.selectbox("Currency", ["GBP", "USD", "EUR"])
amount = form.number_input("Amount", min_value=0.00, format="%.2f")

submit = form.form_submit_button("Add Subscription")

if submit:
    if subscription and currency and amount:
        pd.DataFrame(
            [[subscription, currency, amount]],
            columns=["Subscription", "Currency", "Amount"],
        ).to_csv(FILEPATH, mode="a", header=False, index=False)
        st.success(f"Record added: {subscription}, {currency}, {amount}")
    else:
        st.error("Please fill in all fields.")


st.divider()

df = pd.read_csv(FILEPATH)


currency_converter = CurrencyConverter(verbose=False)

currency = st.selectbox(
    "Currency", CURRENCIES, index=CURRENCIES.index(DEFAULT_CURRENCY)
)

df["Amount"] = df.apply(lambda row: apply_conversion(row, currency), axis=1)

total = df["Amount"].apply(lambda x: float(x.removesuffix(currency).strip())).sum()


st.dataframe(df, hide_index=True)

st.subheader("Monthly Report")

columns = st.columns(2)

columns[0].metric(label="Costs", value=f"{total:.2f} {currency}")
columns[1].metric(label="Remaining", value=calculate_remaining(total, currency))
