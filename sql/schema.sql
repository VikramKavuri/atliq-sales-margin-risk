-- ============================================================================
-- schema.sql — AtliQ Hardware sales data model (MySQL 8.0+)
-- Star schema: one transactions fact, four conformed dimensions.
-- DDL preserved to match data/raw/db_dump.sql exactly (including the source's
-- `custmer_name` misspelling) so a fresh `SOURCE db_dump.sql` reproduces 1:1.
-- ============================================================================

CREATE DATABASE IF NOT EXISTS sales;
USE sales;

-- Dimension: customers (who we sell to, and through which channel) -------------
CREATE TABLE customers (
  customer_code  VARCHAR(45) NOT NULL,
  custmer_name   VARCHAR(45)     NULL,   -- [sic] misspelled in source
  customer_type  VARCHAR(45)     NULL,   -- 'Brick & Mortar' | 'E-Commerce'
  PRIMARY KEY (customer_code)
);

-- Dimension: markets (cities, grouped into zones) -----------------------------
CREATE TABLE markets (
  markets_code  VARCHAR(45) NOT NULL,
  markets_name  VARCHAR(45)     NULL,
  zone          VARCHAR(45)     NULL,    -- 'North' | 'Central' | 'South'
  PRIMARY KEY (markets_code)
);

-- Dimension: products ---------------------------------------------------------
CREATE TABLE products (
  product_code  VARCHAR(45) NOT NULL,
  product_type  VARCHAR(45)     NULL,    -- 'Own Brand' | 'Distribution'
  PRIMARY KEY (product_code)
);

-- Dimension: date (pre-built calendar) ----------------------------------------
CREATE TABLE `date` (
  `date`       DATE NOT NULL,
  cy_date      DATE     NULL,
  `year`       INT      NULL,
  month_name   VARCHAR(45) NULL,
  date_yy_mmm  VARCHAR(45) NULL,
  PRIMARY KEY (`date`)
);

-- Fact: transactions (grain = one product sold to one customer on one date) ---
CREATE TABLE transactions (
  product_code              VARCHAR(45) NULL,
  customer_code             VARCHAR(45) NULL,
  market_code               VARCHAR(45) NULL,
  order_date                DATE        NULL,
  sales_qty                 INT         NULL,
  sales_amount              DOUBLE      NULL,   -- in `currency`
  currency                  VARCHAR(45) NULL,   -- mostly 'INR', a few 'USD'
  profit_margin_percentage  DOUBLE      NULL,
  profit_margin             DOUBLE      NULL,   -- absolute, in `currency`
  cost_price                DOUBLE      NULL,
  KEY ix_tx_customer (customer_code),
  KEY ix_tx_market   (market_code),
  KEY ix_tx_date     (order_date)
);
