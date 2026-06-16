"""Reproduce the entire analysis from the raw dump in one command.

    python src/build_report.py

Loads + cleans the data, writes the processed CSV, regenerates every figure used in
the README, and prints the headline numbers so the run is self-verifying.
"""
from __future__ import annotations

import sys

from data_loader import build_fact, write_processed
import metrics as M
import viz as V


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    fact = build_fact()
    csv = write_processed(fact)

    h = M.headline(fact)
    conc = M.customer_concentration(fact)
    mm = M.margin_by_market(fact)
    zone = M.margin_by_zone(fact)
    chan = M.margin_by_channel(fact)
    ry = M.revenue_by_year(fact)

    figs = [
        V.fig_customer_concentration(conc),
        V.fig_margin_by_market(mm),
        V.fig_channel_margin(chan),
        V.fig_zone_rev_vs_margin(zone),
        V.fig_revenue_trend(ry),
    ]

    print("=" * 64)
    print("ATLIQ SALES — HEADLINE NUMBERS")
    print("=" * 64)
    print(f"Transactions analysed : {h['transactions']:,}")
    print(f"Window                : {h['date_min']} -> {h['date_max']}")
    print(f"Total revenue         : ₹{h['revenue_cr']:.1f} Cr")
    print(f"Overall profit margin : {h['overall_margin_pct']:.2f}%")
    print(f"Top customer share    : {conc.iloc[0]['share_pct']:.1f}%  ({conc.iloc[0]['customer_name']})")
    print(f"Top-5 customer share  : {conc.head(5)['share_pct'].sum():.1f}%")
    loss_making = mm.loc[mm["margin_pct"] < 0].sort_values("margin_pct")
    print(f"Loss-making markets   : {', '.join(loss_making['markets_name'])}")
    print(f"Processed CSV         : {csv}")
    print(f"Figures written       : {len(figs)} -> reports/figures/")
    for f in figs:
        print(f"   - {f.name}")


if __name__ == "__main__":
    main()
