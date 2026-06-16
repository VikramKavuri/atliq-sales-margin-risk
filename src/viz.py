"""Decisive figures for the README and report.

Every chart leads with a *takeaway* title (not "Figure 3"), labels its axes and
units, and is saved at presentation resolution. One chart = one finding.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless: figures render the same in a notebook or in CI
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = PROJECT_ROOT / "reports" / "figures"

INK = "#1b2a4a"
ACCENT = "#2563eb"
GOOD = "#0f9d58"
BAD = "#d93025"
MUTED = "#9aa5b1"

plt.rcParams.update({
    "figure.dpi": 130,
    "savefig.bbox": "tight",
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.titleweight": "bold",
    "axes.titlecolor": INK,
    "axes.labelcolor": INK,
    "axes.edgecolor": MUTED,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "text.color": INK,
})


def _save(fig, name: str, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / name
    fig.savefig(path, facecolor="white")
    plt.close(fig)
    return path


def fig_customer_concentration(conc, out_dir: Path = FIG_DIR, top: int = 10) -> Path:
    d = conc.head(top)
    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.bar(range(len(d)), d["revenue"] / 1e7, color=MUTED, width=0.65)
    bars[0].set_color(BAD)  # the single point of failure
    ax.set_ylabel("Revenue (₹ Cr)")
    ax.set_xticks(range(len(d)))
    ax.set_xticklabels(d["customer_name"], rotation=35, ha="right", fontsize=9)

    ax2 = ax.twinx()
    ax2.plot(range(len(d)), d["cum_share_pct"], color=ACCENT, marker="o", lw=2)
    ax2.set_ylabel("Cumulative share of revenue (%)", color=ACCENT)
    ax2.tick_params(axis="y", labelcolor=ACCENT)
    ax2.set_ylim(0, 105)
    ax2.spines["top"].set_visible(False)
    ax2.axhline(conc.head(5)["share_pct"].sum(), ls="--", color=ACCENT, alpha=0.4)

    top1 = conc.iloc[0]["share_pct"]
    top5 = conc.head(5)["share_pct"].sum()
    ax.set_title(f"One customer is {top1:.0f}% of revenue; the top 5 are {top5:.0f}% — concentration risk")
    ax.annotate(f"{top1:.0f}% of all revenue",
                xy=(0, d.iloc[0]["revenue"] / 1e7), xytext=(1.4, d.iloc[0]["revenue"] / 1e7 * 0.92),
                color=BAD, fontweight="bold", fontsize=10,
                arrowprops=dict(arrowstyle="->", color=BAD))
    return _save(fig, "01_customer_concentration.png", out_dir)


def fig_margin_by_market(mm, out_dir: Path = FIG_DIR) -> Path:
    d = mm.sort_values("margin_pct")
    colors = [BAD if v < 0 else (GOOD if v >= 3.5 else MUTED) for v in d["margin_pct"]]
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ax.barh(d["markets_name"], d["margin_pct"], color=colors)
    ax.axvline(0, color=INK, lw=0.8)
    ax.set_xlabel("Profit margin (%)")
    ax.set_title("Two markets sell at a loss — margin ranges from −21% to +5%")
    for y, (v, name) in enumerate(zip(d["margin_pct"], d["markets_name"])):
        ax.text(v + (0.15 if v >= 0 else -0.15), y, f"{v:.1f}%",
                va="center", ha="left" if v >= 0 else "right", fontsize=8,
                color=BAD if v < 0 else INK)
    return _save(fig, "02_margin_by_market.png", out_dir)


def fig_channel_margin(ch, out_dir: Path = FIG_DIR) -> Path:
    fig, ax = plt.subplots(figsize=(7, 4.5))
    colors = [GOOD if t == "E-Commerce" else MUTED for t in ch["customer_type"]]
    bars = ax.bar(ch["customer_type"], ch["margin_pct"], color=colors, width=0.5)
    ax.set_ylabel("Profit margin (%)")
    ax.set_title("E-Commerce earns 1.5× the margin of Brick & Mortar")
    for b, m, s in zip(bars, ch["margin_pct"], ch["revenue_share_pct"]):
        ax.text(b.get_x() + b.get_width() / 2, m + 0.05, f"{m:.2f}%\n({s:.0f}% of rev)",
                ha="center", va="bottom", fontsize=9)
    ax.set_ylim(0, ch["margin_pct"].max() * 1.35)
    return _save(fig, "03_channel_margin.png", out_dir)


def fig_zone_rev_vs_margin(zone, out_dir: Path = FIG_DIR) -> Path:
    fig, ax = plt.subplots(figsize=(8, 4.8))
    x = range(len(zone))
    ax.bar(x, zone["revenue_share_pct"], width=0.6, color=MUTED, label="Share of revenue (%)")
    ax.set_xticks(list(x))
    ax.set_xticklabels(zone["zone"])
    ax.set_ylabel("Share of revenue (%)")
    for i, v in zip(x, zone["revenue_share_pct"]):
        ax.text(i, v + 1, f"{v:.0f}%", ha="center", fontsize=9, color=MUTED)

    ax2 = ax.twinx()
    ax2.plot(list(x), zone["margin_pct"], color=BAD, marker="o", lw=2, label="Profit margin (%)")
    ax2.set_ylabel("Profit margin (%)", color=BAD)
    ax2.tick_params(axis="y", labelcolor=BAD)
    ax2.set_ylim(0, zone["margin_pct"].max() * 1.4)
    ax2.spines["top"].set_visible(False)
    for i, v in zip(x, zone["margin_pct"]):
        ax2.text(i, v + 0.08, f"{v:.2f}%", ha="center", fontsize=9, color=BAD)
    ax.set_title("North — 69% of revenue — runs a thin 2.4% margin, far below Central's 3.3%")
    return _save(fig, "04_zone_revenue_vs_margin.png", out_dir)


def fig_revenue_trend(ry, out_dir: Path = FIG_DIR) -> Path:
    fig, ax = plt.subplots(figsize=(8, 4.5))
    colors = [MUTED if p else ACCENT for p in ry["partial_year"]]
    bars = ax.bar(ry["year"].astype(str), ry["revenue_cr"], color=colors, width=0.6)
    ax.set_ylabel("Revenue (₹ Cr)")
    for b, v, p in zip(bars, ry["revenue_cr"], ry["partial_year"]):
        label = f"₹{v:.0f} Cr" + (" *" if p else "")
        ax.text(b.get_x() + b.get_width() / 2, v + 5, label, ha="center", fontsize=9)
    ax.set_title("Full-year revenue fell 19% from 2018 to 2019")
    ax.annotate("* partial year (2017 from Oct, 2020 to Jun)", xy=(0.0, -0.18),
                xycoords="axes fraction", fontsize=8, color=MUTED)
    ax.yaxis.set_major_formatter(mticker.StrMethodFormatter("{x:.0f}"))
    return _save(fig, "05_revenue_trend.png", out_dir)
