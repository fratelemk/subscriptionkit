# SubscriptionKit

A [Streamlit](https://github.com/streamlit/streamlit) application that allows you to track, convert, and manage your monthly subscriptions across multiple currencies while monitoring your budget and remaining salary.

The datastore used is a simple CSV file that currently has the following structure:

`Subscription,Currency,Amount`

This simple file-based approach offers several advantages:

- Portability: Easy to backup, share, or migrate your data
- Transparency: View and edit your subscription data in any spreadsheet application
- No dependencies: No database setup or external services required

> [!NOTE]
> **Currency** must comply with [ISO 4217](https://www.iso.org/iso-4217-currency-codes.html) currency codes (e.g., USD, EUR, GBP).

### TODO

- [X] ~~iCloud Integration~~
- [ ] Backup
- [ ] Categorisation
- [ ] PDF Report Generation

---

## Requirements

- **Python 3.x**
- [**Streamlit**](https://github.com/streamlit/streamlit)
- [**CurrencyConverter**](https://github.com/alexprengere/currencyconverter)

You can install the required Python libraries with:

```bash
pip install -r requirements.txt
```

## Usage

```bash
streamlit run app.py
```

> [!NOTE]
> A Docker image is also available, created according to the official [Streamlit's Docker Deployment Guide](https://docs.streamlit.io/deploy/tutorials/docker).
