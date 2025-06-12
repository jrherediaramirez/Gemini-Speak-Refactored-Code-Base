# -*- coding: utf-8 -*-
"""
Structured Logging Configuration
===============================

Professional logging system for Gemini TTS with structured output,
multiple levels, and integration with Anki's logging infrastructure.
"""

import logging
import logging.handlers
import os
import sys
import traceback
from typing import Optional, Dict, Any, Union
from datetime import datetime

class TTSFormatter(logging.Formatter):
    """Custom formatter for TTS logging with structured output"""
    
    def __init__(self):
        # Color codes for console output
        self.colors = {
            'DEBUG': '\033[36m',    # Cyan
            'INFO': '\033[32m',     # Green
            'WARNING': '\033[33m',  # Yellow
            'ERROR': '\033[31m',    # Red
            'CRITICAL': '\033[35m', # Magenta
            'RESET': '\033[0m'      # Reset
        }
        
        # Format template
        super().__init__(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors and structured data"""
        
        # Add color for console output
        if hasattr(record, 'add_color') and record.add_color:
            level_color = self.colors.get(record.levelname, '')
            reset_color = self.colors['RESET']
            
            # Temporarily modify the format
            original_format = self._style._fmt
            self._style._fmt = f'{level_color}{original_format}{reset_color}'
            
            try:
                formatted = super().format(record)
            finally:
                self._style._fmt = original_format
        else:
            formatted = super().format(record)
        
        # Add extra context if available
        if hasattr(record, 'extra_context') and record.extra_context:
            context_str = ' | '.join(f"{k}={v}" for k, v in record.extra_context.items())
            formatted += f" | {context_str}"
        
        return formatted

class TTSLogger:
    """
    Main logging interface for Gemini TTS.
    
    Provides structured logging with multiple output targets and
    proper integration with Anki's logging system.
    """
    
    def __init__(self, name: str = "gemini_tts", level: str = "INFO"):
        """
        Initialize TTS logger.
        
        Args:
            name: Logger name
            level: Default logging level
        """
        self.logger = logging.getLogger(name)
        self.name = name
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            self._setup_logger(level)
    
    def _setup_logger(self, level: str):
        """Configure logger with appropriate handlers and formatters"""
        
        # Set level
        log_level = getattr(logging, level.upper(), logging.INFO)
        self.logger.setLevel(log_level)
        
        # Create formatter
        formatter = TTSFormatter()
        
        # Console handler for development
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        
        # Add color marker for console
        console_filter = self._create_console_filter()
        console_handler.addFilter(console_filter)
        
        self.logger.addHandler(console_handler)
        
        # Try to add file handler if possible
        try:
            file_handler = self._create_file_handler(formatter)
            if file_handler:
                self.logger.addHandler(file_handler)
        except Exception:
            # Silently fail if we can't create file handler
            pass
        
        # Prevent propagation to root logger to avoid duplicates
        self.logger.propagate = False
    
    def _create_console_filter(self):
        """Create filter to add color marker for console output"""
        class ConsoleFilter(logging.Filter):
            def filter(self, record):
                record.add_color = True
                return True
        return ConsoleFilter()
    
    def _create_file_handler(self, formatter) -> Optional[logging.Handler]:
        """Create file handler for persistent logging"""
        try:
            # Try to get Anki's data directory
            from aqt import mw
            if mw and hasattr(mw, 'pm') and hasattr(mw.pm, 'base'):
                log_dir = os.path.join(mw.pm.base, 'logs')
            else:
                # Fallback to temp directory
                import tempfile
                log_dir = tempfile.gettempdir()
            
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, 'gemini_tts.log')
            
            # Use rotating file handler to prevent huge log files
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=5*1024*1024,  # 5MB
                backupCount=3
            )
            
            file_handler.setFormatter(formatter)
            return file_handler
            
        except Exception:
            return None
    
    def _log_with_context(self, level: int, message: str, **kwargs):
        """Internal method to log with additional context"""
        
        # Extract exception if provided
        exception = kwargs.pop('exception', None)
        
        # CRITICAL FIX: Remove conflicting parameter names
        kwargs.pop('level', None)  # Remove level from kwargs to avoid conflict
        
        # Prepare extra context
        extra_context = {}
        for key, value in kwargs.items():
            if value is not None:
                extra_context[key] = str(value)
        
        # Create log record
        record_kwargs = {}
        if extra_context:
            record_kwargs['extra'] = {'extra_context': extra_context}
        
        # Log the message
        if exception:
            # Log with exception info
            self.logger.log(level, f"{message}: {str(exception)}", 
                          exc_info=exception, **record_kwargs)
        else:
            self.logger.log(level, message, **record_kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with optional context"""
        self._log_with_context(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message with optional context"""
        self._log_with_context(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with optional context"""
        self._log_with_context(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with optional context"""
        self._log_with_context(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message with optional context"""
        self._log_with_context(logging.CRITICAL, message, **kwargs)
    
    def exception(self, message: str, **kwargs):
        """Log exception with traceback"""
        kwargs['exception'] = sys.exc_info()[1]
        self._log_with_context(logging.ERROR, message, **kwargs)
    
    def log_operation_start(self, operation: str, **kwargs):
        """Log the start of an operation with context"""
        self.info(f"Starting {operation}", operation=operation, **kwargs)
    
    def log_operation_end(self, operation: str, success: bool = True, duration: Optional[float] = None, **kwargs):
        """Log the end of an operation with result"""
        status = "completed" if success else "failed"
        context = {"operation": operation, "status": status}
        
        if duration is not None:
            context["duration_ms"] = round(duration * 1000, 2)
        
        context.update(kwargs)
        
        if success:
            self.info(f"Operation {operation} {status}", **context)
        else:
            self.error(f"Operation {operation} {status}", **context)
    
    def log_api_call(self, endpoint: str, method: str = "POST", status_code: Optional[int] = None, 
                     duration: Optional[float] = None, **kwargs):
        """Log API call with details"""
        context = {
            "endpoint": endpoint,
            "method": method,
            "api_call": True
        }
        
        if status_code is not None:
            context["status_code"] = status_code
        
        if duration is not None:
            context["duration_ms"] = round(duration * 1000, 2)
        
        context.update(kwargs)
        
        if status_code and 200 <= status_code < 300:
            self.info(f"API call to {endpoint}", **context)
        elif status_code and status_code >= 400:
            self.error(f"API call to {endpoint} failed", **context)
        else:
            self.debug(f"API call to {endpoint}", **context)
    
    def log_performance(self, operation: str, duration: float, **kwargs):
        """Log performance metrics"""
        context = {
            "operation": operation,
            "duration_ms": round(duration * 1000, 2),
            "performance": True
        }
        context.update(kwargs)
        
        # Warn about slow operations
        if duration > 10.0:
            self.warning(f"Slow operation: {operation}", **context)
        else:
            self.debug(f"Performance: {operation}", **context)
    
    def log_cache_operation(self, operation: str, cache_key: Optional[str] = None, 
                           hit: Optional[bool] = None, **kwargs):
        """Log cache operations"""
        context = {
            "cache_operation": operation,
            "cache": True
        }
        
        if cache_key:
            context["cache_key"] = cache_key[:16] + "..." if len(cache_key) > 16 else cache_key
        
        if hit is not None:
            context["cache_hit"] = hit
        
        context.update(kwargs)
        
        self.debug(f"Cache {operation}", **context)
    
    def log_user_action(self, action: str, **kwargs):
        """Log user actions for analytics"""
        context = {
            "user_action": action,
            "user": True
        }
        context.update(kwargs)
        
        self.info(f"User action: {action}", **context)
    
    def set_level(self, level: Union[str, int]):
        """Change logging level"""
        if isinstance(level, str):
            level = getattr(logging, level.upper(), logging.INFO)
        
        self.logger.setLevel(level)
        for handler in self.logger.handlers:
            handler.setLevel(level)
        
        self.info(f"Logging level changed", new_level=logging.getLevelName(level))

# Global logger instance
_global_logger: Optional[TTSLogger] = None

def get_logger(name: str = "gemini_tts") -> TTSLogger:
    """Get logger instance (singleton pattern)"""
    global _global_logger
    if _global_logger is None or _global_logger.name != name:
        _global_logger = TTSLogger(name)
    return _global_logger

def setup_logging(level: str = "INFO", name: str = "gemini_tts") -> TTSLogger:
    """Set up logging system"""
    logger = TTSLogger(name, level)
    # Corrected call: Removed the conflicting keyword arguments.
    # The logger's name and level are already included in the log format.
    logger.info("Logging system initialized")
    return logger

# Context manager for operation logging
class LoggedOperation:
    """Context manager for logging operations with timing"""
    
    def __init__(self, logger: TTSLogger, operation: str, **kwargs):
        self.logger = logger
        self.operation = operation
        self.context = kwargs
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.log_operation_start(self.operation, **self.context)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now() - self.start_time).total_seconds()
        success = exc_type is None
        
        if not success and exc_val:
            self.context['error'] = str(exc_val)
        
        self.logger.log_operation_end(
            self.operation, 
            success=success, 
            duration=duration, 
            **self.context
        )
        
        # Don't suppress exceptions
        return False

# Decorator for automatic operation logging
def log_operation(operation_name: str = None, logger_name: str = "gemini_tts"):
    """Decorator to automatically log function operations"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = get_logger(logger_name)
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            
            with LoggedOperation(logger, op_name):
                return func(*args, **kwargs)
        
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    
    return decorator