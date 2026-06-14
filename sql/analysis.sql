-- ============================================================================
-- analysis.sql — the five findings, in SQL.
-- Reads the cleaned view from etl_clean.sql. Each query answers one business
-- question and is annotated with the decision it drives. Run after schema.sql,
-- the data load, and etl_clean.sql.
-- ============================================================================
USE sales;

-- Headline KPIs ---------------------------------------------------------------
SELECT
    COUNT(*)                              AS transactions,
    ROUND(SUM(revenue) / 1e7, 1)          AS revenue_cr,
    ROUND(100 * SUM(profit) / SUM(revenue), 2) AS overall_margin_pct,
    COUNT(DISTINCT customer_name)         AS customers,
    COUNT(DISTINCT markets_name)          AS markets
FROM v_transactions_clean;

-- Finding 1 — Customer concentration (Pareto via a window function) ------------
-- The cumulative-share column is what exposes the single-account dependency:
-- the #1 customer crosses 42%, the top 5 cross 61%.
WITH by_customer AS (
    SELECT customer_name, SUM(revenue) AS revenue
    FROM v_transactions_clean
    GROUP BY customer_name
)
SELECT
    RANK() OVER (ORDER BY revenue DESC)                                   AS rnk,
    customer_name,
    ROUND(revenue / 1e7, 1)                                               AS revenue_cr,
    ROUND(100 * revenue / SUM(revenue) OVER (), 1)                        AS share_pct,
    ROUND(100 * SUM(revenue) OVER (ORDER BY revenue DESC) / SUM(revenue) OVER (), 1)
                                                                          AS cum_share_pct
FROM by_customer
ORDER BY revenue DESC
LIMIT 10;
-- DECISION: account diversification is a board-level risk, not a sales nicety.

-- Finding 2 — Markets ranked by margin (find the value destroyers) -------------
SELECT
    markets_name,
    ROUND(SUM(revenue) / 1e7, 1)               AS revenue_cr,
    ROUND(100 * SUM(profit) / SUM(revenue), 2) AS margin_pct
FROM v_transactions_clean
GROUP BY markets_name
ORDER BY margin_pct ASC;     -- Bengaluru (-20.8%) and Kanpur (-0.5%) surface at the top
-- DECISION: re-price or exit loss-making markets before chasing new growth.

-- Finding 3 — Zone: revenue share vs margin (growth in the wrong place) --------
SELECT
    zone,
    ROUND(100 * SUM(revenue) / SUM(SUM(revenue)) OVER (), 1) AS revenue_share_pct,
    ROUND(100 * SUM(profit)  / SUM(revenue), 2)              AS margin_pct
FROM v_transactions_clean
GROUP BY zone
ORDER BY SUM(revenue) DESC;  -- North is biggest (69% of rev) but low-margin (2.4%); Central most profitable (3.3%)
-- DECISION: tilt sales incentives toward Central/South.

-- Finding 4 — Channel margin (E-Commerce vs Brick & Mortar) --------------------
SELECT
    customer_type,
    ROUND(100 * SUM(revenue) / SUM(SUM(revenue)) OVER (), 1) AS revenue_share_pct,
    ROUND(100 * SUM(profit)  / SUM(revenue), 2)              AS margin_pct
FROM v_transactions_clean
GROUP BY customer_type
ORDER BY margin_pct DESC;    -- E-Commerce 3.5% vs Brick & Mortar 2.3%
-- DECISION: move marginal volume online to lift profit on existing revenue.

-- Finding 5 — Full-year revenue trend (exclude partial 2017 & 2020) ------------
SELECT
    order_year,
    ROUND(SUM(revenue) / 1e7, 1) AS revenue_cr
FROM v_transactions_clean
WHERE order_year IN (2018, 2019)   -- the only two complete calendar years
GROUP BY order_year
ORDER BY order_year;                -- ₹414M -> ₹336M  ≈  -19%
-- DECISION: the fixes above stabilise a shrinking, low-margin book.
