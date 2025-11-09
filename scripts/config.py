"""
Configuration management for Kajabi import system.

This module handles all configuration, environment variables, and settings.
"""
import os
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class DatabaseConfig:
    """Database connection configuration."""
    url: str

    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        """Load database config from environment."""
        url = os.environ.get('DATABASE_URL')
        if not url:
            raise ValueError(
                "DATABASE_URL environment variable is required. "
                "Please set it in your .env file or environment."
            )
        return cls(url=url)


@dataclass
class ImportConfig:
    """Import process configuration."""
    batch_size: int = 1000
    max_retries: int = 3
    retry_backoff_seconds: int = 1
    default_currency: str = "USD"
    default_product_type: str = "course"

    # Payment status mapping
    status_mapping: Dict[str, str] = field(default_factory=lambda: {
        'succeeded': 'completed',
        'success': 'completed',
        'completed': 'completed',
        'pending': 'pending',
        'failed': 'failed',
        'failure': 'failed',
        'refunded': 'refunded',
        'refund': 'refunded',
        'disputed': 'disputed',
        'dispute': 'disputed',
    })

    @classmethod
    def from_env(cls) -> 'ImportConfig':
        """Load import config from environment."""
        return cls(
            batch_size=int(os.environ.get('KAJABI_BATCH_SIZE', 1000)),
            max_retries=int(os.environ.get('MAX_RETRIES', 3)),
            retry_backoff_seconds=int(os.environ.get('RETRY_BACKOFF_SECONDS', 1)),
        )


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    environment: str = "development"

    @classmethod
    def from_env(cls) -> 'LoggingConfig':
        """Load logging config from environment."""
        return cls(
            level=os.environ.get('LOG_LEVEL', 'INFO').upper(),
            environment=os.environ.get('ENVIRONMENT', 'development').lower(),
        )


@dataclass
class AppConfig:
    """Application configuration."""
    database: DatabaseConfig
    import_config: ImportConfig
    logging: LoggingConfig

    @classmethod
    def from_env(cls) -> 'AppConfig':
        """Load complete application config from environment."""
        return cls(
            database=DatabaseConfig.from_env(),
            import_config=ImportConfig.from_env(),
            logging=LoggingConfig.from_env(),
        )


# Global config instance (initialized on first use)
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """Get application configuration singleton."""
    global _config
    if _config is None:
        _config = AppConfig.from_env()
    return _config
