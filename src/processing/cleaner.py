import re
import logging
from src.utils.helpers import clean_text

class DataCleaner:
    def __init__(self):
        """Initializes the data sanitation engine."""
        self.logger = logging.getLogger(__name__)

    def clean_title(self, title): 
        """Sanitizes product titles by removing extra whitespaces and handling empty values."""
        if not title or title == "Unknown Title":
            return "Unknown Product"
        
        # Offloaded standard text cleaning to helpers
        return clean_text(title)

    def clean_price(self, price_str):
        """Converts raw price strings (e.g. '1.500,99') into clean floats."""
        if not price_str or price_str in ["N/A", "0"]:
            return 0.0
        
        try:
            match = re.search(r'[\d.,]+', str(price_str))
            if not match:
                return 0.0
                
            val = match.group(0).strip('.,')
            if not val:
                return 0.0
                     
            # Standardize thousand and decimal separators
            val = val.replace('.', '').replace(',', '.')
            return float(val)
            
        except Exception as e:
            self.logger.warning(f"Price cleaning failed for '{price_str}': {e}")
            return 0.0

    def clean_rating(self, rating_str):
        """Extracts numerical rating from strings like '4.5 out of 5 stars'."""
        if not rating_str or rating_str == "N/A":
            return 0.0
            
        try:
            match = re.search(r'(\d+[\.,]\d+)', str(rating_str))
            if match:
                val = match.group(1).replace(',', '.')
                return float(val)
            
            match_int = re.search(r'(\d+)', str(rating_str))
            if match_int:
                return float(match_int.group(1))
                
            return 0.0
        except Exception as e:
            self.logger.debug(f"Rating extraction failed: {e}")
            return 0.0