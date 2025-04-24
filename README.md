# SubscriptionKit

A [Streamlit](https://github.com/streamlit/streamlit) application that allows you to keep track of your monthly subscriptions.

The datastore used is a simple CSV file that currently has the following header:

`Subscription,Currency,Amount`

The **Currency** must be in [ISO 4217](https://www.iso.org/iso-4217-currency-codes.html) format.


## Requirements

- **Python 3.x**
- **Streamlit** 
- **CurrencyConverter**

You can install the required Python libraries with:

```bash
pip install -r requirements.txt
```

## Usage

```bash
streamlit run app.py
```

