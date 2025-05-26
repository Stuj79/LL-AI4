"""
Logging setup utilities for the Legal AI Marketing Assistant.

This module provides configuration-driven logging initialization that integrates
with the new centralized configuration system using LoggingConfig.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional
from rich.logging import RichHandler
from rich.console import Console

from llai.config.settings import LoggingConfig, get_config

# Global console instance for rich logging
console = Console()

def setup_logging(config: Optional[LoggingConfig] = None) -> None:
    """
    Initialize the Python logging system based on LoggingConfig.
    
    Args:
        config: Optional LoggingConfig instance. If None, will get from global config.
    """
    if config is None:
        app_config = get_config()
        config = app_config.logging
    
    # Clear any existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Set the root logging level
    try:
        log_level = getattr(logging, config.level.upper())
    except AttributeError:
        log_level = logging.INFO
        print(f"Warning: Invalid log level '{config.level}', defaulting to INFO")
    
    root_logger.setLevel(log_level)
    
    # Create formatters
    detailed_formatter = logging.Formatter(config.format)
    simple_formatter = logging.Formatter('%(levelname)s - %(message)s')
    
    # Add console handler
    if config.enable_rich_logging:
        console_handler = RichHandler(
            console=console,
            show_time=True,
            show_path=True,
            markup=True,
            rich_tracebacks=True
        )
        console_handler.setFormatter(simple_formatter)
    else:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(detailed_formatter)
    
    console_handler.setLevel(log_level)
    root_logger.addHandler(console_handler)
    
    # Add file handler if file path is specified
    if config.file_path:
        try:
            # Ensure the directory exists
            log_file_path = Path(config.file_path)
            log_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create rotating file handler
            file_handler = logging.handlers.RotatingFileHandler(
                filename=config.file_path,
                maxBytes=config.max_file_size,
                backupCount=config.backup_count,
                encoding='utf-8'
            )
            file_handler.setFormatter(detailed_formatter)
            file_handler.setLevel(log_level)
            root_logger.addHandler(file_handler)
            
            logging.info(f"File logging enabled: {config.file_path}")
            
        except Exception as e:
            logging.error(f"Failed to setup file logging: {e}")
    
    # Log the successful setup
    logging.info(f"Logging initialized - Level: {config.level}, Rich: {config.enable_rich_logging}")

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: The name for the logger (typically __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)

def setup_module_logger(module_name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Setup and configure a logger for a specific module.
    
    Args:
        module_name: The name of the module (typically __name__)
        level: Optional specific log level for this module
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(module_name)
    
    if level:
        try:
            log_level = getattr(logging, level.upper())
            logger.setLevel(log_level)
        except AttributeError:
            logger.warning(f"Invalid log level '{level}' for module {module_name}")
    
    return logger

def log_system_info() -> None:
    """Log system and configuration information for debugging."""
    import platform
    import sys
    from datetime import datetime
    
    logger = get_logger(__name__)
    
    logger.info("=== System Information ===")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Platform: {platform.platform()}")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    
    try:
        config = get_config()
        logger.info(f"App name: {config.app_name}")
        logger.info(f"App version: {config.version}")
        logger.info(f"Debug mode: {config.debug_mode}")
        logger.info(f"LLM provider: {config.llm_provider.default_model}")
    except Exception as e:
        logger.warning(f"Could not log configuration info: {e}")
    
    logger.info("=== End System Information ===")

def configure_third_party_loggers() -> None:
    """Configure logging levels for third-party libraries to reduce noise."""
    # Reduce noise from common third-party libraries
    noisy_loggers = [
        'urllib3.connectionpool',
        'requests.packages.urllib3.connectionpool',
        'httpx',
        'httpcore',
        'openai',
        'anthropic',
        'streamlit',
        'watchdog'
    ]
    
    for logger_name in noisy_loggers:
        logging.getLogger(logger_name).setLevel(logging.WARNING)

def setup_error_logging() -> None:
    """Setup specialized error logging for atomic exceptions."""
    from .exceptions_atomic import AtomicException, log_error_with_context
    
    # Create a specialized handler for atomic errors
    error_logger = get_logger('atomic_errors')
    
    # You could add a separate file handler specifically for errors here
    # This is useful for monitoring and debugging in production
    
    def log_atomic_error(error: AtomicException, include_traceback: bool = False) -> None:
        """Log an atomic error with full context."""
        log_error_with_context(error, include_traceback)
        
        # Additional error-specific logging could go here
        # e.g., sending to error monitoring service
    
    # Make the function available globally
    import builtins
    builtins.log_atomic_error = log_atomic_error

def initialize_application_logging() -> None:
    """
    Initialize logging for the entire application.
    
    This function should be called early in the application startup process.
    """
    # Setup basic logging
    setup_logging()
    
    # Configure third-party loggers
    configure_third_party_loggers()
    
    # Setup error logging
    setup_error_logging()
    
    # Log system information
    log_system_info()
    
    logger = get_logger(__name__)
    logger.info("Application logging initialized successfully")

def create_context_logger(context: str, base_logger: Optional[logging.Logger] = None) -> logging.Logger:
    """
    Create a logger with additional context information.
    
    Args:
        context: Context string to add to log messages
        base_logger: Base logger to extend (defaults to root logger)
        
    Returns:
        Logger with context information
    """
    if base_logger is None:
        base_logger = logging.getLogger()
    
    # Create a custom logger adapter that adds context
    class ContextAdapter(logging.LoggerAdapter):
        def process(self, msg, kwargs):
            return f"[{self.extra['context']}] {msg}", kwargs
    
    return ContextAdapter(base_logger, {'context': context})

# Convenience functions for common logging patterns

def log_function_entry(func_name: str, args: dict = None, logger: logging.Logger = None) -> None:
    """Log function entry with arguments."""
    if logger is None:
        logger = get_logger(__name__)
    
    if args:
        logger.debug(f"Entering {func_name} with args: {args}")
    else:
        logger.debug(f"Entering {func_name}")

def log_function_exit(func_name: str, result: any = None, logger: logging.Logger = None) -> None:
    """Log function exit with result."""
    if logger is None:
        logger = get_logger(__name__)
    
    if result is not None:
        logger.debug(f"Exiting {func_name} with result type: {type(result).__name__}")
    else:
        logger.debug(f"Exiting {func_name}")

def log_performance(operation: str, duration: float, logger: logging.Logger = None) -> None:
    """Log performance information."""
    if logger is None:
        logger = get_logger(__name__)
    
    logger.info(f"Performance: {operation} took {duration:.3f} seconds")

# Decorator for automatic function logging
def logged_function(logger: logging.Logger = None):
    """Decorator to automatically log function entry and exit."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            func_logger = logger or get_logger(func.__module__)
            func_name = f"{func.__module__}.{func.__name__}"
            
            log_function_entry(func_name, {'args': len(args), 'kwargs': list(kwargs.keys())}, func_logger)
            
            try:
                result = func(*args, **kwargs)
                log_function_exit(func_name, result, func_logger)
                return result
            except Exception as e:
                func_logger.error(f"Exception in {func_name}: {e}")
                raise
        
        return wrapper
    return decorator
