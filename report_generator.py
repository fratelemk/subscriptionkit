from pandas import DataFrame
from fpdf import FPDF, XPos, YPos
from datetime import datetime
from typing import ClassVar, Dict, List, Literal, NamedTuple

CurrencyCode = Literal["GBP", "USD", "EUR", "RON"]


class Font(NamedTuple):
    style: str
    size: int
    family: str = "Helvetica"


class Fonts:
    TITLE = Font("B", 16)
    HEADER = Font("B", 12)
    BODY = Font("", 12)
    FOOTER = Font("I", 8)


class PDF(FPDF):
    def footer(self) -> None:
        self.set_y(-15)
        self.set_font(*Fonts.FOOTER)
        footer_text = f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Disclaimer: This report was automatically generated."
        self.cell(0, 5, footer_text, align="L")


class MonthlyReports:
    month: ClassVar[str] = datetime.now().strftime("%B %Y")  # e.g. September 2025
    orientation: ClassVar[Literal["L", "P"]] = "P"
    format: ClassVar[Literal["A4", "A5"]] = "A5"
    currency_symbols: ClassVar[Dict[CurrencyCode, str]] = dict(
        GBP="£", USD="$", EUR="€", RON="RON"
    )
    _instances: ClassVar[List["MonthlyReports"]] = []

    def __init__(self, data: DataFrame) -> None:
        pdf = PDF()
        pdf.alias_nb_pages()
        pdf.add_page(
            orientation=MonthlyReports.orientation, format=MonthlyReports.format
        )

        # Title
        pdf.set_font(*Fonts.TITLE)
        pdf.cell(
            0,
            10,
            f"Monthly Expenses - {MonthlyReports.month}",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
            align="L",
        )
        pdf.ln(5)

        # Table Header
        pdf.set_font(*Fonts.HEADER)
        pdf.cell(100, 10, "Subscription", new_x=XPos.RIGHT, new_y=YPos.TOP, align="L")
        pdf.cell(40, 10, "Amount", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="L")

        # Table Rows
        pdf.set_font(*Fonts.BODY)
        total = 0
        for _, row in data.iterrows():
            subscription = row["Subscription"]
            currency_code = row["Currency"]
            amount = float(row["Amount"])

            symbol = MonthlyReports.currency_symbols.get(
                currency_code, currency_code
            )  # Replace with symbol if known
            amount_str = f"{symbol}{amount:.2f}"

            pdf.cell(100, 10, subscription, new_x=XPos.RIGHT, new_y=YPos.TOP, align="L")
            pdf.cell(40, 10, amount_str, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="L")

            total += amount

        # Total Row
        pdf.set_font(*Fonts.HEADER)
        pdf.cell(100, 10, "Total", new_x=XPos.RIGHT, new_y=YPos.TOP, align="L")
        pdf.cell(
            40, 10, f"£{total:.2f}", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="L"
        )

        self.pdf = pdf

        MonthlyReports._instances.append(self)


if __name__ == "__main__":
    import pandas as pd

    g1 = MonthlyReports(pd.read_csv("data.csv"))
    g2 = MonthlyReports(pd.read_csv("data.csv"))

    for i, report in enumerate(MonthlyReports._instances):
        report.pdf.output(f"{i}_report.pdf")
