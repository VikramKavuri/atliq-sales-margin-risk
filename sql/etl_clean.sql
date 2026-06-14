-- ============================================================================
-- etl_clean.sql — the cleaning layer, as a reusable view.
-- Mirrors src/data_loader.build_fact() exactly so SQL and Python agree:
--   1. trim stray whitespace on currency,
--   2. keep only real sales (sales_amount > 0),
--   3. normalise every row to INR (a few rows are booked in USD).
-- Downstream analysis and Tableau read from this view, never from raw.
-- ============================================================================
USE sales;

CREATE OR REPLACE VIEW v_transactions_clean AS
SELECT
    t.product_code,
    t.customer_code,
    t.market_code,
    t.order_date,
    YEAR(t.order_date)                              AS order_year,
    c.custmer_name                                  AS customer_name,
    c.customer_type,
    m.markets_name,
    m.zone,
    p.product_type,
    t.sales_qty,
    UPPER(TRIM(t.currency))                         AS currency,
    -- INR normalisation (USD ≈ 75 INR over the 2017–2020 window)
    CASE WHEN UPPER(TRIM(t.currency)) LIKE 'USD%'
         THEN t.sales_amount  * 75 ELSE t.sales_amount  END AS revenue,
    CASE WHEN UPPER(TRIM(t.currency)) LIKE 'USD%'
         THEN t.profit_margin * 75 ELSE t.profit_margin END AS profit
FROM transactions t
LEFT JOIN customers c ON c.customer_code = t.customer_code
LEFT JOIN markets   m ON m.markets_code  = t.market_code
LEFT JOIN products  p ON p.product_code  = t.product_code
WHERE t.sales_amount > 0;   -- drop non-positive data-entry artefacts
