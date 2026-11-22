"""
Online Retail Sales Analytics - Analytics REST API Blueprint
Provides RESTful JSON endpoints for all analytical features, KPI metrics,
and dynamic business insights.
"""

from flask import Blueprint, jsonify, request
from services.analytics_service import AnalyticsService
from services.insights_service import InsightsService
from database.db_manager import db

analytics_bp = Blueprint("analytics", __name__, url_prefix="/api")


def _extract_filters(req):
    """Extracts common query parameter filters from HTTP request."""
    return {
        "startDate": req.args.get("startDate") or None,
        "endDate": req.args.get("endDate") or None,
        "category": req.args.get("category") or None,
        "city": req.args.get("city") or None,
        "status": req.args.get("status") or "all_active"
    }


@analytics_bp.route("/dashboard", methods=["GET"])
def get_dashboard_summary():
    """
    Returns high-level KPI card values:
    1. Total Revenue
    2. Total Orders
    3. Total Products Sold
    4. Total Customers
    5. Average Order Value (AOV)
    6. Total Product Categories
    """
    try:
        filters = _extract_filters(request)
        kpi_data = AnalyticsService.get_kpi_summary(filters)
        db_status = db.get_status()
        return jsonify({
            "status": "success",
            "data": kpi_data,
            "database": db_status
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@analytics_bp.route("/revenue", methods=["GET"])
def get_revenue():
    """
    Feature 1: Calculate Total Revenue
    Returns total revenue, revenue by product, revenue by category, and revenue by city.
    """
    try:
        filters = _extract_filters(request)
        data = AnalyticsService.get_revenue_analysis(filters)
        return jsonify({"status": "success", "data": data}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@analytics_bp.route("/best-selling-products", methods=["GET"])
def get_best_selling_products():
    """
    Feature 2: Best-Selling Products
    Identifies top 10 best-selling products by quantity and revenue with Chart.js payload.
    """
    try:
        limit = int(request.args.get("limit", 10))
        sort_by = request.args.get("sortBy", "quantity")
        filters = _extract_filters(request)
        data = AnalyticsService.get_best_selling_products(limit=limit, sort_by=sort_by, filters=filters)
        return jsonify({"status": "success", "data": data}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@analytics_bp.route("/monthly-sales", methods=["GET"])
def get_monthly_sales():
    """
    Feature 3: Monthly Sales Analysis
    Calculates monthly revenue, order volume, AOV, identifies peak month, and MoM growth %.
    """
    try:
        filters = _extract_filters(request)
        data = AnalyticsService.get_monthly_sales_analysis(filters)
        return jsonify({"status": "success", "data": data}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@analytics_bp.route("/top-customers", methods=["GET"])
def get_top_customers():
    """
    Feature 4: Top Customers
    Identifies top 10 customers based on spending, total orders, and average order value.
    """
    try:
        limit = int(request.args.get("limit", 10))
        filters = _extract_filters(request)
        data = AnalyticsService.get_top_customers(limit=limit, filters=filters)
        return jsonify({"status": "success", "data": data}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@analytics_bp.route("/category-analysis", methods=["GET"])
def get_category_analysis():
    """
    Feature 5: Product Category Comparison
    Compares revenue across product categories, calculates quantity, and market share %.
    """
    try:
        filters = _extract_filters(request)
        data = AnalyticsService.get_category_comparison(filters)
        return jsonify({"status": "success", "data": data}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@analytics_bp.route("/city-analysis", methods=["GET"])
def get_city_analysis():
    """
    Feature 6: High-Revenue Cities
    Identifies cities generating the highest revenue, orders, and customer counts.
    """
    try:
        limit = int(request.args.get("limit", 12))
        filters = _extract_filters(request)
        data = AnalyticsService.get_city_analysis(limit=limit, filters=filters)
        return jsonify({"status": "success", "data": data}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@analytics_bp.route("/business-insights", methods=["GET"])
def get_business_insights():
    """
    Feature 7: Business Insights Generator
    Generates meaningful, dynamic business insights derived strictly from SQL analysis.
    """
    try:
        filters = _extract_filters(request)
        insights = InsightsService.generate_dynamic_insights(filters)
        return jsonify({"status": "success", "data": insights}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@analytics_bp.route("/filters", methods=["GET"])
def get_filter_options():
    """Returns available categories, cities, date bounds, and statuses for UI filter controls."""
    try:
        options = AnalyticsService.get_filter_options()
        return jsonify({"status": "success", "data": options}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@analytics_bp.route("/db-status", methods=["GET"])
def get_db_status():
    """Returns live connection status of Oracle Database or local fallback engine."""
    return jsonify({"status": "success", "data": db.get_status()}), 200


@analytics_bp.route("/sql-queries", methods=["GET"])
def get_sql_queries():
    """Returns catalog of Oracle SQL analytical queries powering the dashboard for transparency."""
    queries = [
        {
            "id": "kpi_summary",
            "title": "Overall KPI Metrics Summary",
            "features_used": "SUM, COUNT(DISTINCT), ROUND, NULLIF, INNER JOIN, Aggregate Functions",
            "query": """SELECT
    ROUND(SUM((oi.QUANTITY * oi.UNIT_PRICE) - oi.DISCOUNT), 2) AS TOTAL_REVENUE,
    COUNT(DISTINCT o.ORDER_ID)                                 AS TOTAL_ORDERS,
    SUM(oi.QUANTITY)                                           AS TOTAL_PRODUCTS_SOLD,
    COUNT(DISTINCT o.CUSTOMER_ID)                              AS TOTAL_CUSTOMERS,
    ROUND(SUM((oi.QUANTITY * oi.UNIT_PRICE) - oi.DISCOUNT) / NULLIF(COUNT(DISTINCT o.ORDER_ID), 0), 2) AS AVERAGE_ORDER_VALUE,
    COUNT(DISTINCT p.CATEGORY_ID)                              AS TOTAL_PRODUCT_CATEGORIES
FROM ORDERS o
INNER JOIN ORDER_ITEMS oi ON o.ORDER_ID = oi.ORDER_ID
INNER JOIN PRODUCTS p     ON oi.PRODUCT_ID = p.PRODUCT_ID
WHERE o.ORDER_STATUS != 'Cancelled';"""
        },
        {
            "id": "best_selling_products",
            "title": "Top 10 Best-Selling Products",
            "features_used": "CTE (WITH), Window Functions (DENSE_RANK, ROW_NUMBER), GROUP BY, ORDER BY",
            "query": """WITH ProductSales AS (
    SELECT 
        p.PRODUCT_ID,
        p.PRODUCT_NAME,
        c.CATEGORY_NAME,
        p.PRICE,
        p.STOCK_QUANTITY,
        SUM(oi.QUANTITY) AS TOTAL_QUANTITY_SOLD,
        ROUND(SUM((oi.QUANTITY * oi.UNIT_PRICE) - oi.DISCOUNT), 2) AS TOTAL_REVENUE,
        DENSE_RANK() OVER (ORDER BY SUM(oi.QUANTITY) DESC) AS RANK_BY_QTY
    FROM PRODUCTS p
    INNER JOIN CATEGORIES c   ON p.CATEGORY_ID = c.CATEGORY_ID
    INNER JOIN ORDER_ITEMS oi ON p.PRODUCT_ID = oi.PRODUCT_ID
    INNER JOIN ORDERS o       ON oi.ORDER_ID = o.ORDER_ID
    WHERE o.ORDER_STATUS != 'Cancelled'
    GROUP BY p.PRODUCT_ID, p.PRODUCT_NAME, c.CATEGORY_NAME, p.PRICE, p.STOCK_QUANTITY
)
SELECT * FROM ProductSales WHERE RANK_BY_QTY <= 10;"""
        },
        {
            "id": "monthly_sales_growth",
            "title": "Monthly Revenue Trends & MoM Growth Rate",
            "features_used": "CTEs, Date Functions (TO_CHAR, TRUNC), Window Function (LAG() OVER, DENSE_RANK), CASE",
            "query": """WITH MonthlyStats AS (
    SELECT 
        TO_CHAR(o.ORDER_DATE, 'YYYY-MM') AS SALES_MONTH,
        TRUNC(o.ORDER_DATE, 'MM') AS MONTH_DATE,
        COUNT(DISTINCT o.ORDER_ID) AS ORDER_COUNT,
        SUM(oi.QUANTITY) AS UNITS_SOLD,
        ROUND(SUM((oi.QUANTITY * oi.UNIT_PRICE) - oi.DISCOUNT), 2) AS MONTHLY_REVENUE
    FROM ORDERS o
    INNER JOIN ORDER_ITEMS oi ON o.ORDER_ID = oi.ORDER_ID
    WHERE o.ORDER_STATUS != 'Cancelled'
    GROUP BY TO_CHAR(o.ORDER_DATE, 'YYYY-MM'), TRUNC(o.ORDER_DATE, 'MM')
)
SELECT 
    SALES_MONTH,
    ORDER_COUNT,
    UNITS_SOLD,
    MONTHLY_REVENUE,
    LAG(MONTHLY_REVENUE, 1) OVER (ORDER BY MONTH_DATE) AS PREV_MONTH_REV,
    ROUND(((MONTHLY_REVENUE - LAG(MONTHLY_REVENUE, 1) OVER (ORDER BY MONTH_DATE)) / 
           NULLIF(LAG(MONTHLY_REVENUE, 1) OVER (ORDER BY MONTH_DATE), 0)) * 100, 2) AS MOM_GROWTH_PERCENT
FROM MonthlyStats
ORDER BY MONTH_DATE ASC;"""
        },
        {
            "id": "top_customers",
            "title": "Top 10 Customers by Total Spending & AOV",
            "features_used": "Window Function (DENSE_RANK() OVER), CASE Expressions, GROUP BY, Aggregate Functions",
            "query": """WITH CustSpending AS (
    SELECT 
        c.CUSTOMER_ID,
        c.CUSTOMER_NAME,
        c.EMAIL,
        c.CITY,
        c.STATE,
        COUNT(DISTINCT o.ORDER_ID) AS TOTAL_ORDERS,
        SUM(oi.QUANTITY) AS TOTAL_ITEMS_BOUGHT,
        ROUND(SUM((oi.QUANTITY * oi.UNIT_PRICE) - oi.DISCOUNT), 2) AS TOTAL_SPENDING,
        ROUND(SUM((oi.QUANTITY * oi.UNIT_PRICE) - oi.DISCOUNT) / NULLIF(COUNT(DISTINCT o.ORDER_ID), 0), 2) AS AVERAGE_ORDER_VALUE,
        DENSE_RANK() OVER (ORDER BY SUM((oi.QUANTITY * oi.UNIT_PRICE) - oi.DISCOUNT) DESC) AS SPENDING_RANK
    FROM CUSTOMERS c
    INNER JOIN ORDERS o       ON c.CUSTOMER_ID = o.CUSTOMER_ID
    INNER JOIN ORDER_ITEMS oi ON o.ORDER_ID = oi.ORDER_ID
    WHERE o.ORDER_STATUS != 'Cancelled'
    GROUP BY c.CUSTOMER_ID, c.CUSTOMER_NAME, c.EMAIL, c.CITY, c.STATE
)
SELECT * FROM CustSpending WHERE SPENDING_RANK <= 10;"""
        },
        {
            "id": "category_market_share",
            "title": "Product Category Market Share Analysis",
            "features_used": "Window Function (SUM() OVER ()), DENSE_RANK(), Subqueries, Multi-table JOINs",
            "query": """WITH CatSales AS (
    SELECT 
        c.CATEGORY_NAME,
        COUNT(DISTINCT p.PRODUCT_ID) AS DISTINCT_PRODUCTS,
        COUNT(DISTINCT o.ORDER_ID) AS TOTAL_ORDERS,
        SUM(oi.QUANTITY) AS TOTAL_QUANTITY_SOLD,
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
    ROUND((TOTAL_REVENUE / NULLIF(SUM(TOTAL_REVENUE) OVER (), 0)) * 100, 2) AS REVENUE_SHARE_PERCENT
FROM CatSales
ORDER BY TOTAL_REVENUE DESC;"""
        },
        {
            "id": "high_revenue_cities",
            "title": "High-Revenue Cities Ranking",
            "features_used": "Window Function (DENSE_RANK() OVER), HAVING, GROUP BY, Aggregate Functions",
            "query": """WITH CitySales AS (
    SELECT 
        cust.CITY,
        cust.STATE,
        COUNT(DISTINCT cust.CUSTOMER_ID) AS CUSTOMER_COUNT,
        COUNT(DISTINCT o.ORDER_ID) AS TOTAL_ORDERS,
        SUM(oi.QUANTITY) AS TOTAL_UNITS_SOLD,
        ROUND(SUM((oi.QUANTITY * oi.UNIT_PRICE) - oi.DISCOUNT), 2) AS TOTAL_REVENUE,
        ROUND(SUM((oi.QUANTITY * oi.UNIT_PRICE) - oi.DISCOUNT) / NULLIF(COUNT(DISTINCT o.ORDER_ID), 0), 2) AS AOV_PER_CITY
    FROM CUSTOMERS cust
    INNER JOIN ORDERS o       ON cust.CUSTOMER_ID = o.CUSTOMER_ID
    INNER JOIN ORDER_ITEMS oi ON o.ORDER_ID = oi.ORDER_ID
    WHERE o.ORDER_STATUS != 'Cancelled'
    GROUP BY cust.CITY, cust.STATE
    HAVING COUNT(DISTINCT o.ORDER_ID) >= 1
)
SELECT 
    DENSE_RANK() OVER (ORDER BY TOTAL_REVENUE DESC) AS CITY_RANK,
    CITY,
    STATE,
    CUSTOMER_COUNT,
    TOTAL_ORDERS,
    TOTAL_UNITS_SOLD,
    TOTAL_REVENUE,
    AOV_PER_CITY
FROM CitySales
ORDER BY CITY_RANK ASC;"""
        }
    ]
    return jsonify({"status": "success", "queries": queries}), 200
