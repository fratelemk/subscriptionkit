import os
import sys
import re
import emoji
import pandas as pd
import streamlit as st
from currency_converter import CurrencyConverter
from pyicloud import PyiCloudService

api = PyiCloudService(os.environ["APPLE_ID"], os.environ["PASSWORD"])
if api.requires_2fa:
    print("Two-factor authentication required.")
    code = input("Enter the code you received of one of your approved devices: ")
    result = api.validate_2fa_code(code)
    print("Code validation result: %s" % result)

    if not result:
        print("Failed to verify security code")
        sys.exit(1)

    if not api.is_trusted_session:
        print("Session is not trusted. Requesting trust...")
        result = api.trust_session()
        print("Session trust result %s" % result)

        if not result:
            print("Failed to request trust. You will likely be prompted for the code again in the coming weeks")

file = api.drive["Subscriptions.csv"]

currency_converter = CurrencyConverter(verbose=False)

def apply_conversion(row: pd.Series, new_currency):
    if new_currency == row['Currency']:
        return f"{row['Amount']} {row['Currency']}"

    converted_rate = currency_converter.convert(row['Amount'], row['Currency'], new_currency)

    return f"{converted_rate:.2f} {new_currency}"


if file:
    with file.open(stream=True) as response:
        df = pd.read_csv(filepath_or_buffer=response.raw)
        currency_options = ("🇺🇸USD", "🇬🇧GBP", "🇪🇺EUR", "🇷🇴RON")
        currency = st.selectbox('Currency', currency_options)
        currency_value = re.sub(r'\s+', '', emoji.replace_emoji(currency, replace=''))

        df['Amount'] = df.apply(lambda row: apply_conversion(row, currency_value), axis=1)
        df.drop("Currency", axis=1, inplace=True)

        total = df['Amount'].apply(lambda x: float(x.removesuffix(currency_value).strip())).sum()

    st.dataframe(df)
    st.metric(label="Total", value=f"{total:.2f} {currency_value}")
