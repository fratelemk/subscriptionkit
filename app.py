import re
import emoji
import pandas as pd
import streamlit as st
from currency_converter import CurrencyConverter

currency_converter = CurrencyConverter(verbose=False)

def apply_conversion(row: pd.Series, new_currency):
    if new_currency == row['Currency']:
        return f"{row['Amount']} {row['Currency']}"

    converted_rate = currency_converter.convert(row['Amount'], row['Currency'], new_currency)

    return f"{converted_rate:.2f} {new_currency}"

conn = st.connection('testing', type="sql")


# from queries import SELECT, VIEW, CREATE
# from datetime import date
# from sqlalchemy import text

# with conn.session as s:
#     s.execute(text(CREATE))
#     s.execute(text(VIEW))
#
#     s.commit()
#
#     subscriptions: pd.DataFrame = conn.query(SELECT)
#     subscriptions['Active'] = subscriptions['Active'].astype(bool)
#     subscriptions['Renewal'] = subscriptions['Renewal'].apply(lambda x: date.fromtimestamp(x).strftime('%d %B'))
#
#     st.write(subscriptions)

f = st.file_uploader("Upload")
if f:
    df = pd.read_csv(filepath_or_buffer=f)
    currency_options = ("🇺🇸USD", "🇬🇧GBP", "🇪🇺EUR", "🇷🇴RON")
    currency = st.selectbox('Currency', currency_options)
    currency_value = re.sub(r'\s+', '', emoji.replace_emoji(currency, replace=''))

    df['Amount'] = df.apply(lambda row: apply_conversion(row, currency_value), axis=1)
    df.drop("Currency", axis=1, inplace=True)

    st.dataframe(df)
