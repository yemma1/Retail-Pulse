"""
Online Retail Sales Analytics - Database Connection Manager
Provides unified database access supporting:
1. Enterprise Oracle Database (via python-oracledb, thin or thick client)
2. Standalone SQLite Local Fallback with automatic schema creation and data seeding

This ensures production Oracle compatibility while allowing developers and evaluators
to run the application instantly without requiring an external Oracle instance.
"""

import os
import sqlite3
import pandas as pd
from datetime import datetime
from config import Config

# Try importing oracledb (Oracle client)
try:
    import oracledb
    ORACLE_AVAILABLE = True
except ImportError:
    ORACLE_AVAILABLE = False


class DatabaseManager:
    _instance = None

    def __init__(self):
        self.config = Config
        self.engine_type = "UNKNOWN"
        self.oracle_pool = None
        self.sqlite_db_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "retail_analytics.db"
        )
        self.initialize_engine()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = DatabaseManager()
        return cls._instance

    def initialize_engine(self):
        """Initializes Oracle connection pool if configured, else initializes SQLite."""
        if ORACLE_AVAILABLE and self.config.is_oracle_configured():
            try:
                # Test Oracle connection
                params = self.config.get_oracle_params()
                connection = oracledb.connect(**params)
                connection.close()
                self.engine_type = "ORACLE"
                print(f"[DB] Successfully connected to Oracle Database at {params.get('dsn')}")
                return
            except Exception as e:
                print(f"[DB WARNING] Failed to connect to Oracle DB: {e}. Falling back to SQLite local engine.")

        # Local SQLite fallback
        self.engine_type = "SQLITE"
        self._setup_local_sqlite()
        print(f"[DB] Using Local Embedded Database at: {self.sqlite_db_path}")

    def _setup_local_sqlite(self):
        """Creates SQLite tables and seeds sample data if database does not exist or is empty."""
        conn = sqlite3.connect(self.sqlite_db_path)
        cursor = conn.cursor()

        # Check if tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ORDERS'")
        table_exists = cursor.fetchone()

        if not table_exists:
            print("[DB] Initializing local database schema and seeding sample data...")
            # Create schema
            cursor.executescript("""
                CREATE TABLE IF NOT EXISTS CUSTOMERS (
                    CUSTOMER_ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    CUSTOMER_NAME TEXT NOT NULL,
                    EMAIL TEXT NOT NULL UNIQUE,
                    CITY TEXT NOT NULL,
                    STATE TEXT NOT NULL,
                    COUNTRY TEXT DEFAULT 'USA' NOT NULL,
                    REGISTRATION_DATE DATE DEFAULT CURRENT_TIMESTAMP NOT NULL
                );

                CREATE TABLE IF NOT EXISTS CATEGORIES (
                    CATEGORY_ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    CATEGORY_NAME TEXT NOT NULL UNIQUE,
                    DESCRIPTION TEXT
                );

                CREATE TABLE IF NOT EXISTS PRODUCTS (
                    PRODUCT_ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    PRODUCT_NAME TEXT NOT NULL,
                    CATEGORY_ID INTEGER NOT NULL,
                    PRICE REAL NOT NULL,
                    STOCK_QUANTITY INTEGER DEFAULT 0 NOT NULL,
                    FOREIGN KEY (CATEGORY_ID) REFERENCES CATEGORIES (CATEGORY_ID)
                );

                CREATE TABLE IF NOT EXISTS ORDERS (
                    ORDER_ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    CUSTOMER_ID INTEGER NOT NULL,
                    ORDER_DATE DATE DEFAULT CURRENT_TIMESTAMP NOT NULL,
                    ORDER_STATUS TEXT DEFAULT 'Completed' NOT NULL,
                    PAYMENT_METHOD TEXT DEFAULT 'Credit Card' NOT NULL,
                    FOREIGN KEY (CUSTOMER_ID) REFERENCES CUSTOMERS (CUSTOMER_ID)
                );

                CREATE TABLE IF NOT EXISTS ORDER_ITEMS (
                    ORDER_ITEM_ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    ORDER_ID INTEGER NOT NULL,
                    PRODUCT_ID INTEGER NOT NULL,
                    QUANTITY INTEGER NOT NULL,
                    UNIT_PRICE REAL NOT NULL,
                    DISCOUNT REAL DEFAULT 0.00 NOT NULL,
                    FOREIGN KEY (ORDER_ID) REFERENCES ORDERS (ORDER_ID) ON DELETE CASCADE,
                    FOREIGN KEY (PRODUCT_ID) REFERENCES PRODUCTS (PRODUCT_ID)
                );

                CREATE INDEX IF NOT EXISTS IDX_CUST_CITY ON CUSTOMERS (CITY);
                CREATE INDEX IF NOT EXISTS IDX_PROD_CATEGORY ON PRODUCTS (CATEGORY_ID);
                CREATE INDEX IF NOT EXISTS IDX_ORDERS_DATE ON ORDERS (ORDER_DATE);
                CREATE INDEX IF NOT EXISTS IDX_ORDERS_STATUS ON ORDERS (ORDER_STATUS);
                CREATE INDEX IF NOT EXISTS IDX_ITEMS_ORDER ON ORDER_ITEMS (ORDER_ID);
            """)
            conn.commit()

            # Seed data using seed_data generator
            from database.seed_data import (
                CATEGORIES, PRODUCTS, generate_customers, generate_orders_and_items
            )
            customers = generate_customers(105)
            orders, order_items = generate_orders_and_items(105, 330)

            cursor.executemany(
                "INSERT INTO CATEGORIES (CATEGORY_ID, CATEGORY_NAME, DESCRIPTION) VALUES (?, ?, ?)",
                CATEGORIES
            )
            cursor.executemany(
                "INSERT INTO PRODUCTS (PRODUCT_ID, PRODUCT_NAME, CATEGORY_ID, PRICE, STOCK_QUANTITY) VALUES (?, ?, ?, ?, ?)",
                PRODUCTS
            )
            cursor.executemany(
                "INSERT INTO CUSTOMERS (CUSTOMER_ID, CUSTOMER_NAME, EMAIL, CITY, STATE, COUNTRY, REGISTRATION_DATE) VALUES (?, ?, ?, ?, ?, ?, ?)",
                customers
            )
            cursor.executemany(
                "INSERT INTO ORDERS (ORDER_ID, CUSTOMER_ID, ORDER_DATE, ORDER_STATUS, PAYMENT_METHOD) VALUES (?, ?, ?, ?, ?)",
                orders
            )
            cursor.executemany(
                "INSERT INTO ORDER_ITEMS (ORDER_ITEM_ID, ORDER_ID, PRODUCT_ID, QUANTITY, UNIT_PRICE, DISCOUNT) VALUES (?, ?, ?, ?, ?, ?)",
                order_items
            )
            conn.commit()
            print("[DB] Local schema and seed data created successfully!")

        conn.close()

    def get_connection(self):
        """Returns active database connection."""
        if self.engine_type == "ORACLE":
            params = self.config.get_oracle_params()
            return oracledb.connect(**params)
        else:
            conn = sqlite3.connect(self.sqlite_db_path)
            conn.row_factory = sqlite3.Row
            return conn

    def execute_query(self, query: str, params: dict = None) -> pd.DataFrame:
        """
        Executes a SQL query and returns results as a Pandas DataFrame.
        Handles dialect adaptation if running in SQLite fallback mode.
        """
        if params is None:
            params = {}

        if self.engine_type == "ORACLE":
            conn = self.get_connection()
            try:
                # In Oracle, params are :param_name
                df = pd.read_sql_query(query, conn, params=params)
                # Oracle returns UPPERCASE column names
                df.columns = [col.upper() for col in df.columns]
                return df
            finally:
                conn.close()
        else:
            # SQLite fallback: translate Oracle-specific constructs for local execution
            sqlite_query = self._adapt_oracle_sql_for_sqlite(query)
            conn = self.get_connection()
            try:
                # Convert named parameters :name into SQLite format
                df = pd.read_sql_query(sqlite_query, conn, params=params)
                df.columns = [col.upper() for col in df.columns]
                return df
            finally:
                conn.close()

    def _adapt_oracle_sql_for_sqlite(self, sql: str) -> str:
        """Adapts Oracle SQL date/analytical syntax to SQLite when running offline."""
        translated = sql
        # Oracle NVL -> SQLite COALESCE / IFNULL
        translated = translated.replace("NVL(", "COALESCE(")
        
        # Oracle TO_CHAR(col, 'YYYY-MM') -> strftime('%Y-%m', col)
        translated = translated.replace("TO_CHAR(o.ORDER_DATE, 'YYYY-MM')", "strftime('%Y-%m', o.ORDER_DATE)")
        translated = translated.replace("TO_CHAR(ORDER_DATE, 'YYYY-MM')", "strftime('%Y-%m', ORDER_DATE)")
        
        # Oracle TRUNC(col, 'MM') -> strftime('%Y-%m-01', col)
        translated = translated.replace("TRUNC(o.ORDER_DATE, 'MM')", "strftime('%Y-%m-01', o.ORDER_DATE)")
        translated = translated.replace("TRUNC(ORDER_DATE, 'MM')", "strftime('%Y-%m-01', ORDER_DATE)")

        # Oracle string concatenation || is supported in SQLite
        # Oracle ROWNUM <= 1 -> LIMIT 1
        if "WHERE ROWNUM = 1" in translated:
            translated = translated.replace("WHERE ROWNUM = 1", "")
            translated = translated.rstrip(" ;") + " LIMIT 1"
        elif "WHERE ROWNUM <= " in translated:
            import re
            m = re.search(r"WHERE ROWNUM <= (\d+)", translated)
            if m:
                limit_val = m.group(1)
                translated = re.sub(r"WHERE ROWNUM <= \d+", "", translated)
                translated = translated.rstrip(" ;") + f" LIMIT {limit_val}"

        return translated

    def get_status(self):
        """Returns database engine status metadata."""
        return {
            "engine": self.engine_type,
            "is_oracle": self.engine_type == "ORACLE",
            "sqlite_fallback": self.engine_type == "SQLITE",
            "oracle_available": ORACLE_AVAILABLE,
            "database_name": "Oracle Cloud / Autonomous / On-Prem" if self.engine_type == "ORACLE" else "SQLite In-Memory / File Engine"
        }


# Global singleton instance
db = DatabaseManager.get_instance()
