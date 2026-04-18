import sqlite3
from datetime import datetime
import logging
import os
import pandas as pd

class AmazonDB:
    def __init__(self, config):
        """
        Initializes the database connection and ensures the schema is ready.
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Get DB path from config or use default
        self.db_name = self.config.get('database', {}).get('path', 'data/amazon_intelligence.db')
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(self.db_name), exist_ok=True)
        self._init_db()

    def _get_conn(self):
        """
        Creates a new connection to the SQLite database.
        """
        return sqlite3.connect(self.db_name)

    def _init_db(self):
        """
        Creates the required tables if they do not exist.
        """
        try:
            with self._get_conn() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS product_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT,
                        price REAL,
                        rating REAL,
                        timestamp DATETIME,
                        search_query TEXT
                    )
                """)
                self.logger.info("Database initialized successfully.")
        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}")

    def save_results(self, products, query):
        """
        Saves a list of product dictionaries into the database with a timestamp.
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with self._get_conn() as conn:
                data = [(p['title'], p['price'], p['rating'], now, query) for p in products]
                conn.executemany("""
                    INSERT INTO product_history (title, price, rating, timestamp, search_query) 
                    VALUES (?, ?, ?, ?, ?)
                """, data)
                self.logger.info(f"Successfully saved {len(products)} items to database for query: '{query}'")
        except Exception as e:
            self.logger.error(f"Failed to save products to database: {e}")

    def get_df_by_query(self, search_query):
        """
        Returns a DataFrame containing all history for a SPECIFIC search query.
        Useful for trend analysis of a single product.
        """
        try:
            with self._get_conn() as conn:
                query_str = "SELECT * FROM product_history WHERE search_query = ?"
                return pd.read_sql_query(query_str, conn, params=(search_query,))
        except Exception as e:
            self.logger.error(f"Error fetching data for query '{search_query}': {e}")
            return pd.DataFrame()

    def get_all_history_df(self):
        """
        Returns a DataFrame containing the ENTIRE database history.
        Essential for Category Comparison (Box Plots) across different products.
        """
        try:
            with self._get_conn() as conn:
                query_str = "SELECT * FROM product_history"
                return pd.read_sql_query(query_str, conn)
        except Exception as e:
            self.logger.error(f"Error fetching all history: {e}")
            return pd.DataFrame()

    def get_price_change(self, product_title):
        """
        Retrieves the price history of a specific product by its title.
        """
        try:
            with self._get_conn() as conn:
                cursor = conn.execute("""
                    SELECT price, timestamp FROM product_history 
                    WHERE title = ? 
                    ORDER BY timestamp DESC
                """, (product_title,))
                return cursor.fetchall()
        except Exception as e:
            self.logger.error(f"Error fetching price change for '{product_title}': {e}")
            return []