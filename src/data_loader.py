"""Load and clean the AtliQ Hardware sales data.

The source ships as a MySQL dump (``data/raw/db_dump.sql``). To keep the analysis
reproducible *without* requiring a running MySQL server, this module parses the
dump's ``INSERT`` statements directly into pandas DataFrames, applies the cleaning
rules documented in ``sql/etl_clean.sql``, and returns a single analytic fact table
joined to its dimensions.

Cleaning rules (kept in lock-step with the SQL ETL so both paths agree):
  * Trim stray whitespace on string keys/currency (the raw ``currency`` column
    carries trailing characters on some rows).
  * Drop non-positive ``sales_amount`` rows — they are data-entry artefacts, not
    real sales, and would distort revenue and margin.
  * Normalise every transaction to INR so totals are comparable
    (a handful of rows are booked in USD).
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

# Approx. average INR/USD over the data window (Oct-2017 -> Jun-2020).
# Only two rows are in USD, so the headline numbers are insensitive to this; it is
# made explicit rather than hidden so the assumption is auditable.
USD_TO_INR = 75.0

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_SQL = PROJECT_ROOT / "data" / "raw" / "db_dump.sql"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

_SCHEMA = {
    "customers": ["customer_code", "customer_name", "customer_type"],
    "date": ["date", "cy_date", "year", "month_name", "date_yy_mmm"],
    "markets": ["markets_code", "markets_name", "zone"],
    "products": ["product_code", "product_type"],
    "transactions": [
        "product_code", "customer_code", "market_code", "order_date", "sales_qty",
        "sales_amount", "currency", "profit_margin_percentage", "profit_margin", "cost_price",
    ],
}


def _parse_tuple(body: str) -> list:
    """Split one ``(...)`` row body into fields, respecting quoted strings."""
    out, cur, quote, i = [], "", None, 0
    while i < len(body):
        ch = body[i]
        if quote:
            if ch == chr(92) and i + 1 < len(body):   # backslash escape
                cur += body[i + 1]; i += 2; continue
            if ch == quote:
                quote = None; i += 1; continue
            cur += ch
        else:
            if ch in ("'", '"'):
                quote = ch; i += 1; continue
            if ch == ",":
                out.append(cur.strip()); cur = ""; i += 1; continue
            cur += ch
        i += 1
    out.append(cur.strip())
    return [None if v == "NULL" else v for v in out]


def _load_table(sql_text: str, table: str) -> pd.DataFrame:
    rows: list[list] = []
    for match in re.finditer(rf"INSERT INTO `{table}` VALUES (.*?);\n", sql_text, re.S):
        body = match.group(1).strip()[1:-1]            # strip outer parentheses
        for row in re.split(r"\)\s*,\s*\(", body):
            rows.append(_parse_tuple(row))
    return pd.DataFrame(rows, columns=_SCHEMA[table])


def load_raw(sql_path: Path | str = RAW_SQL) -> dict[str, pd.DataFrame]:
    """Parse every table out of the MySQL dump into DataFrames."""
    sql_text = Path(sql_path).read_text(encoding="utf-8", errors="replace")
    return {name: _load_table(sql_text, name) for name in _SCHEMA}


def build_fact(tables: dict[str, pd.DataFrame] | None = None) -> pd.DataFrame:
    """Return a cleaned, INR-normalised transaction fact table joined to dimensions.

    Adds two derived, currency-normalised columns used everywhere downstream:
      * ``revenue``       — sales_amount in INR
      * ``profit``        — profit_margin in INR
    """
    tables = tables or load_raw()
    tx = tables["transactions"].copy()

    tx["sales_qty"] = pd.to_numeric(tx["sales_qty"], errors="coerce")
    for col in ["sales_amount", "profit_margin_percentage", "profit_margin", "cost_price"]:
        tx[col] = pd.to_numeric(tx[col], errors="coerce")
    tx["currency"] = tx["currency"].astype(str).str.strip().str.upper()
    for col in ["product_code", "customer_code", "market_code"]:
        tx[col] = tx[col].astype(str).str.strip()

    # Rule: a real sale moved money. Drop non-positive amounts.
    tx = tx[tx["sales_amount"] > 0].copy()

    is_usd = tx["currency"].str.startswith("USD")
    tx["revenue"] = np.where(is_usd, tx["sales_amount"] * USD_TO_INR, tx["sales_amount"])
    tx["profit"] = np.where(is_usd, tx["profit_margin"] * USD_TO_INR, tx["profit_margin"])

    fact = (
        tx.merge(tables["customers"], on="customer_code", how="left")
          .merge(tables["markets"], left_on="market_code", right_on="markets_code", how="left")
          .merge(tables["products"], on="product_code", how="left")
          .merge(tables["date"][["date", "year"]], left_on="order_date", right_on="date", how="left")
    )
    fact["year"] = pd.to_numeric(fact["year"], errors="coerce").astype("Int64")
    return fact


def write_processed(fact: pd.DataFrame, out_dir: Path | str = PROCESSED_DIR) -> Path:
    """Persist the cleaned fact table for downstream tools (e.g. Tableau)."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    keep = [
        "order_date", "year",
        "customer_code", "customer_name", "customer_type",
        "market_code", "markets_name", "zone",
        "product_code", "product_type",
        "sales_qty", "currency", "revenue", "profit",
    ]
    path = out_dir / "transactions_clean.csv"
    fact[keep].to_csv(path, index=False)
    return path


if __name__ == "__main__":
    fact = build_fact()
    out = write_processed(fact)
    print(f"Clean fact table: {len(fact):,} rows -> {out}")
