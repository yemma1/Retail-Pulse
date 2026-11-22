"""
Online Retail Sales Analytics - Dashboard Blueprint
Serves the presentation view templates and CSV data export utilities.
"""

from io import StringIO
from flask import Blueprint, render_template, request, Response
import pandas as pd
from services.analytics_service import AnalyticsService
from database.db_manager import db

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/", methods=["GET"])
def index():
    """Renders the main Business Intelligence Dashboard."""
    db_status = db.get_status()
    return render_template("index.html", db_status=db_status)


@dashboard_bp.route("/export/csv/<report_type>", methods=["GET"])
def export_csv(report_type):
    """
    Exports analytical query results to downloadable CSV files.
    Supports: products, customers, monthly, categories, cities.
    """
    filters = {
        "startDate": request.args.get("startDate") or None,
        "endDate": request.args.get("endDate") or None,
        "category": request.args.get("category") or None,
        "city": request.args.get("city") or None,
        "status": request.args.get("status") or "all_active"
    }

    df = pd.DataFrame()
    filename = f"retail_{report_type}_export.csv"

    if report_type == "products":
        data = AnalyticsService.get_best_selling_products(limit=50, filters=filters)
        df = pd.DataFrame(data.get("products", []))
    elif report_type == "customers":
        data = AnalyticsService.get_top_customers(limit=50, filters=filters)
        df = pd.DataFrame(data.get("customers", []))
    elif report_type == "monthly":
        data = AnalyticsService.get_monthly_sales_analysis(filters=filters)
        df = pd.DataFrame(data.get("monthly_data", []))
    elif report_type == "categories":
        data = AnalyticsService.get_category_comparison(filters=filters)
        df = pd.DataFrame(data.get("categories", []))
    elif report_type == "cities":
        data = AnalyticsService.get_city_analysis(limit=50, filters=filters)
        df = pd.DataFrame(data.get("cities", []))
    else:
        return Response("Invalid report type specified.", status=400)

    output = StringIO()
    df.to_csv(output, index=False)
    csv_data = output.getvalue()

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )
