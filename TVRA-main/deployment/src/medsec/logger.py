import logging
import os

def get_logger(name='TVRA', log_file=None):
    """
    Get a configured logger instance.
    
    Args:
        name (str): Name of the logger (default: 'TVRA')
        log_file (str): Path to the log file. If None, defaults to environment variable
                       MEDSEC_LOG_FILE or "medsec.log"
    
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Only configure if handlers haven't been added yet
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Create console handler
        ch_console = logging.StreamHandler()
        ch_console.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch_console.setFormatter(formatter)
        
        # Add console handler
        logger.addHandler(ch_console)
        
        # Add file handler if specified
        if log_file is None:
            log_file = os.environ.get('MEDSEC_LOG_FILE', 'medsec.log')
        
        ch_file = logging.FileHandler(log_file, mode="a")
        ch_file.setLevel(logging.INFO)
        ch_file.setFormatter(formatter)
        logger.addHandler(ch_file)
    
    return logger 