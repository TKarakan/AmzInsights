import os
import re
import pandas as pd

def ensure_dir(path):
    """
    Checks if a directory exists, and creates it if it doesn't.
    Centralizes folder creation logic for exporters and visualizers.
    """
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

def get_safe_filename(name):
    """
    Removes special characters to create a safe and clean filename.
    Example: 'PlayStation 5 / Pro' -> 'PlayStation_5_Pro'
    """
    if not name:
        return "export"
    # Remove invalid file characters and replace spaces with underscores
    clean_name = re.sub(r'[\\/*?:"<>|]', "", str(name))
    return clean_name.replace(" ", "_")

def clean_text(text):
    """
    Standardizes raw text by removing extra whitespaces and newlines.
    Used for cleaning scraped titles and descriptions.
    """
    if not text:
        return ""
    return " ".join(str(text).split()).strip()

def format_timestamp_series(series, fmt="%Y-%m-%d %H:%M"):
    """
    Formats a Pandas Series of timestamps into human-readable strings.
    """
    try:
        return pd.to_datetime(series).dt.strftime(fmt)
    except:
        return series