"""
GOD-TIER AUTOBUY STACK - Advanced Logger
Production-ready logging system with structured logging
"""

import logging
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger as loguru_logger

class AdvancedLogger:
    """
    Production-ready Advanced Logger
    Provides structured logging with multiple outputs
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config

        # Logging configuration
        logging_config = config.get('monitoring', {}).get('logging', {})
        self.log_level = logging_config.get('level', 'INFO')
        self.log_format = logging_config.get('format', 'json')
        self.log_file = logging_config.get('file', 'logs/autobuy.log')
        self.max_size = logging_config.get('max_size', '100MB')
        self.backup_count = logging_config.get('backup_count', 5)

        # Initialize logger
        self.setup_logging()

        # Performance tracking
        self.performance_metrics = {}

        self.info("Advanced Logger initialized")

    def setup_logging(self):
        """Setup logging configuration"""
        # Create logs directory
        Path(self.log_file).parent.mkdir(parents=True, exist_ok=True)

        # Remove default loguru handler
        loguru_logger.remove()

        # Console handler
        loguru_logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=self.log_level,
            colorize=True
        )

        # File handler
        loguru_logger.add(
            self.log_file,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level=self.log_level,
            rotation=self.max_size,
            retention=self.backup_count,
            compression="gz"
        )

        # JSON handler for structured logging
        json_log_file = self.log_file.replace('.log', '.json')
        loguru_logger.add(
            json_log_file,
            format=lambda record: json.dumps({
                "timestamp": record["time"].isoformat(),
                "level": record["level"].name,
                "logger": record["name"],
                "function": record["function"],
                "line": record["line"],
                "message": record["message"],
                "extra": record.get("extra", {})
            }) + "\n",
            level=self.log_level,
            rotation=self.max_size,
            retention=self.backup_count
        )

    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log debug message"""
        self._log("DEBUG", message, extra)

    def info(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log info message"""
        self._log("INFO", message, extra)

    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log warning message"""
        self._log("WARNING", message, extra)

    def error(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log error message"""
        self._log("ERROR", message, extra)

    def critical(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log critical message"""
        self._log("CRITICAL", message, extra)

    def _log(self, level: str, message: str, extra: Optional[Dict[str, Any]] = None):
        """Internal logging method"""
        if extra:
            loguru_logger.bind(**extra).log(level, message)
        else:
            loguru_logger.log(level, message)

    def log_performance(self, operation: str, duration: float, extra: Optional[Dict[str, Any]] = None):
        """Log performance metrics"""
        perf_data = {
            "operation": operation,
            "duration": duration,
            "timestamp": datetime.now().isoformat()
        }

        if extra:
            perf_data.update(extra)

        self.info(f"Performance: {operation} took {duration:.2f}s", perf_data)

        # Store for metrics
        self.performance_metrics[operation] = {
            "duration": duration,
            "timestamp": datetime.now()
        }

    def log_task_start(self, task_id: str, task_type: str, parameters: Dict[str, Any]):
        """Log task start"""
        self.info(
            f"Task started: {task_id}",
            {
                "task_id": task_id,
                "task_type": task_type,
                "parameters": parameters,
                "event": "task_start"
            }
        )

    def log_task_complete(self, task_id: str, result: Dict[str, Any]):
        """Log task completion"""
        self.info(
            f"Task completed: {task_id}",
            {
                "task_id": task_id,
                "result": result,
                "event": "task_complete"
            }
        )

    def log_task_error(self, task_id: str, error: str):
        """Log task error"""
        self.error(
            f"Task failed: {task_id}",
            {
                "task_id": task_id,
                "error": error,
                "event": "task_error"
            }
        )

    def log_browser_action(self, action: str, selector: str, result: bool, extra: Optional[Dict[str, Any]] = None):
        """Log browser automation action"""
        log_data = {
            "action": action,
            "selector": selector,
            "result": result,
            "event": "browser_action"
        }

        if extra:
            log_data.update(extra)

        level = "INFO" if result else "WARNING"
        message = f"Browser action: {action} on {selector} - {'Success' if result else 'Failed'}"

        self._log(level, message, log_data)

    def log_api_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Log API request"""
        self.info(
            f"API {method} {endpoint} - {status_code} ({duration:.2f}s)",
            {
                "method": method,
                "endpoint": endpoint,
                "status_code": status_code,
                "duration": duration,
                "event": "api_request"
            }
        )

    def log_security_event(self, event_type: str, details: Dict[str, Any]):
        """Log security event"""
        self.warning(
            f"Security event: {event_type}",
            {
                "event_type": event_type,
                "details": details,
                "event": "security"
            }
        )

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return self.performance_metrics.copy()

    def clear_performance_metrics(self):
        """Clear performance metrics"""
        self.performance_metrics.clear()
        self.info("Performance metrics cleared")


class MetricsCollector:
    """
    Production-ready Metrics Collector
    Collects and exposes metrics for monitoring
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = AdvancedLogger(config)

        # Metrics storage
        self.metrics = {
            "requests_total": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "browser_actions": 0,
            "api_calls": 0,
            "errors": 0
        }

        self.logger.info("Metrics Collector initialized")

    async def start_collection(self):
        """Start metrics collection"""
        self.logger.info("Metrics collection started")

    def increment_metric(self, metric_name: str, value: int = 1):
        """Increment metric"""
        if metric_name in self.metrics:
            self.metrics[metric_name] += value
            self.logger.debug(f"Metric incremented: {metric_name} = {self.metrics[metric_name]}")

    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics"""
        return self.metrics.copy()

    def reset_metrics(self):
        """Reset all metrics"""
        self.metrics = {key: 0 for key in self.metrics}
        self.logger.info("Metrics reset")
