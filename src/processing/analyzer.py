import pandas as pd
import logging
import numpy as np


class AmazonAnalyzer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def get_market_summary(self, df):
        """Returns a dictionary of key market statistics including average price, rating, and standard deviation."""
        if df.empty:
            return "Nothing here"

        summary = {
            "total_products": len(df),
            "avg_price": round(df['price'].mean(), 2),
            "max_price": df['price'].max(),
            "min_price": df['price'].min(),
            "std_dev": round(df['price'].std(), 2),
            "avg_rating": round(df['rating'].mean(), 1)
        }
        return summary

    def find_best_deals(self, df):
        """Returns products with a rating of 4.0 or above, sorted by price ascending."""
        if df.empty:
            return []

        best_deals = df[df['rating'] >= 4.0].sort_values(by='price', ascending=True)
        return best_deals.to_dict(orient='records')

    def get_price_trends(self, df):
        """
        Groups products by date and returns average daily prices as a dictionary.
        Handles both string and datetime timestamp formats safely.
        """
        if df.empty:
            return {}

        df = df.copy()
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df = df.dropna(subset=['timestamp'])

        trends = df.groupby(df['timestamp'].dt.date)['price'].mean()
        return trends.to_dict()

    def detect_outliers(self, df, threshold=2):
        """
        Identifies products whose price deviates more than the given number
        of standard deviations from the mean (Z-score method).
        Returns an empty list if data is insufficient or all prices are identical.
        """
        if df.empty or len(df) < 3:
            return []

        mean = df['price'].mean()
        std = df['price'].std()

        if std == 0:
            return []

        df = df.copy()
        df['z_score'] = (df['price'] - mean) / std
        outliers = df[df['z_score'].abs() > threshold]
        return outliers.to_dict(orient='records')

    def remove_garbage_prices(self, df, min_p=None, max_p=None):
        """
        Filters out zero-priced entries, accessory products (cases, covers, etc.),
        products outside the given price range, and statistical outliers using IQR.
        Also parses the timestamp column into a readable string format.
        """
        if df.empty:
            return df

        df = df[df['price'] > 0].copy()

        garbage_keywords = [
            'kılıf', 'case', 'lens', 'cam', 'ekran koruyucu', 'glass', 'cover',
            'film', 'kapak', 'koruyucu', 'set', 'kit', 'askı', 'kordon', 'aparat'
        ]
        pattern = '|'.join(garbage_keywords)
        df = df[~df['title'].str.contains(pattern, case=False, na=False)]

        if min_p is not None:
            df = df[df['price'] >= min_p]
        if max_p is not None:
            df = df[df['price'] <= max_p]

        if len(df) >= 5:
            Q1 = df['price'].quantile(0.25)
            Q3 = df['price'].quantile(0.75)
            IQR = Q3 - Q1
            df = df[(df['price'] >= Q1 - 1.5 * IQR) & (df['price'] <= Q3 + 1.5 * IQR)]

        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce').dt.strftime('%Y-%m-%d %H:%M')

        return df