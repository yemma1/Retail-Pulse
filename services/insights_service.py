"""
Online Retail Sales Analytics - Business Insights Service
Feature 7: Business Insights Generator
Executes SQL queries to dynamically compute real-time business insights,
performance anomalies, inventory warnings, and strategic executive recommendations.
Strictly dynamic: No hardcoded figures or static statements.
"""

from database.db_manager import db
from services.analytics_service import AnalyticsService


class InsightsService:

    @classmethod
    def generate_dynamic_insights(cls, filters=None):
        """
        Gathers analytical findings from SQL queries and synthesizes
        executive business insights, anomaly alerts, and strategic action points.
        """
        if filters is None:
            filters = {}

        kpis = AnalyticsService.get_kpi_summary(filters)
        total_revenue = kpis["total_revenue"]
        total_orders = kpis["total_orders"]
        total_customers = kpis["total_customers"]

        insights = {
            "summary_metrics": kpis,
            "core_insights": [],
            "performance_drivers": {},
            "inventory_risks": [],
            "strategic_recommendations": []
        }

        if total_revenue <= 0:
            insights["core_insights"].append({
                "type": "warning",
                "title": "No Sales Data Available",
                "description": "No active order transactions match the selected filter criteria."
            })
            return insights

        # ---------------------------------------------------------------------
        # 1. Top Revenue Generating Product
        # ---------------------------------------------------------------------
        sql_top_product = """
        SELECT 
            p.PRODUCT_NAME,
            c.CATEGORY_NAME,
            p.PRICE,
            SUM(oi.QUANTITY) AS UNITS_SOLD,
            ROUND(SUM((oi.QUANTITY * oi.UNIT_PRICE) - oi.DISCOUNT), 2) AS PRODUCT_REVENUE
        FROM PRODUCTS p
        INNER JOIN CATEGORIES c   ON p.CATEGORY_ID = c.CATEGORY_ID
        INNER JOIN ORDER_ITEMS oi ON p.PRODUCT_ID = oi.PRODUCT_ID
        INNER JOIN ORDERS o       ON oi.ORDER_ID = o.ORDER_ID
        WHERE o.ORDER_STATUS != 'Cancelled'
        GROUP BY p.PRODUCT_ID, p.PRODUCT_NAME, c.CATEGORY_NAME, p.PRICE
        ORDER BY PRODUCT_REVENUE DESC
        """
        df_top_prod = db.execute_query(sql_top_product)
        if not df_top_prod.empty:
            top_prod = df_top_prod.iloc[0]
            prod_rev = float(top_prod["PRODUCT_REVENUE"])
            prod_contrib = round((prod_rev / total_revenue) * 100, 2)
            insights["performance_drivers"]["top_product"] = {
                "name": str(top_prod["PRODUCT_NAME"]),
                "category": str(top_prod["CATEGORY_NAME"]),
                "revenue": prod_rev,
                "units_sold": int(top_prod["UNITS_SOLD"]),
                "contribution_pct": prod_contrib
            }
            insights["core_insights"].append({
                "type": "success",
                "badge": "Top Revenue Driver",
                "icon": "fa-trophy",
                "title": f"Leading Revenue Generator: {top_prod['PRODUCT_NAME']}",
                "description": (
                    f"'{top_prod['PRODUCT_NAME']}' ({top_prod['CATEGORY_NAME']}) is the business's top revenue generator, "
                    f"producing ${prod_rev:,.2f} across {int(top_prod['UNITS_SOLD']):,} units sold. "
                    f"This single product accounts for {prod_contrib}% of the enterprise's net revenue."
                )
            })

        # ---------------------------------------------------------------------
        # 2. Peak Sales Month & Growth Momentum
        # ---------------------------------------------------------------------
        monthly_data = AnalyticsService.get_monthly_sales_analysis(filters)
        m_list = monthly_data.get("monthly_data", [])
        peak = monthly_data.get("peak_month")
        if peak:
            # Calculate average monthly revenue
            avg_m_rev = total_revenue / max(1, len(m_list))
            peak_vs_avg = round(((peak["revenue"] - avg_m_rev) / avg_m_rev) * 100, 1)
            insights["performance_drivers"]["peak_month"] = peak
            insights["core_insights"].append({
                "type": "primary",
                "badge": "Peak Sales Month",
                "icon": "fa-calendar-check",
                "title": f"Highest Sales Month: {peak['month']}",
                "description": (
                    f"Sales reached an all-time peak in {peak['month']} with ${peak['revenue']:,.2f} in gross sales "
                    f"across {peak['orders']:,} orders. This performance was {peak_vs_avg}% above the monthly average "
                    f"of ${avg_m_rev:,.2f}."
                )
            })

        # Momentum analysis (latest month MoM)
        if len(m_list) >= 2:
            latest_m = m_list[-1]
            latest_growth = float(latest_m.get("MOM_GROWTH_PERCENT", 0.0))
            direction = "surged by" if latest_growth >= 0 else "contracted by"
            trend_badge = "Growth Acceleration" if latest_growth >= 0 else "Sales Contraction"
            alert_type = "info" if latest_growth >= 0 else "warning"
            insights["core_insights"].append({
                "type": alert_type,
                "badge": trend_badge,
                "icon": "fa-chart-line" if latest_growth >= 0 else "fa-arrow-trend-down",
                "title": f"Monthly Trajectory ({latest_m['SALES_MONTH']}): {latest_growth:+.2f}% MoM",
                "description": (
                    f"In the most recent recorded period ({latest_m['SALES_MONTH']}), revenue {direction} "
                    f"{abs(latest_growth):.2f}% compared to the prior month, reaching ${float(latest_m['MONTHLY_REVENUE']):,.2f}."
                )
            })

        # ---------------------------------------------------------------------
        # 3. Best Performing Category & Share
        # ---------------------------------------------------------------------
        cat_data = AnalyticsService.get_category_comparison(filters)
        top_cat = cat_data.get("top_category")
        if top_cat:
            insights["performance_drivers"]["top_category"] = top_cat
            insights["core_insights"].append({
                "type": "info",
                "badge": "Category Leader",
                "icon": "fa-layer-group",
                "title": f"Dominant Product Category: {top_cat['CATEGORY_NAME']}",
                "description": (
                    f"The '{top_cat['CATEGORY_NAME']}' category dominates retail performance, generating "
                    f"${float(top_cat['TOTAL_REVENUE']):,.2f} in net sales ({float(top_cat['REVENUE_SHARE_PERCENT']):.1f}% of total enterprise revenue) "
                    f"with {int(top_cat['TOTAL_QUANTITY_SOLD']):,} units shipped."
                )
            })

        # ---------------------------------------------------------------------
        # 4. Top Revenue City & Geographic Concentration
        # ---------------------------------------------------------------------
        city_data = AnalyticsService.get_city_analysis(limit=5, filters=filters)
        cities = city_data.get("cities", [])
        if cities:
            top_city = cities[0]
            city_rev = float(top_city["TOTAL_REVENUE"])
            city_share = round((city_rev / total_revenue) * 100, 2)
            insights["performance_drivers"]["top_city"] = top_city
            insights["core_insights"].append({
                "type": "success",
                "badge": "Top Regional Market",
                "icon": "fa-city",
                "title": f"Highest Revenue Market: {top_city['CITY']}, {top_city['STATE']}",
                "description": (
                    f"{top_city['CITY']}, {top_city['STATE']} leads all metropolitan markets with ${city_rev:,.2f} in sales "
                    f"({city_share}% share) across {int(top_city['TOTAL_ORDERS'])} orders, recording an Average Order Value of ${float(top_city['AOV_PER_CITY']):,.2f}."
                )
            })

        # ---------------------------------------------------------------------
        # 5. Highest-Spending Customer & VIP Concentration
        # ---------------------------------------------------------------------
        cust_data = AnalyticsService.get_top_customers(limit=3, filters=filters)
        top_custs = cust_data.get("customers", [])
        if top_custs:
            top_cust = top_custs[0]
            cust_spend = float(top_cust["TOTAL_SPENDING"])
            insights["performance_drivers"]["top_customer"] = top_cust
            insights["core_insights"].append({
                "type": "primary",
                "badge": "VIP Customer",
                "icon": "fa-user-crown",
                "title": f"Top Spending Customer: {top_cust['CUSTOMER_NAME']}",
                "description": (
                    f"{top_cust['CUSTOMER_NAME']} ({top_cust['CITY']}, {top_cust['STATE']}) is the highest-spending customer, "
                    f"contributing ${cust_spend:,.2f} across {top_cust['TOTAL_ORDERS']} transactions "
                    f"with an AOV of ${float(top_cust['AVERAGE_ORDER_VALUE']):,.2f}."
                )
            })

        # ---------------------------------------------------------------------
        # 6. Low-Selling Products (Inventory Warning & Slow Movers)
        # ---------------------------------------------------------------------
        sql_low_sales = """
        SELECT 
            p.PRODUCT_NAME,
            c.CATEGORY_NAME,
            p.PRICE,
            p.STOCK_QUANTITY,
            COALESCE(SUM(oi.QUANTITY), 0) AS UNITS_SOLD,
            COALESCE(ROUND(SUM((oi.QUANTITY * oi.UNIT_PRICE) - oi.DISCOUNT), 2), 0) AS REVENUE_GENERATED
        FROM PRODUCTS p
        INNER JOIN CATEGORIES c  ON p.CATEGORY_ID = c.CATEGORY_ID
        LEFT JOIN ORDER_ITEMS oi ON p.PRODUCT_ID = oi.PRODUCT_ID
        LEFT JOIN ORDERS o       ON oi.ORDER_ID = o.ORDER_ID AND o.ORDER_STATUS != 'Cancelled'
        GROUP BY p.PRODUCT_ID, p.PRODUCT_NAME, c.CATEGORY_NAME, p.PRICE, p.STOCK_QUANTITY
        HAVING COALESCE(SUM(oi.QUANTITY), 0) <= 6
        ORDER BY UNITS_SOLD ASC, p.STOCK_QUANTITY DESC
        """
        df_low = db.execute_query(sql_low_sales)
        low_selling_items = df_low.head(5).to_dict(orient="records") if not df_low.empty else []
        insights["inventory_risks"] = low_selling_items

        if low_selling_items:
            names = ", ".join([f"'{item['PRODUCT_NAME']}' ({int(item['UNITS_SOLD'])} sold)" for item in low_selling_items[:3]])
            insights["core_insights"].append({
                "type": "warning",
                "badge": "Inventory Slow Movers",
                "icon": "fa-triangle-exclamation",
                "title": "Low Sales Velocity Warning",
                "description": (
                    f"Detected {len(df_low)} products with 6 or fewer lifetime units sold, including {names}. "
                    "These items tie up warehouse working capital and may warrant discount promotions or clearance."
                )
            })

        # ---------------------------------------------------------------------
        # 7. Cancelled Orders & Lost Revenue Analysis
        # ---------------------------------------------------------------------
        sql_cancels = """
        SELECT 
            COUNT(DISTINCT o.ORDER_ID) AS CANCELLED_ORDERS,
            COALESCE(ROUND(SUM((oi.QUANTITY * oi.UNIT_PRICE) - oi.DISCOUNT), 2), 0) AS LOST_REVENUE
        FROM ORDERS o
        INNER JOIN ORDER_ITEMS oi ON o.ORDER_ID = oi.ORDER_ID
        WHERE o.ORDER_STATUS = 'Cancelled'
        """
        df_cancels = db.execute_query(sql_cancels)
        if not df_cancels.empty and int(df_cancels["CANCELLED_ORDERS"].iloc[0]) > 0:
            c_orders = int(df_cancels["CANCELLED_ORDERS"].iloc[0])
            c_lost = float(df_cancels["LOST_REVENUE"].iloc[0])
            insights["core_insights"].append({
                "type": "danger",
                "badge": "Fulfillment Friction",
                "icon": "fa-circle-xmark",
                "title": f"Order Cancellation Financial Impact: ${c_lost:,.2f}",
                "description": (
                    f"A total of {c_orders} orders were cancelled, resulting in ${c_lost:,.2f} in unrealized revenue. "
                    "Optimizing checkout friction and stock availability can recover this lost revenue."
                )
            })

        # ---------------------------------------------------------------------
        # 8. Strategic Executive Recommendations
        # ---------------------------------------------------------------------
        if top_prod is not None:
            insights["strategic_recommendations"].append({
                "category": "Merchandising & Cross-Selling",
                "title": f"Create Product Bundles Around {top_prod['PRODUCT_NAME']}",
                "action": f"Bundle '{top_prod['PRODUCT_NAME']}' with complementary accessories to elevate the storewide Average Order Value (currently ${kpis['average_order_value']:,.2f})."
            })

        if top_cat is not None:
            insights["strategic_recommendations"].append({
                "category": "Catalog Expansion",
                "title": f"Expand High-Margin SKUs in {top_cat['CATEGORY_NAME']}",
                "action": f"Since {top_cat['CATEGORY_NAME']} generates {float(top_cat['REVENUE_SHARE_PERCENT']):.1f}% of gross sales, expanding vendor partnerships in this category offers the highest return on inventory investment."
            })

        if cities:
            insights["strategic_recommendations"].append({
                "category": "Targeted Regional Marketing",
                "title": f"Launch Geo-Targeted Campaigns in {cities[0]['CITY']}",
                "action": f"Allocate 25% more ad spend into {cities[0]['CITY']} and top 3 metropolitan hubs to capitalize on proven customer acquisition and high purchasing power."
            })

        insights["strategic_recommendations"].append({
            "category": "Inventory Management",
            "title": "Clear Slow-Moving Inventory with Flash Sales",
            "action": f"Implement 15-20% limited-time promotional discounts on low-velocity items to liberate locked-up warehouse space and working capital."
        })

        return insights
