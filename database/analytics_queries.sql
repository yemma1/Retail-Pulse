-- ============================================================================
-- ONLINE RETAIL SALES ANALYTICS - ORACLE SQL ANALYTICAL QUERIES
-- File: analytics_queries.sql
-- Description: Production-grade Oracle SQL queries powering the dashboard,
--              featuring CTEs, Window Functions (RANK, DENSE_RANK, ROW_NUMBER),
--              Aggregations, Subqueries, Date Functions, and CASE expressions.
-- Formula: Net Revenue = SUM((oi.QUANTITY * oi.UNIT_PRICE) - oi.DISCOUNT)
-- Note: Excludes cancelled orders (o.ORDER_STATUS != 'Cancelled')
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. OVERALL KPI METRICS SUMMARY
-- Calculates Total Revenue, Total Orders, Total Units Sold, Unique Customers,
-- Average Order Value (AOV), and Active Product Categories.
-- Concepts: Aggregate Functions, Subqueries, DISTINCT, CASE, JOINs
-- ----------------------------------------------------------------------------
SELECT
    ROUND(SUM((oi.QUANTITY * oi.UNIT_PRICE) - oi.DISCOUNT), 2) AS TOTAL_REVENUE,
    COUNT(DISTINCT o.ORDER_ID)                                 AS TOTAL_ORDERS,
    SUM(oi.QUANTITY)                                           AS TOTAL_PRODUCTS_SOLD,
    COUNT(DISTINCT o.CUSTOMER_ID)                              AS TOTAL_CUSTOMERS,
    ROUND(
        SUM((oi.QUANTITY * oi.UNIT_PRICE) - oi.DISCOUNT) / 
        NULLIF(COUNT(DISTINCT o.ORDER_ID), 0), 2
    )                                                          AS AVERAGE_ORDER_VALUE,
    COUNT(DISTINCT p.CATEGORY_ID)                              AS TOTAL_ACTIVE_CATEGORIES
FROM ORDERS o
INNER JOIN ORDER_ITEMS oi ON o.ORDER_ID = oi.ORDER_ID
INNER JOIN PRODUCTS p     ON oi.PRODUCT_ID = p.PRODUCT_ID
WHERE o.ORDER_STATUS != 'Cancelled';


-- ----------------------------------------------------------------------------
-- 2. FEATURE 1: TOTAL REVENUE BREAKDOWN
-- 2A. Revenue by Product Category
-- Concepts: GROUP BY, ORDER BY, Aggregates, Rounding
-- ----------------------------------------------------------------------------
SELECT 
    c.CATEGORY_NAME,
    COUNT(DISTINCT o.ORDER_ID)                                 AS ORDER_COUNT,
    SUM(oi.QUANTITY)                                           AS TOTAL_QUANTITY_SOLD,
    ROUND(SUM((oi.QUANTITY * oi.UNIT_PRICE) - oi.DISCOUNT), 2) AS TOTAL_REVENUE,
    ROUND(AVG((oi.QUANTITY * oi.UNIT_PRICE) - oi.DISCOUNT), 2) AS AVG_ITEM_REVENUE
FROM CATEGORIES c
INNER JOIN PRODUCTS p     ON c.CATEGORY_ID = p.CATEGORY_ID
INNER JOIN ORDER_ITEMS oi ON p.PRODUCT_ID = oi.PRODUCT_ID
INNER JOIN ORDERS o       ON oi.ORDER_ID = o.ORDER_ID
WHERE o.ORDER_STATUS != 'Cancelled'
GROUP BY c.CATEGORY_ID, c.CATEGORY_NAME
ORDER BY TOTAL_REVENUE DESC;


-- 2B. Revenue by Customer City
-- Concepts: INNER JOIN across 4 tables, GROUP BY, Aggregate functions
-- ----------------------------------------------------------------------------
SELECT 
    cust.CITY,
    cust.STATE,
    COUNT(DISTINCT cust.CUSTOMER_ID)                           AS TOTAL_CUSTOMERS,
    COUNT(DISTINCT o.ORDER_ID)                                 AS TOTAL_ORDERS,
    SUM(oi.QUANTITY)                                           AS UNITS_SOLD,
    ROUND(SUM((oi.QUANTITY * oi.UNIT_PRICE) - oi.DISCOUNT), 2) AS TOTAL_REVENUE
FROM CUSTOMERS cust
INNER JOIN ORDERS o       ON cust.CUSTOMER_ID = o.CUSTOMER_ID
INNER JOIN ORDER_ITEMS oi ON o.ORDER_ID = oi.ORDER_ID
WHERE o.ORDER_STATUS != 'Cancelled'
GROUP BY cust.CITY, cust.STATE
ORDER BY TOTAL_REVENUE DESC;


-- ----------------------------------------------------------------------------
-- 3. FEATURE 2: TOP 10 BEST-SELLING PRODUCTS
-- Identifies top 10 products by quantity sold with total revenue generated.
-- Concepts: CTE (WITH clause), Window Function (DENSE_RANK() OVER), WHERE filter
-- ----------------------------------------------------------------------------
WITH ProductSalesRank AS (
    SELECT 
        p.PRODUCT_ID,
        p.PRODUCT_NAME,
        c.CATEGORY_NAME,
        p.PRICE                                                    AS CURRENT_UNIT_PRICE,
        p.STOCK_QUANTITY                                           AS REMAINING_STOCK,
        SUM(oi.QUANTITY)                                           AS TOTAL_QUANTITY_SOLD,
        ROUND(SUM((oi.QUANTITY * oi.UNIT_PRICE) - oi.DISCOUNT), 2) AS TOTAL_REVENUE,
        DENSE_RANK() OVER (ORDER BY SUM(oi.QUANTITY) DESC)         AS SALES_RANK_BY_QTY,
        DENSE_RANK() OVER (
            ORDER BY SUM((oi.QUANTITY * oi.UNIT_PRICE) - oi.DISCOUNT) DESC
        )                                                          AS SALES_RANK_BY_REVENUE
    FROM PRODUCTS p
    INNER JOIN CATEGORIES c   ON p.CATEGORY_ID = c.CATEGORY_ID
    INNER JOIN ORDER_ITEMS oi ON p.PRODUCT_ID = oi.PRODUCT_ID
    INNER JOIN ORDERS o       ON oi.ORDER_ID = o.ORDER_ID
    WHERE o.ORDER_STATUS != 'Cancelled'
    GROUP BY p.PRODUCT_ID, p.PRODUCT_NAME, c.CATEGORY_NAME, p.PRICE, p.STOCK_QUANTITY
)
SELECT 
    SALES_RANK_BY_QTY AS RANK,
    PRODUCT_NAME,
    CATEGORY_NAME,
    CURRENT_UNIT_PRICE,
    TOTAL_QUANTITY_SOLD,
    TOTAL_REVENUE,
    REMAINING_STOCK,
    SALES_RANK_BY_REVENUE
FROM ProductSalesRank
WHERE SALES_RANK_BY_QTY <= 10
ORDER BY TOTAL_QUANTITY_SOLD DESC, TOTAL_REVENUE DESC;


-- ----------------------------------------------------------------------------
-- 4. FEATURE 3: MONTHLY SALES ANALYSIS & MOM GROWTH
-- Calculates monthly revenue, order count, AOV, and Month-over-Month (MoM) growth %.
-- Concepts: CTE, Date Functions (TO_CHAR, TRUNC), Window Function (LAG() OVER)
-- ----------------------------------------------------------------------------
WITH MonthlySummary AS (
    SELECT 
        TO_CHAR(o.ORDER_DATE, 'YYYY-MM')                           AS SALES_MONTH,
        TRUNC(o.ORDER_DATE, 'MM')                                  AS MONTH_DATE,
        COUNT(DISTINCT o.ORDER_ID)                                 AS ORDER_COUNT,
        SUM(oi.QUANTITY)                                           AS UNITS_SOLD,
        ROUND(SUM((oi.QUANTITY * oi.UNIT_PRICE) - oi.DISCOUNT), 2) AS MONTHLY_REVENUE,
        ROUND(
            SUM((oi.QUANTITY * oi.UNIT_PRICE) - oi.DISCOUNT) / 
            NULLIF(COUNT(DISTINCT o.ORDER_ID), 0), 2
        )                                                          AS MONTHLY_AOV
    FROM ORDERS o
    INNER JOIN ORDER_ITEMS oi ON o.ORDER_ID = oi.ORDER_ID
    WHERE o.ORDER_STATUS != 'Cancelled'
    GROUP BY TO_CHAR(o.ORDER_DATE, 'YYYY-MM'), TRUNC(o.ORDER_DATE, 'MM')
),
MonthlyGrowth AS (
    SELECT 
        SALES_MONTH,
        MONTH_DATE,
        ORDER_COUNT,
        UNITS_SOLD,
        MONTHLY_REVENUE,
        MONTHLY_AOV,
        LAG(MONTHLY_REVENUE, 1) OVER (ORDER BY MONTH_DATE)         AS PREVIOUS_MONTH_REVENUE,
        DENSE_RANK() OVER (ORDER BY MONTHLY_REVENUE DESC)          AS REVENUE_RANK
    FROM MonthlySummary
)
SELECT 
    SALES_MONTH,
    ORDER_COUNT,
    UNITS_SOLD,
    MONTHLY_REVENUE,
    MONTHLY_AOV,
    NVL(PREVIOUS_MONTH_REVENUE, 0)                                 AS PREV_MONTH_REVENUE,
    CASE 
        WHEN PREVIOUS_MONTH_REVENUE IS NULL THEN 0.00
        WHEN PREVIOUS_MONTH_REVENUE = 0 THEN 0.00
        ELSE ROUND(((MONTHLY_REVENUE - PREVIOUS_MONTH_REVENUE) / PREVIOUS_MONTH_REVENUE) * 100, 2)
    END                                                            AS MOM_GROWTH_PERCENT,
    CASE 
        WHEN REVENUE_RANK = 1 THEN 'Highest Revenue Month'
        ELSE 'Regular'
    END                                                            AS MONTH_HIGHLIGHT
FROM MonthlyGrowth
ORDER BY MONTH_DATE ASC;


-- ----------------------------------------------------------------------------
-- 5. FEATURE 4: TOP 10 CUSTOMERS BY SPENDING
-- Identifies VIP customers with orders, total spend, AOV, and customer rank.
-- Concepts: Window Functions (ROW_NUMBER, DENSE_RANK), Subqueries, Aggregation
-- ----------------------------------------------------------------------------
WITH CustomerSpending AS (
    SELECT 
        c.CUSTOMER_ID,
        c.CUSTOMER_NAME,
        c.EMAIL,
        c.CITY,
        c.STATE,
        COUNT(DISTINCT o.ORDER_ID)                                 AS TOTAL_ORDERS,
        SUM(oi.QUANTITY)                                           AS TOTAL_ITEMS_BOUGHT,
        ROUND(SUM((oi.QUANTITY * oi.UNIT_PRICE) - oi.DISCOUNT), 2) AS TOTAL_SPENDING,
        ROUND(
            SUM((oi.QUANTITY * oi.UNIT_PRICE) - oi.DISCOUNT) / 
            NULLIF(COUNT(DISTINCT o.ORDER_ID), 0), 2
        )                                                          AS AVERAGE_ORDER_VALUE,
        DENSE_RANK() OVER (
            ORDER BY SUM((oi.QUANTITY * oi.UNIT_PRICE) - oi.DISCOUNT) DESC
        )                                                          AS SPENDING_RANK,
        ROW_NUMBER() OVER (
            ORDER BY SUM((oi.QUANTITY * oi.UNIT_PRICE) - oi.DISCOUNT) DESC
        )                                                          AS ROW_NUM
    FROM CUSTOMERS c
    INNER JOIN ORDERS o       ON c.CUSTOMER_ID = o.CUSTOMER_ID
    INNER JOIN ORDER_ITEMS oi ON o.ORDER_ID = oi.ORDER_ID
    WHERE o.ORDER_STATUS != 'Cancelled'
    GROUP BY c.CUSTOMER_ID, c.CUSTOMER_NAME, c.EMAIL, c.CITY, c.STATE
)
SELECT 
    SPENDING_RANK AS RANK,
    CUSTOMER_NAME,
    EMAIL,
    CITY || ', ' || STATE                                          AS LOCATION,
    TOTAL_ORDERS,
    TOTAL_ITEMS_BOUGHT,
    TOTAL_SPENDING,
    AVERAGE_ORDER_VALUE,
    CASE 
        WHEN SPENDING_RANK = 1 THEN 'Tier 1 - Platinum'
        WHEN SPENDING_RANK <= 3 THEN 'Tier 2 - Gold'
        WHEN SPENDING_RANK <= 10 THEN 'Tier 3 - Silver'
        ELSE 'Standard'
    END                                                            AS CUSTOMER_TIER
FROM CustomerSpending
WHERE SPENDING_RANK <= 10
ORDER BY SPENDING_RANK ASC;


-- ----------------------------------------------------------------------------
-- 6. FEATURE 5: PRODUCT CATEGORY COMPARISON & MARKET SHARE
-- Compares revenue across product categories, calculates quantity, and market share %.
-- Concepts: Analytic Window Function SUM() OVER (), Ratio-to-Report equivalent
-- ----------------------------------------------------------------------------
WITH CategoryTotals AS (
    SELECT 
        c.CATEGORY_ID,
        c.CATEGORY_NAME,
        COUNT(DISTINCT p.PRODUCT_ID)                               AS DISTINCT_PRODUCTS,
        COUNT(DISTINCT o.ORDER_ID)                                 AS TOTAL_ORDERS,
        SUM(oi.QUANTITY)                                           AS TOTAL_QUANTITY_SOLD,
        ROUND(SUM((oi.QUANTITY * oi.UNIT_PRICE) - oi.DISCOUNT), 2) AS TOTAL_REVENUE
    FROM CATEGORIES c
    INNER JOIN PRODUCTS p     ON c.CATEGORY_ID = p.CATEGORY_ID
    INNER JOIN ORDER_ITEMS oi ON p.PRODUCT_ID = oi.PRODUCT_ID
    INNER JOIN ORDERS o       ON oi.ORDER_ID = o.ORDER_ID
    WHERE o.ORDER_STATUS != 'Cancelled'
    GROUP BY c.CATEGORY_ID, c.CATEGORY_NAME
)
SELECT 
    CATEGORY_NAME,
    DISTINCT_PRODUCTS,
    TOTAL_ORDERS,
    TOTAL_QUANTITY_SOLD,
    TOTAL_REVENUE,
    ROUND(
        (TOTAL_REVENUE / NULLIF(SUM(TOTAL_REVENUE) OVER (), 0)) * 100, 2
    )                                                              AS REVENUE_SHARE_PERCENT,
    DENSE_RANK() OVER (ORDER BY TOTAL_REVENUE DESC)                AS CATEGORY_RANK,
    CASE 
        WHEN DENSE_RANK() OVER (ORDER BY TOTAL_REVENUE DESC) = 1 
            THEN 'Top Performing Category'
        ELSE 'Standard Category'
    END                                                            AS PERFORMANCE_STATUS
FROM CategoryTotals
ORDER BY TOTAL_REVENUE DESC;


-- ----------------------------------------------------------------------------
-- 7. FEATURE 6: HIGH-REVENUE CITIES RANKING
-- Identifies high-revenue cities and ranks them.
-- Concepts: DENSE_RANK() OVER, Aggregate Functions, HAVING clause
-- ----------------------------------------------------------------------------
WITH CityMetrics AS (
    SELECT 
        cust.CITY,
        cust.STATE,
        COUNT(DISTINCT cust.CUSTOMER_ID)                           AS CUSTOMER_COUNT,
        COUNT(DISTINCT o.ORDER_ID)                                 AS TOTAL_ORDERS,
        SUM(oi.QUANTITY)                                           AS TOTAL_UNITS_SOLD,
        ROUND(SUM((oi.QUANTITY * oi.UNIT_PRICE) - oi.DISCOUNT), 2) AS TOTAL_REVENUE,
        ROUND(
            SUM((oi.QUANTITY * oi.UNIT_PRICE) - oi.DISCOUNT) / 
            NULLIF(COUNT(DISTINCT o.ORDER_ID), 0), 2
        )                                                          AS AOV_PER_CITY
    FROM CUSTOMERS cust
    INNER JOIN ORDERS o       ON cust.CUSTOMER_ID = o.CUSTOMER_ID
    INNER JOIN ORDER_ITEMS oi ON o.ORDER_ID = oi.ORDER_ID
    WHERE o.ORDER_STATUS != 'Cancelled'
    GROUP BY cust.CITY, cust.STATE
    HAVING COUNT(DISTINCT o.ORDER_ID) >= 1
)
SELECT 
    DENSE_RANK() OVER (ORDER BY TOTAL_REVENUE DESC)                AS CITY_RANK,
    CITY,
    STATE,
    CUSTOMER_COUNT,
    TOTAL_ORDERS,
    TOTAL_UNITS_SOLD,
    TOTAL_REVENUE,
    AOV_PER_CITY
FROM CityMetrics
ORDER BY CITY_RANK ASC;


-- ----------------------------------------------------------------------------
-- 8. FEATURE 7: BUSINESS INSIGHTS SQL QUERIES (DYNAMIC ENGINE)
-- 8A. Top Revenue Product
-- ----------------------------------------------------------------------------
SELECT * FROM (
    SELECT 
        p.PRODUCT_NAME,
        c.CATEGORY_NAME,
        SUM(oi.QUANTITY)                                           AS UNITS_SOLD,
        ROUND(SUM((oi.QUANTITY * oi.UNIT_PRICE) - oi.DISCOUNT), 2) AS REVENUE,
        ROUND(
            (SUM((oi.QUANTITY * oi.UNIT_PRICE) - oi.DISCOUNT) / 
             (SELECT SUM((oi2.QUANTITY * oi2.UNIT_PRICE) - oi2.DISCOUNT) 
              FROM ORDER_ITEMS oi2 
              INNER JOIN ORDERS o2 ON oi2.ORDER_ID = o2.ORDER_ID 
              WHERE o2.ORDER_STATUS != 'Cancelled')) * 100, 2
        )                                                          AS REVENUE_CONTRIBUTION_PCT
    FROM PRODUCTS p
    INNER JOIN CATEGORIES c   ON p.CATEGORY_ID = c.CATEGORY_ID
    INNER JOIN ORDER_ITEMS oi ON p.PRODUCT_ID = oi.PRODUCT_ID
    INNER JOIN ORDERS o       ON oi.ORDER_ID = o.ORDER_ID
    WHERE o.ORDER_STATUS != 'Cancelled'
    GROUP BY p.PRODUCT_ID, p.PRODUCT_NAME, c.CATEGORY_NAME
    ORDER BY REVENUE DESC
) WHERE ROWNUM = 1;


-- 8B. Low-Selling Products (Inventory Warning)
-- Concepts: LEFT JOIN, NVL, HAVING clause, ORDER BY
-- ----------------------------------------------------------------------------
SELECT 
    p.PRODUCT_NAME,
    c.CATEGORY_NAME,
    p.STOCK_QUANTITY                                               AS CURRENT_STOCK,
    NVL(SUM(oi.QUANTITY), 0)                                       AS UNITS_SOLD,
    NVL(ROUND(SUM((oi.QUANTITY * oi.UNIT_PRICE) - oi.DISCOUNT), 2), 0) AS TOTAL_REVENUE
FROM PRODUCTS p
INNER JOIN CATEGORIES c        ON p.CATEGORY_ID = c.CATEGORY_ID
LEFT JOIN ORDER_ITEMS oi       ON p.PRODUCT_ID = oi.PRODUCT_ID
LEFT JOIN ORDERS o             ON oi.ORDER_ID = o.ORDER_ID AND o.ORDER_STATUS != 'Cancelled'
GROUP BY p.PRODUCT_ID, p.PRODUCT_NAME, c.CATEGORY_NAME, p.STOCK_QUANTITY
HAVING NVL(SUM(oi.QUANTITY), 0) <= 5
ORDER BY UNITS_SOLD ASC, TOTAL_REVENUE ASC;


-- 8C. Order Fulfillment & Cancellation Impact
-- Evaluates the financial impact of cancelled orders.
-- Concepts: CASE WHEN, GROUP BY, Financial Loss Calculation
-- ----------------------------------------------------------------------------
SELECT 
    o.ORDER_STATUS,
    COUNT(DISTINCT o.ORDER_ID)                                     AS ORDER_COUNT,
    ROUND(
        COUNT(DISTINCT o.ORDER_ID) * 100.0 / 
        (SELECT COUNT(*) FROM ORDERS), 2
    )                                                              AS STATUS_PERCENTAGE,
    ROUND(SUM((oi.QUANTITY * oi.UNIT_PRICE) - oi.DISCOUNT), 2)     AS GROSS_VALUE
FROM ORDERS o
INNER JOIN ORDER_ITEMS oi ON o.ORDER_ID = oi.ORDER_ID
GROUP BY o.ORDER_STATUS
ORDER BY GROSS_VALUE DESC;
