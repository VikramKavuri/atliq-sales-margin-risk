# Tableau Build Guide — AtliQ Sales: Revenue + Risk

A start-to-finish recipe to build the AtliQ dashboards natively in **Tableau Public / Desktop**, reproducing the original revenue view **and** extending it with the risk-analysis findings from the README. Budget ~30 minutes.

> **Why this guide exists.** Tableau workbooks can't be reliably authored outside Tableau, so the heavy lifting (cleaning, currency normalisation, joins) is done once in Python and handed to Tableau as a single flat table. Tableau just visualises it — which is exactly how a clean BI stack should work.

> **Important — measure consistency.** Build everything on the **`Revenue`** field in the CSV (cleaned, INR-normalised raw sales). This makes the dashboard **agree with the README and SQL** (Delhi NCR is the #1 market, Electricalsara = 42%). Do **not** reintroduce the old "Normalized Amount" measure — that's what made the previous dashboard disagree with the analysis.

---

## 0. Data source

1. Generate the Tableau-ready extract (one denormalised table, no joins needed):
   ```bash
   pip install -r requirements.txt
   python src/build_report.py        # writes data/processed/transactions_clean.csv
   ```
2. Tableau → **Connect → Text file** → select `data/processed/transactions_clean.csv`.
3. Confirm field roles on the data-source tab:

| Field | Role | Notes |
|---|---|---|
| `order_date` | Date (Dimension) | set to Date |
| `year` | Dimension (discrete) | convert to dimension; use as discrete |
| `customer_name`, `customer_type` | Dimension | customer + channel (Brick & Mortar / E-Commerce) |
| `markets_name`, `zone` | Dimension | city + region |
| `product_code`, `product_type` | Dimension | |
| `sales_qty` | Measure (SUM) | units |
| **`revenue`** | **Measure (SUM)** | cleaned, INR — **the headline measure** |
| **`profit`** | **Measure (SUM)** | cleaned, INR |
| `currency` | Dimension | INR (kept for transparency) |

4. Tableau Public creates the extract automatically for this CSV when publishing; if your Desktop version shows a **Live / Extract** toggle, use **Extract** for speed.

---

## 1. Calculated fields (create these once)

Right-click in the Data pane → **Create Calculated Field** for each:

```
// --- KPI measures ---
Revenue (₹ Cr)        =  SUM([revenue]) / 10000000
Profit (₹ Cr)         =  SUM([profit])  / 10000000
Profit Margin %       =  SUM([profit]) / SUM([revenue])          // format as Percentage, 1 dp
Sales Quantity        =  SUM([sales_qty])

// --- Customer concentration (Pareto) : these are TABLE CALCS ---
% of Revenue          =  SUM([revenue]) / TOTAL(SUM([revenue]))
Cumulative % Revenue  =  RUNNING_SUM(SUM([revenue])) / TOTAL(SUM([revenue]))
// (Tableau computes both along the customer axis sorted descending — set in step 2.6)

// --- Margin / risk colouring ---
Margin Sign           =  IF SUM([profit]) < 0 THEN 'Loss-making' ELSE 'Profitable' END

// --- Year handling (2017 & 2020 are partial) ---
Year Completeness     =  IF [year] = 2017 OR [year] = 2020 THEN 'Partial year' ELSE 'Full year' END
Full-Year Revenue     =  IF [year] = 2018 OR [year] = 2019 THEN [revenue] END
```

Optional KPI label string (for the header tiles):
```
KPI Revenue Label     =  '₹' + STR(ROUND(SUM([revenue])/10000000,1)) + ' Cr'
```

---

## 2. Worksheets

Build each as its own sheet. Titles are written as **takeaways**, not labels (per the project standard).

### Dashboard 1 — "Revenue Overview" (reproduces the screenshot)

**2.1 KPI · Total Revenue** — new sheet `KPI Revenue`
- Marks: **Text**. Drag `Revenue (₹ Cr)` → Text. Format big/bold. Title: "Total Revenue".
- Target value: **₹98.5 Cr**.

**2.2 KPI · Sales Quantity** — `KPI Qty`
- Marks: Text. `Sales Quantity` → Text. Target: **~2.43M units**.

**2.3 KPI · Total Profit** — `KPI Profit`
- Marks: Text. `Profit (₹ Cr)` → Text, plus `Profit Margin %` as a second line. Targets: **₹2.6 Cr**, **2.6%**.

**2.4 Revenue by Markets** — `Rev by Market`
- Columns: `revenue` · Rows: `markets_name`.
- Sort `markets_name` descending by `revenue`. Marks: Bar. Label with `Revenue (₹ Cr)`.
- Title: **"Delhi NCR drives the book — one city is half of revenue."** (Delhi NCR ≈ ₹52 Cr.)

**2.5 Sales Quantity by Markets** — `Qty by Market`
- Columns: `sales_qty` · Rows: `markets_name`, sorted desc. Marks: Bar.

**2.6 Top 5 Customers** — `Top 5 Customers`
- Columns: `revenue` · Rows: `customer_name`.
- Filter `customer_name` → **Top → By field → Top 5 by SUM(revenue)**.
- Sort desc. Marks: Bar. Title: **"The top 5 customers are 61% of revenue."**

**2.7 Top 5 Products** — `Top 5 Products`
- Columns: `revenue` · Rows: `product_code`. Filter Top 5 by SUM(revenue). Bar, sorted desc.

**2.8 Revenue by Year** — `Rev by Year`
- Columns: `year` (discrete) · Rows: `revenue`.
- Color by `Year Completeness` (grey = partial). Marks: Bar or Line. Label `Revenue (₹ Cr)`.
- Title: **"Full-year revenue fell 19% (2018 → 2019)."** Add a caption: *2017 & 2020 are partial.*

### Dashboard 2 — "Risk & Margin" (the extension)

**2.9 Customer Concentration (Pareto)** — `Concentration`
- Columns: `customer_name` (sorted desc by `revenue`) · Rows: `revenue` (bars) **and** `Cumulative % Revenue` (dual axis, line).
- For `Cumulative % Revenue`: **Compute Using → customer_name**. Synchronise/secondary axis 0–100%.
- Colour the #1 bar (Electricalsara) red. Title: **"One customer = 42% of revenue — a single point of failure."**

**2.10 Margin by Market** — `Margin by Market`
- Columns: `Profit Margin %` · Rows: `markets_name`, sorted **ascending** by `Profit Margin %`.
- Color by `Margin Sign` (red = loss-making). Marks: Bar. Label with `Profit Margin %`.
- Title: **"Two markets sell at a loss — Bengaluru −20.8%, Kanpur −0.5%."**

**2.11 Profit Margin by Channel** — `Channel Margin`
- Columns: `customer_type` · Rows: `Profit Margin %`. Bar. Label %.
- Title: **"E-Commerce earns 1.5× the margin of Brick & Mortar (3.5% vs 2.3%)."**

**2.12 Zone — Revenue vs Margin** — `Zone`
- Rows: `% of Revenue` (bar) and `Profit Margin %` (line, dual axis) · Columns: `zone`.
- Title: **"North — the biggest region (69% of revenue) — runs a thin 2.4% margin (Central earns 3.3%)."**

---

## 3. Assemble the dashboards

**Dashboard 1 — Revenue Overview** (size: fixed, 1200×800 or Automatic)
- Top row: a horizontal container with the 3 KPI sheets (2.1–2.3).
- Middle row: `Rev by Market` | `Qty by Market`.
- Bottom row: `Rev by Year` spanning, with `Top 5 Customers` | `Top 5 Products` beside/under it.
- Add a Title text object: **"AtliQ Sales — Revenue Overview"**.

**Dashboard 2 — Risk & Margin** (same size)
- Top: `Concentration` (full width — it's the headline).
- Middle: `Margin by Market` | `Channel Margin`.
- Bottom: `Zone`.
- Title: **"AtliQ Sales — Where the business is fragile"**.

---

## 4. Interactivity (what makes it feel real)

- **Dashboard → Actions → Add Filter action:** source `Rev by Market`, run on **Select**, target all other sheets → clicking a market filters the whole dashboard.
- Add a **Year** filter (from `year`) and **Show Filter**; apply to all worksheets using this data source.
- Add a **Zone / Channel** highlight action for quick comparison.
- Add a market **Map** later if you geocode `markets_name` (optional polish).

---

## 5. Publish & live URL

1. **Server → Tableau Public → Save to Tableau Public As…** → name it `AtliQ-Sales-Insights`.
2. Published workbook: <https://public.tableau.com/app/profile/thrivikrama.rao.kavuri6778/viz/AtliQ-Sales-Insights/RevenueOverview>
3. Confirm both dashboards are reachable from the published view through visible tabs or dashboard navigation buttons.

---

## 6. QA — verify your build matches the analysis

If your numbers don't match these (from `python src/build_report.py`), something's off — likely a missed filter or the wrong measure:

| Check | Expected |
|---|---|
| Total revenue | **₹98.5 Cr** (₹985M) |
| Overall profit margin | **2.6%** |
| #1 customer share | **Electricalsara Stores = 42%** |
| Top-5 customer share | **61%** |
| #1 market by revenue | **Delhi NCR (≈ ₹52 Cr)** |
| Loss-making markets | **Bengaluru −20.8%, Kanpur −0.5%** |
| Channel margins | **E-Commerce 3.5% vs Brick & Mortar 2.3%** |
| Full-year trend | **2018 ₹414M → 2019 ₹336M (−19%)** |

When these line up, the live Tableau dashboard and the README finally tell the **same story** — which is the whole point.
