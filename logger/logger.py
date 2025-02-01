import logging
import os
from pathlib import Path
from colorama import Fore, Style, init

from constant.global_var import DATA_STORE_ROOT

# Initialize colorama for Windows compatibility
init()

class ColorLogger(logging.Logger):
    def __init__(self, name, level=logging.NOTSET):
        super().__init__(name, level)
        self.red = self.red_message

    def red_message(self, msg, *args, **kwargs):
        if self.isEnabledFor(logging.INFO):
            msg = f"{Fore.RED}{msg}{Style.RESET_ALL}"
            self._log(logging.INFO, msg, args, **kwargs)

class ColorFormatter(logging.Formatter):
    def format(self, record):
        if hasattr(record, 'red_message'):
            record.msg = f"{Fore.RED}{record.msg}{Style.RESET_ALL}"
        return super().format(record)

def setup_logger(
    name: str = 'app_logger', 
    log_files: list = None, 
    level: int = logging.INFO,
    console: bool = True
) -> ColorLogger:
    """
    Set up a logger with the given name, log files, and level.
    Optionally, enable logging to console.
    
    :param name: Name of the logger.
    :param log_files: List of file paths for the log files.
    :param level: Logging level (e.g., logging.INFO, logging.DEBUG).
    :param console: Whether to log to console.
    :return: Configured logger instance.
    """
    if log_files is None:
        log_files = ['app.log']

    logging.setLoggerClass(ColorLogger)
    logger = logging.getLogger(name)
    logger.setLevel(level)

    formatter = ColorFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Ensure each log directory exists and add file handlers
    for log_file in log_files:
        log_dir = Path(log_file).parent
        os.makedirs(log_dir, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Console handler configuration
    if console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger

# Set up a shared logger
shared_logger = setup_logger(name='chatgroup_app', log_files=[f'{DATA_STORE_ROOT}/logs/main.log'], level=logging.DEBUG, console=True)
