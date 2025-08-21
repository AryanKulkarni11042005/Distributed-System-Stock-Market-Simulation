import logging
import sys
from datetime import datetime
import Pyro4
from utils.config import load_config

def setup_logger(name, level=logging.INFO):
    """Setup logger with consistent formatting"""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

def get_synchronized_time(service_id):
    """Get synchronized time from time server using Pyro4"""
    try:
        config = load_config()
        time_server = Pyro4.Proxy(config.TIME_SERVER_URI)
        return time_server.get_synchronized_time(service_id)
    except Exception as e:
        # Fallback to local time if time server unavailable
        return datetime.utcnow().isoformat()

def log_with_sync_time(logger, level, message, service_id):
    """Log message with synchronized timestamp"""
    sync_time = get_synchronized_time(service_id)
    formatted_message = f"[{sync_time}] {message}"
    logger.log(level, formatted_message)
    return sync_time