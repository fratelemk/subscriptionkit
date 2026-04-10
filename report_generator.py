from pandas import isna, read_csv, DataFrame, Series
from datetime import datetime, date
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from currency_converter import CurrencyConverter

COLUMNS = [
    ("Service", 38),
    ("Category", 30),
    ("Currency", 20),
    ("Amount", 22),
    ("Payment Method", 38),
    ("Notes", 38),
]

TABLE_WIDTH = sum(w for _, w in COLUMNS)
TEMPLATED_FILE_NAME = "data/reports/subscriptions_{date:%m_%d_%Y}_RON.pdf"


class Report(FPDF):
    def __init__(self):
        super().__init__(orientation="L", unit="mm", format="A5")
        self.set_margins(12, 12, 12)
        self.set_auto_page_break(auto=True, margin=18)

    def header(self):
        self.set_xy(self.l_margin, 8)
        self.set_font("Helvetica", "B", 20)
        self.set_text_color(0, 0, 0)
        self.cell(0, 10, "Subscriptions", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        self.set_x(self.l_margin)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(80, 80, 80)
        self.cell(
            0, 6, datetime.now().strftime("%B %Y"), new_x=XPos.LMARGIN, new_y=YPos.NEXT
        )

        # Horizontal rule aligned to table width
        y = self.get_y() + 1
        self.set_draw_color(0, 0, 0)
        self.set_line_width(0.5)
        self.line(self.l_margin, y, self.l_margin + TABLE_WIDTH, y)
        self.ln(5)

    def footer(self):
        self.set_xy(self.l_margin, -14)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(
            0,
            6,
            f"This report was automatically generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.",
            align="L",
        )

    def _table_header(self):
        self.set_fill_color(30, 30, 30)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 9)
        self.set_x(self.l_margin)
        for label, width in COLUMNS:
            self.cell(
                width,
                8,
                label,
                border=0,
                align="L",
                fill=True,
                new_x=XPos.RIGHT,
                new_y=YPos.TOP,
            )
        self.ln(8)

    def _table_row(self, row: "Series", fill: bool):
        self.set_fill_color(245, 245, 245 if fill else 255)
        self.set_text_color(0, 0, 0)
        self.set_font("Helvetica", "", 8.5)

        def val(col):
            v = row.get(col)
            return "" if isna(v) else str(v)

        values = [
            val("Service"),
            val("Category"),
            val("Currency"),
            val("Amount"),
            val("Payment Method"),
            val("Notes"),
        ]

        row_h = 7
        self.set_font("Helvetica", "", 8.5)
        self.set_x(self.l_margin)
        for (_, width), value in zip(COLUMNS, values):
            self.cell(
                width,
                row_h,
                value,
                border=0,
                align="L",
                fill=fill,
                new_x=XPos.RIGHT,
                new_y=YPos.TOP,
            )
        self.ln(row_h)

        # row separator
        y = self.get_y()
        self.set_draw_color(200, 200, 200)
        self.set_line_width(0.1)
        self.line(self.l_margin, y, self.l_margin + TABLE_WIDTH, y)

    def _summary(self, df: "DataFrame"):
        total_by_currency = df.groupby("Currency")["Amount"].sum()
        cc = CurrencyConverter()

        self.ln(5)
        self.set_x(self.l_margin)
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(0, 0, 0)
        self.cell(0, 7, "Summary", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        self.set_font("Helvetica", "", 9)
        self.set_x(self.l_margin)
        self.cell(
            0,
            6,
            f"Active subscriptions: {len(df)}",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )

        total_ron = 0.0
        for currency, total in sorted(total_by_currency.items()):
            self.set_x(self.l_margin)
            self.cell(
                0,
                6,
                f"Total ({currency}): {total:.2f}",
                new_x=XPos.LMARGIN,
                new_y=YPos.NEXT,
            )
            try:
                total_ron += cc.convert(total, currency, "RON")
            except Exception:
                pass

        self.set_x(self.l_margin)
        self.set_font("Helvetica", "B", 9)
        self.cell(
            0,
            6,
            f"Total (RON): {total_ron:.2f}",
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
        )

    def build(self, df: "DataFrame"):
        self.add_page()
        self._table_header()
        for i, (_, row) in enumerate(df.iterrows()):
            self._table_row(row, fill=i % 2 == 0)
        self._summary(df)


def main():
    data = read_csv(filepath_or_buffer="data/subscriptions.csv")
    data = data[data["Active"] == True]
    if data.empty:
        return

    pdf = Report()
    pdf.build(data)
    pdf.output(TEMPLATED_FILE_NAME.format(date=date.today()))


if __name__ == "__main__":
    main()
