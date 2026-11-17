import logging
import os

import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


class DatabaseConnection:
    def __init__(self):
        self.host = os.getenv("DB_HOST", "localhost")
        self.port = os.getenv("DB_PORT", "5432")
        self.database = os.getenv("DB_NAME", "webshop_analytics")
        self.user = os.getenv("DB_USER", "postgres")
        self.password = os.getenv("DB_PASSWORD", "postgres")

    def get_connection(self):
        return psycopg2.connect(
            host=self.host,
            port=self.port,
            database=self.database,
            user=self.user,
            password=self.password,
        )

    def execute_query(self, query: str, params=None):
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute(query, params)

        if cursor.description:
            results = cursor.fetchall()
        else:
            results = None

        conn.commit()
        cursor.close()
        conn.close()

        return results

    def init_database(self):

        create = """
        CREATE TABLE IF NOT EXISTS sessions (
            session_id VARCHAR(255) PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP NOT NULL,
            duration_minutes FLOAT NOT NULL,
            event_count INTEGER NOT NULL,
            has_order BOOLEAN NOT NULL,
            process_date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_customer_id ON sessions(customer_id);
        CREATE INDEX IF NOT EXISTS idx_has_order ON sessions(has_order);
        CREATE INDEX IF NOT EXISTS idx_start_time ON sessions(start_time);
        CREATE INDEX IF NOT EXISTS idx_process_date ON sessions(process_date);
        
        CREATE TABLE IF NOT EXISTS user_metrics (
            id SERIAL PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            calculation_date DATE NOT NULL,
            total_sessions_30d INTEGER NOT NULL,
            single_event_sessions_30d INTEGER NOT NULL,
            avg_sessions_between_purchases FLOAT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(customer_id, calculation_date)
        );
        
        CREATE INDEX IF NOT EXISTS idx_user_metrics_customer ON user_metrics(customer_id);
        CREATE INDEX IF NOT EXISTS idx_user_metrics_date ON user_metrics(calculation_date);
        """

        self.execute_query(create)
        logger.info("Database initialized successfully")


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    dc = DatabaseConnection()
    if sys.argv[1] == "init":
        dc.init_database()
