import yaml
import logging
import sys

def load_config():
   
    logger = logging.getLogger(__name__)
    
    try:
        
        with open("config/settings.yaml", "r", encoding='utf-8') as f:
            settings = yaml.safe_load(f) or {}
            
        
        with open("config/selectors.yaml", "r", encoding='utf-8') as f:
            selectors = yaml.safe_load(f) or {}
            
        
        combined_config = {**settings, **selectors}
        logger.info("Configuration files successfully loaded and merged.")
        return combined_config
        
    except FileNotFoundError as e:
        logger.error(f"Config file is missing: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Critical error parsing config files: {e}")
        sys.exit(1)