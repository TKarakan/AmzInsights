import sys
import os
import pytest
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.orchestrator import Orchestrator
from src.utils.helpers import get_safe_filename


@pytest.fixture
def config():
    """
    Provides a mock configuration dictionary for the test environment.
    Uses a separate database and output directories to avoid polluting production data.
    Browser delays are reduced to minimum to speed up test execution.
    """
    return {
        'amazon': {
            'product_card': "div[data-component-type='s-search-result']",
            'title': "h2",
            'price': "span.a-price span.a-offscreen",
            'rating': "span.a-icon-alt",
            'dismiss_btn': "input[data-action-type='DISMISS']",
            'next_button': "a.s-pagination-next",
            'base_url': "https://www.amazon.com.tr",
            'search_endpoint': "/s?k="
        },
        'browser': {
            'min_delay': 1,
            'max_delay': 2
        },
        'database': {
            'path': 'data/test_amazon.db'
        },
        'paths': {
            'visualization_output': 'data/processed/tests',
            'export_output': 'data/exports/tests'
        },
        'visualization': {
            'fig_size': [10, 6],
            'style': 'ggplot'
        }
    }


def test_full_orchestration_pipeline(config):
    """
    Integration test for the complete pipeline.
    Verifies that scraping, cleaning, database persistence, and
    visualization file generation all complete successfully for a real keyword.
    """
    orchestrator = Orchestrator(config)

    keyword = "mechanical keyboard"
    results = orchestrator.run(keyword, pages=1)

    assert len(results) > 0, "Mission failed: No products were collected."

    first_item = results[0]
    assert isinstance(first_item['price'], float), \
        f"Data type error: Price should be float, got {type(first_item['price'])}"
    assert first_item['title'] != "Unknown Product", \
        "Data quality error: Product titles are missing."

    df = orchestrator.db.get_df_by_query(keyword)
    assert not df.empty, "Database error: Scraped data was not found in SQLite."
    assert 'search_query' in df.columns, "Schema error: 'search_query' column missing in DB."

    safe_kw = get_safe_filename(keyword)
    expected_plot = os.path.join(
        config['paths']['visualization_output'],
        f"{safe_kw}_trend.png"
    )
    assert os.path.exists(expected_plot), \
        f"Visualization error: Expected plot not found at {expected_plot}"

    print(f"\n✅ SUCCESS: {len(results)} items processed and visualized.")


@pytest.mark.parametrize("invalid_keyword", ["", " "])
def test_orchestrator_with_empty_input(config, invalid_keyword):
    """
    Verifies that the orchestrator returns an empty list and does not crash
    when given an empty or whitespace-only keyword.
    """
    orchestrator = Orchestrator(config)
    results = orchestrator.run(invalid_keyword, pages=1)
    assert results == [], \
        "Edge case error: Orchestrator should return empty list for invalid keywords."