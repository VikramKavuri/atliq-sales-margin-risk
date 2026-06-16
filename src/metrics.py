"""Finding-level metrics for the AtliQ sales analysis.

Each function takes the cleaned fact table from :mod:`data_loader` and returns a
small, labelled DataFrame that answers one business question. Keeping them pure and
separate means the notebook, the figures, and the tests all read the same numbers.
"""
from __future__ import annotations

import pandas as pd

CR = 1e7  # 1 crore = 10,000,000 — the unit Indian finance teams read in.


def headline(fact: pd.DataFrame) -> dict:
    """One-glance KPIs for the TL;DR."""
    rev = fact["revenue"].sum()
    profit = fact["profit"].sum()
    return {
        "transactions": len(fact),
        "revenue_inr": rev,
        "revenue_cr": rev / CR,
        "profit_inr": profit,
        "overall_margin_pct": 100 * profit / rev,
        "n_customers": fact["customer_name"].nunique(),
        "n_markets": fact["markets_name"].nunique(),
        "n_products": fact["product_code"].nunique(),
        "date_min": fact["order_date"].min(),
        "date_max": fact["order_date"].max(),
    }


def revenue_by_year(fact: pd.DataFrame) -> pd.DataFrame:
    out = fact.groupby("year", dropna=True)["revenue"].sum().rename("revenue").reset_index()
    out["revenue_cr"] = out["revenue"] / CR
    # 2017 (starts Oct) and 2020 (ends Jun) are partial years — flag for honesty.
    out["partial_year"] = out["year"].isin([2017, 2020])
    return out


def customer_concentration(fact: pd.DataFrame) -> pd.DataFrame:
    """Revenue by customer with cumulative share — the Pareto / single-point-of-failure view."""
    out = (
        fact.groupby("customer_name")["revenue"].sum()
            .sort_values(ascending=False).rename("revenue").reset_index()
    )
    total = out["revenue"].sum()
    out["share_pct"] = 100 * out["revenue"] / total
    out["cum_share_pct"] = out["share_pct"].cumsum()
    out["rank"] = range(1, len(out) + 1)
    return out


def margin_by_market(fact: pd.DataFrame) -> pd.DataFrame:
    out = (
        fact.groupby("markets_name")
            .agg(revenue=("revenue", "sum"), profit=("profit", "sum"))
            .reset_index()
    )
    out["margin_pct"] = 100 * out["profit"] / out["revenue"]
    out["revenue_cr"] = out["revenue"] / CR
    return out.sort_values("revenue", ascending=False).reset_index(drop=True)


def margin_by_zone(fact: pd.DataFrame) -> pd.DataFrame:
    out = (
        fact.groupby("zone")
            .agg(revenue=("revenue", "sum"), profit=("profit", "sum"))
            .reset_index()
    )
    out["margin_pct"] = 100 * out["profit"] / out["revenue"]
    out["revenue_share_pct"] = 100 * out["revenue"] / out["revenue"].sum()
    return out.sort_values("revenue", ascending=False).reset_index(drop=True)


def margin_by_channel(fact: pd.DataFrame) -> pd.DataFrame:
    out = (
        fact.groupby("customer_type")
            .agg(revenue=("revenue", "sum"), profit=("profit", "sum"))
            .reset_index()
    )
    out["margin_pct"] = 100 * out["profit"] / out["revenue"]
    out["revenue_share_pct"] = 100 * out["revenue"] / out["revenue"].sum()
    return out.sort_values("revenue", ascending=False).reset_index(drop=True)
