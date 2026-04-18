import logging
import pandas as pd
from src.core.scraper import AmazonScraper
from src.processing.cleaner import DataCleaner
from src.database.db_manager import AmazonDB
from src.processing.analyzer import AmazonAnalyzer
from src.processing.visualizer import AmazonVisualizer
from src.utils.exporter import AmazonExporter
from src.utils.helpers import get_safe_filename, format_timestamp_series


class Orchestrator:
    def __init__(self, config):
        """Initializes all pipeline components: scraper, cleaner, database, analyzer, visualizer, and exporter."""
        self.logger = logging.getLogger(__name__)
        self.config = config

        self.scraper = AmazonScraper(self.config)
        self.cleaner = DataCleaner()
        self.db = AmazonDB(self.config)
        self.analyzer = AmazonAnalyzer()
        self.visualizer = AmazonVisualizer(self.config)
        self.exporter = AmazonExporter(self.config)

    def run(self, keyword, pages=2, min_p=0, max_p=1000000):
        """
        Executes the full data pipeline in order:
        Scrape -> Clean -> Store -> Filter -> Analyze -> Visualize -> Export.
        Returns the cleaned product list, or an empty list if the keyword is
        invalid or any stage fails. The browser is always closed in the finally block.
        """
        if not keyword or not keyword.strip():
            self.logger.warning("Empty keyword provided. Aborting.")
            return []

        self.logger.info(f"Mission Started: Scraping {pages} pages for '{keyword}'")

        try:
            # 1. DATA COLLECTION
            raw_data = self.scraper.get_multiple_pages(keyword, max_pages=pages)
            if not raw_data:
                self.logger.warning("No data found during scraping.")
                return []

            # 2. DATA CLEANING
            cleaned_list = []
            for item in raw_data:
                item['title'] = self.cleaner.clean_title(item.get('title', ''))
                item['price'] = self.cleaner.clean_price(item.get('price', 0))
                item['rating'] = self.cleaner.clean_rating(item.get('rating', 0))
                cleaned_list.append(item)

            self.logger.info(f"Cleaning complete: {len(cleaned_list)} items processed.")

            # 3. DATABASE STORAGE
            self.db.save_results(cleaned_list, keyword)
            self.logger.info("Data successfully stored in database.")

            # 4. ANALYSIS & VISUALIZATION
            df = self.db.get_df_by_query(keyword)
            all_history_df = self.db.get_all_history_df()

            if not df.empty:
                clean_df = self.analyzer.remove_garbage_prices(df, min_p=min_p, max_p=max_p)

                if not clean_df.empty:
                    trends = self.analyzer.get_price_trends(clean_df)
                    self.visualizer.create_trend_chart(trends, keyword)
                    self.visualizer.create_value_for_money_chart(clean_df, keyword)
                    self.visualizer.create_price_segments_chart(clean_df, keyword)
                    self.visualizer.create_wordcloud(clean_df, keyword)

                    if not all_history_df.empty:
                        self.visualizer.create_category_comparison(all_history_df, keyword)

                    export_df = clean_df.copy()
                    export_df['timestamp'] = format_timestamp_series(export_df['timestamp'])
                    safe_keyword = get_safe_filename(keyword)

                    export_list = export_df.to_dict(orient='records')
                    self.exporter.export_data(export_list, f"{safe_keyword}_export", format="excel")
                    self.exporter.export_data(export_list, f"{safe_keyword}_export", format="json")

                else:
                    self.logger.warning("No data left after filtering.")

            self.logger.info("Mission accomplished: Analysis and exports are ready.")
            return cleaned_list

        except Exception as e:
            self.logger.error(f"Mission failed: {str(e)}")
            return []

        finally:
            try:
                self.scraper.close_driver()
            except Exception as e:
                self.logger.warning(f"Could not close driver cleanly: {e}")