"""
Online Retail Sales Analytics - Application Entry Point
Flask Application Factory and Server Startup Script.
"""

import os
from flask import Flask, jsonify
from flask_cors import CORS
from config import Config
from routes.dashboard import dashboard_bp
from routes.analytics import analytics_bp
from database.db_manager import db


def create_app(config_class=Config):
    """Application factory for Online Retail Sales Analytics."""
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(config_class)

    # Enable Cross-Origin Resource Sharing for API routes
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Register Blueprints
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(analytics_bp)

    # Database Initialization log
    status = db.get_status()
    print("=" * 70)
    print("  ONLINE RETAIL SALES ANALYTICS DASHBOARD")
    print(f"  Database Engine: {status['database_name']} ({status['engine']})")
    print(f"  Oracle Driver Available: {status['oracle_available']}")
    print("=" * 70)

    # Global HTTP Error Handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({"status": "error", "message": "Resource not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"status": "error", "message": "Internal server error occurred"}), 500

    return app


app = create_app()

if __name__ == "__main__":
    host = Config.HOST
    port = Config.PORT
    debug = Config.DEBUG
    print(f"Server starting on http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)
