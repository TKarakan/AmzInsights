import pandas as pd
import json
import os
import logging
from src.utils.helpers import ensure_dir

class AmazonExporter:
    def __init__(self, config):
        """Initializes the export engine and ensures the output directory exists."""
        self.logger = logging.getLogger(__name__)
        self.config = config
        
        self.output_dir = config.get('paths', {}).get('export_output', 'data/exports')
        
        # Offloaded directory checking to helpers
        ensure_dir(self.output_dir)

    def export_data(self, data, filename, format="excel"):
        """
        Exports the provided dictionary list into Excel or JSON format.
        """
        if not data:
            self.logger.warning("No data to export.")
            return

        file_path = os.path.join(self.output_dir, filename)

        try:
            # Convert list of dictionaries to Pandas DataFrame
            df = pd.DataFrame(data)

            if format.lower() == "excel":
                full_path = f"{file_path}.xlsx"
                # Save as Excel (requires openpyxl engine)
                df.to_excel(full_path, index=False)
                self.logger.info(f"📁 Excel export successful: {full_path}")
            
            elif format.lower() == "json":
                full_path = f"{file_path}.json"
                # Save as JSON (force_ascii=False preserves localized characters)
                df.to_json(full_path, orient='records', force_ascii=False, indent=4)
                self.logger.info(f"📁 JSON export successful: {full_path}")
            
            return full_path
            
        except Exception as e:
            self.logger.error(f"Export failed: {e}")
            return None