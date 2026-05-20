import os
import yaml
import pandas as pd
from pandas import Series, DataFrame
from currency_converter import CurrencyConverter
from typing import NamedTuple

CONFIG_FILE = "config.yaml"


class Subscription(NamedTuple):
    service: str
    category: str
    amount: float
    currency: str
    payment_method: str
    active: bool = True
    notes: str = ""


def load_config() -> dict:
    with open(CONFIG_FILE, "r") as f:
        return yaml.safe_load(f)


def save_config(config: dict) -> None:
    with open(CONFIG_FILE, "w") as f:
        yaml.safe_dump(config, f)


def convert_currency(
    converter: CurrencyConverter,
    amount: float,
    from_currency: str,
    to_currency: str,
) -> float:
    if from_currency == to_currency:
        return amount
    return float(converter.convert(amount, from_currency, to_currency))


def apply_conversion(
    converter: CurrencyConverter, row: Series, target_currency: str
) -> float:
    amount = float(row["Amount"])
    from_currency = str(row["Currency"])
    return convert_currency(converter, amount, from_currency, target_currency)


def format_amount(amount: float, currency: str) -> str:
    return f"{amount:.2f} {currency}"


def load_subscriptions(config: dict) -> DataFrame:
    if not os.path.exists(config["DATA_PATH"]):
        df = pd.DataFrame(columns=config["CSV_HEADER"])
        df.to_csv(config["DATA_PATH"], index=False)
    df = pd.read_csv(config["DATA_PATH"])
    if df.empty:
        return pd.DataFrame(columns=config["CSV_HEADER"])
    return df


def append_subscription(config: dict, record: dict) -> None:
    add_header = (
        not os.path.exists(config["DATA_PATH"])
        or os.path.getsize(config["DATA_PATH"]) == 0
    )
    pd.DataFrame([record]).reindex(columns=config["CSV_HEADER"]).to_csv(
        config["DATA_PATH"], mode="a", header=add_header, index=False
    )


def build_display_df(
    converter: CurrencyConverter, df: DataFrame, display_currency: str
) -> DataFrame:
    out = df.copy()
    out["Converted Amount"] = out.apply(
        lambda r: format_amount(
            apply_conversion(converter, r, display_currency), display_currency
        ),
        axis=1,
    )
    out["Status"] = out["Active"].map(lambda a: "Active" if a else "Inactive")
    return out


def persist_edits(edited: DataFrame, config: dict) -> None:
    persisted = edited.drop(
        columns=["Converted Amount", "Status"], errors="ignore"
    )
    persisted = persisted[config["CSV_HEADER"]]
    persisted.to_csv(config["DATA_PATH"], index=False)


def total_converted(
    converter: CurrencyConverter, df: DataFrame, target_currency: str
) -> float:
    if df.empty:
        return 0.0
    return float(
        df.apply(lambda r: apply_conversion(
            converter, r, target_currency), axis=1).sum()
    )
