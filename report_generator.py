import pandas as pd
from fpdf import FPDF, XPos, YPos
from datetime import datetime


class PDF(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", style="I", size=8)
        footer_text = f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Disclaimer: This report was automatically generated."
        self.cell(0, 5, footer_text, align="L")


# PDF setup
orientation = "P"
format = "A5"
month = datetime.now().strftime("%B %Y")  # e.g., "September 2025"
currency_symbols = {"GBP": "£", "USD": "$", "EUR": "€"}

df = pd.read_csv("data.csv")
expenses = [
    ("Rent", 1200),
    ("Utilities", 150),
    ("Groceries", 400),
    ("Internet", 60),
    ("Transport", 100),
]

pdf = PDF()
pdf.alias_nb_pages()  # Enable total page number
pdf.add_page(orientation=orientation, format=format)

# Title
pdf.set_font("Helvetica", "B", 16)
pdf.cell(
    0, 10, f"Monthly Expenses - {month}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="L"
)
pdf.ln(5)

# Table header (no borders)
pdf.set_font("Helvetica", "B", 12)
pdf.cell(100, 10, "Subscription", new_x=XPos.RIGHT, new_y=YPos.TOP, align="L")
pdf.cell(40, 10, "Amount", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="L")

# Table rows (no borders)
pdf.set_font("Helvetica", "", 12)
total = 0
for idx, row in df.iterrows():
    subscription = row["Subscription"]
    currency_code = row["Currency"]
    amount = float(row["Amount"])

    symbol = currency_symbols.get(
        currency_code, currency_code
    )  # Replace with symbol if known
    amount_str = f"{symbol}{amount:.2f}"

    pdf.cell(100, 10, subscription, new_x=XPos.RIGHT, new_y=YPos.TOP, align="L")
    pdf.cell(40, 10, amount_str, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="L")

    total += amount

# Total row
pdf.set_font("Helvetica", "B", 12)
pdf.cell(100, 10, "Total", new_x=XPos.RIGHT, new_y=YPos.TOP, align="L")
pdf.cell(40, 10, f"£{total:.2f}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="L")

# Save PDF
pdf.output("monthly_expenses.pdf")
