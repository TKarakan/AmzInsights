import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import os
import logging
from wordcloud import WordCloud
from src.utils.helpers import ensure_dir, get_safe_filename


class AmazonVisualizer:
    def __init__(self, config):
        """
        Initializes the visualization engine, sets the output directory,
        applies the configured plot style, and ensures the output folder exists.
        """
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.output_dir = config.get('paths', {}).get('visualization_output', 'data/processed')

        viz_config = config.get('visualization', {})
        self.fig_size = tuple(viz_config.get('fig_size', [10, 6]))
        self.style = viz_config.get('style', 'ggplot')

        ensure_dir(self.output_dir)

        try:
            plt.style.use(self.style)
        except Exception:
            self.logger.warning(f"Style '{self.style}' not found, falling back to ggplot.")
            plt.style.use('ggplot')

        self.logger.info(f"Visualizer initialized. Output directory: {self.output_dir}")

    def create_trend_chart(self, trend_data, search_query):
        """
        Plots average daily prices over time as a line chart and saves it to disk.
        Uses the isolated fig/ax API to avoid state pollution between concurrent charts.
        """
        if not trend_data:
            return None
        try:
            dates = list(trend_data.keys())
            prices = list(trend_data.values())

            fig, ax = plt.subplots(figsize=self.fig_size)
            ax.plot(dates, prices, marker='o', color='b', linestyle='-', linewidth=2)
            ax.set_title(f"Price Trend Analysis: {search_query.upper()}", fontsize=14)
            ax.set_xlabel("Date")
            ax.set_ylabel("Average Price (TL)")
            plt.xticks(rotation=45)
            ax.grid(True, linestyle="--", alpha=0.7)
            fig.tight_layout()

            file_name = f"{get_safe_filename(search_query)}_trend.png"
            save_path = os.path.join(self.output_dir, file_name)
            fig.savefig(save_path)
            plt.close(fig)

            self.logger.info(f"Trend chart saved: {save_path}")
            return save_path
        except Exception as e:
            self.logger.error(f"Failed to create trend chart: {e}")
            return None

    def create_value_for_money_chart(self, df, search_query):
        """
        Creates a scatter plot of price vs. rating, colored by Z-score anomaly.
        If the z_score column is not present, it is computed on the fly.
        """
        if df.empty:
            return None
        try:
            if 'z_score' not in df.columns:
                mean = df['price'].mean()
                std = df['price'].std()
                if std == 0:
                    return None
                df = df.copy()
                df['z_score'] = (df['price'] - mean) / std

            fig, ax = plt.subplots(figsize=self.fig_size)
            sns.scatterplot(
                data=df, x='price', y='rating',
                hue='z_score', palette='RdYlGn_r',
                size='rating', sizes=(50, 200), alpha=0.7, ax=ax
            )
            ax.set_title(f"Value For Money Analysis: {search_query.upper()}")
            ax.set_xlabel("Price (TL)")
            ax.set_ylabel("Rating (0-5)")
            ax.legend(title="Price Anomaly (Z)", bbox_to_anchor=(1.05, 1), loc='upper left')

            file_name = f"{get_safe_filename(search_query)}_value_analysis.png"
            save_path = os.path.join(self.output_dir, file_name)
            fig.tight_layout()
            fig.savefig(save_path)
            plt.close(fig)
            self.logger.info(f"Value chart saved: {save_path}")
            return save_path
        except Exception as e:
            self.logger.error(f"Failed to create value chart: {e}")
            return None

    def create_wordcloud(self, df, search_query):
        """
        Generates a word cloud from product titles, excluding common Turkish filler words,
        and saves the result as a PNG image.
        """
        if df.empty or 'title' not in df.columns:
            return None
        try:
            text = " ".join(title for title in df['title'].astype(str))
            excluded = {"ve", "için", "ile", "fiyat", "kargo", "bedava", "dahil", "bir", "siyah", "beyaz"}
            wc = WordCloud(
                width=800, height=400,
                background_color='white',
                stopwords=excluded,
                colormap='magma'
            ).generate(text)

            fig, ax = plt.subplots(figsize=self.fig_size)
            ax.imshow(wc, interpolation='bilinear')
            ax.axis("off")
            ax.set_title(f"Market Feature Cloud: {search_query.upper()}")

            file_name = f"{get_safe_filename(search_query)}_wordcloud.png"
            save_path = os.path.join(self.output_dir, file_name)
            fig.savefig(save_path)
            plt.close(fig)
            self.logger.info(f"WordCloud saved: {save_path}")
            return save_path
        except Exception as e:
            self.logger.error(f"Failed to create WordCloud: {e}")
            return None

    def create_category_comparison(self, df, search_query):
        """
        Draws a box plot overlaid with a strip plot to compare price distributions
        across all searched categories in the database.
        """
        if 'search_query' not in df.columns:
            return None
        try:
            fig, ax = plt.subplots(figsize=self.fig_size)
            sns.boxplot(
                data=df, x='search_query', y='price',
                hue='search_query', palette='Set2', legend=False, ax=ax
            )
            sns.stripplot(
                data=df, x='search_query', y='price',
                color='black', size=3, alpha=0.3, ax=ax
            )
            ax.set_title("Market Category Comparison")
            ax.set_ylabel("Price (TL)")
            plt.xticks(rotation=45)

            file_name = f"{get_safe_filename(search_query)}_comparison.png"
            save_path = os.path.join(self.output_dir, file_name)
            fig.tight_layout()
            fig.savefig(save_path)
            plt.close(fig)
            self.logger.info(f"Comparison chart saved: {save_path}")
            return save_path
        except Exception as e:
            self.logger.error(f"Failed comparison chart: {e}")
            return None

    def create_price_segments_chart(self, df, search_query):
        """
        Divides products into four price segments (Budget, Standard, Mid-High, Premium)
        using quantile-based binning and displays the distribution as a pie chart.
        Handles cases where fewer than four distinct segments exist.
        """
        if df.empty:
            return None
        try:
            df = df.copy()
            df['segment'] = pd.qcut(
                df['price'], q=4,
                labels=['Budget', 'Standard', 'Mid-High', 'Premium'],
                duplicates='drop'
            )

            all_labels = ['Budget', 'Standard', 'Mid-High', 'Premium']
            range_labels = []
            for label in all_labels:
                subset = df[df['segment'] == label]['price']
                if not subset.empty:
                    range_labels.append(f"{label}\n({int(subset.min())} - {int(subset.max())} TL)")

            counts = df['segment'].value_counts().sort_index()

            fig, ax = plt.subplots(figsize=(8, 8))
            ax.pie(
                counts,
                labels=range_labels,
                autopct='%1.1f%%',
                startangle=140,
                colors=sns.color_palette('pastel'),
                explode=[0.05] + [0] * (len(counts) - 1)
            )
            ax.set_title(f"Market Segmentation (Price Ranges): {search_query.upper()}")

            file_name = f"{get_safe_filename(search_query)}_segments.png"
            save_path = os.path.join(self.output_dir, file_name)
            fig.savefig(save_path)
            plt.close(fig)
            self.logger.info(f"Segmentation chart saved: {save_path}")
            return save_path
        except Exception as e:
            self.logger.error(f"Failed pie chart: {e}")
            return None