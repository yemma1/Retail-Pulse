"""
Online Retail Sales Analytics - Application Configuration
Reads environment variables for Oracle SQL Database credentials and Flask runtime settings.
"""

import os
from dotenv import load_dotenv

# Load .env file if available
load_dotenv()

class Config:
    # Flask Settings
    SECRET_KEY = os.getenv("SECRET_KEY", "retail-sales-analytics-super-secret-key-2024")
    DEBUG = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1", "yes")
    HOST = os.getenv("FLASK_HOST", "0.0.0.0")
    PORT = int(os.getenv("FLASK_PORT", 5000))

    # Oracle Database Settings
    ORACLE_USER = os.getenv("ORACLE_USER", "")
    ORACLE_PASSWORD = os.getenv("ORACLE_PASSWORD", "")
    ORACLE_DSN = os.getenv("ORACLE_DSN", "")  # e.g., "localhost:1521/XEPDB1" or Oracle Cloud TNS
    ORACLE_WALLET_DIR = os.getenv("ORACLE_WALLET_DIR", None)
    ORACLE_WALLET_PASSWORD = os.getenv("ORACLE_WALLET_PASSWORD", None)

    @classmethod
    def is_oracle_configured(cls) -> bool:
        """Checks if minimum Oracle configuration parameters are present."""
        return bool(cls.ORACLE_USER and cls.ORACLE_PASSWORD and cls.ORACLE_DSN)

    @classmethod
    def get_oracle_params(cls) -> dict:
        """Constructs connection parameters for python-oracledb."""
        params = {
            "user": cls.ORACLE_USER,
            "password": cls.ORACLE_PASSWORD,
            "dsn": cls.ORACLE_DSN
        }
        if cls.ORACLE_WALLET_DIR:
            params["wallet_location"] = cls.ORACLE_WALLET_DIR
        if cls.ORACLE_WALLET_PASSWORD:
            params["wallet_password"] = cls.ORACLE_WALLET_PASSWORD
        return params
