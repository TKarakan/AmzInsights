import logging
from pathlib import Path

def setup_global_logger():
    """Initializes the central logging system for the entire project."""
    
    # Ensure logs directory exists using modern Pathlib
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Global logging configuration
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            
            logging.FileHandler(
                log_dir / "amazon_intelligence.log", 
                encoding='utf-8', 
                mode='w'
            ),
            logging.StreamHandler()  # Outputs to the console/terminal
        ],
        force=True  # Allows re-configuration (Required for Python 3.8+)
    )
    
    logger = logging.getLogger("amazon_pro")
    logger.info("✅ Global logger initialized successfully.")
    
    return logger