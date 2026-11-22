"""
Online Retail Sales Analytics - Analytics Service
Implements core business intelligence and analytical SQL executions using Oracle SQL.
Processes and aggregates retail data using Pandas and SQL Window Functions.
"""

import pandas as pd
from database.db_manager import db


class AnalyticsService:

    @staticmethod
    def _build_filter_clause(start_date=None, end_date=None, category=None, city=None, status="Completed"):
        """
        Dynamically constructs SQL WHERE clauses and parameters based on user filter criteria.
        Ensures cancelled orders are excluded unless explicitly requested.
        """
        clauses = []
        params = {}

        if status:
            if status.lower() == "all_active":
                clauses.append("o.ORDER_STATUS != 'Cancelled'")
            elif status.lower() != "all":
                clauses.append("o.ORDER_STATUS = :status")
                params["status"] = status
        else:
            clauses.append("o.ORDER_STATUS != 'Cancelled'")

        if start_date:
            clauses.append("o.ORDER_DATE >= :start_date")
            params["start_date"] = start_date

        if end_date:
            clauses.append("o.ORDER_DATE <= :end_date")
            params["end_date"] = end_date

        if category and category.lower() != "all":
            clauses.append("c.CATEGORY_NAME = :category")
            params["category"] = category

        if city and city.lower() != "all":
            clauses.append("cust.CITY = :city")
            params["city"] = city

        where_sql = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        return where_sql, params

    @classmethod
    def get_kpi_summary(cls, filters=None):
        """
        Calculates the 6 core KPI metrics dynamically from the database:
        1. Total Revenue
        2. Total Orders
        3. Total Products Sold
        4. Total Customers
        5. Average Order Value (AOV)
        6. Total Product Categories
        """
        if filters is None:
            filters = {}

        where_sql, params = cls._build_filter_clause(
            start_date=filters.get("startDate"),
            end_date=filters.get("endDate"),
            category=filters.get("category"),
            city=filters.get("city"),
            status=filters.get("status", "all_active")
        )

        sql = f"""
        SELECT 
            ROUND(SUM((oi.QUANTITY * oi.UNIT_PRICE) - oi.DISCOUNT), 2) AS TOTAL_REVENUE,
            COUNT(DISTINCT o.ORDER_ID)                                 AS TOTAL_ORDERS,
            SUM(oi.QUANTITY)                                           AS TOTAL_PRODUCTS_SOLD,
            COUNT(DISTINCT o.CUSTOMER_ID)                              AS TOTAL_CUSTOMERS,
            ROUND(
                SUM((oi.QUANTITY * oi.UNIT_PRICE) - oi.DISCOUNT) / 
                NULLIF(COUNT(DISTINCT o.ORDER_ID), 0), 2
            )                                                          AS AVERAGE_ORDER_VALUE,
            COUNT(DISTINCT p.CATEGORY_ID)                              AS TOTAL_PRODUCT_CATEGORIES
        FROM ORDERS o
        INNER JOIN ORDER_ITEMS oi ON o.ORDER_ID = oi.ORDER_ID
        INNER JOIN PRODUCTS p     ON oi.PRODUCT_ID = p.PRODUCT_ID
        INNER JOIN CATEGORIES c   ON p.CATEGORY_ID = c.CATEGORY_ID
        INNER JOIN CUSTOMERS cust ON o.CUSTOMER_ID = cust.CUSTOMER_ID
        {where_sql}
        """

        df = db.execute_query(sql, params)
        if df.empty or pd.isna(df["TOTAL_REVENUE"].iloc[0]):
            return {
                "total_revenue": 0.0,
                "total_orders": 0,
                "total_products_sold": 0,
                "total_customers": 0,
                "average_order_value": 0.0,
                "total_categories": 0
            }

        row = df.iloc[0]
        return {
            "total_revenue": float(row.get("TOTAL_REVENUE", 0.0) or 0.0),
            "total_orders": int(row.get("TOTAL_ORDERS", 0) or 0),
            "total_products_sold": int(row.get("TOTAL_PRODUCTS_SOLD", 0) or 0),
            "total_customers": int(row.get("TOTAL_CUSTOMERS", 0) or 0),
            "average_order_value": float(row.get("AVERAGE_ORDER_VALUE", 0.0) or 0.0),
            "total_categories": int(row.get("TOTAL_PRODUCT_CATEGORIES", 0) or 0)
        }

    @classmethod
    def get_revenue_analysis(cls, filters=None):
        """
        Feature 1: Comprehensive Revenue Breakdown
        - Total revenue
        - Revenue by product
        - Revenue by category
        - Revenue by city
        """
        if filters is None:
            filters = {}

        where_sql, params = cls._build_filter_clause(
            start_date=filters.get("startDate"),
            end_date=filters.get("endDate"),
            category=filters.get("category"),
            city=filters.get("city"),
            status=filters.get("status", "all_active")
        )

        # 1. Total Overall Revenue
        kpi = cls.get_kpi_summary(filters)

        # 2. Revenue by Product (Top 15)
        sql_product = f"""
        SELECT 
            p.PRODUCT_NAME,
            c.CATEGORY_NAME,
            SUM(oi.QUANTITY)                                           AS QUANTITY_SOLD,
            ROUND(SUM((oi.QUANTITY * oi.UNIT_PRICE) - oi.DISCOUNT), 2) AS REVENUE
        FROM PRODUCTS p
        INNER JOIN CATEGORIES c   ON p.CATEGORY_ID = c.CATEGORY_ID
        INNER JOIN ORDER_ITEMS oi ON p.PRODUCT_ID = oi.PRODUCT_ID
        INNER JOIN ORDERS o       ON oi.ORDER_ID = o.ORDER_ID
        INNER JOIN CUSTOMERS cust ON o.CUSTOMER_ID = cust.CUSTOMER_ID
        {where_sql}
        GROUP BY p.PRODUCT_ID, p.PRODUCT_NAME, c.CATEGORY_NAME
        ORDER BY REVENUE DESC
        """
        df_prod = db.execute_query(sql_product, params)
        revenue_by_product = df_prod.head(15).to_dict(orient="records")

        # 3. Revenue by Category
        sql_cat = f"""
        SELECT 
            c.CATEGORY_NAME,
            COUNT(DISTINCT o.ORDER_ID)                                 AS TOTAL_ORDERS,
            SUM(oi.QUANTITY)                                           AS QUANTITY_SOLD,
            ROUND(SUM((oi.QUANTITY * oi.UNIT_PRICE) - oi.DISCOUNT), 2) AS REVENUE
        FROM CATEGORIES c
        INNER JOIN PRODUCTS p     ON c.CATEGORY_ID = p.CATEGORY_ID
        INNER JOIN ORDER_ITEMS oi ON p.PRODUCT_ID = oi.PRODUCT_ID
        INNER JOIN ORDERS o       ON oi.ORDER_ID = o.ORDER_ID
        INNER JOIN CUSTOMERS cust ON o.CUSTOMER_ID = cust.CUSTOMER_ID
        {where_sql}
        GROUP BY c.CATEGORY_ID, c.CATEGORY_NAME
        ORDER BY REVENUE DESC
        """
        df_cat = db.execute_query(sql_cat, params)
        revenue_by_category = df_cat.to_dict(orient="records")

        # 4. Revenue by City (Top 15)
        sql_city = f"""
        SELECT 
            cust.CITY,
            cust.STATE,
            COUNT(DISTINCT o.ORDER_ID)                                 AS TOTAL_ORDERS,
            SUM(oi.QUANTITY)                                           AS QUANTITY_SOLD,
            ROUND(SUM((oi.QUANTITY * oi.UNIT_PRICE) - oi.DISCOUNT), 2) AS REVENUE
        FROM CUSTOMERS cust
        INNER JOIN ORDERS o       ON cust.CUSTOMER_ID = o.CUSTOMER_ID
        INNER JOIN ORDER_ITEMS oi ON o.ORDER_ID = oi.ORDER_ID
        INNER JOIN PRODUCTS p     ON oi.PRODUCT_ID = p.PRODUCT_ID
        INNER JOIN CATEGORIES c   ON p.CATEGORY_ID = c.CATEGORY_ID
        {where_sql}
        GROUP BY cust.CITY, cust.STATE
        ORDER BY REVENUE DESC
        """
        df_city = db.execute_query(sql_city, params)
        revenue_by_city = df_city.head(15).to_dict(orient="records")

        return {
            "total_revenue": kpi["total_revenue"],
            "revenue_by_product": revenue_by_product,
            "revenue_by_category": revenue_by_category,
            "revenue_by_city": revenue_by_city
        }

    @classmethod
    def get_best_selling_products(cls, limit=10, sort_by="quantity", filters=None):
        """
        Feature 2: Best-Selling Products
        Identifies top products with name, total quantity sold, total revenue, and rank.
        Uses Oracle Window Function DENSE_RANK() OVER (...).
        """
        if filters is None:
            filters = {}

        where_sql, params = cls._build_filter_clause(
            start_date=filters.get("startDate"),
            end_date=filters.get("endDate"),
            category=filters.get("category"),
            city=filters.get("city"),
            status=filters.get("status", "all_active")
        )

        order_clause = "TOTAL_QUANTITY_SOLD DESC, TOTAL_REVENUE DESC" if sort_by == "quantity" else "TOTAL_REVENUE DESC, TOTAL_QUANTITY_SOLD DESC"

        sql = f"""
        WITH ProductSales AS (
            SELECT 
                p.PRODUCT_ID,
                p.PRODUCT_NAME,
                c.CATEGORY_NAME,
                p.PRICE                                                    AS UNIT_PRICE,
                p.STOCK_QUANTITY,
                SUM(oi.QUANTITY)                                           AS TOTAL_QUANTITY_SOLD,
                ROUND(SUM((oi.QUANTITY * oi.UNIT_PRICE) - oi.DISCOUNT), 2) AS TOTAL_REVENUE,
                DENSE_RANK() OVER (ORDER BY SUM(oi.QUANTITY) DESC)         AS RANK_BY_QTY,
                DENSE_RANK() OVER (
                    ORDER BY SUM((oi.QUANTITY * oi.UNIT_PRICE) - oi.DISCOUNT) DESC
                )                                                          AS RANK_BY_REV
            FROM PRODUCTS p
            INNER JOIN CATEGORIES c   ON p.CATEGORY_ID = c.CATEGORY_ID
            INNER JOIN ORDER_ITEMS oi ON p.PRODUCT_ID = oi.PRODUCT_ID
            INNER JOIN ORDERS o       ON oi.ORDER_ID = o.ORDER_ID
            INNER JOIN CUSTOMERS cust ON o.CUSTOMER_ID = cust.CUSTOMER_ID
            {where_sql}
            GROUP BY p.PRODUCT_ID, p.PRODUCT_NAME, c.CATEGORY_NAME, p.PRICE, p.STOCK_QUANTITY
        )
        SELECT 
            ROW_NUMBER() OVER (ORDER BY {order_clause}) AS RANK,
            PRODUCT_NAME,
            CATEGORY_NAME,
            UNIT_PRICE,
            TOTAL_QUANTITY_SOLD,
            TOTAL_REVENUE,
            STOCK_QUANTITY,
            RANK_BY_QTY,
            RANK_BY_REV
        FROM ProductSales
        ORDER BY {order_clause}
        """

        df = db.execute_query(sql, params)
        top_df = df.head(limit)

        # Prepare payload for frontend and Chart.js
        chart_labels = top_df["PRODUCT_NAME"].tolist() if not top_df.empty else []
        chart_quantities = top_df["TOTAL_QUANTITY_SOLD"].tolist() if not top_df.empty else []
        chart_revenues = top_df["TOTAL_REVENUE"].tolist() if not top_df.empty else []

        return {
            "products": top_df.to_dict(orient="records"),
            "chart_data": {
                "labels": chart_labels,
                "quantities": chart_quantities,
                "revenues": chart_revenues
            }
        }

    @classmethod
    def get_monthly_sales_analysis(cls, filters=None):
        """
        Feature 3: Monthly Sales Analysis & MoM Growth
        Calculates monthly revenue, orders, AOV, identifies peak month, and calculates MoM % growth.
        Uses Oracle Window Function LAG() OVER (...) and TRUNC().
        """
        if filters is None:
            filters = {}

        where_sql, params = cls._build_filter_clause(
            start_date=filters.get("startDate"),
            end_date=filters.get("endDate"),
            category=filters.get("category"),
            city=filters.get("city"),
            status=filters.get("status", "all_active")
        )

        sql = f"""
        WITH MonthlyStats AS (
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
            INNER JOIN PRODUCTS p     ON oi.PRODUCT_ID = p.PRODUCT_ID
            INNER JOIN CATEGORIES c   ON p.CATEGORY_ID = c.CATEGORY_ID
            INNER JOIN CUSTOMERS cust ON o.CUSTOMER_ID = cust.CUSTOMER_ID
            {where_sql}
            GROUP BY TO_CHAR(o.ORDER_DATE, 'YYYY-MM'), TRUNC(o.ORDER_DATE, 'MM')
        ),
        GrowthStats AS (
            SELECT 
                SALES_MONTH,
                MONTH_DATE,
                ORDER_COUNT,
                UNITS_SOLD,
                MONTHLY_REVENUE,
                MONTHLY_AOV,
                LAG(MONTHLY_REVENUE, 1) OVER (ORDER BY MONTH_DATE) AS PREV_MONTH_REV,
                DENSE_RANK() OVER (ORDER BY MONTHLY_REVENUE DESC)  AS REV_RANK
            FROM MonthlyStats
        )
        SELECT 
            SALES_MONTH,
            ORDER_COUNT,
            UNITS_SOLD,
            MONTHLY_REVENUE,
            MONTHLY_AOV,
            NVL(PREV_MONTH_REV, 0) AS PREVIOUS_MONTH_REVENUE,
            CASE 
                WHEN PREV_MONTH_REV IS NULL THEN 0.00
                WHEN PREV_MONTH_REV = 0 THEN 0.00
                ELSE ROUND(((MONTHLY_REVENUE - PREV_MONTH_REV) / PREV_MONTH_REV) * 100, 2)
            END AS MOM_GROWTH_PERCENT,
            CASE 
                WHEN REV_RANK = 1 THEN 'Peak Month'
                ELSE 'Normal'
            END AS STATUS_FLAG
        FROM GrowthStats
        ORDER BY MONTH_DATE ASC
        """

        df = db.execute_query(sql, params)
        months_list = df.to_dict(orient="records") if not df.empty else []

        peak_month = None
        if not df.empty:
            peak_row = df.loc[df["MONTHLY_REVENUE"].idxmax()]
            peak_month = {
                "month": str(peak_row["SALES_MONTH"]),
                "revenue": float(peak_row["MONTHLY_REVENUE"]),
                "orders": int(peak_row["ORDER_COUNT"])
            }

        chart_labels = df["SALES_MONTH"].tolist() if not df.empty else []
        chart_revenues = df["MONTHLY_REVENUE"].tolist() if not df.empty else []
        chart_orders = df["ORDER_COUNT"].tolist() if not df.empty else []
        chart_growth = df["MOM_GROWTH_PERCENT"].tolist() if not df.empty else []

        return {
            "monthly_data": months_list,
            "peak_month": peak_month,
            "chart_data": {
                "labels": chart_labels,
                "revenues": chart_revenues,
                "orders": chart_orders,
                "growth_percentages": chart_growth
            }
        }

    @classmethod
    def get_top_customers(cls, limit=10, filters=None):
        """
        Feature 4: Top Customers
        Identifies top spending customers with orders, total spend, AOV, and customer rank.
        Uses Oracle Window Function DENSE_RANK() OVER (...).
        """
        if filters is None:
            filters = {}

        where_sql, params = cls._build_filter_clause(
            start_date=filters.get("startDate"),
            end_date=filters.get("endDate"),
            category=filters.get("category"),
            city=filters.get("city"),
            status=filters.get("status", "all_active")
        )

        sql = f"""
        WITH CustSpending AS (
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
                )                                                          AS SPENDING_RANK
            FROM CUSTOMERS c
            INNER JOIN ORDERS o       ON c.CUSTOMER_ID = o.CUSTOMER_ID
            INNER JOIN ORDER_ITEMS oi ON o.ORDER_ID = oi.ORDER_ID
            INNER JOIN PRODUCTS p     ON oi.PRODUCT_ID = p.PRODUCT_ID
            INNER JOIN CATEGORIES cat ON p.CATEGORY_ID = cat.CATEGORY_ID
            {where_sql}
            GROUP BY c.CUSTOMER_ID, c.CUSTOMER_NAME, c.EMAIL, c.CITY, c.STATE
        )
        SELECT 
            SPENDING_RANK AS RANK,
            CUSTOMER_NAME,
            EMAIL,
            CITY,
            STATE,
            TOTAL_ORDERS,
            TOTAL_ITEMS_BOUGHT,
            TOTAL_SPENDING,
            AVERAGE_ORDER_VALUE,
            CASE 
                WHEN SPENDING_RANK = 1 THEN 'Platinum Elite'
                WHEN SPENDING_RANK <= 3 THEN 'Gold VIP'
                WHEN SPENDING_RANK <= 10 THEN 'Silver Premier'
                ELSE 'Standard'
            END AS VIP_TIER
        FROM CustSpending
        ORDER BY TOTAL_SPENDING DESC
        """

        df = db.execute_query(sql, params)
        top_df = df.head(limit)

        return {
            "customers": top_df.to_dict(orient="records"),
            "chart_data": {
                "labels": top_df["CUSTOMER_NAME"].tolist() if not top_df.empty else [],
                "spending": top_df["TOTAL_SPENDING"].tolist() if not top_df.empty else []
            }
        }

    @classmethod
    def get_category_comparison(cls, filters=None):
        """
        Feature 5: Product Category Comparison
        Compares revenue, quantities, and calculates market share % using Oracle Window Function SUM() OVER ().
        """
        if filters is None:
            filters = {}

        where_sql, params = cls._build_filter_clause(
            start_date=filters.get("startDate"),
            end_date=filters.get("endDate"),
            category=filters.get("category"),
            city=filters.get("city"),
            status=filters.get("status", "all_active")
        )

        sql = f"""
        WITH CatSales AS (
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
            INNER JOIN CUSTOMERS cust ON o.CUSTOMER_ID = cust.CUSTOMER_ID
            {where_sql}
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
            ) AS REVENUE_SHARE_PERCENT,
            DENSE_RANK() OVER (ORDER BY TOTAL_REVENUE DESC) AS CATEGORY_RANK
        FROM CatSales
        ORDER BY TOTAL_REVENUE DESC
        """

        df = db.execute_query(sql, params)
        categories_list = df.to_dict(orient="records") if not df.empty else []

        top_category = categories_list[0] if categories_list else None

        chart_labels = df["CATEGORY_NAME"].tolist() if not df.empty else []
        chart_revenues = df["TOTAL_REVENUE"].tolist() if not df.empty else []
        chart_quantities = df["TOTAL_QUANTITY_SOLD"].tolist() if not df.empty else []
        chart_shares = df["REVENUE_SHARE_PERCENT"].tolist() if not df.empty else []

        return {
            "categories": categories_list,
            "top_category": top_category,
            "chart_data": {
                "labels": chart_labels,
                "revenues": chart_revenues,
                "quantities": chart_quantities,
                "shares": chart_shares
            }
        }

    @classmethod
    def get_city_analysis(cls, limit=12, filters=None):
        """
        Feature 6: High-Revenue Cities Analysis
        Ranks cities based on revenue using Oracle Window Function DENSE_RANK() OVER (...).
        """
        if filters is None:
            filters = {}

        where_sql, params = cls._build_filter_clause(
            start_date=filters.get("startDate"),
            end_date=filters.get("endDate"),
            category=filters.get("category"),
            city=filters.get("city"),
            status=filters.get("status", "all_active")
        )

        sql = f"""
        WITH CitySales AS (
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
            INNER JOIN PRODUCTS p     ON oi.PRODUCT_ID = p.PRODUCT_ID
            INNER JOIN CATEGORIES c   ON p.CATEGORY_ID = c.CATEGORY_ID
            {where_sql}
            GROUP BY cust.CITY, cust.STATE
        )
        SELECT 
            DENSE_RANK() OVER (ORDER BY TOTAL_REVENUE DESC) AS RANK,
            CITY,
            STATE,
            CUSTOMER_COUNT,
            TOTAL_ORDERS,
            TOTAL_UNITS_SOLD,
            TOTAL_REVENUE,
            AOV_PER_CITY
        FROM CitySales
        ORDER BY TOTAL_REVENUE DESC
        """

        df = db.execute_query(sql, params)
        top_cities = df.head(limit)

        chart_labels = [f"{row['CITY']}, {row['STATE']}" for _, row in top_cities.iterrows()] if not top_cities.empty else []
        chart_revenues = top_cities["TOTAL_REVENUE"].tolist() if not top_cities.empty else []
        chart_orders = top_cities["TOTAL_ORDERS"].tolist() if not top_cities.empty else []

        return {
            "cities": top_cities.to_dict(orient="records"),
            "chart_data": {
                "labels": chart_labels,
                "revenues": chart_revenues,
                "orders": chart_orders
            }
        }

    @classmethod
    def get_filter_options(cls):
        """Fetches distinct categories, cities, date boundaries, and order statuses for UI filters."""
        sql_cats = "SELECT DISTINCT CATEGORY_NAME FROM CATEGORIES ORDER BY CATEGORY_NAME ASC"
        sql_cities = "SELECT DISTINCT CITY, STATE FROM CUSTOMERS ORDER BY CITY ASC"
        sql_dates = "SELECT MIN(ORDER_DATE) AS MIN_DATE, MAX(ORDER_DATE) AS MAX_DATE FROM ORDERS"
        sql_statuses = "SELECT DISTINCT ORDER_STATUS FROM ORDERS ORDER BY ORDER_STATUS ASC"

        df_cats = db.execute_query(sql_cats)
        df_cities = db.execute_query(sql_cities)
        df_dates = db.execute_query(sql_dates)
        df_statuses = db.execute_query(sql_statuses)

        min_d = str(df_dates["MIN_DATE"].iloc[0])[:10] if not df_dates.empty else "2023-01-01"
        max_d = str(df_dates["MAX_DATE"].iloc[0])[:10] if not df_dates.empty else "2024-12-31"

        return {
            "categories": df_cats["CATEGORY_NAME"].tolist() if not df_cats.empty else [],
            "cities": [f"{r['CITY']}" for _, r in df_cities.iterrows()] if not df_cities.empty else [],
            "date_range": {"min_date": min_d, "max_date": max_d},
            "statuses": df_statuses["ORDER_STATUS"].tolist() if not df_statuses.empty else ["Completed", "Shipped", "Processing", "Cancelled"]
        }
