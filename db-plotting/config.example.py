"""
Database configuration examples
Copy to config.py and update with your credentials
"""

# SQLite
SQLITE_CONFIG = {
    "db_path": "data.db"
}

# PostgreSQL
POSTGRES_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "mydb",
    "user": "username",
    "password": "password"
}

# MySQL
MYSQL_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "database": "mydb",
    "user": "username",
    "password": "password"
}

# Query examples
SAMPLE_QUERIES = {
    "time_series": "SELECT timestamp, value FROM metrics ORDER BY timestamp",
    "aggregated": "SELECT category, COUNT(*) as count FROM data GROUP BY category",
    "recent": "SELECT * FROM logs WHERE created_at > NOW() - INTERVAL '7 days'"
}
