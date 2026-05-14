"""
F1 Strategy Platform v4.0 - Structured JSON Logging
Production-ready logging with correlation IDs and metrics.
"""
import json
import logging
import sys
import uuid
from datetime import datetime
import os
import time
from functools import wraps


class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.
    Compatible with ELK Stack, Loki, and other log aggregators.
    """
    
    def __init__(self):
        super().__init__()
        self.hostname = os.uname().nodename if hasattr(os, 'uname') else 'unknown'
        self.service = 'f1-strategy-backend'
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'message': record.getMessage(),
            'logger': record.name,
            'service': self.service,
            'hostname': self.hostname,
            'source': {
                'file': record.filename,
                'line': record.lineno,
                'function': record.funcName
            }
        }
        
        # Add correlation ID if available
        if hasattr(record, 'correlation_id'):
            log_data['correlation_id'] = record.correlation_id
        
        # Add user context if available
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'username'):
            log_data['username'] = record.username
        
        # Add extra fields
        if hasattr(record, 'extra_data'):
            log_data.update(record.extra_data)
        
        # Add exception info
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, default=str)


class CorrelationIdFilter(logging.Filter):
    """Filter to add correlation ID to log records."""
    
    def __init__(self):
        super().__init__()
        self._correlation_id = None
    
    def set_correlation_id(self, correlation_id: str):
        self._correlation_id = correlation_id
    
    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = getattr(record, 'correlation_id', self._correlation_id or str(uuid.uuid4())[:8])
        return True


def setup_logging(log_level: str = None) -> logging.Logger:
    """
    Setup structured JSON logging for production.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        
    Returns:
        Configured root logger
    """
    level = log_level or os.getenv('LOG_LEVEL', 'INFO')
    
    # Create formatter
    formatter = JSONFormatter()
    
    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    
    # Add correlation ID filter
    correlation_filter = CorrelationIdFilter()
    handler.addFilter(correlation_filter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    root_logger.handlers = []  # Clear existing handlers
    root_logger.addHandler(handler)
    
    # Reduce noise from third-party libraries
    logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get logger with given name."""
    return logging.getLogger(name)


# Performance logging decorator

def log_performance(logger_name: str = 'performance'):
    """Decorator to log function execution time."""
    logger = get_logger(logger_name)
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                logger.info(
                    f"Function {func.__name__} completed",
                    extra={
                        'extra_data': {
                            'function': func.__name__,
                            'duration_seconds': round(duration, 4),
                            'status': 'success'
                        }
                    }
                )
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                
                logger.error(
                    f"Function {func.__name__} failed",
                    extra={
                        'extra_data': {
                            'function': func.__name__,
                            'duration_seconds': round(duration, 4),
                            'status': 'error',
                            'error': str(e)
                        }
                    }
                )
                raise
        
        return wrapper
    return decorator


# Request logging helper
class RequestLogger:
    """Helper for logging HTTP requests."""
    
    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or get_logger('requests')
    
    def log_request(self, method: str, path: str, status_code: int, 
                   duration_ms: float, user_id: str = None, 
                   error: str = None):
        """Log HTTP request with structured data."""
        log_data = {
            'event': 'http_request',
            'method': method,
            'path': path,
            'status_code': status_code,
            'duration_ms': round(duration_ms, 2)
        }
        
        if user_id:
            log_data['user_id'] = user_id
        
        if error:
            log_data['error'] = error
            self.logger.error('HTTP request failed', extra={'extra_data': log_data})
        elif status_code >= 400:
            self.logger.warning('HTTP request error', extra={'extra_data': log_data})
        else:
            self.logger.info('HTTP request', extra={'extra_data': log_data})


if __name__ == "__main__":
    # Test logging setup
    setup_logging('DEBUG')
    logger = get_logger('test')
    
    logger.info("Application starting")
    logger.warning("This is a warning")
    logger.error("This is an error", exc_info=False)
    
    # Test performance logging
    @log_performance()
    def test_function():
        time.sleep(0.1)
        return "result"
    
    test_function()
    
    # Test request logging
    request_logger = RequestLogger()
    request_logger.log_request('GET', '/api/simulate', 200, 150.5, user_id='user123')
    
    print("\nStructured logging configured!")
